import pandas as pd

from .base import FinancialProvider, ProviderError
from ..models import RawFinancials

UNIT_SCALE_YUAN_TO_MILLION = 1e-6


def normalize_hk_ticker(ticker: str) -> str:
    code = ticker.split(".")[0].strip()
    return code.zfill(5)


def _prepare_long_frame(df):
    if df is None or df.empty:
        return None
    required = {"REPORT_DATE", "STD_ITEM_NAME", "AMOUNT"}
    if not required.issubset(set(df.columns)):
        return None
    work = df.copy()
    work["_date"] = pd.to_datetime(work["REPORT_DATE"], errors="coerce")
    work["_amt"] = pd.to_numeric(work["AMOUNT"], errors="coerce")
    work = work.dropna(subset=["_date"])
    return work if not work.empty else None


def hk_long_frame_to_series(df):
    work = _prepare_long_frame(df)
    if work is None:
        return {}, []
    dates = sorted(work["_date"].unique())
    labels = [str(pd.Timestamp(d).date()) for d in dates]
    series = {}
    for name, group in work.groupby("STD_ITEM_NAME"):
        clean_name = str(name).strip()
        if not clean_name:
            continue
        by_date = dict(zip(group["_date"], group["_amt"]))
        values = []
        for d in dates:
            raw = by_date.get(d)
            if raw is None or pd.isna(raw):
                values.append(None)
            else:
                values.append(float(raw))
        series[clean_name] = values
    return series, labels


def hk_long_frame_to_latest(df):
    work = _prepare_long_frame(df)
    if work is None:
        return {}
    work = work.dropna(subset=["_amt"])
    if work.empty:
        return {}
    latest = work["_date"].max()
    balance = {}
    for _, row in work[work["_date"] == latest].iterrows():
        name = str(row["STD_ITEM_NAME"]).strip()
        if name and name not in balance:
            balance[name] = float(row["_amt"])
    return balance


HK_CURRENCY_HINTS = {
    "CNY": ["人民币", "rmb", "RMB", "元(人民币)"],
    "HKD": ["港元", "港币", "hkd", "HKD", "HK$"],
}


def _infer_hk_currency(income_series: dict) -> str:
    """从报表科目名启发式推断币种，默认 CNY（大多数港股以人民币编制报表）。"""
    all_names = " ".join(str(k) for k in income_series.keys())
    for currency, hints in HK_CURRENCY_HINTS.items():
        if any(h in all_names for h in hints):
            return currency
    return "CNY"


def hk_frames_to_raw(ticker: str, income_df, balance_df, cashflow_df, price=None) -> RawFinancials:
    income, labels = hk_long_frame_to_series(income_df)
    cash_series, _ = hk_long_frame_to_series(cashflow_df)
    merged = dict(income)
    for name, values in cash_series.items():
        key = name if name not in merged else f"{name}（现金流量表）"
        merged[key] = values
    balance = hk_long_frame_to_latest(balance_df)
    currency = _infer_hk_currency({**merged, **balance})
    return RawFinancials(
        market="HK",
        ticker=ticker,
        currency=currency,
        unit_scale=UNIT_SCALE_YUAN_TO_MILLION,
        income=merged,
        balance=balance,
        price=price,
        period_labels=labels or None,
        source="akshare",
    )


class AkshareProvider(FinancialProvider):
    name = "akshare"

    def fetch(self, ticker: str) -> RawFinancials:
        try:
            import akshare as ak
        except ImportError as exc:
            raise ProviderError(f"akshare not installed: {exc}")
        code = normalize_hk_ticker(ticker)
        income_df = self._try(ak.stock_financial_hk_report_em, stock=code, symbol="利润表", indicator="年度")
        balance_df = self._try(ak.stock_financial_hk_report_em, stock=code, symbol="资产负债表", indicator="年度")
        cashflow_df = self._try(ak.stock_financial_hk_report_em, stock=code, symbol="现金流量表", indicator="年度")
        if income_df is None and balance_df is None and cashflow_df is None:
            raise ProviderError(f"akshare returned no report data for {code}")
        price = self._fetch_price(ak, code)
        return hk_frames_to_raw(ticker, income_df, balance_df, cashflow_df, price=price)

    @staticmethod
    def _try(func, **kwargs):
        try:
            return func(**kwargs)
        except Exception:
            return None

    @staticmethod
    def _fetch_price(ak, code):
        try:
            daily = ak.stock_hk_daily(symbol=code)
            if daily is not None and not daily.empty and "close" in daily.columns:
                close = pd.to_numeric(daily["close"], errors="coerce").dropna()
                if not close.empty:
                    return float(close.iloc[-1])
        except Exception:
            pass
        return None
