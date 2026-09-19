from app.config.sotp_presets import get_sotp_preset, SOTP_PRESETS
from app.api.orchestrator import run_full_valuation


def test_sotp_presets_coverage():
    # 测试所有核心标的均能正确索引
    target_tickers = ["01810", "1810", "00700", "700", "03690", "3690", "09988", "BABA", "TSLA", "AAPL", "300750", "09992"]
    for t in target_tickers:
        preset = get_sotp_preset(t)
        assert preset is not None, f"Preset for {t} should not be None"
        assert len(preset["segments"]) > 0, f"Segments for {t} should not be empty"
        assert preset.get("weight") is not None


def test_xiaomi_sotp_valuation():
    preset = get_sotp_preset("01810")
    sotp_params = {
        "segments": preset["segments"],
        "cash": 78223.0,
        "debt": 13202.0,
        "shares": 26694.0,
    }
    params = {
        "wacc_inputs": {"rf": 0.04, "beta": 1.0, "erp": 0.06, "kd": 0.035, "weight_equity": 0.85, "tax_rate": 0.165},
        "forecast_assumptions": {
            "base_revenue": 450000.0,
            "growth": [0.12, 0.10, 0.08, 0.07, 0.06],
            "gross_margin": [0.21, 0.21, 0.22, 0.22, 0.22],
            "selling_ratio": [0.05] * 5,
            "admin_ratio": [0.03] * 5,
            "da_pct": [0.02] * 5,
            "capex_pct": [0.03] * 5,
            "tax_rate": 0.165,
            "nwc_pct_of_rev_delta": 0.1,
        },
        "dcf_params": {"g": 0.03, "exit_multiple": 12.0, "cash": 78223.0, "debt": 13202.0, "shares": 26694.0},
        "sotp": sotp_params,
        "summary": {
            "models": [
                {"key": "dcf_gordon", "label": "Gordon", "weight": 0.15},
                {"key": "dcf_exit", "label": "Exit", "weight": 0.15},
                {"key": "sotp", "label": "SOTP", "weight": 0.40},
            ],
            "current_price": 26.4,
            "sotp_segments": preset["segments"],
        },
    }
    res = run_full_valuation(params)
    assert "sotp" in res
    assert res["sotp"] is not None
    assert res["sotp"]["base"]["implied_price"] > 0
    assert len(res["sotp"]["contributions"]) == 4
    # 验证 SOTP 正常进入 used_models
    assert "sotp" in res["summary"]["used_models"]
    sotp_model = next(m for m in res["summary"]["models"] if m["key"] == "sotp")
    assert sotp_model["available"] is True
    assert sotp_model["weight"] == 0.40
