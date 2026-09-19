"""估值引擎全跑编排器：把 M1 各模块串联为一次完整估值。

run_full_valuation(params) → 完整估值结果 dict
- WACC → forecast → DCF (gordon + exit + sensitivity)
- Comps (peers + target → 4路 + consensus)
- SOTP (segments → 3情境 + 敏感性)
- Summary (5模型加权 + 降级 + 评级)
"""
from ..engine.wacc import WACCInputs, compute_wacc
from ..engine.forecast import ForecastAssumptions, run_forecast
from ..engine.dcf import run_dcf, dcf_sensitivity
from ..engine.comps import Peer, TargetFinancials, comps_valuation, peer_multiples, stats
from ..engine.sotp import Segment, sotp_valuation, sotp_sensitivity
from ..engine.summary import ModelOutput, summarize, apply_degradation
from ..engine.errors import EngineError


def _to_peer(p: dict) -> Peer:
    return Peer(
        name=p["name"],
        ticker=p.get("ticker", ""),
        market_cap=p["market_cap"],
        net_debt=p["net_debt"],
        revenue=p["revenue"],
        ebitda=p["ebitda"],
        ebit=p["ebit"],
        net_income=p["net_income"],
    )


def _to_segment(s: dict) -> Segment:
    return Segment(
        name=s["name"],
        ebit=s["ebit"],
        bear_mult=s["bear_mult"],
        base_mult=s["base_mult"],
        bull_mult=s["bull_mult"],
    )


def _run_wacc(inp: dict) -> dict:
    res = compute_wacc(WACCInputs(**inp))
    return {
        "cost_of_equity": res.cost_of_equity,
        "after_tax_cost_of_debt": res.after_tax_cost_of_debt,
        "wacc": res.wacc,
        "weight_equity": res.weight_equity,
        "weight_debt": res.weight_debt,
    }


def _run_forecast(a: dict) -> dict:
    fa = ForecastAssumptions(**a)
    fr = run_forecast(fa)
    return {
        "revenue": fr.revenue,
        "gross_profit": fr.gross_profit,
        "selling_expense": fr.selling_expense,
        "admin_expense": fr.admin_expense,
        "ebit": fr.ebit,
        "nopat": fr.nopat,
        "da": fr.da,
        "capex": fr.capex,
        "nwc_delta": fr.nwc_delta,
        "ufcf": fr.ufcf,
        "ebit_terminal": fr.ebit_terminal,
        "ebitda_terminal": fr.ebitda_terminal,
    }


def _run_dcf(dcf_params: dict, forecast: dict, wacc: dict) -> dict:
    ufcf = dcf_params.get("ufcf") or forecast["ufcf"]
    wacc_val = dcf_params.get("wacc") or wacc["wacc"]
    ebitda_terminal = dcf_params.get("ebitda_terminal") or forecast["ebitda_terminal"]
    res = run_dcf(
        ufcf=ufcf,
        wacc=wacc_val,
        g=dcf_params["g"],
        exit_multiple=dcf_params["exit_multiple"],
        ebitda_terminal=ebitda_terminal,
        cash=dcf_params["cash"],
        debt=dcf_params["debt"],
        minority_interest=dcf_params.get("minority_interest", 0.0),
        shares=dcf_params["shares"],
    )
    sens = None
    sens_cfg = dcf_params.get("sensitivity")
    if sens_cfg:
        sens_matrix = dcf_sensitivity(
            ufcf=ufcf,
            wacc_list=sens_cfg["wacc_list"],
            g_list=sens_cfg["g_list"],
            cash=dcf_params["cash"],
            debt=dcf_params["debt"],
            minority_interest=dcf_params.get("minority_interest", 0.0),
            shares=dcf_params["shares"],
        )
        sens = {"wacc_list": sens_cfg["wacc_list"], "g_list": sens_cfg["g_list"], "matrix": sens_matrix}

    return {
        "pv_forecast_cashflows": res.pv_forecast_cashflows,
        "discount_factors": res.discount_factors,
        "pv_of_ufcf": res.pv_of_ufcf,
        "gordon": {
            "terminal_value": res.gordon.terminal_value,
            "pv_terminal_value": res.gordon.pv_terminal_value,
            "enterprise_value": res.gordon.enterprise_value,
            "equity_value": res.gordon.equity_value,
            "implied_price": res.gordon.implied_price,
        },
        "exit": {
            "terminal_value": res.exit.terminal_value,
            "pv_terminal_value": res.exit.pv_terminal_value,
            "enterprise_value": res.exit.enterprise_value,
            "equity_value": res.exit.equity_value,
            "implied_price": res.exit.implied_price,
        },
        "sensitivity": sens,
    }


