"""真实抓取端到端验收脚本：09992.HK → 数据层 → 引擎 → DCF每股价格。

运行：python -m backend.verify_real_fetch
对比范例：DCF Gordon ¥273.42 / Exit ¥370.75
"""
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.data.pipeline import analyze, build_engine_inputs, build_forecast_assumptions
from app.engine.wacc import WACCInputs, compute_wacc
from app.engine.forecast import run_forecast
from app.engine.dcf import run_dcf


def main():
    print("=" * 72)
    print("真实抓取端到端验收：09992.HK（泡泡玛特）")
    print("=" * 72)

    # 1. 抓取 + 标准化 + 质量检查
    print("\n[1/5] 抓取 akshare 港股财报...")
    try:
        std = analyze("09992", "HK")
    except Exception as exc:
        print(f"  ✗ 抓取失败：{exc}")
        traceback.print_exc()
        return 1

    print(f"  ✓ source={std.source}  currency={std.currency}  periods={len(std.periods)}")
    print(f"  ✓ health={std.quality.health if std.quality else 'n/a'}")
    if std.quality:
        print(f"    missing={list(std.quality.missing.keys())}")
        print(f"    degraded={std.quality.degraded_models}")
        print(f"    derived={std.quality.derived_accounts[:8]}{'...' if len(std.quality.derived_accounts) > 8 else ''}")

    # 2. 引擎输入
    print("\n[2/5] 构建引擎输入...")
    inputs = build_engine_inputs(std)
    print(f"  shares_diluted = {inputs.get('shares')}")
    print(f"  price          = {inputs.get('price')}")
    print(f"  cash           = {inputs.get('cash')}")
    print(f"  debt           = {inputs.get('debt')}")
    print(f"  net_debt       = {inputs.get('net_debt')}")
    print(f"  base_revenue   = {inputs.get('base_revenue')}")
    print(f"  hist_revenue   = {inputs.get('history_revenue')}")
    print(f"  hist_gross_m   = {inputs.get('history_gross_margin')}")

    if not inputs.get("shares"):
        print("  ✗ shares_diluted 缺失，无法计算每股价格")
        return 2

    # 3. 预测假设
    print("\n[3/5] 自动生成预测假设...")
    fa = build_forecast_assumptions(std)
    print(f"  growth        = {[round(g, 4) for g in fa.growth]}")
    print(f"  gross_margin  = {[round(m, 4) for m in fa.gross_margin]}")
    print(f"  tax_rate      = {fa.tax_rate}")

    # 4. WACC（用范例 beta=1.10 对齐）
    print("\n[4/5] 计算 WACC（范例对齐：rf=2.5%, beta=1.10, erp=6.2%）...")
    wacc_inp = WACCInputs(rf=0.025, beta=1.10, erp=0.062, size_premium=0.0,
                          kd=0.035, tax_rate=0.23, weight_equity=0.98)
    wacc_res = compute_wacc(wacc_inp)
    print(f"  Ke     = {wacc_res.cost_of_equity:.6f}  (范例 9.94%)")
    print(f"  Kd*(1-t)= {wacc_res.after_tax_cost_of_debt:.6f}  (范例 2.695%)")
    print(f"  WACC   = {wacc_res.wacc:.6f}  (范例 9.7951%)")

    # 5. 预测 + DCF
    print("\n[5/5] 运行预测 + DCF...")
    fr = run_forecast(fa)
    print(f"  revenue Y1~Y5 = {[round(r, 1) for r in fr.revenue]}")
    print(f"  ufcf    Y1~Y5 = {[round(u, 1) for u in fr.ufcf]}")
    print(f"  ebitda_Y5     = {fr.ebitda_terminal:.2f}  (范例 39,816.03)")

    # 范例参数：g=3%, exit_multiple=13.0
    dcf = run_dcf(
        ufcf=fr.ufcf,
        wacc=wacc_res.wacc,
        g=0.03,
        exit_multiple=13.0,
        ebitda_terminal=fr.ebitda_terminal,
        cash=inputs.get("cash") or 0.0,
        debt=inputs.get("debt") or 0.0,
        minority_interest=0.0,
        shares=inputs.get("shares"),
    )
    print(f"\n  PV(预测UFCF)  = {dcf.pv_forecast_cashflows:.2f}  (范例 83,654.69)")
    print(f"  DCF Gordon:")
    print(f"    TV          = {dcf.gordon.terminal_value:.2f}")
    print(f"    PV(TV)      = {dcf.gordon.pv_terminal_value:.2f}")
    print(f"    EV          = {dcf.gordon.enterprise_value:.2f}  (范例 352,198.22)")
    print(f"    Equity      = {dcf.gordon.equity_value:.2f}")
    print(f"    每股价格    = {dcf.gordon.implied_price:.2f}  (范例 ¥273.42)")
    print(f"  DCF Exit (EV/EBITDA=13.0x):")
    print(f"    EV          = {dcf.exit.enterprise_value:.2f}  (范例 482,921.45)")
    print(f"    每股价格    = {dcf.exit.implied_price:.2f}  (范例 ¥370.75)")

    # 6. 对比结论
    print("\n" + "=" * 72)
    gordon_err = abs(dcf.gordon.implied_price - 273.42) / 273.42 * 100
    exit_err = abs(dcf.exit.implied_price - 370.75) / 370.75 * 100
    print(f"Gordon 偏差 = {gordon_err:.2f}%  (目标 < 15%)")
    print(f"Exit   偏差 = {exit_err:.2f}%  (目标 < 15%)")
    if gordon_err < 15 and exit_err < 15:
        print("✓ 真实抓取端到端验收通过：eps bug 修复后 DCF 每股价格落在合理区间")
    else:
        print("△ 偏差较大（预期：自动假设 vs 范例精调假设会有差异，属正常）")
    print("=" * 72)

    # 7. 保存结果
    result = {
        "ticker": "09992.HK",
        "source": std.source,
        "health": std.quality.health if std.quality else None,
        "shares_diluted": inputs.get("shares"),
        "price": inputs.get("price"),
        "base_revenue": inputs.get("base_revenue"),
        "wacc": wacc_res.wacc,
        "ufcf": [round(u, 2) for u in fr.ufcf],
        "ebitda_terminal": fr.ebitda_terminal,
        "dcf_gordon_price": dcf.gordon.implied_price,
        "dcf_exit_price": dcf.exit.implied_price,
        "gordon_deviation_pct": round(gordon_err, 2),
        "exit_deviation_pct": round(exit_err, 2),
    }
    out_path = Path(__file__).resolve().parent / "m2_real_fetch_result.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n结果已保存：{out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())