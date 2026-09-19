import pathlib

import yaml

from ..engine.autoforecast import generate_forecast_assumptions
from .mapper import AccountMapper
from .models import StandardFinancials
from .providers.akshare_provider import AkshareProvider
from .providers.base import ProviderError, fetch_with_fallback
from .providers.manual import ManualProvider
from .providers.yfinance_provider import YFinanceProvider
from .quality import check_quality

CONFIG_DIR = pathlib.Path(__file__).resolve().parents[1] / "config"

PROVIDERS_BY_MARKET = {
    "HK": (AkshareProvider, YFinanceProvider),
    "US": (YFinanceProvider, AkshareProvider),
    "CN": (AkshareProvider, YFinanceProvider),
}

# WACC 默认值（动态获取失败时的 fallback）
DEFAULT_WACC_BY_MARKET = {
    "HK": {"rf": 0.042, "erp": 0.062, "size_premium": 0.0, "tax_rate": 0.165},
    "US": {"rf": 0.042, "erp": 0.050, "size_premium": 0.0, "tax_rate": 0.21},
    "CN": {"rf": 0.021, "erp": 0.060, "size_premium": 0.0, "tax_rate": 0.25},
}


def _load_wacc_config(market: str) -> dict:
    """从 wacc_params.yaml 加载 WACC 配置，失败回退默认值。"""
    path = CONFIG_DIR / "wacc_params.yaml"
    try:
        if path.exists():
            config = yaml.safe_load(path.read_text(encoding="utf-8"))
            return config.get(market, {})
    except Exception:
        pass
    return {}


def load_mapper(market: str) -> AccountMapper:
    path = CONFIG_DIR / f"mapper_{str(market).lower()}.yaml"
    if not path.exists():
        raise ValueError(f"unsupported market: {market} (expected one of: hk, us, cn)")
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    return AccountMapper(config)


def build_providers(market: str) -> list:
    market = str(market).upper()
    if market not in PROVIDERS_BY_MARKET:
        raise ValueError(f"unsupported market: {market}")
    return [cls(market=market) for cls in PROVIDERS_BY_MARKET[market]]



def analyze(ticker: str, market: str, manual_data: dict = None) -> StandardFinancials:
    if manual_data is not None:
        raw = ManualProvider(manual_data).fetch(ticker)
    else:
        raw = fetch_with_fallback(build_providers(market), ticker)
    effective_market = raw.market or market
    mapper = load_mapper(effective_market)
    std = mapper.standardize(raw)
    std.quality = check_quality(std)
    return std


# ---- 汇率桥接（Fix 1）----
# 港股行情价格为 HKD，报表通常为 CNY
_DEFAULT_FX = {"HKD_CNY": 0.92, "CNY_HKD": 1.087}


def _apply_fx_bridge(price: float, report_currency: str, price_currency: str = "HKD"):
    """将行情价格统一到报表币种。返回 (adjusted_price, fx_applied)。"""
    if not price or not report_currency:
        return price, False
    rc = report_currency.upper()
    pc = price_currency.upper()
    if rc == pc:
        return price, False
    key = f"{pc}_{rc}"
    fx = _DEFAULT_FX.get(key)
    if fx:
        return round(price * fx, 4), True
    return price, False


# ---- WACC 参数动态采集（升级 1）----

def _fetch_dynamic_wacc_params(ticker: str, market: str) -> dict:
    """动态获取 WACC 参数：Rf、Beta、资本结构。失败时回退默认值。"""
    from .providers.market_data_provider import (
        fetch_risk_free_rate, fetch_beta, fetch_capital_structure_from_market
    )
    result = {}
    # 动态无风险利率
    try:
        rf = fetch_risk_free_rate(market)
        result["rf"] = rf
        result["rf_source"] = "dynamic_TNX"
    except Exception:
        result["rf_source"] = "fallback"
    # 动态 Beta
    try:
        beta = fetch_beta(ticker)
        result["beta"] = beta
        result["beta_source"] = "dynamic_yfinance"
    except Exception:
        result["beta"] = 1.0
        result["beta_source"] = "fallback"
    # 动态资本结构
    try:
        cap = fetch_capital_structure_from_market(ticker)
        result["weight_equity"] = cap["weight_equity"]
        result["kd"] = cap["kd"]
        result["cap_structure_source"] = "dynamic_yfinance"
    except Exception:
        result["cap_structure_source"] = "fallback"
    return result


