"""M2 端到端验收：手动喂入泡泡玛特范例数据 → 数据层标准化 → 桥接 M1 引擎 → 还原范例估值结果。"""
import pytest

from app.data.pipeline import analyze, build_engine_inputs, build_forecast_assumptions
from app.engine.autoforecast import generate_forecast_assumptions
from app.engine.comps import Peer, comps_valuation
from app.engine.forecast import run_forecast

from test_m2_quality import POP_MART_MANUAL


@pytest.fixture(scope="module")
def std(base):
    return analyze("00992", "HK", manual_data=POP_MART_MANUAL)


def test_build_engine_inputs_target_matches_template(std):
    inputs = build_engine_inputs(std)
    target = inputs["target"]
    assert target.revenue == pytest.approx(37120.0, rel=1e-6)
    assert target.ebitda == pytest.approx(18333.0, rel=1e-3)
    assert target.ebit == pytest.approx(16533.0, rel=1e-6)
    assert target.net_income == pytest.approx(12730.0, rel=1e-6)
    assert target.net_debt == pytest.approx(-15000.0, abs=1e-6)
    assert inputs["shares"] == pytest.approx(1343.0, abs=1e-6)
    # FX bridge: 143.0 HKD × 0.92 = 131.56 CNY（报表币种为 CNY）
    assert inputs["price"] == pytest.approx(131.56, abs=0.01)
    assert inputs["price_fx_applied"] is True
    assert inputs["history_revenue"] == pytest.approx([13038.0, 37120.0], rel=1e-9)


def test_bridge_comps_restores_template_values(std, base):
    inputs = build_engine_inputs(std)
    peers = [Peer(**p) for p in base["peers"]]
    result = comps_valuation(peers, inputs["target"], inputs["shares"])
    assert result.methods["pe"].implied_price == pytest.approx(232.04, rel=1e-3)
    assert result.methods["ev_ebitda"].implied_price == pytest.approx(189.49, rel=1e-3)
    assert result.methods["ev_ebit"].implied_price == pytest.approx(224.34, rel=1e-3)
    assert result.methods["ev_sales"].implied_price == pytest.approx(75.47, rel=1e-3)


def test_bridge_autoforecast_runs_and_produces_sane_shapes(std):
    assumptions = build_forecast_assumptions(std)
    assert assumptions.base_revenue == pytest.approx(37120.0, abs=1e-6)
    assert assumptions.growth[0] >= assumptions.growth[4]
    result = run_forecast(assumptions)
    assert len(result.ufcf) == 5
    assert result.revenue[0] > assumptions.base_revenue


def test_manual_generate_forecast_assumptions_from_std_history(std):
    inputs = build_engine_inputs(std)
    assumptions = generate_forecast_assumptions(
        history_revenue=inputs["history_revenue"],
        history_gross_margin=inputs["history_gross_margin"],
        base_revenue=inputs["base_revenue"],
    )
    assert assumptions.growth[0] == pytest.approx(0.30, abs=1e-9)
    assert assumptions.gross_margin[0] <= inputs["history_gross_margin"][-1] + 1e-12