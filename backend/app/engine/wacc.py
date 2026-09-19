from dataclasses import dataclass


@dataclass
class WACCInputs:
    rf: float
    beta: float
    erp: float
    size_premium: float = 0.0
    kd: float = 0.035
    tax_rate: float = 0.23
    weight_equity: float = 0.98


@dataclass
class WACCResult:
    cost_of_equity: float
    after_tax_cost_of_debt: float
    wacc: float
    weight_equity: float
    weight_debt: float


def compute_wacc(inp: WACCInputs) -> WACCResult:
    ke = inp.rf + inp.beta * inp.erp + inp.size_premium
    kd_after = inp.kd * (1 - inp.tax_rate)
    we = inp.weight_equity
    wd = 1.0 - we
    wacc = ke * we + kd_after * wd
    return WACCResult(
        cost_of_equity=ke,
        after_tax_cost_of_debt=kd_after,
        wacc=wacc,
        weight_equity=we,
        weight_debt=wd,
    )