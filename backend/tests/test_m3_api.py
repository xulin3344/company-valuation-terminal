"""M3 API 层测试：/api/recalculate 范例还原 + /api/projects CRUD + /api/comps/pool。"""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api import store

client = TestClient(app)

FIXTURE_PATH = pathlib.Path(__file__).resolve().parent / "fixtures" / "basemart.json"


@pytest.fixture
def basemart():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def recalc_params(basemart):
    """从范例数据构建 /api/recalculate 请求体。"""
    fa = basemart["forecast_assumptions"]
    wi = basemart["wacc_inputs"]
    dcf_in = basemart["dcf_inputs"]
    sens = basemart["dcf_expected"]["sensitivity"]
    return {
        "wacc_inputs": wi,
        "forecast_assumptions": fa,
        "dcf_params": {
            "g": dcf_in["g"],
            "exit_multiple": dcf_in["exit_multiple"],
            "ebitda_terminal": dcf_in["ebitda_terminal"],
            "cash": dcf_in["cash"],
            "debt": dcf_in["debt"],
            "minority_interest": dcf_in["minority_interest"],
            "shares": dcf_in["shares"],
            "sensitivity": {"wacc_list": sens["wacc_list"], "g_list": sens["g_list"]},
        },
        "comps": {
            "peers": basemart["peers"],
            "target": basemart["target"],
            "shares": basemart["comps_shares"],
        },
        "sotp": {
            "segments": basemart["sotp_segments"],
            "cash": basemart["sotp_cash"],
            "debt": basemart["sotp_debt"],
            "shares": basemart["sotp_shares"],
            "sensitivity": basemart["sotp_expected"]["sensitivity"],
        },
        "summary": {
            "models": basemart["summary_models"],
            "current_price": basemart["summary_current_price"],
            "target_net_income": basemart["target"]["net_income"],
            "target_ebitda": basemart["target"]["ebitda"],
            "sotp_segments": basemart["sotp_segments"],
        },
    }


# ---- /api/health ----

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---- /api/recalculate 范例还原（核心门禁：±0.1%） ----

def test_recalculate_wacc(basemart, recalc_params):
    r = client.post("/api/recalculate", json=recalc_params)
    assert r.status_code == 200
    wacc = r.json()["wacc"]
    assert wacc["cost_of_equity"] == pytest.approx(basemart["wacc_expected"]["cost_of_equity"], rel=1e-4)
    assert wacc["wacc"] == pytest.approx(basemart["wacc_expected"]["wacc_precise"], rel=1e-4)


def test_recalculate_forecast(basemart, recalc_params):
    r = client.post("/api/recalculate", json=recalc_params)
    forecast = r.json()["forecast"]
    assert forecast["revenue"][-1] == pytest.approx(basemart["forecast_expected"]["revenue_y5"], rel=1e-3)
    assert forecast["ebitda_terminal"] == pytest.approx(basemart["forecast_expected"]["ebitda_y5"], rel=1e-3)
    for i, expected in enumerate(basemart["forecast_expected"]["ufcf"]):
        assert forecast["ufcf"][i] == pytest.approx(expected, rel=1e-3)


def test_recalculate_dcf_gordon(basemart, recalc_params):
    r = client.post("/api/recalculate", json=recalc_params)
    dcf = r.json()["dcf"]
    gordon = basemart["dcf_expected"]["gordon"]
    assert dcf["pv_forecast_cashflows"] == pytest.approx(basemart["dcf_expected"]["pv_forecast_total"], rel=1e-3)
    assert dcf["gordon"]["enterprise_value"] == pytest.approx(gordon["enterprise_value"], rel=1e-3)
    assert dcf["gordon"]["implied_price"] == pytest.approx(gordon["implied_price"], rel=1e-3)


def test_recalculate_dcf_exit(basemart, recalc_params):
    r = client.post("/api/recalculate", json=recalc_params)
    dcf = r.json()["dcf"]
    exit_exp = basemart["dcf_expected"]["exit"]
    assert dcf["exit"]["enterprise_value"] == pytest.approx(exit_exp["enterprise_value"], rel=1e-3)
    assert dcf["exit"]["implied_price"] == pytest.approx(exit_exp["implied_price"], rel=1e-3)


