"""对比范例表数据与 akshare 真实抓取数据的偏差。"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.data.pipeline import analyze, build_engine_inputs

FIXTURE = pathlib.Path(__file__).resolve().parent / "tests" / "fixtures" / "basemart.json"
basemart = json.loads(FIXTURE.read_text(encoding="utf-8"))

print("=" * 78)
print("范例表数据 vs akshare 真实抓取数据 偏差对比（09992.HK 泡泡玛特）")
print("=" * 78)

# 范例表关键数据
ref = {
    "base_revenue": basemart["forecast_assumptions"]["base_revenue"],
    "shares": basemart["dcf_inputs"]["shares"],
    "cash": basemart["dcf_inputs"]["cash"],
    "debt": basemart["dcf_inputs"]["debt"],
    "net_debt": basemart["target"]["net_debt"],
    "target_revenue": basemart["target"]["revenue"],
    "target_ebitda": basemart["target"]["ebitda"],
    "target_ebit": basemart["target"]["ebit"],
    "target_net_income": basemart["target"]["net_income"],
    "current_price": basemart["summary_current_price"],
}

print("\n[1] 范例表关键财务数据（basemart.json）：")
for k, v in ref.items():
    print(f"    {k:25s} = {v:>12.2f}")

# 真实抓取
print("\n[2] akshare 真实抓取中...")
std = analyze("09992", "HK")
inputs = build_engine_inputs(std)

real = {
    "base_revenue": inputs.get("base_revenue") or 0,
    "shares": inputs.get("shares") or 0,
    "cash": inputs.get("cash") or 0,
    "debt": inputs.get("debt") or 0,
    "net_debt": inputs.get("net_debt") or 0,
    "target_revenue": std.latest("revenue") or 0,
    "target_ebitda": std.latest("ebitda") or 0,
    "target_ebit": std.latest("ebit") or 0,
    "target_net_income": std.latest("net_income") or 0,
    "current_price": std.price or 0,
}

print("\n[3] 真实抓取关键财务数据：")
for k, v in real.items():
    print(f"    {k:25s} = {v:>12.2f}")

# 偏差对比
print("\n[4] 偏差对比：")
print(f"    {'指标':25s}  {'范例表':>12s}  {'真实抓取':>12s}  {'绝对偏差':>12s}  {'相对偏差':>10s}")
print(f"    {'-'*25}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*10}")

results = []
for k in ref:
    ref_val = ref[k]
    real_val = real[k]
    abs_diff = real_val - ref_val
    rel_diff = (abs_diff / abs(ref_val) * 100) if ref_val != 0 else float("inf")
    results.append((k, ref_val, real_val, abs_diff, rel_diff))
    print(f"    {k:25s}  {ref_val:>12.2f}  {real_val:>12.2f}  {abs_diff:>+12.2f}  {rel_diff:>+9.2f}%")

# 营收历史对比
print("\n[5] 营收历史对比（范例表仅有最终值 37,120.0）：")
hist_rev = std.history("revenue")
print(f"    真实抓取营收历史（{len(hist_rev)} 期）：")
for i, v in enumerate(hist_rev):
    print(f"      期 {i+1}: {v:>12.2f} 百万")
print(f"    范例表基准营收: {ref['base_revenue']:>12.2f} 百万")
print(f"    最新期偏差: {hist_rev[-1] - ref['base_revenue']:>+.2f} ({(hist_rev[-1] - ref['base_revenue']) / ref['base_revenue'] * 100:+.2f}%)")

# 估值结果对比
print("\n[6] 估值结果对比（自动假设 vs 范例精调假设）：")
print(f"    范例 DCF Gordon:  ¥273.42")
print(f"    范例 DCF Exit:    ¥370.75")
print(f"    范例 Comps P/E:   ¥232.04")
print(f"    范例 SOTP:        ¥327.54")
print(f"    范例 加权中枢:    ¥278.65")

# 读取真实抓取的估值结果
result_file = pathlib.Path(__file__).resolve().parent / "m2_real_fetch_result.json"
if result_file.exists():
    rr = json.loads(result_file.read_text(encoding="utf-8"))
    print(f"    真实 DCF Gordon:  ¥{rr['dcf_gordon_price']:.2f}  (偏差 {(rr['dcf_gordon_price']/273.42-1)*100:+.2f}%)")
    print(f"    真实 DCF Exit:    ¥{rr['dcf_exit_price']:.2f}  (偏差 {(rr['dcf_exit_price']/370.75-1)*100:+.2f}%)")

print("\n" + "=" * 78)
print("结论：")
rev_err = abs(hist_rev[-1] - ref["base_revenue"]) / ref["base_revenue"] * 100
shares_err = abs(real["shares"] - ref["shares"]) / ref["shares"] * 100
print(f"  营收偏差:   {rev_err:.2f}%  {'✓' if rev_err < 1 else '△'}")
print(f"  股数偏差:   {shares_err:.2f}%  {'✓' if shares_err < 1 else '△'}")
print(f"  现金偏差:   {abs(real['cash']-ref['cash'])/ref['cash']*100:.2f}%")
print(f"  债务偏差:   {abs(real['debt']-ref['debt'])/ref['debt']*100:.2f}%")
print(f"  净债务偏差: {abs(real['net_debt']-ref['net_debt'])/abs(ref['net_debt'])*100:.2f}%")
print("=" * 78)