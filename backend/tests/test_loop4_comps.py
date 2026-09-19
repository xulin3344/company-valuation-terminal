import pytest

from app.engine.comps import Peer, TargetFinancials, comps_valuation, percentile, peer_multiples, stats


def _peers(base):
    return [Peer(**p) for p in base["peers"]]


def _target(base):
    return TargetFinancials(**base["target"])


def test_peer_ev_property(base):
    for peer, raw in zip(_peers(base), base["peers"]):
        assert peer.ev == pytest.approx(raw["market_cap"] + raw["net_debt"], abs=1e-6)


def test_percentile_interpolation():
    values = [20.3125, 23.958333, 25.0, 29.655172]
    assert percentile(values, 0.25) == pytest.approx(23.046875, abs=1e-4)
    assert percentile(values, 0.75) == pytest.approx(26.163793, abs=1e-4)
    assert percentile(values, 0.5) == pytest.approx(24.479166, abs=1e-4)


def test_percentile_empty_raises():
    with pytest.raises(ValueError):
        percentile([], 0.5)


def test_stats_six_bands(base):
    multiples = peer_multiples(_peers(base))
    st = stats([m.pe for m in multiples])
    assert st.maximum == pytest.approx(29.6552, abs=1e-3)
    assert st.minimum == pytest.approx(20.3125, abs=1e-3)
    assert st.median == pytest.approx(base["comps_expected"]["median_pe"], rel=1e-3)
    assert st.p25 < st.median < st.p75


def test_median_multiples(base):
    multiples = peer_multiples(_peers(base))
    assert stats([m.pe for m in multiples]).median == pytest.approx(
        base["comps_expected"]["median_pe"], rel=1e-3
    )
    assert stats([m.ev_ebitda for m in multiples]).median == pytest.approx(
        base["comps_expected"]["median_ev_ebitda"], rel=1e-3
    )
    assert stats([m.ev_ebit for m in multiples]).median == pytest.approx(
        base["comps_expected"]["median_ev_ebit"], rel=1e-3
    )


def test_pe_method_direct_equity_bridge(base):
    result = comps_valuation(_peers(base), _target(base), base["comps_shares"])
    pe = result.methods["pe"]
    assert pe.multiple_used == pytest.approx(base["comps_expected"]["median_pe"], rel=1e-3)
    assert pe.implied_equity == pytest.approx(pe.multiple_used * base["target"]["net_income"], rel=1e-6)
    assert pe.implied_price == pytest.approx(base["comps_expected"]["price_pe"], rel=1e-3)


def test_ev_methods_bridge_through_net_debt(base):
    result = comps_valuation(_peers(base), _target(base), base["comps_shares"])
    for key, expected_price in (
        ("ev_ebitda", base["comps_expected"]["price_ev_ebitda"]),
        ("ev_ebit", base["comps_expected"]["price_ev_ebit"]),
        ("ev_sales", base["comps_expected"]["price_ev_sales"]),
    ):
        method = result.methods[key]
        net_debt = base["target"]["net_debt"]
        assert method.implied_equity == pytest.approx(method.implied_ev - net_debt, rel=1e-6)
        assert method.implied_price == pytest.approx(expected_price, rel=1e-3)


def test_quartile_price_ranges(base):
    result = comps_valuation(_peers(base), _target(base), base["comps_shares"])
    pe_low, pe_high = base["comps_expected"]["pe_range"]
    ev_low, ev_high = base["comps_expected"]["ev_ebitda_range"]
    assert result.methods["pe"].low_price == pytest.approx(pe_low, rel=1e-3)
    assert result.methods["pe"].high_price == pytest.approx(pe_high, rel=1e-3)
    assert result.methods["ev_ebitda"].low_price == pytest.approx(ev_low, rel=15e-4)
    assert result.methods["ev_ebitda"].high_price == pytest.approx(ev_high, rel=15e-4)


def test_consensus_average_of_four_methods(base):
    result = comps_valuation(_peers(base), _target(base), base["comps_shares"])
    expected = base["comps_expected"]["consensus"]
    assert result.consensus_price == pytest.approx(expected, rel=1e-3)
    manual = sum(m.implied_price for m in result.methods.values()) / 4
    assert result.consensus_price == pytest.approx(manual, rel=1e-6)