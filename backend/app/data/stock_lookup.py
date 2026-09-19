"""股票代码与公司名称智能检索与转换服务。
支持输入中文名（如“工业富联”）、拼音（如“gyfl”）、代码（如“601138”）智能解析并标准化。
数据源采用腾讯财经 Smartbox 实时接口与本地精选词库双重兜底。
"""
import re
import urllib.parse
import urllib.request
from typing import List, Optional, Dict, Any

# 本地常用权重股兜底词典
COMMON_STOCKS = [
    {"ticker": "601138", "market": "CN", "name": "工业富联", "pinyin": "gyfl"},
    {"ticker": "002036", "market": "CN", "name": "联创电子", "pinyin": "lcdz"},
    {"ticker": "600519", "market": "CN", "name": "贵州茅台", "pinyin": "gzmt"},
    {"ticker": "300750", "market": "CN", "name": "宁德时代", "pinyin": "ndsd"},
    {"ticker": "002594", "market": "CN", "name": "比亚迪", "pinyin": "byd"},
    {"ticker": "601318", "market": "CN", "name": "中国平安", "pinyin": "zgpa"},
    {"ticker": "00700", "market": "HK", "name": "腾讯控股", "pinyin": "txkg"},
    {"ticker": "03690", "market": "HK", "name": "美团", "pinyin": "mt"},
    {"ticker": "09992", "market": "HK", "name": "泡泡玛特", "pinyin": "ppmt"},
    {"ticker": "09988", "market": "HK", "name": "阿里巴巴", "pinyin": "albb"},
    {"ticker": "AAPL", "market": "US", "name": "苹果公司", "pinyin": "apple"},
    {"ticker": "NVDA", "market": "US", "name": "英伟达", "pinyin": "nvda"},
    {"ticker": "MSFT", "market": "US", "name": "微软", "pinyin": "msft"},
    {"ticker": "TSLA", "market": "US", "name": "特斯拉", "pinyin": "tsla"},
]


def search_stocks_remote(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """通过实时接口查询股票代码、名称、拼音与市场。"""
    query = (query or "").strip()
    if not query:
        return []
    
    url = f"https://smartbox.gtimg.cn/s3/?q={urllib.parse.quote(query)}&t=all"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    
    results = []
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            if '"' in raw:
                val = raw.split('"')[1]
                items = val.split("^")
                for item in items:
                    parts = item.split("~")
                    if len(parts) >= 5:
                        mkt, code, name, py, stype = parts[0], parts[1], parts[2], parts[3], parts[4]
                        
                        # 仅保留股票类型（排除基金 jj、指数 zs、期货等，除非特别需要）
                        if stype not in ("GP-A", "GP", "GP-B"):
                            continue
                        
                        # 识别市场标准命名
                        if mkt in ("sh", "sz", "bj"):
                            market = "CN"
                        elif mkt == "hk":
                            market = "HK"
                            # 港股代码补齐 5 位（如 700 -> 00700）
                            if code.isdigit() and len(code) < 5:
                                code = code.zfill(5)
                        elif mkt == "us":
                            market = "US"
                            # 剔除美股后缀，如 aapl.oq -> AAPL
                            code = code.split(".")[0].upper()
                        else:
                            market = mkt.upper()
                            
                        results.append({
                            "ticker": code,
                            "market": market,
                            "name": name,
                            "pinyin": py,
                            "type": stype
                        })
                        if len(results) >= limit:
                            break
    except Exception:
        pass

    return results


def resolve_stock(query: str, preferred_market: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """解析股票输入为合规的 (ticker, market, name)。
    支持纯代码、中文名、拼音缩写。
    """
    q = (query or "").strip()
    if not q:
        return None

    # 1. 如果是纯 6 位数字，直接判定为 A 股
    if re.fullmatch(r"\d{6}", q):
        # 尝试反查公司名称
        name = ""
        for s in COMMON_STOCKS:
            if s["ticker"] == q:
                name = s["name"]
                break
        return {"ticker": q, "market": "CN", "name": name or q}

    # 2. 如果是纯 5 位数字，直接判定为港股
    if re.fullmatch(r"\d{5}", q):
        name = ""
        for s in COMMON_STOCKS:
            if s["ticker"] == q:
                name = s["name"]
                break
        return {"ticker": q, "market": "HK", "name": name or q}

    # 3. 本地兜底词典匹配（优先精确匹配名称或拼音）
    q_lower = q.lower()
    for s in COMMON_STOCKS:
        if s["name"] == q or s["ticker"].lower() == q_lower or s["pinyin"] == q_lower:
            return s.copy()

    # 4. 远程实时搜索解析
    remote_matches = search_stocks_remote(q, limit=5)
    if remote_matches:
        # 如果指定了偏好市场（如 CN），优先取该市场的结果
        if preferred_market:
            p_mkt = preferred_market.upper()
            for m in remote_matches:
                if m["market"] == p_mkt:
                    return m
        return remote_matches[0]

    # 5. 美股纯字母代码兜底（1-5个字母）
    if re.fullmatch(r"[A-Za-z]{1,5}", q):
        return {"ticker": q.upper(), "market": preferred_market or "US", "name": q.upper()}

    return None
