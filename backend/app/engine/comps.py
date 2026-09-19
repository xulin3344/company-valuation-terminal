import math
from dataclasses import dataclass


@dataclass
class Peer:
    name: str
    ticker: str
    market_cap: float
    net_debt: float
    revenue: float
    ebitda: float
    ebit: float
    net_income: float

    @property
    def ev(self) -> float:
        return self.market_cap + self.net_debt


@dataclass
class PeerMultiples:
    name: str
    ev_sales: float
    ev_ebitda: float
    ev_ebit: float
    pe: float


@dataclass
class MultiplesStats:
    maximum: float
    p75: float
    mean: float
    median: float
    p25: float
    minimum: float


@dataclass
class TargetFinancials:
    revenue: float
    ebitda: float
    ebit: float
    net_income: float
    net_debt: float


@dataclass
class CompsMethod:
    key: str
    multiple_used: float
    implied_ev: float
    implied_equity: float
    implied_price: float
    low_price: float
    high_price: float


@dataclass
class CompsResult:
    methods: dict
    consensus_price: float


def peer_multiples(peers: list) -> list:
    out = []
    for p in peers:
        ev_sales = p.ev / p.revenue if p.revenue else 0.0
        ev_ebitda = p.ev / p.ebitda if p.ebitda else 0.0
        ev_ebit = p.ev / p.ebit if p.ebit else (ev_ebitda * 1.2 if ev_ebitda else 0.0)
        pe = p.market_cap / p.net_income if p.net_income else 0.0
        out.append(
            PeerMultiples(
                name=p.name,
                ev_sales=ev_sales,
                ev_ebitda=ev_ebitda,
                ev_ebit=ev_ebit,
                pe=pe,
            )
        )
    return out



def percentile(values: list, q: float) -> float:
    if not values:
        raise ValueError("values must be non-empty")
    if not 0 <= q <= 1:
        raise ValueError("q must be in [0, 1]")
    vals = sorted(values)
    n = len(vals)
    pos = (n - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def stats(values: list) -> MultiplesStats:
    s = sorted(values)
    return MultiplesStats(
        maximum=s[-1],
        p75=percentile(s, 0.75),
        mean=sum(s) / len(s),
        median=percentile(s, 0.5),
        p25=percentile(s, 0.25),
        minimum=s[0],
    )


def _bridge(mult: float, metric: float, bridge: str, target: TargetFinancials, shares: float):
    if bridge == "equity":
        equity = mult * metric
        ev = equity + target.net_debt
    else:
        ev = mult * metric
        equity = ev - target.net_debt
    return ev, equity, equity / shares


_METHOD_SPECS = (
    ("pe", "pe", "equity", "net_income"),
    ("ev_ebitda", "ev_ebitda", "ev", "ebitda"),
    ("ev_ebit", "ev_ebit", "ev", "ebit"),
    ("ev_sales", "ev_sales", "ev", "revenue"),
)


def comps_valuation(peers: list, target: TargetFinancials, shares: float) -> CompsResult:
    multiples = peer_multiples(peers)
    methods = {}
    prices = []
    for key, mult_attr, bridge, metric_attr in _METHOD_SPECS:
        values = [getattr(m, mult_attr) for m in multiples]
        st = stats(values)
        metric = getattr(target, metric_attr)
        ev, equity, price = _bridge(st.median, metric, bridge, target, shares)
        _, _, low_price = _bridge(st.p25, metric, bridge, target, shares)
        _, _, high_price = _bridge(st.p75, metric, bridge, target, shares)
        methods[key] = CompsMethod(
            key=key,
            multiple_used=st.median,
            implied_ev=ev,
            implied_equity=equity,
            implied_price=price,
            low_price=low_price,
            high_price=high_price,
        )
        prices.append(price)
    consensus = sum(prices) / len(prices)
    return CompsResult(methods=methods, consensus_price=consensus)