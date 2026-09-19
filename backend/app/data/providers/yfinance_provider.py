import time as _time

import pandas as pd

from .base import FinancialProvider, ProviderError
from ..models import RawFinancials


def yf_frame_to_series(df):
    if df is None or df.empty:
        return {}, []
    columns = list(df.columns)
    try:
        parsed = pd.to_datetime([str(c) for c in columns], errors="coerce")
        if not all(pd.isna(p) for p in parsed):
            order = sorted(range(len(columns)), key=lambda i: parsed[i])
            columns = [columns[i] for i in order]
    except Exception:
        pass
    series = {}
    for index, row in df.iterrows():
        name = str(index).strip()
        if not name or name in series:
            continue
        values = []
        for column in columns:
            raw = pd.to_numeric(row[column], errors="coerce")
            values.append(None if pd.isna(raw) else float(raw))
        series[name] = values
    return series, [str(c) for c in columns]


def yf_frame_to_latest(df):
    if df is None or df.empty:
        return {}
    latest_col = df.columns[0]
    balance = {}
    for index, row in df.iterrows():
        name = str(index).strip()
        if not name or name in balance:
            continue
        raw = pd.to_numeric(row[latest_col], errors="coerce")
        if not pd.isna(raw):
            balance[name] = float(raw)
    return balance


def yf_frames_to_raw(ticker: str, income_df, balance_df, cashflow_df, price=None, currency="USD") -> RawFinancials:
    income_series, labels = yf_frame_to_series(income_df)
    cash_series, _ = yf_frame_to_series(cashflow_df)
    merged = dict(income_series)
    for name, values in cash_series.items():
        key = name if name not in merged else f"{name}（现金流量表）"
        merged[key] = values
    balance = yf_frame_to_latest(balance_df)
    return RawFinancials(
        market="US",
        ticker=ticker,
        currency=currency,
        unit_scale=1e-6,
        income=merged,
        balance=balance,
        price=price,
        period_labels=labels or None,
        source="yfinance",
    )


class YFinanceProvider(FinancialProvider):
    name = "yfinance"
    MAX_RETRIES = 2
    RETRY_DELAY = 1.5  # 秒，指数退避基数

    def fetch(self, ticker: str) -> RawFinancials:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ProviderError(f"yfinance not installed: {exc}")

        income_df = balance_df = cashflow_df = None
        last_exc = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                t = yf.Ticker(ticker, session=self._make_session())
                income_df = self._safe(getattr, (t, "income_stmt"))
                balance_df = self._safe(getattr, (t, "balance_sheet"))
                cashflow_df = self._safe(getattr, (t, "cashflow"))
            except Exception as exc:
                last_exc = exc
                if attempt < self.MAX_RETRIES:
                    _time.sleep(self.RETRY_DELAY * (2 ** attempt))
                continue

            income_empty = income_df is None or getattr(income_df, "empty", True)
            balance_empty = balance_df is None or getattr(balance_df, "empty", True)
            if income_empty and balance_empty:
                last_exc = ProviderError(f"yfinance returned no statement data for {ticker}")
                if attempt < self.MAX_RETRIES:
                    _time.sleep(self.RETRY_DELAY * (2 ** attempt))
                continue
            break  # 成功获取数据
        else:
            raise ProviderError(
                f"yfinance failed after {self.MAX_RETRIES + 1} attempts for {ticker} "
                f"(likely rate-limited by Yahoo): {last_exc}"
            )

        price = self._safe_price(t)
        currency = "USD"
        try:
            info = t.info or {}
            currency = info.get("financialCurrency") or "USD"
        except Exception:
            pass
        return yf_frames_to_raw(ticker, income_df, balance_df, cashflow_df, price=price, currency=currency)

    @staticmethod
    def _make_session():
        try:
            import requests
            s = requests.Session()
            s.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            })
            return s
        except Exception:
            return None

    @staticmethod
    def _safe(getter, args):
        try:
            return getter(*args)
        except Exception:
            return None

    @staticmethod
    def _safe_price(ticker_obj):
        try:
            fast = ticker_obj.fast_info
            price = fast["last_price"] if hasattr(fast, "__getitem__") else None
            if price:
                return float(price)
        except Exception:
            pass
        try:
            info = ticker_obj.info or {}
            if info.get("currentPrice"):
                return float(info["currentPrice"])
        except Exception:
            pass
        return None