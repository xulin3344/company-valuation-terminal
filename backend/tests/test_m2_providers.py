import pandas as pd
import pytest

from app.data.providers.akshare_provider import (
    hk_frames_to_raw,
    hk_long_frame_to_latest,
    hk_long_frame_to_series,
    normalize_hk_ticker,
)
from app.data.providers.base import FinancialProvider, ProviderError, fetch_with_fallback
from app.data.providers.manual import ManualProvider
from app.data.providers.yfinance_provider import yf_frame_to_series, yf_frames_to_raw


class ExplodingProvider(FinancialProvider):
    name = "exploding"

    def fetch(self, ticker):
        raise RuntimeError("network down")


class WorkingProvider(FinancialProvider):
    name = "working"

    def fetch(self, ticker):
        return "raw-ok"


def test_normalize_hk_ticker():
    assert normalize_hk_ticker("09992.HK") == "09992"
    assert normalize_hk_ticker("00992") == "00992"
    assert normalize_hk_ticker("992") == "00992"


def test_fetch_with_fallback_returns_first_success():
    result = fetch_with_fallback([ExplodingProvider(), WorkingProvider()], "X")
    assert result == "raw-ok"


def test_fetch_with_fallback_all_fail():
    from app.data.providers.base import _cache
    _cache.clear()  # 清除上一个测试缓存的结果
    with pytest.raises(ProviderError) as excinfo:
        fetch_with_fallback([ExplodingProvider(), ExplodingProvider()], "X")
    assert "exploding" in str(excinfo.value)


def test_detect_unit_scale_removed():
    pass


def test_akshare_long_frame_to_series_orders_oldest_first():
    df = pd.DataFrame({
        "REPORT_DATE": ["2025-12-31", "2024-12-31", "2025-12-31", "2024-12-31"],
        "STD_ITEM_NAME": ["营业额", "营业额", "经营溢利", "经营溢利"],
        "AMOUNT": [37120052000.0, 13038000000.0, 16533000000.0, 3911000000.0],
    })
    series, labels = hk_long_frame_to_series(df)
    assert labels == ["2024-12-31", "2025-12-31"]
    assert series["营业额"] == pytest.approx([13038000000.0, 37120052000.0], rel=1e-9)
    assert series["经营溢利"] == pytest.approx([3911000000.0, 16533000000.0], rel=1e-9)


def test_akshare_long_frame_missing_period_becomes_none():
    df = pd.DataFrame({
        "REPORT_DATE": ["2025-12-31", "2024-12-31"],
        "STD_ITEM_NAME": ["营业额", "经营溢利"],
        "AMOUNT": [37120052000.0, 3911000000.0],
    })
    series, labels = hk_long_frame_to_series(df)
    assert labels == ["2024-12-31", "2025-12-31"]
    assert series["营业额"][0] is None and series["营业额"][1] == pytest.approx(37120052000.0, rel=1e-9)
    assert series["经营溢利"][0] == pytest.approx(3911000000.0, rel=1e-9) and series["经营溢利"][1] is None


def test_akshare_long_frame_to_latest_picks_max_date():
    df = pd.DataFrame({
        "REPORT_DATE": ["2024-12-31", "2025-12-31", "2025-12-31"],
        "STD_ITEM_NAME": ["现金及现金等价物", "现金及现金等价物", "借款"],
        "AMOUNT": [15000000000.0, 17500000000.0, 2500000000.0],
    })
    balance = hk_long_frame_to_latest(df)
    assert balance["现金及现金等价物"] == pytest.approx(17500000000.0, rel=1e-9)
    assert balance["借款"] == pytest.approx(2500000000.0, rel=1e-9)


def test_akshare_frames_to_raw_end_to_end():
    income_df = pd.DataFrame({
        "REPORT_DATE": ["2024-12-31", "2025-12-31"],
        "STD_ITEM_NAME": ["营业额", "营业额"],
        "AMOUNT": [13038000000.0, 37120052000.0],
    })
    balance_df = pd.DataFrame({
        "REPORT_DATE": ["2025-12-31", "2025-12-31"],
        "STD_ITEM_NAME": ["现金及现金等价物", "借款"],
        "AMOUNT": [17500000000.0, 2500000000.0],
    })
    cashflow_df = pd.DataFrame({
        "REPORT_DATE": ["2024-12-31", "2025-12-31"],
        "STD_ITEM_NAME": ["折旧及摊销", "折旧及摊销"],
        "AMOUNT": [950000000.0, 1800000000.0],
    })
    raw = hk_frames_to_raw("00992", income_df, balance_df, cashflow_df, price=143.0)
    assert raw.unit_scale == pytest.approx(1e-6, abs=1e-12)
    assert raw.source == "akshare"
    assert raw.period_labels == ["2024-12-31", "2025-12-31"]
    assert raw.balance["借款"] == pytest.approx(2500000000.0, rel=1e-9)


def test_yfinance_frame_to_series_orders_oldest_first():
    cols = [pd.Timestamp("2025-12-31"), pd.Timestamp("2024-12-31")]
    df = pd.DataFrame(
        [[37120.0, 13038.0], [16533.0, 3911.0]],
        index=["Total Revenue", "Operating Income"],
        columns=cols,
    )
    series, labels = yf_frame_to_series(df)
    assert [label[:10] for label in labels] == ["2024-12-31", "2025-12-31"]
    assert series["Total Revenue"] == pytest.approx([13038.0, 37120.0], rel=1e-9)


def test_yfinance_frames_to_raw_end_to_end():
    cols = [pd.Timestamp("2025-12-31"), pd.Timestamp("2024-12-31")]
    income_df = pd.DataFrame(
        [[37120.0, 13038.0]],
        index=["Total Revenue"],
        columns=cols,
    )
    balance_df = pd.DataFrame(
        [[1000.0, 800.0]],
        index=["Cash And Cash Equivalents"],
        columns=cols,
    )
    cashflow_df = pd.DataFrame(
        [[11.0, 9.0]],
        index=["Depreciation Amortization Depletion"],
        columns=cols,
    )
    raw = yf_frames_to_raw("AAPL", income_df, balance_df, cashflow_df, price=250.0, currency="USD")
    assert raw.currency == "USD"
    assert raw.income["Total Revenue"] == pytest.approx([13038.0, 37120.0], rel=1e-9)
    assert raw.balance["Cash And Cash Equivalents"] == pytest.approx(1000.0, abs=1e-9)
    assert raw.price == pytest.approx(250.0, abs=1e-9)


def test_manual_provider_passthrough():
    data = {
        "market": "HK",
        "currency": "CNY",
        "price": 143.0,
        "income": {"营业额": [1.0]},
        "balance": {"借款": 2.0},
    }
    raw = ManualProvider(data).fetch("00992")
    assert raw.market == "HK"
    assert raw.income["营业额"] == [1.0]
    assert raw.balance["借款"] == 2.0
    assert raw.source == "manual"