"""A 股 (CN) 自动化估值链路单元测试。"""
import pytest

from app.data.providers.akshare_provider import normalize_cn_ticker
from app.data.providers.yfinance_provider import normalize_yf_ticker
from app.data.pipeline import load_mapper, analyze, build_engine_inputs, build_forecast_assumptions
from app.data.models import RawFinancials



def test_normalize_cn_ticker():
    # 深圳股票代码
    code, sym = normalize_cn_ticker("002036")
    assert code == "002036"
    assert sym == "sz002036"

    # 上海主板代码
    code, sym = normalize_cn_ticker("600519")
    assert code == "600519"
    assert sym == "sh600519"

    # 科创板代码
    code, sym = normalize_cn_ticker("688981")
    assert code == "688981"
    assert sym == "sh688981"

    # 带后缀或前缀代码
    code, sym = normalize_cn_ticker("002036.SZ")
    assert code == "002036"
    assert sym == "sz002036"

    code, sym = normalize_cn_ticker("SH600519")
    assert code == "600519"
    assert sym == "sh600519"


def test_normalize_yf_ticker():
    yf_t, market, curr = normalize_yf_ticker("002036", "CN")
    assert yf_t == "002036.SZ"
    assert market == "CN"
    assert curr == "CNY"

    yf_t, market, curr = normalize_yf_ticker("600519", "CN")
    assert yf_t == "600519.SS"
    assert market == "CN"
    assert curr == "CNY"


def test_load_cn_mapper():
    mapper = load_mapper("CN")
    assert mapper.market == "CN"
    assert mapper.map_name("营业总收入") == "revenue"
    assert mapper.map_name("营业成本") == "cogs"
    assert mapper.map_name("研发费用") == "rd_expense"
    assert mapper.map_name("营业利润") == "ebit"
    assert mapper.map_name("利润总额") == "pretax_profit"
    assert mapper.map_name("所得税费用") == "tax_expense"
    assert mapper.map_name("归属于母公司所有者的净利润") == "net_income"
    assert mapper.map_name("货币资金") == "cash"
    assert mapper.map_name("短期借款") == "debt"
    assert mapper.map_name("长期借款") == "debt"
    assert mapper.map_name("实收资本(或股本)") == "shares_diluted"


def test_cn_standardization():
    mapper = load_mapper("CN")
    raw = RawFinancials(
        market="CN",
        ticker="002036",
        currency="CNY",
        unit_scale=1e-6,
        income={
            "营业总收入": [10000e6, 12000e6],
            "营业成本": [8000e6, 9500e6],
            "销售费用": [200e6, 250e6],
            "管理费用": [300e6, 350e6],
            "研发费用": [400e6, 500e6],
            "营业利润": [1100e6, 1400e6],
            "利润总额": [1150e6, 1450e6],
            "所得税费用": [250e6, 300e6],
            "归属于母公司所有者的净利润": [850e6, 1100e6],
            "稀释每股收益": [0.85, 1.10],
        },
        balance={
            "货币资金": 2000e6,
            "短期借款": 1500e6,
            "长期借款": 2500e6,
            "实收资本(或股本)": 1000e6,
            "归属于母公司股东权益合计": 6000e6,
        },
        price=10.0,
        period_labels=["2024-12-31", "2025-12-31"],
        source="akshare",
    )

    std = mapper.standardize(raw)
    assert std.market == "CN"
    assert std.income["revenue"] == [10000.0, 12000.0]
    assert std.income["cogs"] == [8000.0, 9500.0]
    assert std.income["net_income"] == [850.0, 1100.0]
    assert std.balance["cash"] == 2000.0
    assert std.balance["debt"] == 4000.0
    assert std.balance["shares_diluted"] == 1000.0
    assert std.price == 10.0

    # 验证 inputs 与 assumptions 生成
    inputs = build_engine_inputs(std)
    assert inputs["default_wacc_inputs"]["rf"] == 0.021
    assert inputs["default_wacc_inputs"]["tax_rate"] == 0.25

    fa = build_forecast_assumptions(std)
    assert fa.tax_rate == 0.25
    assert fa.base_revenue == 12000.0


def test_resolve_stock_and_chinese_name():
    from app.data.stock_lookup import resolve_stock
    # 测试中文名称解析
    res = resolve_stock("工业富联", preferred_market="CN")
    assert res is not None
    assert res["ticker"] == "601138"
    assert res["market"] == "CN"

    # 测试拼音缩写解析
    res_py = resolve_stock("gyfl", preferred_market="CN")
    assert res_py is not None
    assert res_py["ticker"] == "601138"

    # 测试提供器对中文名自动解析
    code, sym = normalize_cn_ticker("工业富联")
    assert code == "601138"
    assert sym == "sh601138"

    yf_t, market, curr = normalize_yf_ticker("工业富联", "CN")
    assert yf_t == "601138.SS"
    assert market == "CN"
    assert curr == "CNY"

