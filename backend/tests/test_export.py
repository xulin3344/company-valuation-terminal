"""导出功能测试。"""
import json
import pathlib
import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.api import store

client = TestClient(app)
FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "basemart.json"


def _payload():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return {"wacc_inputs": fx["wacc_inputs"], "forecast_assumptions": fx["forecast_assumptions"]}


def test_export_project(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    r = client.post("/api/projects", json={"name": "测试", "ticker": "09992", "market": "HK", "payload": _payload()})
    pid = r.json()["id"]
    r2 = client.get(f"/api/projects/{pid}/export")
    assert r2.status_code == 200
    assert "result" in r2.json()


def test_export_404(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    assert client.get("/api/projects/nonexistent/export").status_code == 404


def test_export_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    r = client.post("/api/projects", json={"name": "PDF测试", "ticker": "09992", "market": "HK", "payload": _payload()})
    pid = r.json()["id"]
    r2 = client.get(f"/api/projects/{pid}/export/pdf")
    assert r2.status_code == 200
    assert r2.headers["content-type"] == "application/pdf"
    assert r2.content[:4] == b"%PDF"


def test_export_all_json(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    client.post("/api/projects", json={"name": "A", "ticker": "09992", "market": "HK", "payload": _payload()})
    client.post("/api/projects", json={"name": "B", "ticker": "00700", "market": "HK", "payload": _payload()})
    r = client.get("/api/projects/export-all")
    assert r.status_code == 200
    assert len(r.json()["projects"]) == 2


def test_export_all_pdf_zip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    client.post("/api/projects", json={"name": "A", "ticker": "09992", "market": "HK", "payload": _payload()})
    client.post("/api/projects", json={"name": "B", "ticker": "00700", "market": "HK", "payload": _payload()})
    r = client.get("/api/projects/export-all/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert r.content[:2] == b"PK"
    assert len(r.content) > 2000


def test_export_selected_zip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "test.db")
    r1 = client.post("/api/projects", json={"name": "A", "ticker": "09992", "market": "HK", "payload": _payload()})
    client.post("/api/projects", json={"name": "B", "ticker": "00700", "market": "HK", "payload": _payload()})
    r = client.post("/api/projects/export-selected", json=[r1.json()["id"]])
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert r.content[:2] == b"PK"
