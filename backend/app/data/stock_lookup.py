"""股票代码与公司名称智能检索与转换服务。
支持输入中文名（如“工业富联”、“智谱”、“MiniMax”）、拼音（如“gyfl”）、代码（如“601138”、“00100”、“02513”）智能解析并标准化。
数据源采用腾讯财经 Smartbox 实时接口、新浪实时行情与本地精选词库多重兜底。
"""
import re
import urllib.parse
import urllib.request
from typing import List, Optional, Dict, Any

# 本地常用权重及明星股词典
COMMON_STOCKS = [
    # 港股明星/大模型与科技龙头
    {"ticker": "00100", "market": "HK", "name": "MiniMax", "fullName": "MiniMax Group Inc. (名之梦)", "pinyin": "minimax"},
    {"ticker": "02513", "market": "HK", "name": "智谱", "fullName": "北京智谱华章科技有限公司 (Zhipu AI / Z.AI)", "pinyin": "zhipu"},
    {"ticker": "00700", "market": "HK", "name": "腾讯控股", "fullName": "腾讯控股有限公司", "pinyin": "txkg"},
    {"ticker": "03690", "market": "HK", "name": "美团", "fullName": "美团", "pinyin": "mt"},
    {"ticker": "09992", "market": "HK", "name": "泡泡玛特", "fullName": "泡泡玛特国际集团有限公司", "pinyin": "ppmt"},
    {"ticker": "09988", "market": "HK", "name": "阿里巴巴", "fullName": "阿里巴巴集团控股有限公司", "pinyin": "albb"},
    {"ticker": "01810", "market": "HK", "name": "小米集团", "fullName": "小米集团", "pinyin": "xmjt"},
    {"ticker": "01024", "market": "HK", "name": "快手", "fullName": "快手科技", "pinyin": "ks"},

    # A股核心资产与硬科技
    {"ticker": "601138", "market": "CN", "name": "工业富联", "fullName": "富士康工业互联网股份有限公司", "pinyin": "gyfl"},
    {"ticker": "002036", "market": "CN", "name": "联创电子", "fullName": "联创电子科技股份有限公司", "pinyin": "lcdz"},
    {"ticker": "600519", "market": "CN", "name": "贵州茅台", "fullName": "贵州茅台酒股份有限公司", "pinyin": "gzmt"},
    {"ticker": "300750", "market": "CN", "name": "宁德时代", "fullName": "宁德时代新能源科技股份有限公司", "pinyin": "ndsd"},
    {"ticker": "002594", "market": "CN", "name": "比亚迪", "fullName": "比亚迪股份有限公司", "pinyin": "byd"},
    {"ticker": "601318", "market": "CN", "name": "中国平安", "fullName": "中国平安保险(集团)股份有限公司", "pinyin": "zgpa"},

    # 美股
    {"ticker": "AAPL", "market": "US", "name": "苹果公司", "fullName": "Apple Inc.", "pinyin": "apple"},
    {"ticker": "NVDA", "market": "US", "name": "英伟达", "fullName": "NVIDIA Corporation", "pinyin": "nvda"},
    {"ticker": "MSFT", "market": "US", "name": "微软", "fullName": "Microsoft Corporation", "pinyin": "msft"},
    {"ticker": "TSLA", "market": "US", "name": "特斯拉", "fullName": "Tesla, Inc.", "pinyin": "tsla"},
]


def clean_company_name(name: str) -> str:
    """清理接口返回的公司名称后缀（如 minimaxw -> MiniMax, 智谱w -> 智谱）。"""
    if not name:
        return ""
    # 特别标的规范化展示
    n_lower = name.lower().strip()
    if "minimax" in n_lower:
        return "MiniMax"
    if "智谱" in name:
        return "智谱"

    # 去除尾部代表同股不同权的 -w, -sw, w, sw 等港股后缀
    cleaned = re.sub(r"[-_]?[swW]{1,2}$", "", name).strip()
    return cleaned if cleaned else name


def get_realtime_name(ticker: str, market: str) -> str:
    """通过行情接口反查上市公司的真实全称。"""
    q_mark = chr(34)
    m = str(market).upper()
    try:
        if m == "HK":
            code = "".join(filter(str.isdigit, ticker)).zfill(5)
            url = f"http://hq.sinajs.cn/list=rt_hk{code}"
            req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                c = resp.read().decode("gbk", errors="ignore")
                if q_mark in c:
                    parts = c.split(q_mark)[1].split(",")
                    if len(parts) > 1:
                        # parts[0]=英文/拼音简写, parts[1]=中文名称
                        name = parts[1] if parts[1] else parts[0]
                        return clean_company_name(name)
        elif m == "CN":
            code = "".join(filter(str.isdigit, ticker))
            prefix = "sh" if code.startswith(("6", "9", "688")) else ("bj" if code.startswith(("8", "4", "920")) else "sz")
            url = f"http://hq.sinajs.cn/list={prefix}{code}"
            req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                c = resp.read().decode("gbk", errors="ignore")
                if q_mark in c:
                    parts = c.split(q_mark)[1].split(",")
                    if len(parts) > 0 and parts[0]:
                        return clean_company_name(parts[0])
    except Exception:
        pass
    return ""


