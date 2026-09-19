import pytest

from app.data.pipeline import analyze


POP_MART_MANUAL = {
    "market": "HK",
    "currency": "CNY",
    "price": 143.0,
    "period_labels": ["FY2024", "FY2025"],
    "income": {
        "营业额": [13038.0, 37120.0],
        "毛利": [8708.0, 26765.0],
        "经营溢利": [3911.0, 16533.0],
        "股东应占溢利": [None, 12730.0],
        "折旧及摊销": [950.0, 1800.0],
        "购置物业厂房及设备": [1100.0, 2200.0],
    },
    "balance": {
        "现金及现金等价物": 17500.0,
        "借款": 2500.0,
        "已发行股份": 1343.0,
    },
}


@pytest.fixture(scope="module")
def popmart_std():
    return analyze("00992", "HK", manual_data=POP_MART_MANUAL)


def test_standardize_key_accounts(popmart_std):
    assert popmart_std.income["revenue"] == pytest.approx([13038.0, 37120.0], rel=1e-9)
    assert popmart_std.latest("ebit") == pytest.approx(16533.0, rel=1e-9)
    assert popmart_std.latest("net_income") == pytest.approx(12730.0, rel=1e-9)
    assert popmart_std.balance["debt"] == pytest.approx(2500.0, abs=1e-6)
    assert popmart_std.balance["shares_diluted"] == pytest.approx(1343.0, abs=1e-6)
    assert popmart_std.price == pytest.approx(143.0, abs=1e-9)


def test_ebitda_derived_matches_template(popmart_std):
    assert popmart_std.latest("ebitda") == pytest.approx(18333.0, rel=1e-6)
    assert "ebitda" in popmart_std.derived


def test_net_debt_matches_template(popmart_std):
    assert popmart_std.net_debt == pytest.approx(-15000.0, abs=1e-6)


def test_quality_good_when_complete(popmart_std):
    report = popmart_std.quality
    assert report.health == "good"
    assert all(not miss for miss in report.missing.values())
    assert report.degraded_models == []


def test_quality_partial_when_capex_missing():
    data = {
        "market": "HK",
        "currency": "CNY",
        "price": 10.0,
        "income": {
            "营业额": [100.0, 120.0],
            "经营溢利": [20.0, 24.0],
            "折旧及摊销": [5.0, 6.0],
        },
        "balance": {"现金及现金等价物": 50.0, "借款": 10.0, "已发行股份": 100.0},
    }
    std = analyze("TEST", "HK", manual_data=data)
    assert "capex" in std.quality.missing["dcf"]
    assert std.quality.health == "partial"


def test_quality_poor_when_everything_missing():
    std = analyze("TEST", "HK", manual_data={"market": "HK", "income": {}, "balance": {}})
    assert std.quality.health == "poor"


def test_quality_flags_lossemaker():
    data = {
        "market": "HK",
        "currency": "CNY",
        "price": 10.0,
        "income": {
            "营业额": [100.0, 120.0],
            "经营溢利": [20.0, 24.0],
            "折旧及摊销": [5.0, 6.0],
            "购置物业厂房及设备": [4.0, 5.0],
            "股东应占溢利": [-30.0, -50.0],
        },
        "balance": {"现金及现金等价物": 50.0, "借款": 10.0, "已发行股份": 100.0},
    }
    std = analyze("LOSS", "HK", manual_data=data)
    degraded = dict(std.quality.degraded_models)
    assert degraded.get("comps_pe") == "net_income <= 0"


def test_quality_flags_negative_ebitda():
    data = {
        "market": "HK",
        "currency": "CNY",
        "price": 10.0,
        "income": {
            "营业额": [100.0, 120.0],
            "经营溢利": [-60.0, -80.0],
            "折旧及摊销": [5.0, 6.0],
            "购置物业厂房及设备": [4.0, 5.0],
            "股东应占溢利": [-30.0, -50.0],
        },
        "balance": {"现金及现金等价物": 50.0, "借款": 10.0, "已发行股份": 100.0},
    }
    std = analyze("NEGE", "HK", manual_data=data)
    degraded = dict(std.quality.degraded_models)
    assert degraded.get("comps_ev_ebitda") == "ebitda <= 0"