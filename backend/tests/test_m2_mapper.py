import pytest

from app.data.mapper import AccountMapper, normalize_name
from app.data.models import RawFinancials
from app.data.pipeline import load_mapper


@pytest.fixture(scope="module")
def hk_mapper():
    return load_mapper("HK")


@pytest.fixture(scope="module")
def us_mapper():
    return load_mapper("US")


def test_normalize_name_strips_spaces_and_case():
    assert normalize_name("Total  Revenue ") == normalize_name("totalrevenue")
    assert normalize_name("Ｔotal Revenue") == normalize_name("total revenue")


def test_hk_synonym_matching(hk_mapper):
    assert hk_mapper.map_name("营业额") == "revenue"
    assert hk_mapper.map_name("经营溢利") == "ebit"
    assert hk_mapper.map_name("股东应占溢利") == "net_income"
    assert hk_mapper.map_name("折旧及摊销") == "da"
    assert hk_mapper.map_name("未知科目xyz") is None


def test_us_synonym_matching(us_mapper):
    assert us_mapper.map_name("Total Revenue") == "revenue"
    assert us_mapper.map_name("TOTAL  REVENUE") == "revenue"
    assert us_mapper.map_name("Operating Income") == "ebit"
    assert us_mapper.map_name("Net Income Common Stockholders") == "net_income"


def test_ifrs16_lease_debt_inclusion(hk_mapper):
    raw = RawFinancials(market="HK", balance={"借款": 2000.0, "租赁负债": 500.0})
    std = hk_mapper.standardize(raw)
    assert std.balance["debt"] == pytest.approx(2500.0, abs=1e-6)


def test_hk_without_lease_account_unchanged(hk_mapper):
    raw = RawFinancials(market="HK", balance={"借款": 2000.0})
    std = hk_mapper.standardize(raw)
    assert std.balance["debt"] == pytest.approx(2000.0, abs=1e-6)


def test_us_lease_excluded_from_debt(us_mapper):
    raw = RawFinancials(market="US", balance={"Long Term Debt": 2000.0, "Lease liabilities": 500.0})
    std = us_mapper.standardize(raw)
    assert std.balance["debt"] == pytest.approx(2000.0, abs=1e-6)


def test_multi_account_summation(us_mapper):
    raw = RawFinancials(
        market="US",
        balance={
            "Cash And Cash Equivalents": 1000.0,
            "Other Short Term Investments": 500.0,
            "Long Term Debt": 1000.0,
            "Current Debt": 300.0,
        },
    )
    std = us_mapper.standardize(raw)
    assert std.balance["cash"] == pytest.approx(1500.0, abs=1e-6)
    assert std.balance["debt"] == pytest.approx(1300.0, abs=1e-6)


def test_unit_scale_conversion(hk_mapper):
    raw = RawFinancials(market="HK", unit_scale=1e3, income={"营业额": [100.0, 110.0]})
    std = hk_mapper.standardize(raw)
    assert std.income["revenue"] == pytest.approx([100000.0, 110000.0], rel=1e-9)


def test_derivation_chain_full(hk_mapper):
    raw = RawFinancials(
        market="HK",
        income={
            "营业额": [37120.0],
            "销售成本": [10355.0],
            "销售及分销开支": [8082.0],
            "一般及行政开支": [2150.0],
            "折旧及摊销": [1800.0],
        },
    )
    std = hk_mapper.standardize(raw)
    assert std.income["gross_profit"] == pytest.approx([26765.0], rel=1e-6)
    assert std.income["ebit"] == pytest.approx([16533.0], rel=1e-6)
    assert std.income["ebitda"] == pytest.approx([18333.0], rel=1e-6)
    for account in ("gross_profit", "ebit", "ebitda"):
        assert account in std.derived


def test_derivation_reverse_da(hk_mapper):
    raw = RawFinancials(
        market="HK",
        income={"经营溢利": [16533.0], "EBITDA": [18333.0]},
    )
    std = hk_mapper.standardize(raw)
    assert std.income["da"] == pytest.approx([1800.0], rel=1e-6)
    assert "da" in std.derived


def test_derivation_with_rd_expense(hk_mapper):
    raw = RawFinancials(
        market="HK",
        income={
            "营业额": [1000.0],
            "销售成本": [400.0],
            "销售及分销开支": [200.0],
            "一般及行政开支": [100.0],
            "研发费用": [50.0],
        },
    )
    std = hk_mapper.standardize(raw)
    assert std.income["ebit"] == pytest.approx([250.0], rel=1e-6)


def test_derivation_pretax_to_net_income(hk_mapper):
    raw = RawFinancials(market="HK", income={"除税前溢利": [1000.0], "所得税开支": [230.0]})
    std = hk_mapper.standardize(raw)
    assert std.income["net_income"] == pytest.approx([770.0], rel=1e-6)


def test_net_debt_property(hk_mapper):
    raw = RawFinancials(market="HK", balance={"借款": 2500.0, "现金及现金等价物": 17500.0})
    std = hk_mapper.standardize(raw)
    assert std.net_debt == pytest.approx(-15000.0, abs=1e-6)


def test_eps_diluted_not_scaled(hk_mapper):
    raw = RawFinancials(market="HK", unit_scale=1e-6, income={"每股摊薄盈利": [9.58]})
    std = hk_mapper.standardize(raw)
    assert std.income["eps_diluted"] == pytest.approx([9.58], rel=1e-9)


def test_shares_derived_from_eps_in_million_scale(hk_mapper):
    raw = RawFinancials(
        market="HK",
        unit_scale=1e-6,
        income={"每股摊薄盈利": [9.58], "股东应占溢利": [12775689000.0]},
    )
    std = hk_mapper.standardize(raw)
    shares = std.balance["shares_diluted"]
    assert shares == pytest.approx(12775.689 / 9.58, rel=1e-3)
    assert "shares_diluted" in std.derived
    assert shares < 1e6


def test_load_mapper_unsupported_market():
    with pytest.raises(ValueError):
        load_mapper("JP")


def test_income_series_alignment_unequal_lengths(hk_mapper):
    raw = RawFinancials(
        market="HK",
        income={"营业额": [10.0, 12.0], "毛利": [5.0]},
    )
    std = hk_mapper.standardize(raw)
    assert len(std.income["revenue"]) == 2
    assert len(std.income["gross_profit"]) == 1
    assert std.periods == ["FY-2", "FY-1"]