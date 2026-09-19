from dataclasses import dataclass

from .errors import InvalidAssumptionError

YEARS = 5


@dataclass
class DCFScenario:
    label: str
    terminal_value: float
    pv_terminal_value: float
    pv_forecast_cashflows: float
    enterprise_value: float
    equity_value: float
    implied_price: float


@dataclass
class DCFResult:
    discount_factors: list
    pv_of_ufcf: list
    pv_forecast_cashflows: float
    gordon: DCFScenario
    exit: DCFScenario


def _discount_factors(wacc: float, n: int = YEARS) -> list:
    return [1.0 / (1.0 + wacc) ** t for t in range(1, n + 1)]


def _bridge(ev: float, cash: float, debt: float, minority_interest: float, shares: float):
    equity = ev + cash - debt - minority_interest
    return equity, equity / shares


def run_dcf(
    ufcf: list,
    wacc: float,
    g: float,
    exit_multiple: float,
    ebitda_terminal: float,
    cash: float,
    debt: float,
    minority_interest: float = 0.0,
    shares: float = 1.0,
) -> DCFResult:
    if len(ufcf) != YEARS:
        raise InvalidAssumptionError(f"ufcf must contain exactly {YEARS} yearly values")
    if wacc <= g:
        raise InvalidAssumptionError("perpetual growth g must be lower than WACC")
    factors = _discount_factors(wacc)
    pvs = [cf * f for cf, f in zip(ufcf, factors)]
    pv_total = sum(pvs)

    ufcf_next = ufcf[-1] * (1 + g)
    tv_gordon = ufcf_next / (wacc - g)
    pv_tv_gordon = tv_gordon * factors[-1]
    ev_gordon = pv_total + pv_tv_gordon
    eq_gordon, price_gordon = _bridge(ev_gordon, cash, debt, minority_interest, shares)

    tv_exit = ebitda_terminal * exit_multiple
    pv_tv_exit = tv_exit * factors[-1]
    ev_exit = pv_total + pv_tv_exit
    eq_exit, price_exit = _bridge(ev_exit, cash, debt, minority_interest, shares)

    return DCFResult(
        discount_factors=factors,
        pv_of_ufcf=pvs,
        pv_forecast_cashflows=pv_total,
        gordon=DCFScenario("gordon", tv_gordon, pv_tv_gordon, pv_total, ev_gordon, eq_gordon, price_gordon),
        exit=DCFScenario("exit", tv_exit, pv_tv_exit, pv_total, ev_exit, eq_exit, price_exit),
    )


def dcf_sensitivity(
    ufcf: list,
    wacc_list: list,
    g_list: list,
    cash: float,
    debt: float,
    minority_interest: float = 0.0,
    shares: float = 1.0,
) -> list:
    matrix = []
    for w in wacc_list:
        row = []
        for g in g_list:
            res = run_dcf(ufcf, w, g, 1.0, 0.0, cash, debt, minority_interest, shares)
            row.append(res.gordon.implied_price)
        matrix.append(row)
    return matrix