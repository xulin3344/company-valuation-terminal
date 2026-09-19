"""动态市场数据采集：无风险利率、Beta、资本结构、分析师预期。"""
import logging

logger = logging.getLogger(__name__)


def _safe_yf_info(ticker: str) -> dict:
    """安全获取 yfinance info 字典，失败返回空字典。"""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        return t.info or {}
    except Exception as exc:
        logger.warning("yfinance info fetch failed for %s: %s", ticker, exc)
        return {}


def fetch_risk_free_rate(market: str = "US") -> float:
    """获取无风险利率：美股用 10 年期美债 ^TNX，失败回退默认值。"""
    try:
        import yfinance as yf
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="5d")
        if hist is not None and not hist.empty and "Close" in hist.columns:
            val = hist["Close"].dropna()
            if not val.empty:
                return round(float(val.iloc[-1]) / 100, 4)  # 百分比 → 小数
    except Exception as exc:
        logger.warning("fetch_risk_free_rate failed: %s", exc)
    # 回退默认值
    return {"US": 0.042, "HK": 0.042}.get(market, 0.042)


def fetch_beta(ticker: str) -> float:
    """获取个股 Beta（yfinance 提供的 5 年月度回归 Beta）。"""
    info = _safe_yf_info(ticker)
    beta = info.get("beta")
    if beta and isinstance(beta, (int, float)) and 0 < beta < 5:
        return round(float(beta), 3)
    return 1.0  # fallback


def fetch_sector_industry(ticker: str) -> dict:
    """获取行业与细分行业分类。"""
    info = _safe_yf_info(ticker)
    return {
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
    }


def fetch_capital_structure_from_market(ticker: str) -> dict:
    """从 yfinance info 获取市值、总债务、总现金，推算资本结构和有效债务成本。"""
    info = _safe_yf_info(ticker)
    market_cap = info.get("marketCap", 0) or 0
    total_debt = info.get("totalDebt", 0) or 0
    total_cash = info.get("totalCash", 0) or 0
    # 推算有效债务成本
    interest = info.get("interestExpense")
    if interest and total_debt:
        kd = abs(interest) / total_debt
        kd = max(0.01, min(0.15, kd))  # 限制在合理区间
    else:
        kd = 0.035
    total = market_cap + total_debt
    we = market_cap / total if total > 0 else 0.98
    we = max(0.30, min(0.99, round(we, 4)))
    return {
        "market_cap": market_cap,
        "total_debt": total_debt,
        "total_cash": total_cash,
        "weight_equity": we,
        "kd": round(kd, 4),
    }


def fetch_analyst_estimates(ticker: str) -> dict:
    """采集 Yahoo Finance 分析师一致预期（价格目标、EPS、营收预测）。"""
    estimates = {}
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        # 价格目标
        try:
            pt = t.analyst_price_targets
            if pt:
                estimates["price_targets"] = dict(pt) if not isinstance(pt, dict) else pt
        except Exception:
            pass
        # EPS 一致预期
        try:
            ee = t.earnings_estimate
            if ee is not None and not getattr(ee, "empty", True):
                estimates["earnings_estimate"] = ee.reset_index().to_dict(orient="records")
        except Exception:
            pass
        # 营收一致预期
        try:
            re = t.revenue_estimate
            if re is not None and not getattr(re, "empty", True):
                estimates["revenue_estimate"] = re.reset_index().to_dict(orient="records")
        except Exception:
            pass
    except Exception as exc:
        logger.warning("fetch_analyst_estimates failed for %s: %s", ticker, exc)
    return estimates


def fetch_market_overview(ticker: str) -> dict:
    """获取行情概览数据：52周高低、市盈率等。"""
    info = _safe_yf_info(ticker)
    return {
        "market_cap": info.get("marketCap"),
        "enterprise_value": info.get("enterpriseValue"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "ev_to_ebitda": info.get("enterpriseToEbitda"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "dividend_yield": info.get("dividendYield"),
        "shares_outstanding": info.get("sharesOutstanding"),
    }


def fetch_dynamic_peers(ticker: str, max_peers: int = 6) -> list:
    """根据目标公司行业自动从候选池获取可比公司实时财务数据。"""
    info = _safe_yf_info(ticker)
    industry = info.get("industry", "")
    sector = info.get("sector", "")

    # 按行业预设候选 ticker（可通过配置文件扩展）
    INDUSTRY_CANDIDATES = {
        "Consumer Electronics": ["AAPL", "SONY", "1810.HK", "005930.KS", "7974.T"],
        "Internet Content & Information": ["GOOGL", "META", "0700.HK", "BIDU", "NAVER"],
        "Entertainment": ["DIS", "NFLX", "CMCSA", "9992.HK", "WBD"],
        "Software - Application": ["MSFT", "CRM", "ORCL", "SAP", "ADBE"],
        "Software - Infrastructure": ["MSFT", "ORCL", "NOW", "SNOW", "PLTR"],
        "Semiconductors": ["NVDA", "TSM", "AMD", "INTC", "AVGO"],
        "Drug Manufacturers - General": ["JNJ", "PFE", "MRK", "ABBV", "LLY"],
        "Banks - Diversified": ["JPM", "BAC", "WFC", "C", "GS"],
        "Luxury Goods": ["MC.PA", "RMS.PA", "KER.PA", "1913.HK", "CPRI"],
    }
    # 按 sector 的 fallback 候选
    SECTOR_CANDIDATES = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
        "Communication Services": ["GOOGL", "META", "DIS", "NFLX", "0700.HK"],
        "Consumer Cyclical": ["AMZN", "TSLA", "NKE", "MCD", "SBUX"],
        "Healthcare": ["JNJ", "UNH", "PFE", "MRK", "ABBV"],
        "Financial Services": ["JPM", "BAC", "GS", "MS", "BRK-B"],
        "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST"],
        "Industrials": ["CAT", "HON", "UPS", "BA", "GE"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
        "Real Estate": ["PLD", "AMT", "SPG", "O", "WELL"],
    }

    candidates = INDUSTRY_CANDIDATES.get(industry, SECTOR_CANDIDATES.get(sector, []))
    if not candidates:
        return []

    import yfinance as yf
    peers = []
    ticker_upper = ticker.upper().replace(".HK", "").replace("0", "", 1)  # rough dedup
    for peer_ticker in candidates[:max_peers + 2]:
        pt_clean = peer_ticker.upper().replace(".HK", "").replace("0", "", 1)
        if pt_clean == ticker_upper:
            continue
        try:
            pt = yf.Ticker(peer_ticker)
            pi = pt.info or {}
            mc = pi.get("marketCap", 0) or 0
            if mc == 0:
                continue
            peers.append({
                "name": pi.get("shortName", peer_ticker),
                "ticker": peer_ticker,
                "market_cap": round(mc / 1e6, 1),
                "net_debt": round(((pi.get("totalDebt", 0) or 0) - (pi.get("totalCash", 0) or 0)) / 1e6, 1),
                "revenue": round((pi.get("totalRevenue", 0) or 0) / 1e6, 1),
                "ebitda": round((pi.get("ebitda", 0) or 0) / 1e6, 1),
                "ebit": round((pi.get("operatingIncome", 0) or 0) / 1e6, 1),
                "net_income": round((pi.get("netIncomeToCommon", 0) or 0) / 1e6, 1),
            })
            if len(peers) >= max_peers:
                break
        except Exception:
            continue
    return peers
