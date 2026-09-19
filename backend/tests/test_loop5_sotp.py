import pytest

from app.engine.errors import InvalidAssumptionError
from app.engine.sotp import Segment, sotp_sensitivity, sotp_valuation


def _segments(base):
    return [Segment(**s) for s in base["sotp_segments"]]


def _kwargs(base):
    return dict(
        cash=base["sotp_cash"],
        debt=base["sotp_debt"],
        minority_interest=0.0,
        shares=base["sotp_shares"],
    )


def test_three_scenarios(base):
    result = sotp_valuation(_segments(base), **_kwargs(base))
    for scenario, ev_expected, price_expected in zip(
        (result.bear, result.base, result.bull),
        base["sotp_expected"]["ev"],
        base["sotp_expected"]["price"],
    ):
        assert scenario.enterprise_value == pytest.approx(ev_expected, rel=1e-3)
        assert scenario.implied_price == pytest.approx(price_expected, rel=1e-3)


def test_bear_below_base_below_bull(base):
    result = sotp_valuation(_segments(base), **_kwargs(base))
    assert result.bear.implied_price < result.base.implied_price < result.bull.implied_price


def test_contribution_sums_to_one(base):
    result = sotp_valuation(_segments(base), **_kwargs(base))
    total = sum(c["pct"] for c in result.contributions)
    assert total == pytest.approx(1.0, abs=1e-9)


def test_top_segment_contribution(base):
    result = sotp_valuation(_segments(base), **_kwargs(base))
    top = max(result.contributions, key=lambda c: c["pct"])
    assert top["pct"] == pytest.approx(base["sotp_expected"]["top_contribution_pct"], rel=1e-3)
    assert "LABUBU" in top["name"]


def test_empty_segments_raise(base):
    with pytest.raises(InvalidAssumptionError):
        sotp_valuation([], **_kwargs(base))


def test_sensitivity_matrix_cells(base):
    sens = base["sotp_expected"]["sensitivity"]
    matrix = sotp_sensitivity(
        sens["core_ebit"],
        sens["exp_ebit"],
        sens["core_mults"],
        sens["exp_mults"],
        base["sotp_cash"],
        base["sotp_debt"],
        0.0,
        base["sotp_shares"],
    )
    assert matrix[0][0] == pytest.approx(sens["corner_tl"], rel=1e-3)
    assert matrix[-1][-1] == pytest.approx(sens["corner_br"], rel=1e-3)
    base_row = sens["core_mults"].index(25.239553)
    base_col = sens["exp_mults"].index(25.0)
    assert matrix[base_row][base_col] == pytest.approx(sens["base_cell"], rel=1e-3)
    row_28 = sens["core_mults"].index(28.0)
    col_30 = sens["exp_mults"].index(30.0)
    assert matrix[row_28][col_30] == pytest.approx(sens["cell_28_30"], rel=1e-3)


def test_sensitivity_monotonic(base):
    sens = base["sotp_expected"]["sensitivity"]
    matrix = sotp_sensitivity(
        sens["core_ebit"],
        sens["exp_ebit"],
        sens["core_mults"],
        sens["exp_mults"],
        base["sotp_cash"],
        base["sotp_debt"],
        0.0,
        base["sotp_shares"],
    )
    for row in matrix:
        assert all(a < b for a, b in zip(row, row[1:]))
    for col in range(len(sens["exp_mults"])):
        column = [matrix[r][col] for r in range(len(sens["core_mults"]))]
        assert all(a < b for a, b in zip(column, column[1:]))