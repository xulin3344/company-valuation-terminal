from .models import QualityReport

MODEL_REQUIREMENTS = {
    "dcf": (["revenue", "da", "capex"], ["cash", "debt", "shares_diluted"], True),
    "comps_pe": (["net_income"], [], False),
    "comps_ev_ebitda": (["ebitda"], [], False),
    "comps_ev_ebit": (["ebit"], [], False),
    "sotp": ([], [], False),
}


def check_quality(std) -> QualityReport:
    missing = {}
    for model, (income_req, balance_req, needs_price) in MODEL_REQUIREMENTS.items():
        miss = []
        for account in income_req:
            series = std.income.get(account)
            if not series or all(v is None for v in series):
                miss.append(account)
        for account in balance_req:
            if std.balance.get(account) is None:
                miss.append(account)
        if needs_price and std.price is None:
            miss.append("price")
        missing[model] = miss

    degraded = []
    net_income = std.latest("net_income")
    if net_income is not None and net_income <= 0:
        degraded.append(("comps_pe", "net_income <= 0"))
    ebitda = std.latest("ebitda")
    if ebitda is not None and ebitda <= 0:
        degraded.append(("comps_ev_ebitda", "ebitda <= 0"))

    evaluated = [k for k in MODEL_REQUIREMENTS if k != "sotp"]
    fully_missing = [k for k in evaluated if missing.get(k)]
    if not fully_missing:
        health = "good"
    elif len(fully_missing) == len(evaluated):
        health = "poor"
    else:
        health = "partial"

    warnings = []
    if str(std.market).upper() == "HK" and not std.currency:
        warnings.append("报表币种未知（数据源未提供），金额按公司报告币种计价；行情价格通常为港元")
    if "shares_diluted" in std.derived:
        warnings.append(
            "shares_diluted 由 net_income / eps_diluted 反推得出，"
            "EPS 四舍五入可能导致约 ±2% 的股数偏差"
        )

    return QualityReport(
        missing=missing,
        degraded_models=degraded,
        derived_accounts=list(std.derived),
        warnings=warnings,
        health=health,
    )