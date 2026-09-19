"""验证 /api/analyze 端到端 ≤30s 门禁。"""
import time
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)
t0 = time.time()
r = client.post("/api/analyze", json={"ticker": "09992", "market": "HK"})
elapsed = time.time() - t0
print(f"status={r.status_code}  elapsed={elapsed:.1f}s")
if r.status_code == 200:
    d = r.json()
    print(f"health={d['health']}  source={d['source']}")
    rev = d["standard_financials"]["income"]["revenue"][-1]
    print(f"revenue_latest={rev:.1f}")
    s = d["result"]["summary"]
    if s:
        print(f"fair_value={s['fair_value']:.2f}  rating={s['rating']}")
    print(f"elapsed_api={d['elapsed_seconds']}s")
    print(f"gate_30s={'PASS' if elapsed <= 30 else 'FAIL'}")
else:
    print(r.json())