import pytest

from app.engine.dcf import dcf_sensitivity, run_dcf
from app.engine.errors import InvalidAssumptionError


def _inputs(base):
    return base["dcf_inputs"]


def test_pv_forecast_cashflows(base):
    result = run_dcf(**_inputs(base))
    expected = base["dcf_expected"]["pv_forecast_total"]
    assert result.pv_forecast_cashflows == pytest.approx(expected, rel=1e-3)


def test_gordon_scenario(base):
    result = run_dcf(**_inputs(base))
    expected = base["dcf_expected"]["gordon"]
    assert result.gordon.terminal_value == pytest.approx(expected["terminal_value"], rel=1e-3)
    assert result.gordon.pv_terminal_value == pytest.approx(expected["pv_terminal_value"], rel=1e-3)
    assert result.gordon.enterprise_value == pytest.approx(expected["enterprise_value"], rel=1e-3)
    assert result.gordon.equity_value == pytest.approx(expected["equity_value"], rel=1e-3)
    assert result.gordon.implied_price == pytest.approx(expected["implied_price"], rel=1e-3)


def test_exit_scenario(base):
    result = run_dcf(**_inputs(base))
    expected = base["dcf_expected"]["exit"]
    assert result.exit.terminal_value == pytest.approx(expected["terminal_value"], rel=1e-3)
    assert result.exit.pv_terminal_value == pytest.approx(expected["pv_terminal_value"], rel=1e-3)
    assert result.exit.enterprise_value == pytest.approx(expected["enterprise_value"], rel=1e-3)
    assert result.exit.equity_value == pytest.approx(expected["equity_value"], rel=1e-3)
    assert result.exit.implied_price == pytest.approx(expected["implied_price"], rel=1e-3)


def test_equity_bridge_with_net_cash(base):
    result = run_dcf(**_inputs(base))
    inputs = _inputs(base)
    net_cash = inputs["cash"] - inputs["debt"]
    assert result.gordon.equity_value == pytest.approx(
        result.gordon.enterprise_value + net_cash, rel=1e-6
    )


def test_sensitivity_center_and_corners(base):
    inputs = _inputs(base)
    sens = base["dcf_expected"]["sensitivity"]
    matrix = dcf_sensitivity(
        inputs["ufcf"],
        sens["wacc_list"],
        sens["g_list"],
        inputs["cash"],
        inputs["debt"],
        inputs["minority_interest"],
        inputs["shares"],
    )
    w_center = sens["wacc_list"].index(0.098)
    g_center = sens["g_list"].index(0.03)
    assert matrix[w_center][g_center] == pytest.approx(sens["center_price"], rel=1e-3)
    assert matrix[0][0] == pytest.approx(sens["corner_tl"], rel=1e-3)
    assert matrix[-1][-1] == pytest.approx(sens["corner_br"], rel=1e-3)


def test_monotonic_decrease_along_wacc(base):
    inputs = _inputs(base)
    sens = base["dcf_expected"]["sensitivity"]
    matrix = dcf_sensitivity(
        inputs["ufcf"],
        sens["wacc_list"],
        sens["g_list"],
        inputs["cash"],
        inputs["debt"],
        inputs["minority_interest"],
        inputs["shares"],
    )
    for row in matrix:
        assert all(a < b for a, b in zip(row, row[1:]))
    for col in range(len(sens["g_list"])):
        column = [matrix[r][col] for r in range(len(sens["wacc_list"]))]
        assert all(a > b for a, b in zip(column, column[1:]))


def test_g_equal_wacc_raises(base):
    inputs = _inputs(base)
    with pytest.raises(InvalidAssumptionError):
        run_dcf(**{**inputs, "g": inputs["wacc"]})


def test_g_greater_wacc_raises(base):
    inputs = _inputs(base)
    with pytest.raises(InvalidAssumptionError):
        run_dcf(**{**inputs, "g": 0.2})


def test_wrong_ufcf_length_raises(base):
    inputs = _inputs(base)
    with pytest.raises(InvalidAssumptionError):
        run_dcf(**{**inputs, "ufcf": inputs["ufcf"][:3]})