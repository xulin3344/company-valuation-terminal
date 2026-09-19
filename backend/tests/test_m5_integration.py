"""M5 联调验收测试：项目保存/载入一致性 + 端到端演示 + 免责声明。"""
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


# ---- 项目保存/载入一致性 ----

def test_project_save_load_consistency(tmp_path, monkeypatch, basemart):
    """保存项目 → 载入 → 数据完全一致。"""
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    payload = {
        "wacc_inputs": basemart["wacc_inputs"],
        "forecast_assumptions": basemart["forecast_assumptions"],
        "dcf_params": {"g": 0.03, "exit_multiple": 16.0, "cash": 17500, "debt": 2500, "shares": 1343},
    }

    r = client.post("/api/projects", json={"name": "泡泡玛特估值", "ticker": "09992", "market": "HK", "payload": payload})
    assert r.status_code == 200
    saved = r.json()
    pid = saved["id"]

    r2 = client.get(f"/api/projects/{pid}")
    assert r2.status_code == 200
    loaded = r2.json()

    assert loaded["id"] == pid
    assert loaded["name"] == "泡泡玛特估值"
    assert loaded["ticker"] == "09992"
    assert loaded["market"] == "HK"
    assert loaded["payload"] == payload


def test_project_update_preserves_id(tmp_path, monkeypatch):
    """更新项目后 ID 不变、payload 被替换。"""
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")

    r = client.post("/api/projects", json={"name": "A", "ticker": "09992", "market": "HK", "payload": {"v": 1}})
    pid = r.json()["id"]

    r2 = client.post("/api/projects", json={"name": "B", "ticker": "09992", "market": "HK", "payload": {"v": 2}, "project_id": pid})
    assert r2.json()["id"] == pid
    assert r2.json()["name"] == "B"

    r3 = client.get(f"/api/projects/{pid}")
    assert r3.json()["payload"] == {"v": 2}


def test_project_list_order(tmp_path, monkeypatch):
    """列出项目按 updated_at 降序。"""
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")

    client.post("/api/projects", json={"name": "first", "ticker": "A", "market": "HK", "payload": {}})
    client.post("/api/projects", json={"name": "second", "ticker": "B", "market": "HK", "payload": {}})

    r = client.get("/api/projects")
    projects = r.json()["projects"]
    assert len(projects) == 2
    assert projects[0]["name"] == "second"


# ---- 端到端：recalculate → save → load → recalculate 一致 ----

def test_roundtrip_recalc_save_load_recalc(tmp_path, monkeypatch, basemart):
    """完整流程：recalculate → 保存 → 载入 → 再 recalculate → 结果一致。"""
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")

    fa = basemart["forecast_assumptions"]
    wi = basemart["wacc_inputs"]
    dcf_in = basemart["dcf_inputs"]
    params = {
        "wacc_inputs": wi,
        "forecast_assumptions": fa,
        "dcf_params": {
            "g": dcf_in["g"], "exit_multiple": dcf_in["exit_multiple"],
            "ebitda_terminal": dcf_in["ebitda_terminal"],
            "cash": dcf_in["cash"], "debt": dcf_in["debt"],
            "minority_interest": dcf_in["minority_interest"], "shares": dcf_in["shares"],
        },
        "comps": {"peers": basemart["peers"], "target": basemart["target"], "shares": basemart["comps_shares"]},
        "sotp": {"segments": basemart["sotp_segments"], "cash": basemart["sotp_cash"], "debt": basemart["sotp_debt"], "shares": basemart["sotp_shares"]},
        "summary": {"models": basemart["summary_models"], "current_price": basemart["summary_current_price"], "target_net_income": basemart["target"]["net_income"], "target_ebitda": basemart["target"]["ebitda"], "sotp_segments": basemart["sotp_segments"]},
    }

    r1 = client.post("/api/recalculate", json=params)
    assert r1.status_code == 200
    result1 = r1.json()

    sp = client.post("/api/projects", json={"name": "roundtrip", "ticker": "09992", "market": "HK", "payload": params})
    pid = sp.json()["id"]

    lp = client.get(f"/api/projects/{pid}")
    loaded_params = lp.json()["payload"]

    r2 = client.post("/api/recalculate", json=loaded_params)
    assert r2.status_code == 200
    result2 = r2.json()

    assert result2["summary"]["fair_value"] == pytest.approx(result1["summary"]["fair_value"], rel=1e-6)
    assert result2["dcf"]["gordon"]["implied_price"] == pytest.approx(result1["dcf"]["gordon"]["implied_price"], rel=1e-6)


# ---- 健康检查 + 版本 ----

def test_health_has_version():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert "version" in r.json()