def _run_comps(comps_params: dict) -> dict:
    peers = [_to_peer(p) for p in comps_params["peers"]]
    target = TargetFinancials(**comps_params["target"])
    shares = comps_params["shares"]
    res = comps_valuation(peers, target, shares)

    multiples = peer_multiples(peers)
    multiples_out = {}
    for attr in ("ev_sales", "ev_ebitda", "ev_ebit", "pe"):
        values = [getattr(m, attr) for m in multiples]
        st = stats(values)
        multiples_out[attr] = {
            "maximum": st.maximum,
            "p75": st.p75,
            "mean": st.mean,
            "median": st.median,
            "p25": st.p25,
            "minimum": st.minimum,
        }

    methods_out = {}
    for key, m in res.methods.items():
        methods_out[key] = {
            "multiple_used": m.multiple_used,
            "implied_ev": m.implied_ev,
            "implied_equity": m.implied_equity,
            "implied_price": m.implied_price,
            "low_price": m.low_price,
            "high_price": m.high_price,
        }

    return {"multiples": multiples_out, "methods": methods_out, "consensus_price": res.consensus_price}


def _run_sotp(sotp_params: dict) -> dict:
    segments = [_to_segment(s) for s in sotp_params.get("segments", [])]
    if not segments:
        return None
    cash = float(sotp_params.get("cash", 0.0) or 0.0)
    debt = float(sotp_params.get("debt", 0.0) or 0.0)
    minority_interest = float(sotp_params.get("minority_interest", 0.0) or 0.0)
    shares = float(sotp_params.get("shares", 1.0) or 1.0)
    res = sotp_valuation(
        segments=segments,
        cash=cash,
        debt=debt,
        minority_interest=minority_interest,
        shares=shares,
    )
    sens = None
    sens_cfg = sotp_params.get("sensitivity")
    if sens_cfg:
        sens_matrix = sotp_sensitivity(
            core_ebit=sens_cfg["core_ebit"],
            exp_ebit=sens_cfg["exp_ebit"],
            core_mults=sens_cfg["core_mults"],
            exp_mults=sens_cfg["exp_mults"],
            cash=cash,
            debt=debt,
            minority_interest=minority_interest,
            shares=shares,
        )
        sens = {"matrix": sens_matrix}

    return {
        "bear": {"enterprise_value": res.bear.enterprise_value, "equity_value": res.bear.equity_value, "implied_price": res.bear.implied_price},
        "base": {"enterprise_value": res.base.enterprise_value, "equity_value": res.base.equity_value, "implied_price": res.base.implied_price},
        "bull": {"enterprise_value": res.bull.enterprise_value, "equity_value": res.bull.equity_value, "implied_price": res.bull.implied_price},
        "contributions": res.contributions,
        "sensitivity": sens,
    }


