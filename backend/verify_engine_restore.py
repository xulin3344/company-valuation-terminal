"""证明引擎逻辑还原无偏差：传入范例表完整假设包 → 输出 vs 范例预期。"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.api.orchestrator import run_full_valuation

fx = json.loads(pathlib.Path("tests/fixtures/basemart.json").read_text(encoding="utf-8"))

params = {
    "wacc_inputs": fx["wacc_inputs"],
    "forecast_assumptions": fx["forecast_assumptions"],
    "dcf_params": {
        "g": fx["dcf_inputs"]["g"],
        "exit_multiple": fx["dcf_inputs"]["exit_multiple"],
        "ebitda_terminal": fx["dcf_inputs"]["ebitda_terminal"],
        "cash": fx["dcf_inputs"]["cash"],
        "debt": fx["dcf_inputs"]["debt"],
        "minority_interest": fx["dcf_inputs"]["minority_interest"],
        "shares": fx["dcf_inputs"]["shares"],
        "sensitivity": {"wacc_list": fx["dcf_expected"]["sensitivity"]["wacc_list"], "g_list": fx["dcf_expected"]["sensitivity"]["g_list"]},
    },
    "comps": {"peers": fx["peers"], "target": fx["target"], "shares": fx["comps_shares"]},
    "sotp": {"segments": fx["sotp_segments"], "cash": fx["sotp_cash"], "debt": fx["sotp_debt"], "shares": fx["sotp_shares"]},
    "summary": {"models": fx["summary_models"], "current_price": fx["summary_current_price"], "target_net_income": fx["target"]["net_income"], "target_ebitda": fx["target"]["ebitda"], "sotp_segments": fx["sotp_segments"]},
}

result = run_full_valuation(params)

print("=" * 80)
print("引擎逻辑还原验证：传入范例表完整假设 → 输出 vs 范例预期")
print("=" * 80)

checks = [
    ("WACC", result["wacc"]["wacc"], fx["wacc_expected"]["wacc_precise"]),
    ("DCF Gordon 每股", result["dcf"]["gordon"]["implied_price"], fx["dcf_expected"]["gordon"]["implied_price"]),
    ("DCF Exit 每股", result["dcf"]["exit"]["implied_price"], fx["dcf_expected"]["exit"]["implied_price"]),
    ("Comps P/E", result["comps"]["methods"]["pe"]["implied_price"], fx["comps_expected"]["price_pe"]),
    ("Comps EV/EBITDA", result["comps"]["methods"]["ev_ebitda"]["implied_price"], fx["comps_expected"]["price_ev_ebitda"]),
    ("Comps EV/EBIT", result["comps"]["methods"]["ev_ebit"]["implied_price"], fx["comps_expected"]["price_ev_ebit"]),
    ("Comps EV/Sales", result["comps"]["methods"]["ev_sales"]["implied_price"], fx["comps_expected"]["price_ev_sales"]),
    ("SOTP Bear", result["sotp"]["bear"]["implied_price"], fx["sotp_expected"]["price"][0]),
    ("SOTP Base", result["sotp"]["base"]["implied_price"], fx["sotp_expected"]["price"][1]),
    ("SOTP Bull", result["sotp"]["bull"]["implied_price"], fx["sotp_expected"]["price"][2]),
    ("汇总加权中枢", result["summary"]["fair_value"], fx["summary_expected"]["fair_value"]),
    ("汇总加权下限", result["summary"]["weighted_low"], fx["summary_expected"]["weighted_low"]),
    ("汇总加权上限", result["summary"]["weighted_high"], fx["summary_expected"]["weighted_high"]),
    ("汇总包络下限", result["summary"]["full_low"], fx["summary_expected"]["full_low"]),
    ("汇总包络上限", result["summary"]["full_high"], fx["summary_expected"]["full_high"]),
    ("上行空间", result["summary"]["upside"], fx["summary_expected"]["upside"]),
]

print(f"\n  {'指标':20s}  {'引擎输出':>12s}  {'范例预期':>12s}  {'偏差':>10s}")
print(f"  {'-'*20}  {'-'*12}  {'-'*12}  {'-'*10}")

all_pass = True
for name, actual, expected in checks:
    diff = abs(actual - expected) / abs(expected) * 100 if expected != 0 else 0
    ok = "✓" if diff < 0.1 else "✗"
    if diff >= 0.1:
        all_pass = False
    print(f"  {name:20s}  {actual:>12.4f}  {expected:>12.4f}  {diff:>8.4f}%  {ok}")

print(f"\n  评级: {result['summary']['rating']}")
print(f"  范例: {fx['summary_expected']['rating']}")

print("\n" + "=" * 80)
if all_pass:
    print("✅ 结论：引擎逻辑还原 100% 通过——全部 16 项指标偏差 < 0.1%")
    print("   传入范例表同样的假设 → 输出与范例表完全一致")
    print("   逻辑还原没有问题。")
else:
    print("✗ 存在偏差 >= 0.1% 的指标")
print("=" * 80)