def _estimate_capital_structure(std: StandardFinancials) -> dict:
    """从资产负债表推算资本结构（报表数据 fallback）。"""
    cash = std.balance.get("cash", 0.0)
    debt = std.balance.get("debt", 0.0)
    equity_book = std.balance.get("total_equity", 0.0)
    shares = std.balance.get("shares_diluted")
    if std.price and shares:
        equity_market = std.price * shares
    else:
        equity_market = equity_book or 1.0
    total = equity_market + debt
    weight_equity = equity_market / total if total > 0 else 0.98
    weight_equity = max(0.30, min(0.99, round(weight_equity, 4)))
    kd = 0.035 if debt < equity_market * 0.5 else 0.045
    return {"weight_equity": weight_equity, "kd": kd, "beta": 1.0}


def build_engine_inputs(std: StandardFinancials) -> dict:
    market = str(std.market).upper()
    # Fix 1：港股行情价格汇率桥接
    price = std.price
    fx_applied = False
    if market == "HK" and std.currency:
        price, fx_applied = _apply_fx_bridge(std.price, std.currency, "HKD")
    return {
        "history_revenue": std.history("revenue"),
        "history_gross_margin": _margin_history(std),
        "history_selling_ratio": _ratio_history(std, "selling_expense"),
        "history_admin_ratio": _ratio_history(std, "admin_expense"),
        "base_revenue": std.latest("revenue"),
        "target": _build_target(std),
        "shares": std.balance.get("shares_diluted"),
        "price": price,
        "price_fx_applied": fx_applied,
        "cash": std.balance.get("cash"),
        "debt": std.balance.get("debt"),
        "net_debt": std.net_debt,
        "currency": std.currency,
        "default_wacc_inputs": DEFAULT_WACC_BY_MARKET.get(market, DEFAULT_WACC_BY_MARKET["US"]),
        "auto_wacc_params": _estimate_capital_structure(std),
        "dynamic_wacc_params": _fetch_dynamic_wacc_params(std.ticker, market),
        "wacc_config": _load_wacc_config(market),
    }


def build_forecast_assumptions(std: StandardFinancials):
    inputs = build_engine_inputs(std)
    return generate_forecast_assumptions(
        history_revenue=inputs["history_revenue"],
        history_gross_margin=inputs["history_gross_margin"],
        history_selling_ratio=inputs["history_selling_ratio"] or None,
        history_admin_ratio=inputs["history_admin_ratio"] or None,
        base_revenue=inputs["base_revenue"],
        tax_rate=inputs["default_wacc_inputs"]["tax_rate"],
        history_ebit_margin=_ebit_margin_history(std),
        history_da_ratio=_ratio_history(std, "da"),       # Fix 4
        history_capex_ratio=_ratio_history(std, "capex"),  # Fix 4
    )


def _build_target(std: StandardFinancials):
    from ..engine.comps import TargetFinancials

    return TargetFinancials(
        revenue=std.latest("revenue") or 0.0,
        ebitda=std.latest("ebitda") or 0.0,
        ebit=std.latest("ebit") or 0.0,
        net_income=std.latest("net_income") or 0.0,
        net_debt=std.net_debt,
    )


def _margin_history(std: StandardFinancials) -> list:
    revenue = std.income.get("revenue", [])
    gross = std.income.get("gross_profit", [])
    out = []
    for r, g in zip(revenue, gross):
        if r and g is not None:
            out.append(g / r)
    return out


def _ratio_history(std: StandardFinancials, account: str) -> list:
    revenue = std.income.get("revenue", [])
    expense = std.income.get(account, [])
    out = []
    for r, e in zip(revenue, expense):
        if r and e is not None:
            out.append(e / r)
    return out


def _ebit_margin_history(std: StandardFinancials) -> list:
    revenue = std.income.get("revenue", [])
    ebit = std.income.get("ebit", [])
    out = []
    for r, e in zip(revenue, ebit):
        if r and e is not None:
            out.append(e / r)
    return out


__all__ = [
    "analyze",
    "build_engine_inputs",
    "build_forecast_assumptions",
    "load_mapper",
    "build_providers",
    "ProviderError",
]