def clean_query_string(query: str) -> tuple[str, Optional[str]]:
    """清洗用户输入并智能推断市场。
    支持处理:
    - 'HK00100' -> ('00100', 'HK')
    - '00100.HK' -> ('00100', 'HK')
    - '00100 MINIMAX' -> ('00100', 'HK')
    - 'SH601138' -> ('601138', 'CN')
    - '601138.SS' -> ('601138', 'CN')
    - 'SZ002036' -> ('002036', 'CN')
    """
    q = (query or "").strip()
    if not q:
        return "", None

    # 去除常见的两端市场前后缀
    mkt = None
    if re.match(r"^HK\d+", q, re.I):
        mkt = "HK"
        q = q[2:].strip()
    elif q.upper().endswith(".HK"):
        mkt = "HK"
        q = q[:-3].strip()
    elif re.match(r"^(SH|SZ|BJ)\d+", q, re.I):
        mkt = "CN"
        q = q[2:].strip()
    elif q.upper().endswith((".SS", ".SZ", ".BJ")):
        mkt = "CN"
        q = q[:-3].strip()

    # 如果输入中同时包含数字与文字（如 "00100 MINIMAX"、"601138 工业富联"），尝试优先提取其中的股票代码
    tokens = q.split()
    if len(tokens) > 1:
        for t in tokens:
            digits = "".join(filter(str.isdigit, t))
            if len(digits) == 5:
                return digits, "HK"
            elif len(digits) == 6:
                return digits, "CN"
            elif len(digits) in (3, 4) and mkt == "HK":
                return digits.zfill(5), "HK"

    return q, mkt


def search_stocks_remote(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """通过实时接口查询股票代码、名称、拼音与市场。"""
    clean_q, inferred_mkt = clean_query_string(query)
    if not clean_q:
        return []
    
    url = f"https://smartbox.gtimg.cn/s3/?q={urllib.parse.quote(clean_q)}&t=all"
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
                        
                        # 仅保留股票类型（排除基金 jj、指数 zs、期货等）
                        if stype not in ("GP-A", "GP", "GP-B"):
                            continue
                        
                        # 识别市场标准命名
                        if mkt in ("sh", "sz", "bj"):
                            market = "CN"
                        elif mkt == "hk":
                            market = "HK"
                            # 港股代码补齐 5 位（如 100 -> 00100, 700 -> 00700）
                            if code.isdigit() and len(code) < 5:
                                code = code.zfill(5)
                        elif mkt == "us":
                            market = "US"
                            # 剔除美股后缀，如 aapl.oq -> AAPL
                            code = code.split(".")[0].upper()
                        else:
                            market = mkt.upper()
                            
                        clean_name = clean_company_name(name)
                        results.append({
                            "ticker": code,
                            "market": market,
                            "name": clean_name,
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
    支持纯代码、中文名、拼音缩写、前后缀及代码+名称混合输入。
    """
    clean_q, inferred_mkt = clean_query_string(query)
    if not clean_q:
        return None

    market_hint = inferred_mkt or preferred_market

    # 1. 匹配本地兜底词典（精准名称、代码、拼音）
    q_lower = clean_q.lower()
    for s in COMMON_STOCKS:
        if (
            s["name"].lower() == q_lower
            or s["ticker"].lower() == q_lower
            or s["pinyin"] == q_lower
            or (market_hint and s["market"] == market_hint.upper() and s["ticker"].lstrip("0") == clean_q.lstrip("0"))
        ):
            res = s.copy()
            return res

    # 2. 如果是纯 6 位数字，直接判定为 A 股
    if re.fullmatch(r"\d{6}", clean_q):
        name = get_realtime_name(clean_q, "CN")
        return {"ticker": clean_q, "market": "CN", "name": name or clean_q}

    # 3. 如果是纯 5 位数字，直接判定为港股
    if re.fullmatch(r"\d{5}", clean_q):
        name = get_realtime_name(clean_q, "HK")
        return {"ticker": clean_q, "market": "HK", "name": name or clean_q}

    # 4. 如果是 1~4 位数字且指定为港股市场，自动补齐5位判定为港股（如 100 -> 00100, 700 -> 00700）
    if re.fullmatch(r"\d{1,4}", clean_q) and market_hint == "HK":
        code_padded = clean_q.zfill(5)
        name = get_realtime_name(code_padded, "HK")
        return {"ticker": code_padded, "market": "HK", "name": name or code_padded}

    # 5. 远程实时搜索解析
    remote_matches = search_stocks_remote(clean_q, limit=6)
    if remote_matches:
        # 如果指定或推断了市场，优先取该市场的结果
        if market_hint:
            p_mkt = market_hint.upper()
            for m in remote_matches:
                if m["market"] == p_mkt:
                    if not m.get("name") or m["name"] == m["ticker"]:
                        m["name"] = get_realtime_name(m["ticker"], m["market"]) or m["ticker"]
                    return m
        top = remote_matches[0]
        if not top.get("name") or top["name"] == top["ticker"]:
            top["name"] = get_realtime_name(top["ticker"], top["market"]) or top["ticker"]
        return top

    # 6. 美股纯字母代码兜底（1-5个字母）
    if re.fullmatch(r"[A-Za-z]{1,5}", clean_q):
        return {"ticker": clean_q.upper(), "market": market_hint or "US", "name": clean_q.upper()}

    return None
