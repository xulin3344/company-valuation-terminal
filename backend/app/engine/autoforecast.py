from .forecast import ForecastAssumptions

GROWTH_CAP = 0.30
GROWTH_FLOOR = 0.02
TERMINAL_GROWTH_CEILING = 0.04
DEFAULT_DA_PCT = 0.045
DEFAULT_CAPEX_PCT = 0.05


def generate_forecast_assumptions(
    history_revenue: list,
    history_gross_margin: list,
    history_selling_ratio: list = None,
    history_admin_ratio: list = None,
    base_revenue: float = None,
    tax_rate: float = 0.23,
    nwc_pct_of_rev_delta: float = 0.03,
    history_ebit_margin: list = None,
    history_da_ratio: list = None,
    history_capex_ratio: list = None,
) -> ForecastAssumptions:
    if len(history_revenue) < 2:
        cagr = 0.10
    else:
        cagr = (history_revenue[-1] / history_revenue[0]) ** (1 / (len(history_revenue) - 1)) - 1
    g1 = max(min(cagr, GROWTH_CAP), -GROWTH_CAP)
    g5 = min(TERMINAL_GROWTH_CEILING, max(g1 * 0.27, GROWTH_FLOOR))
    growth = [g1 + (g5 - g1) * i / 4 for i in range(5)]

    if history_gross_margin:
        gm_mean = sum(history_gross_margin) / len(history_gross_margin)
        gm_last = history_gross_margin[-1]
    else:
        gm_mean = gm_last = 0.50
    gross_margin = [gm_last + (gm_mean - gm_last) * (i + 1) / 5 for i in range(5)]

    selling_last = history_selling_ratio[-1] if history_selling_ratio else 0.20
    admin_last = history_admin_ratio[-1] if history_admin_ratio else 0.06

    ebit_margin = None
    if history_ebit_margin:
        em_mean = sum(history_ebit_margin) / len(history_ebit_margin)
        em_last = history_ebit_margin[-1]
        ebit_margin = [em_last + (em_mean - em_last) * (i + 1) / 5 for i in range(5)]

    # Fix 4：D&A 和 CapEx 优先使用近3年历史均值
    if history_da_ratio and len(history_da_ratio) >= 1:
        recent_da = history_da_ratio[-min(3, len(history_da_ratio)):]
        da_base = sum(recent_da) / len(recent_da)
    else:
        da_base = DEFAULT_DA_PCT

    if history_capex_ratio and len(history_capex_ratio) >= 1:
        recent_capex = history_capex_ratio[-min(3, len(history_capex_ratio)):]
        capex_base = abs(sum(recent_capex) / len(recent_capex))
    else:
        capex_base = DEFAULT_CAPEX_PCT

    base_rev = base_revenue if base_revenue is not None else (history_revenue[-1] if history_revenue else 0.0)

    return ForecastAssumptions(
        base_revenue=base_rev,
        growth=growth,
        gross_margin=gross_margin,
        selling_ratio=[selling_last] * 5,
        admin_ratio=[admin_last] * 5,
        da_pct=[da_base] * 5,
        capex_pct=[capex_base] * 5,
        nwc_pct_of_rev_delta=nwc_pct_of_rev_delta,
        tax_rate=tax_rate,
        ebit_margin=ebit_margin,
    )