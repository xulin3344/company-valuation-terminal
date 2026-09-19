"""测试不同公司API返回数据是否不同。"""
from fastapi.testclient import TestClient
from app.api.main import app

c = TestClient(app)
for ticker in ["09992", "00700", "03690"]:
    r = c.post("/api/analyze", json={"ticker": ticker, "market": "HK"})
    d = r.json()
    rev = d["standard_financials"]["income"].get("revenue", [None])
    s = d.get("result", {}).get("summary", {})
    fair = s.get("fair_value", 0)
    print(f"{ticker}: rev={rev[-1]:.0f}  fair={fair:.1f}  health={d['health']}")