from dataclasses import dataclass

from .errors import InvalidAssumptionError


@dataclass
class Segment:
    name: str
    ebit: float
    bear_mult: float
    base_mult: float
    bull_mult: float


@dataclass
class SOTPScenario:
    label: str
    enterprise_value: float
    equity_value: float
    implied_price: float


@dataclass
class SOTPResult:
    bear: SOTPScenario
    base: SOTPScenario
    bull: SOTPScenario
    contributions: list


def _scenario_ev(segments: list, attr: str) -> float:
    return sum(getattr(s, attr) * s.ebit for s in segments)


def sotp_valuation(
    segments: list,
    cash: float,
    debt: float,
    minority_interest: float = 0.0,
    shares: float = 1.0,
) -> SOTPResult:
    if not segments:
        raise InvalidAssumptionError("sotp requires at least one segment")
    ev_bear = _scenario_ev(segments, "bear_mult")
    ev_base = _scenario_ev(segments, "base_mult")
    ev_bull = _scenario_ev(segments, "bull_mult")

    def _mk(label, ev):
        equity = ev + cash - debt - minority_interest
        return SOTPScenario(label, ev, equity, equity / shares)

    base_contrib = [
        {"name": s.name, "ev": s.base_mult * s.ebit, "pct": (s.base_mult * s.ebit) / ev_base}
        for s in segments
    ]
    return SOTPResult(
        bear=_mk("bear", ev_bear),
        base=_mk("base", ev_base),
        bull=_mk("bull", ev_bull),
        contributions=base_contrib,
    )


def sotp_sensitivity(
    core_ebit: float,
    exp_ebit: float,
    core_mults: list,
    exp_mults: list,
    cash: float,
    debt: float,
    minority_interest: float = 0.0,
    shares: float = 1.0,
) -> list:
    return [
        [
            (core_ebit * cm + exp_ebit * em + cash - debt - minority_interest) / shares
            for em in exp_mults
        ]
        for cm in core_mults
    ]