from dataclasses import dataclass, replace

from .errors import NoValuationError


@dataclass
class ModelOutput:
    key: str
    label: str
    price: float
    low: float
    high: float
    weight: float
    available: bool = True
    exclude_reason: str = ""


@dataclass
class ValuationSummary:
    fair_value: float
    weighted_low: float
    weighted_high: float
    full_low: float
    full_high: float
    upside: float
    rating: str
    used_models: list


RATING_RULES = (
    (-0.10, "Overvalued 高估"),
    (0.15, "Fair 合理"),
    (0.50, "Undervalued 低估"),
    (float("inf"), "Significantly Undervalued 显著低估"),
)


def rate_upside(upside: float) -> str:
    for threshold, label in RATING_RULES:
        if upside < threshold:
            return label
    return RATING_RULES[-1][1]


DEGRADATION_RULES = (
    ("comps_pe", "net_income", 0.0, "net_income <= 0"),
    ("comps_ev_ebitda", "ebitda", 0.0, "ebitda <= 0"),
    ("sotp", "segment_count", 0, "no segments"),
)


def apply_degradation(models: list, net_income: float = None, ebitda: float = None, segment_count: int = None) -> list:
    context = {"net_income": net_income, "ebitda": ebitda, "segment_count": segment_count}
    out = list(models)
    for key, metric_name, floor, reason in DEGRADATION_RULES:
        value = context[metric_name]
        if value is None:
            continue
        if value <= floor:
            out = [
                replace(m, available=False, exclude_reason=reason) if m.key == key and m.available else m
                for m in out
            ]
    return out


def summarize(models: list, current_price: float) -> ValuationSummary:
    available = [m for m in models if m.available and m.weight > 0]
    if not available:
        raise NoValuationError("all valuation models are unavailable")
    weight_sum = sum(m.weight for m in available)
    if weight_sum <= 0:
        raise NoValuationError("total weight of available models must be positive")
    fair = sum(m.price * m.weight for m in available) / weight_sum
    weighted_low = sum(m.low * m.weight for m in available) / weight_sum
    weighted_high = sum(m.high * m.weight for m in available) / weight_sum
    full_low = min(m.low for m in available)
    full_high = max(m.high for m in available)
    upside = fair / current_price - 1
    return ValuationSummary(
        fair_value=fair,
        weighted_low=weighted_low,
        weighted_high=weighted_high,
        full_low=full_low,
        full_high=full_high,
        upside=upside,
        rating=rate_upside(upside),
        used_models=[m.key for m in available],
    )