def test_recalculate_dcf_sensitivity(basemart, recalc_params):
    r = client.post("/api/recalculate", json=recalc_params)
    sens = r.json()["dcf"]["sensitivity"]
    sens_exp = basemart["dcf_expected"]["sensitivity"]
    matrix = sens["matrix"]
    assert matrix[0][0] == pytest.approx(sens_exp["corner_tl"], rel=1e-3)
    assert matrix[-1][-1] == pytest.approx(sens_exp["corner_br"], rel=1e-3)


def test_recalculate_comps(basemart, recalc_params):
    r = client.post("/api/recalculate", json=recalc_params)
    comps = r.json()["comps"]
    ce = basemart["comps_expected"]
    assert comps["methods"]["pe"]["implied_price"] == pytest.approx(ce["price_pe"], rel=1e-3)
    assert comps["methods"]["ev_ebitda"]["implied_price"] == pytest.approx(ce["price_ev_ebitda"], rel=1.5e-3)
    assert comps["methods"]["ev_ebit"]["implied_price"] == pytest.approx(ce["price_ev_ebit"], rel=1e-3)
    assert comps["methods"]["ev_sales"]["implied_price"] == pytest.approx(ce["price_ev_sales"], rel=1e-3)
    assert comps["consensus_price"] == pytest.approx(ce["consensus"], rel=1e-3)


def test_recalculate_sotp(basemart, recalc_params):
    r = client.post("/api/recalculate", json=recalc_params)
    sotp = r.json()["sotp"]
    se = basemart["sotp_expected"]
    assert sotp["base"]["implied_price"] == pytest.approx(se["price"][1], rel=1e-3)
    assert sotp["bear"]["implied_price"] == pytest.approx(se["price"][0], rel=1e-3)
    assert sotp["bull"]["implied_price"] == pytest.approx(se["price"][2], rel=1e-3)


def test_recalculate_summary(basemart, recalc_params):
    r = client.post("/api/recalculate", json=recalc_params)
    summary = r.json()["summary"]
    se = basemart["summary_expected"]
    assert summary["fair_value"] == pytest.approx(se["fair_value"], rel=1e-3)
    assert summary["weighted_low"] == pytest.approx(se["weighted_low"], rel=1e-3)
    assert summary["weighted_high"] == pytest.approx(se["weighted_high"], rel=1e-3)
    assert summary["full_low"] == pytest.approx(se["full_low"], rel=1e-3)
    assert summary["full_high"] == pytest.approx(se["full_high"], rel=1e-3)
    assert summary["upside"] == pytest.approx(se["upside"], rel=1e-3)


# ---- /api/comps/pool ----

def test_comps_pool():
    r = client.get("/api/comps/pool")
    assert r.status_code == 200
    peers = r.json()["peers"]
    assert len(peers) == 4
    assert peers[0]["name"] == "三丽鸥 (Sanrio)"


# ---- /api/projects CRUD ----

def test_project_crud(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    payload = {"wacc_inputs": {"rf": 0.025}, "forecast_assumptions": {"base_revenue": 1000}}

    r = client.post("/api/projects", json={"name": "测试项目", "ticker": "09992", "market": "HK", "payload": payload})
    assert r.status_code == 200
    proj = r.json()
    pid = proj["id"]
    assert proj["name"] == "测试项目"
    assert proj["payload"] == payload

    r = client.get("/api/projects")
    assert r.status_code == 200
    assert len(r.json()["projects"]) == 1

    r = client.get(f"/api/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid

    r = client.post("/api/projects", json={"name": "更新后", "ticker": "09992", "market": "HK", "payload": payload, "project_id": pid})
    assert r.status_code == 200
    assert r.json()["name"] == "更新后"

    r = client.delete(f"/api/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["deleted"] is True

    r = client.get(f"/api/projects/{pid}")
    assert r.status_code == 404


def test_project_404(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    r = client.get("/api/projects/nonexistent")
    assert r.status_code == 404
    r = client.delete("/api/projects/nonexistent")
    assert r.status_code == 404