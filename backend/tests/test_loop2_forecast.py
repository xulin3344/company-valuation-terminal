import pytest

from app.engine.errors import InvalidAssumptionError
from app.engine.forecast import ForecastAssumptions, run_forecast


def _assumptions(base):
    return ForecastAssumptions(**base["forecast_assumptions"])


def test_revenue_projection(base):
    result = run_forecast(_assumptions(base))
    assert result.revenue[0] == pytest.approx(base["forecast_expected"]["revenue_y1"], rel=1e-3)
    assert result.revenue[4] == pytest.approx(base["forecast_expected"]["revenue_y5"], rel=1e-3)


def test_ebit_path(base):
    result = run_forecast(_assumptions(base))
    for actual, expected in zip(result.ebit, base["forecast_expected"]["ebit"]):
        assert actual == pytest.approx(expected, rel=1e-3)


def test_nwc_delta_is_pct_of_revenue_delta(base):
    result = run_forecast(_assumptions(base))
    for actual, expected in zip(result.nwc_delta, base["forecast_expected"]["nwc_delta"]):
        assert actual == pytest.approx(expected, rel=1e-3)


def test_ufcf_path(base):
    result = run_forecast(_assumptions(base))
    for actual, expected in zip(result.ufcf, base["forecast_expected"]["ufcf"]):
        assert actual == pytest.approx(expected, rel=1e-3)


def test_terminal_ebitda(base):
    result = run_forecast(_assumptions(base))
    assert result.ebitda_terminal == pytest.approx(base["forecast_expected"]["ebitda_y5"], rel=1e-3)


def test_invalid_ratio_length_raises(base):
    bad = ForecastAssumptions(**{**base["forecast_assumptions"], "growth": [0.1] * 3})
    with pytest.raises(InvalidAssumptionError):
        run_forecast(bad)


def test_invalid_tax_rate_raises(base):
    bad = ForecastAssumptions(**{**base["forecast_assumptions"], "tax_rate": 1.5})
    with pytest.raises(InvalidAssumptionError):
        run_forecast(bad)