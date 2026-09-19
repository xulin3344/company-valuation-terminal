"""PDF 导出：将估值结果生成 PDF 报告。"""
import io
import os
from pathlib import Path
from fpdf import FPDF


def _fmt(v, d=2):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:,.{d}f}"
    return str(v)


def _pct(v, d=2):
    if v is None:
        return "—"
    return f"{v * 100:.{d}f}%"


def _find_cjk_font():
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def generate_pdf(project: dict, assumptions: dict, result: dict) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    cjk_font = _find_cjk_font()
    if cjk_font:
        pdf.add_font("CJK", "", cjk_font)
        pdf.add_font("CJK", "B", cjk_font)
        font_family = "CJK"
    else:
        font_family = "Helvetica"

    pdf.add_page()

    pdf.set_font(font_family, "B", 16)
    pdf.cell(0, 10, f"Valuation Report - {project.get('name', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, "", 10)
    pdf.cell(0, 6, f"Ticker: {project.get('ticker', '')}  Market: {project.get('market', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Date: {project.get('updated_at', '')[:10]}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    w = result.get("wacc", {})
    pdf.set_font(font_family, "B", 12)
    pdf.cell(0, 8, "WACC", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, "", 10)
    pdf.cell(0, 6, f"  Cost of Equity: {_pct(w.get('cost_of_equity'))}   After-tax Kd: {_pct(w.get('after_tax_cost_of_debt'))}   WACC: {_pct(w.get('wacc'))}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    f = result.get("forecast", {})
    pdf.set_font(font_family, "B", 12)
    pdf.cell(0, 8, "Forecast (5Y)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, "", 9)
    rev = f.get("revenue", [])
    ufcf = f.get("ufcf", [])
    pdf.cell(0, 6, f"  Revenue Y1~Y5: {', '.join(_fmt(v, 0) for v in rev)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  UFCF Y1~Y5: {', '.join(_fmt(v, 0) for v in ufcf)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  EBITDA Y5: {_fmt(f.get('ebitda_terminal'), 0)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    dcf = result.get("dcf", {})
    if dcf:
        pdf.set_font(font_family, "B", 12)
        pdf.cell(0, 8, "DCF", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, "", 10)
        g = dcf.get("gordon", {})
        e = dcf.get("exit", {})
        pdf.cell(0, 6, f"  Gordon:  EV={_fmt(g.get('enterprise_value'), 0)}  Price={_fmt(g.get('implied_price'))}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"  Exit:    EV={_fmt(e.get('enterprise_value'), 0)}  Price={_fmt(e.get('implied_price'))}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    comps = result.get("comps", {})
    if comps and comps.get("methods"):
        pdf.set_font(font_family, "B", 12)
        pdf.cell(0, 8, "Comps", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, "", 10)
        for k, m in comps["methods"].items():
            pdf.cell(0, 6, f"  {k}:  multiple={_fmt(m.get('multiple_used'))}  price={_fmt(m.get('implied_price'))}  range=[{_fmt(m.get('low_price'))}, {_fmt(m.get('high_price'))}]", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"  Consensus: {_fmt(comps.get('consensus_price'))}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    sotp = result.get("sotp", {})
    if sotp:
        pdf.set_font(font_family, "B", 12)
        pdf.cell(0, 8, "SOTP", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, "", 10)
        for label in ("bear", "base", "bull"):
            s = sotp.get(label, {})
            pdf.cell(0, 6, f"  {label}:  EV={_fmt(s.get('enterprise_value'), 0)}  Price={_fmt(s.get('implied_price'))}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    s = result.get("summary", {})
    if s:
        pdf.set_font(font_family, "B", 12)
        pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, "", 10)
        pdf.cell(0, 6, f"  Fair Value: {_fmt(s.get('fair_value'))}   Range: [{_fmt(s.get('weighted_low'))}, {_fmt(s.get('weighted_high'))}]", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"  Envelope: [{_fmt(s.get('full_low'))}, {_fmt(s.get('full_high'))}]   Upside: {_pct(s.get('upside'))}", new_x="LMARGIN", new_y="NEXT")
        rating = s.get("rating", "")
        pdf.cell(0, 6, f"  Rating: {rating}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    pdf.set_font(font_family, "", 8)
    pdf.multi_cell(0, 4, "Disclaimer: This report is for reference only and does not constitute investment advice. Valuation results are highly sensitive to assumptions. Users should exercise independent judgment and consult licensed advisors.")

    return bytes(pdf.output())


__all__ = ["generate_pdf"]