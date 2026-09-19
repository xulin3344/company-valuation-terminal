import dataclasses

import pytest

from app.engine.autoforecast import (
    GROWTH_CAP,
    TERMINAL_GROWTH_CEILING,
    generate_forecast_assumptions,
)
from app.engine.errors import NoValuationError
from app.engine.summary import ModelOutput, apply_degradation, rate_upside, summarize


def _models(base):
    return [ModelOutput(**m) for m in base["summary_models"]]


def test_weighted_fair_value(base):
    summary = summarize(_models(base), base["summary_current_price"])
    assert summary.fair_value == pytest.approx(base["summary_expected"]["fair_value"], rel=1e-3)


def test_weighted_and_full_range(base):
    summary = summarize(_models(base), base["summary_current_price"])
    expected = base["summary_expected"]
    assert summary.weighted_low == pytest.approx(expected["weighted_low"], rel=1e-3)
    assert summary.weighted_high == pytest.approx(expected["weighted_high"], rel=1e-3)
    assert summary.full_low == pytest.approx(expected["full_low"], rel=1e-3)
    assert summary.full_high == pytest.approx(expected["full_high"], rel=1e-3)
    assert summary.full_low < summary.weighted_low
    assert summary.weighted_high < summary.full_high


def test_upside_and_rating(base):
    summary = summarize(_models(base), base["summary_current_price"])
    assert summary.upside == pytest.approx(base["summary_expected"]["upside"], rel=1e-3)
    assert summary.rating == base["summary_expected"]["rating"]
    assert summary.used_models == [m["key"] for m in base["summary_models"]]


def test_weight_normalization_with_unequal_weights(base):
    models = _models(base)
    weights = [0.4, 0.3, 0.2, 0.1, 0.0]
    adjusted = [dataclasses.replace(m, weight=w) for m, w in zip(models, weights)]
    summary = summarize(adjusted, base["summary_current_price"])
    manual = sum(m.price * w for m, w in zip(models[:4], weights[:4])) / sum(weights[:4])
    assert summary.fair_value == pytest.approx(manual, rel=1e-9)
    assert "sotp" not in summary.used_models or weights[4] > 0


def test_degradation_excludes_pe_when_net_income_negative(base):
    degraded = apply_degradation(_models(base), net_income=-100.0)
    pe = next(m for m in degraded if m.key == "comps_pe")
    assert not pe.available
    summary = summarize(degraded, base["summary_current_price"])
    assert "pe" not in summary.used_models
    manual = sum(m.price * m.weight for m in degraded if m.available) / sum(
        m.weight for m in degraded if m.available
    )
    assert summary.fair_value == pytest.approx(manual, rel=1e-9)
    assert summary.fair_value == pytest.approx(290.30, rel=1e-3)


def test_degradation_excludes_ev_ebitda_when_ebitda_negative(base):
    degraded = apply_degradation(_models(base), ebitda=-1.0)
    assert not next(m for m in degraded if m.key == "comps_ev_ebitda").available
    summary = summarize(degraded, base["summary_current_price"])
    assert "ev_ebitda" not in summary.used_models


def test_degradation_excludes_sotp_when_no_segments(base):
    degraded = apply_degradation(_models(base), segment_count=0)
    assert not next(m for m in degraded if m.key == "sotp").available
    summary = summarize(degraded, base["summary_current_price"])
    assert "sotp" not in summary.used_models


def test_degradation_zero_weight_sum_after_normalization(base):
    degraded = apply_degradation(_models(base), net_income=-1.0, ebitda=-1.0)
    summary = summarize(degraded, base["summary_current_price"])
    assert len(summary.used_models) == 3
    manual = sum(m.price * m.weight for m in degraded if m.available) / sum(
        m.weight for m in degraded if m.available
    )
    assert summary.fair_value == pytest.approx(manual, rel=1e-9)


def test_no_valuation_error_when_all_excluded(base):
    models = [dataclasses.replace(m, available=False, exclude_reason="forced") for m in _models(base)]
    with pytest.raises(NoValuationError):
        summarize(models, base["summary_current_price"])


def test_rating_thresholds():
    assert rate_upside(-0.5) == "Overvalued 高估"
    assert rate_upside(-0.10) == "Fair 合理"
    assert rate_upside(0.0) == "Fair 合理"
    assert rate_upside(0.149) == "Fair 合理"
    assert rate_upside(0.15) == "Undervalued 低估"
    assert rate_upside(0.50) == "Significantly Undervalued 显著低估"
    assert rate_upside(0.9486) == "Significantly Undervalued 显著低估"


def test_autoforecast_growth_cap_and_decay():
    assumptions = generate_forecast_assumptions(
        history_revenue=[13038.0, 37120.0],
        history_gross_margin=[0.6679, 0.7210],
    )
    assert assumptions.growth[0] == pytest.approx(GROWTH_CAP, abs=1e-9)
    assert assumptions.growth[4] == pytest.approx(TERMINAL_GROWTH_CEILING, abs=1e-9)
    assert all(a > b for a, b in zip(assumptions.growth, assumptions.growth[1:]))
    assert assumptions.base_revenue == pytest.approx(37120.0, abs=1e-6)


def test_autoforecast_margin_mean_reversion():
    history_gm = [0.6679, 0.7210]
    assumptions = generate_forecast_assumptions(
        history_revenue=[13038.0, 37120.0],
        history_gross_margin=history_gm,
    )
    mean_gm = sum(history_gm) / 2
    assert all(mean_gm <= g <= history_gm[-1] + 1e-12 for g in assumptions.gross_margin)
    assert assumptions.gross_margin[0] > assumptions.gross_margin[-1]
    assert assumptions.gross_margin[-1] == pytest.approx(mean_gm, abs=1e-9)


def test_autoforecast_ratios_carry_forward():
    assumptions = generate_forecast_assumptions(
        history_revenue=[13038.0, 37120.0],
        history_gross_margin=[0.6679, 0.7210],
        history_selling_ratio=[0.28, 0.2177],
        history_admin_ratio=[0.088, 0.0579],
    )
    assert assumptions.selling_ratio == [0.2177] * 5
    assert assumptions.admin_ratio == [0.0579] * 5