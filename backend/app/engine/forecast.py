from dataclasses import dataclass

from .errors import InvalidAssumptionError

YEARS = 5

_RATIO_FIELDS = ("growth", "gross_margin", "selling_ratio", "admin_ratio", "da_pct", "capex_pct")


@dataclass
class ForecastAssumptions:
    base_revenue: float
    growth: list
    gross_margin: list
    selling_ratio: list
    admin_ratio: list
    da_pct: list
    capex_pct: list
    nwc_pct_of_rev_delta: float = 0.03
    tax_rate: float = 0.23
    ebit_margin: list = None

    def validate(self) -> None:
        for name in _RATIO_FIELDS:
            if len(getattr(self, name)) != YEARS:
                raise InvalidAssumptionError(f"{name} must contain exactly {YEARS} yearly values")
        if not 0 < self.tax_rate < 1:
            raise InvalidAssumptionError("tax_rate must be in (0, 1)")
        if self.nwc_pct_of_rev_delta < 0:
            raise InvalidAssumptionError("nwc_pct_of_rev_delta must be non-negative")
        if self.ebit_margin is not None and len(self.ebit_margin) != YEARS:
            raise InvalidAssumptionError(f"ebit_margin must contain exactly {YEARS} yearly values")


@dataclass
class ForecastResult:
    revenue: list
    gross_profit: list
    selling_expense: list
    admin_expense: list
    ebit: list
    nopat: list
    da: list
    capex: list
    nwc_delta: list
    ufcf: list
    ebit_terminal: float
    ebitda_terminal: float


def run_forecast(a: ForecastAssumptions) -> ForecastResult:
    a.validate()
    revenue = []
    prev = a.base_revenue
    for g in a.growth:
        cur = prev * (1 + g)
        revenue.append(cur)
        prev = cur
    gross_profit = [r * m for r, m in zip(revenue, a.gross_margin)]
    selling = [r * s for r, s in zip(revenue, a.selling_ratio)]
    admin = [r * s for r, s in zip(revenue, a.admin_ratio)]
    if a.ebit_margin is not None:
        ebit = [r * m for r, m in zip(revenue, a.ebit_margin)]
    else:
        ebit = [gp - se - ge for gp, se, ge in zip(gross_profit, selling, admin)]
    nopat = [e * (1 - a.tax_rate) for e in ebit]
    da = [r * d for r, d in zip(revenue, a.da_pct)]
    capex = [r * c for r, c in zip(revenue, a.capex_pct)]
    nwc_delta = []
    prev = a.base_revenue
    for r in revenue:
        nwc_delta.append((r - prev) * a.nwc_pct_of_rev_delta)
        prev = r
    ufcf = [n + d - c - w for n, d, c, w in zip(nopat, da, capex, nwc_delta)]
    return ForecastResult(
        revenue=revenue,
        gross_profit=gross_profit,
        selling_expense=selling,
        admin_expense=admin,
        ebit=ebit,
        nopat=nopat,
        da=da,
        capex=capex,
        nwc_delta=nwc_delta,
        ufcf=ufcf,
        ebit_terminal=ebit[-1],
        ebitda_terminal=ebit[-1] + da[-1],
    )