def _build_summary_models(dcf: dict, comps: dict, sotp: dict, summary_cfg: dict) -> list:
    models_cfg = summary_cfg["models"]
    prices = {
        "dcf_gordon": dcf["gordon"]["implied_price"] if dcf else None,
        "dcf_exit": dcf["exit"]["implied_price"] if dcf else None,
        "comps_pe": comps["methods"]["pe"]["implied_price"] if comps else None,
        "comps_ev_ebitda": comps["methods"]["ev_ebitda"]["implied_price"] if comps else None,
        "sotp": sotp["base"]["implied_price"] if sotp else None,
    }
    lows = {
        "dcf_gordon": summary_cfg.get("dcf_gordon_low"),
        "dcf_exit": summary_cfg.get("dcf_exit_low"),
        "comps_pe": comps["methods"]["pe"]["low_price"] if comps else None,
        "comps_ev_ebitda": comps["methods"]["ev_ebitda"]["low_price"] if comps else None,
        "sotp": sotp["bear"]["implied_price"] if sotp else None,
    }
    highs = {
        "dcf_gordon": summary_cfg.get("dcf_gordon_high"),
        "dcf_exit": summary_cfg.get("dcf_exit_high"),
        "comps_pe": comps["methods"]["pe"]["high_price"] if comps else None,
        "comps_ev_ebitda": comps["methods"]["ev_ebitda"]["high_price"] if comps else None,
        "sotp": sotp["bull"]["implied_price"] if sotp else None,
    }
    out = []
    for m in models_cfg:
        key = m["key"]
        price = prices.get(key)
        if price is None:
            continue
        low = m.get("low") if m.get("low") is not None else lows.get(key)
        high = m.get("high") if m.get("high") is not None else highs.get(key)
        out.append(ModelOutput(
            key=key,
            label=m["label"],
            price=price,
            low=low if low is not None else price,
            high=high if high is not None else price,
            weight=m.get("weight", 0.2),
        ))
    return out


def _run_summary(summary_cfg: dict, dcf: dict, comps: dict, sotp: dict) -> dict:
    models = _build_summary_models(dcf, comps, sotp, summary_cfg)
    net_income = summary_cfg.get("target_net_income")
    ebitda = summary_cfg.get("target_ebitda")
    segment_count = len(summary_cfg.get("sotp_segments", [])) or (1 if sotp else 0)
    models = apply_degradation(models, net_income=net_income, ebitda=ebitda, segment_count=segment_count)
    res = summarize(models, summary_cfg["current_price"])
    return {
        "fair_value": res.fair_value,
        "weighted_low": res.weighted_low,
        "weighted_high": res.weighted_high,
        "full_low": res.full_low,
        "full_high": res.full_high,
        "upside": res.upside,
        "rating": res.rating,
        "used_models": res.used_models,
        "models": [
            {"key": m.key, "label": m.label, "price": m.price, "low": m.low, "high": m.high,
             "weight": m.weight, "available": m.available, "exclude_reason": m.exclude_reason}
            for m in models
        ],
    }


def run_full_valuation(params: dict) -> dict:
    """完整估值编排：接收完整假设包，跑全部引擎模块，返回完整结果。

    params keys:
      wacc_inputs, forecast_assumptions, dcf_params, comps, sotp, summary
    """
    wacc = _run_wacc(params["wacc_inputs"])
    forecast = _run_forecast(params["forecast_assumptions"])

    dcf = None
    if params.get("dcf_params"):
        dcf_params = dict(params["dcf_params"])
        dcf_params.setdefault("shares", params["dcf_params"].get("shares", 1.0))
        dcf = _run_dcf(dcf_params, forecast, wacc)

    comps = None
    if params.get("comps") and params["comps"].get("peers"):
        comps = _run_comps(params["comps"])

    sotp = None
    if params.get("sotp") and params["sotp"].get("segments"):
        sotp = _run_sotp(params["sotp"])

    summary = None
    if params.get("summary"):
        summary = _run_summary(params["summary"], dcf, comps, sotp)

    return {
        "wacc": wacc,
        "forecast": forecast,
        "dcf": dcf,
        "comps": comps,
        "sotp": sotp,
        "summary": summary,
    }


__all__ = ["run_full_valuation"]