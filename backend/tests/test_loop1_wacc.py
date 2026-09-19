import pytest

from app.engine.wacc import WACCInputs, compute_wacc


def _inputs(base):
    return WACCInputs(**base["wacc_inputs"])


def test_capm_cost_of_equity(base):
    result = compute_wacc(_inputs(base))
    expected = base["wacc_expected"]["cost_of_equity"]
    assert result.cost_of_equity == pytest.approx(expected, abs=1e-6)


def test_after_tax_cost_of_debt(base):
    result = compute_wacc(_inputs(base))
    expected = base["wacc_expected"]["after_tax_cost_of_debt"]
    assert result.after_tax_cost_of_debt == pytest.approx(expected, abs=1e-6)


def test_wacc_precise_value(base):
    result = compute_wacc(_inputs(base))
    assert result.wacc == pytest.approx(base["wacc_expected"]["wacc_precise"], abs=1e-6)


def test_wacc_matches_displayed_template_value(base):
    result = compute_wacc(_inputs(base))
    assert result.wacc == pytest.approx(base["wacc_expected"]["wacc_displayed"], rel=1e-3)


def test_full_equity_structure(base):
    kwargs = {k: v for k, v in base["wacc_inputs"].items() if k != "weight_equity"}
    inputs = WACCInputs(**kwargs, weight_equity=1.0)
    result = compute_wacc(inputs)
    assert result.wacc == pytest.approx(result.cost_of_equity, abs=1e-12)
    assert result.weight_debt == pytest.approx(0.0, abs=1e-12)


def test_full_debt_structure(base):
    kwargs = {k: v for k, v in base["wacc_inputs"].items() if k != "weight_equity"}
    inputs = WACCInputs(**kwargs, weight_equity=0.0)
    result = compute_wacc(inputs)
    assert result.wacc == pytest.approx(result.after_tax_cost_of_debt, abs=1e-12)


def test_size_premium_raises_ke(base):
    result = compute_wacc(_inputs(base))
    kwargs = {k: v for k, v in base["wacc_inputs"].items() if k != "size_premium"}
    premium = compute_wacc(WACCInputs(**kwargs, size_premium=0.02))
    assert premium.cost_of_equity == pytest.approx(result.cost_of_equity + 0.02, abs=1e-12)