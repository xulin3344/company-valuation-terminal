import pandas as pd

from .base import FinancialProvider, ProviderError
from ..models import RawFinancials

UNIT_SCALE_YUAN_TO_MILLION = 1e-6


def normalize_hk_ticker(ticker: str) -> str:
    code = ticker.split(".")[0].strip()
    return code.zfill(5)


def normalize_cn_ticker(ticker: str) -> tuple[str, str]:
    """标准化 A 股代码：返回 (6位纯数字代码, 带交易所前缀小写代码如 sz002036)。"""
    raw = str(ticker).strip()
    digits = "".join(filter(str.isdigit, raw))
    if len(digits) == 6:
        code = digits
    else:
        # 若不是6位数字，尝试智能名称/拼音解析
        try:
            from ..stock_lookup import resolve_stock
            res = resolve_stock(raw, preferred_market="CN")
            if res and res.get("ticker") and len(res["ticker"]) == 6:
                code = res["ticker"]
            else:
                code = raw.split(".")[0].strip().lower()
        except Exception:
            code = raw.split(".")[0].strip().lower()

    if len(code) == 6 and code.isdigit():
        if code.startswith(("6", "9", "688")):
            prefix = "sh"
        elif code.startswith(("8", "4", "920")):
            prefix = "bj"
        else:
            prefix = "sz"
        return code, f"{prefix}{code}"

    return code, code



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


def cn_sina_to_raw(ticker: str, income_df, balance_df, cashflow_df, price=None) -> RawFinancials:
    """将新浪 A 股宽表财报转换为 RawFinancials 格式。"""
    income_series = {}
    labels = []
    if income_df is not None and not income_df.empty:
        date_col = income_df.columns[0]
        # 筛选年度报告（以 1231 结尾）
        annual_p = income_df[income_df[date_col].astype(str).str.endswith("1231")].copy()
        annual_p = annual_p.sort_values(by=date_col).tail(5)  # 取最近最多5年
        dates = annual_p[date_col].astype(str).tolist()
        labels = [f"{d[:4]}-12-31" for d in dates]
        for col in annual_p.columns:
            if col == date_col:
                continue
            vals = []
            for v in annual_p[col]:
                try:
                    vals.append(float(v) if pd.notna(v) else None)
                except Exception:
                    vals.append(None)
            income_series[str(col).strip()] = vals

    merged = dict(income_series)

    # 现金流量表
    if cashflow_df is not None and not cashflow_df.empty:
        c_date_col = cashflow_df.columns[0]
        annual_c = cashflow_df[cashflow_df[c_date_col].astype(str).str.endswith("1231")].copy()
        annual_c = annual_c.sort_values(by=c_date_col).tail(len(labels) if labels else 5)
        for col in annual_c.columns:
            if col == c_date_col:
                continue
            clean_name = str(col).strip()
            vals = []
            for v in annual_c[col]:
                try:
                    vals.append(float(v) if pd.notna(v) else None)
                except Exception:
                    vals.append(None)
            key = clean_name if clean_name not in merged else f"{clean_name}（现金流量表）"
            merged[key] = vals

    # 资产负债表：取最新一期报告（含最新季度/半年报快照）
    balance = {}
    if balance_df is not None and not balance_df.empty:
        b_date_col = balance_df.columns[0]
        latest_row_b = balance_df.sort_values(by=b_date_col).iloc[-1]
        for col in balance_df.columns:
            if col == b_date_col:
                continue
            clean_name = str(col).strip()
            try:
                v = latest_row_b[col]
                if pd.notna(v):
                    balance[clean_name] = float(v)
            except Exception:
                pass

    return RawFinancials(
        market="CN",
        ticker=ticker,
        currency="CNY",
        unit_scale=UNIT_SCALE_YUAN_TO_MILLION,
        income=merged,
        balance=balance,
        price=price,
        period_labels=labels or None,
        source="akshare",
    )


class AkshareProvider(FinancialProvider):
    name = "akshare"

    def __init__(self, market: str = None):
        self.market = str(market).upper() if market else None

    def fetch(self, ticker: str) -> RawFinancials:
        try:
            import akshare as ak
        except ImportError as exc:
            raise ProviderError(f"akshare not installed: {exc}")

        # 判断是否为 A 股
        is_cn = False
        digits = "".join(filter(str.isdigit, str(ticker)))
        if self.market == "CN":
            is_cn = True
        elif self.market is None and len(digits) == 6 and not str(ticker).upper().endswith(".HK"):
            is_cn = True

        if is_cn:
            return self._fetch_cn(ak, ticker)
        return self._fetch_hk(ak, ticker)

    def _fetch_cn(self, ak, ticker: str) -> RawFinancials:
        code, symbol_with_prefix = normalize_cn_ticker(ticker)
        income_df = self._try(ak.stock_financial_report_sina, stock=code, symbol="利润表")
        balance_df = self._try(ak.stock_financial_report_sina, stock=code, symbol="资产负债表")
        cashflow_df = self._try(ak.stock_financial_report_sina, stock=code, symbol="现金流量表")
        if income_df is None and balance_df is None and cashflow_df is None:
            raise ProviderError(f"akshare returned no report data for A-share {code}")
        price = self._fetch_price_cn(ak, symbol_with_prefix, code)
        return cn_sina_to_raw(code, income_df, balance_df, cashflow_df, price=price)

    def _fetch_hk(self, ak, ticker: str) -> RawFinancials:
        code = normalize_hk_ticker(ticker)
        income_df = self._try(ak.stock_financial_hk_report_em, stock=code, symbol="利润表", indicator="年度")
        balance_df = self._try(ak.stock_financial_hk_report_em, stock=code, symbol="资产负债表", indicator="年度")
        cashflow_df = self._try(ak.stock_financial_hk_report_em, stock=code, symbol="现金流量表", indicator="年度")
        if income_df is None and balance_df is None and cashflow_df is None:
            raise ProviderError(f"akshare returned no report data for {code}")
        price = self._fetch_price_hk(ak, code)
        return hk_frames_to_raw(ticker, income_df, balance_df, cashflow_df, price=price)

    @staticmethod
    def _try(func, **kwargs):
        try:
            return func(**kwargs)
        except Exception:
            return None

    @staticmethod
    def _fetch_price_hk(ak, code):
        try:
            daily = ak.stock_hk_daily(symbol=code)
            if daily is not None and not daily.empty and "close" in daily.columns:
                close = pd.to_numeric(daily["close"], errors="coerce").dropna()
                if not close.empty:
                    return float(close.iloc[-1])
        except Exception:
            pass
        return None

    @staticmethod
    def _fetch_price_cn(ak, symbol_with_prefix: str, code: str):
        try:
            daily = ak.stock_zh_a_daily(symbol=symbol_with_prefix)
            if daily is not None and not daily.empty and "close" in daily.columns:
                close = pd.to_numeric(daily["close"], errors="coerce").dropna()
                if not close.empty:
                    return float(close.iloc[-1])
        except Exception:
            pass
        # 尝试历史K线备用
        try:
            hist = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            if hist is not None and not hist.empty and "收盘" in hist.columns:
                close = pd.to_numeric(hist["收盘"], errors="coerce").dropna()
                if not close.empty:
                    return float(close.iloc[-1])
        except Exception:
            pass
        return None

