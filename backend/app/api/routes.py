"""FastAPI 路由：analyze / recalculate / comps pool / projects CRUD。"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Body, Response
from pydantic import BaseModel, Field

from ..data.pipeline import analyze as fetch_and_standardize, build_engine_inputs, build_forecast_assumptions
from ..data.providers.market_data_provider import fetch_analyst_estimates, fetch_dynamic_peers, fetch_market_overview
from ..data.models import StandardFinancials
from .orchestrator import run_full_valuation
from .pdf_export import generate_pdf
from . import store
from ..config.sotp_presets import get_sotp_preset


router = APIRouter(prefix="/api")


# ---- 请求/响应模型 ----

class AnalyzeRequest(BaseModel):
    ticker: str
    market: str = Field(..., description="HK, US or CN")



class RecalculateRequest(BaseModel):
    wacc_inputs: dict
    forecast_assumptions: dict
    dcf_params: Optional[dict] = None
    comps: Optional[dict] = None
    sotp: Optional[dict] = None
    summary: Optional[dict] = None


class SaveProjectRequest(BaseModel):
    name: str
    ticker: str
    market: str
    payload: dict
    project_id: Optional[str] = None


# ---- 预设可比公司池（Fix 3：按行业分组）----

PEERS_BY_INDUSTRY = {
    "consumer_ip": [
        {"name": "三丽鸥 (Sanrio)", "ticker": "8136.T", "market_cap": 43000, "net_debt": -12000, "revenue": 6200, "ebitda": 2150, "ebit": 1900, "net_income": 1450},
        {"name": "万代南梦宫控股 (Bandai Namco)", "ticker": "7832.T", "market_cap": 115000, "net_debt": -28000, "revenue": 50000, "ebitda": 7400, "ebit": 6450, "net_income": 4800},
        {"name": "孩之宝与美泰同业组 (Hasbro & Mattel)", "ticker": "HAS/MAT", "market_cap": 65000, "net_debt": 18000, "revenue": 42000, "ebitda": 6800, "ebit": 4500, "net_income": 3200},
        {"name": "华特迪士尼公司 (Walt Disney)", "ticker": "DIS", "market_cap": 1450000, "net_debt": 290000, "revenue": 650000, "ebitda": 125000, "ebit": 95000, "net_income": 58000},
    ],
    "tech_internet": [
        {"name": "Alphabet (Google)", "ticker": "GOOGL", "market_cap": 2100000, "net_debt": -100000, "revenue": 350000, "ebitda": 115000, "ebit": 95000, "net_income": 80000},
        {"name": "Meta Platforms", "ticker": "META", "market_cap": 1500000, "net_debt": -58000, "revenue": 160000, "ebitda": 72000, "ebit": 56000, "net_income": 46000},
        {"name": "Microsoft", "ticker": "MSFT", "market_cap": 3200000, "net_debt": -40000, "revenue": 245000, "ebitda": 125000, "ebit": 110000, "net_income": 88000},
        {"name": "Apple", "ticker": "AAPL", "market_cap": 3400000, "net_debt": 50000, "revenue": 390000, "ebitda": 135000, "ebit": 120000, "net_income": 100000},
    ],
    "generic": [],  # 通用：返回空池，用户自选
}

# 向后兼容
DEFAULT_PEERS_POOL = PEERS_BY_INDUSTRY["consumer_ip"]


@router.get("/search")
def search_endpoint(q: str = "", market: Optional[str] = None):
    """搜索股票代码与公司名称（支持中文、拼音、数字代码、带市场前后缀）。"""
    q = (q or "").strip()
    if not q:
        return {"results": []}

    from ..data.stock_lookup import search_stocks_remote, COMMON_STOCKS, clean_query_string
    clean_q, inferred_mkt = clean_query_string(q)
    target_market = inferred_mkt or market

    results = []
    seen = set()

    # 1. 优先匹配本地精选常用股票
    q_lower = clean_q.lower()
    for item in COMMON_STOCKS:
        if (
            q_lower in item["name"].lower()
            or q_lower in item["ticker"].lower()
            or q_lower in item["pinyin"].lower()
            or (clean_q.isdigit() and item["ticker"].lstrip("0") == clean_q.lstrip("0"))
        ):
            key = f"{item['market']}:{item['ticker']}"
            if key not in seen:
                seen.add(key)
                results.append(item)

    # 2. 实时网络搜索
    try:
        remote = search_stocks_remote(clean_q, limit=10)
        for item in remote:
            key = f"{item['market']}:{item['ticker']}"
            if key not in seen:
                seen.add(key)
                results.append(item)
    except Exception:
        pass

    if target_market:
        m = target_market.upper()
        results.sort(key=lambda x: 0 if x.get("market") == m else 1)

    return {"results": results[:10]}



# ---- /api/analyze ----

@router.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    """抓取财报 → 标准化 → 自动假设 → 引擎全跑 → 完整估值结果。"""
    t0 = time.time()
    from ..data.stock_lookup import resolve_stock
    resolved = resolve_stock(req.ticker, preferred_market=req.market)
    company_name = ""
    if resolved:
        company_name = resolved.get("name", "")
        req.ticker = resolved.get("ticker", req.ticker)
        req.market = resolved.get("market", req.market)

    try:
        std = fetch_and_standardize(req.ticker, req.market)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"data fetch failed: {exc}")

    try:
        inputs = build_engine_inputs(std)
        fa = build_forecast_assumptions(std)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"assumption generation failed: {exc}")


    # 升级 1：合并动态 WACC 参数（Rf/Beta/资本结构来自市场实时数据）
    wacc_defaults = inputs.get("default_wacc_inputs") or {"rf": 0.042, "erp": 0.050, "size_premium": 0.0, "tax_rate": 0.21}
    wacc_config = inputs.get("wacc_config", {})
    dynamic = inputs.get("dynamic_wacc_params", {})
    auto = inputs.get("auto_wacc_params", {})
    wacc_inputs = {
        **wacc_defaults,
        "erp": wacc_config.get("erp", wacc_defaults.get("erp", 0.050)),
        "tax_rate": wacc_config.get("default_tax_rate", wacc_defaults.get("tax_rate", 0.21)),
        "rf": dynamic.get("rf", wacc_defaults.get("rf", 0.042)),
        "beta": dynamic.get("beta", auto.get("beta", 1.0)),
        "kd": dynamic.get("kd", auto.get("kd", 0.035)),
        "weight_equity": dynamic.get("weight_equity", auto.get("weight_equity", 0.98)),
    }

    forecast_assumptions = {
        "base_revenue": fa.base_revenue,
        "growth": fa.growth,
        "gross_margin": fa.gross_margin,
        "selling_ratio": fa.selling_ratio,
        "admin_ratio": fa.admin_ratio,
        "da_pct": fa.da_pct,
        "capex_pct": fa.capex_pct,
        "nwc_pct_of_rev_delta": fa.nwc_pct_of_rev_delta,
        "tax_rate": fa.tax_rate,
        "ebit_margin": fa.ebit_margin,
    }

    shares = inputs.get("shares") or 1.0
    cash = inputs.get("cash") or 0.0
    debt = inputs.get("debt") or 0.0
    price = inputs.get("price") or 0.0

    dcf_params = {
        "g": 0.03,
        "exit_multiple": 16.0,
        "cash": cash,
        "debt": debt,
        "shares": shares,
        "sensitivity": {
            "wacc_list": [0.085, 0.09, 0.095, 0.098, 0.102, 0.108, 0.115],
            "g_list": [0.02, 0.025, 0.03, 0.035, 0.04, 0.045],
        },
    }

    target = inputs.get("target")
    comps = None
    if target and shares:
        # 升级 3：尝试动态获取可比公司实时数据
        try:
            dynamic_peers = fetch_dynamic_peers(req.ticker, max_peers=6)
        except Exception:
            dynamic_peers = []
        peers_list = dynamic_peers if dynamic_peers else DEFAULT_PEERS_POOL
        comps = {
            "peers": peers_list,
            "peers_source": "dynamic" if dynamic_peers else "static_fallback",
            "target": {
                "revenue": target.revenue,
                "ebitda": target.ebitda,
                "ebit": target.ebit,
                "net_income": target.net_income,
                "net_debt": target.net_debt,
            },
            "shares": shares,
        }

    sotp_preset = get_sotp_preset(req.ticker)
    sotp_segments = sotp_preset["segments"] if sotp_preset else []

    sotp_params = None
    sotp_weight = sotp_preset.get("weight", 0.2) if sotp_preset else 0.2
    rem_weight = round((1.0 - sotp_weight) / 4.0, 4) if sotp_preset else 0.2

    summary = {
        "models": [
            {"key": "dcf_gordon", "label": "DCF 永续增长法", "weight": rem_weight},
            {"key": "dcf_exit", "label": "DCF 退出乘数法", "weight": rem_weight},
            {"key": "comps_pe", "label": "可比公司 P/E 乘数法", "weight": rem_weight},
            {"key": "comps_ev_ebitda", "label": "可比公司 EV/EBITDA 乘数法", "weight": rem_weight},
            {"key": "sotp", "label": "分部加总估值法 (SOTP)", "weight": sotp_weight},
        ],
        "current_price": price or 1.0,
        "target_net_income": target.net_income if target else None,
        "target_ebitda": target.ebitda if target else None,
        "sotp_segments": sotp_segments,
    }

    if sotp_preset:
        sotp_params = {
            "segments": sotp_segments,
            "cash": cash,
            "debt": debt,
            "shares": shares,
        }

    params = {
        "wacc_inputs": wacc_inputs,
        "forecast_assumptions": forecast_assumptions,
        "dcf_params": dcf_params,
        "comps": comps,
        "sotp": sotp_params,
        "summary": summary,
    }

    try:
        result = run_full_valuation(params)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"valuation engine failed: {exc}")

    elapsed = time.time() - t0
    # 升级 2+4：采集分析师预期和行情概览（异步友好，失败不阻塞）
    analyst_data = {}
    market_overview = {}
    try:
        analyst_data = fetch_analyst_estimates(req.ticker)
    except Exception:
        pass
    try:
        market_overview = fetch_market_overview(req.ticker)
    except Exception:
        pass

    response_payload = {
        "ticker": std.ticker,
        "company_name": company_name or std.ticker,
        "market": std.market,
        "source": std.source,
        "currency": std.currency,

        "health": std.quality.health if std.quality else None,
        "analyst_estimates": analyst_data,
        "market_overview": market_overview,
        "wacc_sources": {
            "rf_source": dynamic.get("rf_source", "fallback"),
            "beta_source": dynamic.get("beta_source", "fallback"),
            "cap_structure_source": dynamic.get("cap_structure_source", "fallback"),
        },
        "quality": {
            "missing": std.quality.missing if std.quality else {},
            "degraded_models": std.quality.degraded_models if std.quality else [],
            "derived_accounts": std.quality.derived_accounts if std.quality else [],
            "warnings": std.quality.warnings if std.quality else [],
        },
        "standard_financials": {
            "periods": std.periods,
            "income": std.income,
            "balance": std.balance,
            "price": std.price,
            "net_debt": std.net_debt,
        },
        "assumptions": params,
        "result": result,
        "elapsed_seconds": round(elapsed, 2),
    }
    return _sanitize_floats(response_payload)


def _sanitize_floats(obj):
    import math
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_floats(v) for v in obj]
    return obj



# ---- /api/recalculate ----

@router.post("/recalculate")
def recalculate_endpoint(req: RecalculateRequest):
    """传入完整假设包 → 引擎重跑 → 新结果（不抓取）。"""
    try:
        result = run_full_valuation(req.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"valuation engine failed: {exc}")
    return result


# ---- /api/comps/pool ----

@router.get("/comps/pool")
def comps_pool_endpoint(industry: str = "consumer_ip"):
    """获取预设可比公司池（支持按行业筛选）。"""
    peers = PEERS_BY_INDUSTRY.get(industry, [])
    return {"peers": peers, "available_industries": list(PEERS_BY_INDUSTRY.keys())}


# ---- /api/projects CRUD ----

@router.post("/projects")
def save_project_endpoint(req: SaveProjectRequest):
    """保存项目（新建或更新）。"""
    return store.save_project(req.name, req.ticker, req.market, req.payload, req.project_id)


@router.get("/projects")
def list_projects_endpoint():
    """列出全部项目。"""
    return {"projects": store.list_projects()}


@router.get("/projects/export-all")
def export_all_projects_endpoint():
    """一键导出全部项目（合并 JSON 数组）。"""
    projects = store.list_projects()
    out = []
    for proj in projects:
        try:
            result = run_full_valuation(proj["payload"])
        except Exception:
            result = None
        out.append({
            "project": {
                "id": proj["id"],
                "name": proj["name"],
                "ticker": proj["ticker"],
                "market": proj["market"],
                "created_at": proj["created_at"],
                "updated_at": proj["updated_at"],
            },
            "assumptions": proj["payload"],
            "result": result,
        })
    return {"projects": out}


@router.get("/projects/export-all/pdf")
def export_all_projects_pdf_endpoint():
    """一键导出全部项目为 PDF 压缩包（ZIP）。"""
    import io
    import zipfile

    projects = store.list_projects()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for proj in projects:
            try:
                result = run_full_valuation(proj["payload"])
            except Exception:
                continue
            pdf_bytes = generate_pdf(
                {"name": proj["name"], "ticker": proj["ticker"], "market": proj["market"], "updated_at": proj["updated_at"]},
                proj["payload"],
                result,
            )
            safe_name = proj["ticker"].replace(".", "_")
            zf.writestr(f"{safe_name}_valuation.pdf", pdf_bytes)
    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=all_valuations.zip"},
    )


@router.post("/projects/export-selected")
def export_selected_projects_endpoint(ids: list = Body(...)):
    """导出选中项目为 PDF 压缩包（ZIP）。"""
    import io
    import zipfile

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for pid in ids:
            proj = store.load_project(pid)
            if not proj:
                continue
            try:
                result = run_full_valuation(proj["payload"])
            except Exception:
                continue
            pdf_bytes = generate_pdf(
                {"name": proj["name"], "ticker": proj["ticker"], "market": proj["market"], "updated_at": proj["updated_at"]},
                proj["payload"],
                result,
            )
            safe_name = proj["ticker"].replace(".", "_")
            zf.writestr(f"{safe_name}_valuation.pdf", pdf_bytes)
    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=selected_valuations.zip"},
    )


@router.get("/projects/{project_id}")
def load_project_endpoint(project_id: str):
    """载入单个项目。"""
    proj = store.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="project not found")
    return proj


@router.delete("/projects/{project_id}")
def delete_project_endpoint(project_id: str):
    """删除项目。"""
    deleted = store.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="project not found")
    return {"deleted": True, "id": project_id}


# ---- /api/projects/{id}/export ----

@router.get("/projects/{project_id}/export")
def export_project_endpoint(project_id: str):
    """导出项目完整估值结果（载入 → 重算 → 返回假设+结果 JSON）。"""
    proj = store.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="project not found")
    try:
        result = run_full_valuation(proj["payload"])
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"valuation engine failed: {exc}")
    return {
        "project": {
            "id": proj["id"],
            "name": proj["name"],
            "ticker": proj["ticker"],
            "market": proj["market"],
            "created_at": proj["created_at"],
            "updated_at": proj["updated_at"],
        },
        "assumptions": proj["payload"],
        "result": result,
    }


@router.get("/projects/{project_id}/export/pdf")
def export_project_pdf_endpoint(project_id: str):
    """导出项目估值结果为 PDF 文件。"""
    proj = store.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="project not found")
    try:
        result = run_full_valuation(proj["payload"])
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"valuation engine failed: {exc}")
    pdf_bytes = generate_pdf(
        {"name": proj["name"], "ticker": proj["ticker"], "market": proj["market"], "updated_at": proj["updated_at"]},
        proj["payload"],
        result,
    )
    return Response(content=pdf_bytes, media_type="application/pdf",
                     headers={"Content-Disposition": f'attachment; filename="{proj["ticker"]}_valuation.pdf"'})
