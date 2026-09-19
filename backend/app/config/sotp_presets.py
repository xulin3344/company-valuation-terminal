"""SOTP (分部加总估值) 常用上市公司与多元化巨头预置模板库

覆盖标的：
- 01810 小米集团 (手机 + IoT + 互联网 + 汽车)
- 00700 腾讯控股 (增值服务 + 广告 + 金融科技云 + 战略投资)
- 03690 美团 (核心本地商业 + 新业务及其他)
- 09988 阿里巴巴 (淘天 + 阿里云 + 国际数字商业 + 菜鸟本地生活)
- TSLA 特斯拉 (整车制造 + 储能系统 + FSD与AI软件订阅)
- AAPL 苹果公司 (硬件产品线 + 软件订阅生态)
- 300750 宁德时代 (动力电池 + 储能系统 + 电池材料回收)
- 09992 泡泡玛特 (五大IP与乐园海外分部)
"""
from typing import Optional, Dict, Any, List


SOTP_PRESETS: Dict[str, Dict[str, Any]] = {
    # 01810 小米集团
    "01810": {
        "name": "小米集团 (01810.HK)",
        "weight": 0.40,
        "segments": [
            {
                "name": "智能手机业务 (高端化与全球出海)",
                "ebit": 16500.0,
                "bear_mult": 8.0,
                "base_mult": 10.5,
                "bull_mult": 13.0,
            },
            {
                "name": "IoT与生活消费产品 (智能家电/穿戴/平板)",
                "ebit": 8200.0,
                "bear_mult": 11.0,
                "base_mult": 14.0,
                "bull_mult": 17.0,
            },
            {
                "name": "互联网服务 (高毛利澎湃OS广告与软件分发)",
                "ebit": 23500.0,
                "bear_mult": 15.0,
                "base_mult": 18.5,
                "bull_mult": 22.0,
            },
            {
                "name": "智能电动汽车及创新业务 (SU7/YU7量产与研发)",
                "ebit": 4500.0,
                "bear_mult": 18.0,
                "base_mult": 25.0,
                "bull_mult": 32.0,
            },
        ],
    },
    # 00700 腾讯控股
    "00700": {
        "name": "腾讯控股 (00700.HK)",
        "weight": 0.40,
        "segments": [
            {
                "name": "增值服务 (网络游戏与社交网络生态)",
                "ebit": 75000.0,
                "bear_mult": 12.0,
                "base_mult": 15.0,
                "bull_mult": 18.0,
            },
            {
                "name": "网络广告 (微信视频号/朋友圈/数字媒体)",
                "ebit": 35000.0,
                "bear_mult": 15.0,
                "base_mult": 18.0,
                "bull_mult": 22.0,
            },
            {
                "name": "金融科技与企业服务 (微信支付/腾讯云/混元AI)",
                "ebit": 62000.0,
                "bear_mult": 16.0,
                "base_mult": 20.0,
                "bull_mult": 25.0,
            },
            {
                "name": "战略联营与上市公司对外投资版图",
                "ebit": 25000.0,
                "bear_mult": 10.0,
                "base_mult": 12.0,
                "bull_mult": 15.0,
            },
        ],
    },
    # 03690 美团
    "03690": {
        "name": "美团 (03690.HK)",
        "weight": 0.45,
        "segments": [
            {
                "name": "核心本地商业 (餐饮外卖/即时闪购/到店酒旅)",
                "ebit": 38500.0,
                "bear_mult": 13.0,
                "base_mult": 16.5,
                "bull_mult": 20.0,
            },
            {
                "name": "新业务及其他 (小象超市/快驴供应链/Keeta海外)",
                "ebit": 5000.0,
                "bear_mult": 10.0,
                "base_mult": 14.0,
                "bull_mult": 18.0,
            },
        ],
    },
    # 09988 / BABA 阿里巴巴
    "09988": {
        "name": "阿里巴巴 (09988.HK / BABA)",
        "weight": 0.45,
        "segments": [
            {
                "name": "淘天集团 (淘宝/天猫国内电商零售与批发现金牛)",
                "ebit": 125000.0,
                "bear_mult": 7.5,
                "base_mult": 9.5,
                "bull_mult": 12.0,
            },
            {
                "name": "阿里云智能集团 (公共云与通义千问AI算力基础设施)",
                "ebit": 15000.0,
                "bear_mult": 18.0,
                "base_mult": 22.0,
                "bull_mult": 28.0,
            },
            {
                "name": "阿里国际数字商业 (速卖通Choice/Lazada/Trendyol)",
                "ebit": 8000.0,
                "bear_mult": 12.0,
                "base_mult": 15.0,
                "bull_mult": 20.0,
            },
            {
                "name": "菜鸟与本地生活服务 (高德地图/饿了么/菜鸟物流)",
                "ebit": 9500.0,
                "bear_mult": 10.0,
                "base_mult": 12.5,
                "bull_mult": 16.0,
            },
        ],
    },
    # TSLA 特斯拉
    "TSLA": {
        "name": "特斯拉 (TSLA.US)",
        "weight": 0.45,
        "segments": [
            {
                "name": "电动汽车整车制造与销售交付 (Model 3/Y/CyberTruck)",
                "ebit": 8500.0,
                "bear_mult": 16.0,
                "base_mult": 22.0,
                "bull_mult": 28.0,
            },
            {
                "name": "储能与清洁能源系统 (Megapack电网储能与Powerwall)",
                "ebit": 2500.0,
                "bear_mult": 20.0,
                "base_mult": 28.0,
                "bull_mult": 36.0,
            },
            {
                "name": "FSD全自动驾驶软件订阅与Robotaxi前瞻AI期权",
                "ebit": 2000.0,
                "bear_mult": 25.0,
                "base_mult": 35.0,
                "bull_mult": 48.0,
            },
        ],
    },
    # AAPL 苹果公司
    "AAPL": {
        "name": "苹果公司 (AAPL.US)",
        "weight": 0.15,
        "segments": [
            {
                "name": "高端硬件产品生态 (iPhone / Mac / iPad / 智能穿戴)",
                "ebit": 82000.0,
                "bear_mult": 18.0,
                "base_mult": 21.0,
                "bull_mult": 25.0,
            },
            {
                "name": "高粘性软件与订阅生态 (App Store / iCloud / Apple Pay)",
                "ebit": 45000.0,
                "bear_mult": 28.0,
                "base_mult": 32.0,
                "bull_mult": 38.0,
            },
        ],
    },
    # 300750 宁德时代
    "300750": {
        "name": "宁德时代 (300750.SZ)",
        "weight": 0.15,
        "segments": [
            {
                "name": "动力电池系统 (全球新能源乘用车与商用车锂电池)",
                "ebit": 38000.0,
                "bear_mult": 14.0,
                "base_mult": 18.0,
                "bull_mult": 22.0,
            },
            {
                "name": "储能电池系统 (全球电网侧与工商业储能电芯)",
                "ebit": 12500.0,
                "bear_mult": 18.0,
                "base_mult": 24.0,
                "bull_mult": 30.0,
            },
            {
                "name": "电池关键材料与锂资源回收循环体系",
                "ebit": 3500.0,
                "bear_mult": 10.0,
                "base_mult": 13.0,
                "bull_mult": 16.0,
            },
        ],
    },
    # 09992 泡泡玛特
    "09992": {
        "name": "泡泡玛特 (09992.HK)",
        "weight": 0.20,
        "segments": [
            {
                "name": "THE MONSTERS 头部超级IP (LABUBU)",
                "ebit": 7646.0,
                "bear_mult": 20.0,
                "base_mult": 28.0,
                "bull_mult": 36.0,
            },
            {
                "name": "经典艺术家核心IP矩阵 (MOLLY/SKULLPANDA/DIMOO)",
                "ebit": 6336.0,
                "bear_mult": 16.0,
                "base_mult": 22.0,
                "bull_mult": 28.0,
            },
            {
                "name": "新锐孵化与外部授权合作IP",
                "ebit": 2310.0,
                "bear_mult": 18.0,
                "base_mult": 25.0,
                "bull_mult": 35.0,
            },
            {
                "name": "主题乐园与线下沉浸体验零售",
                "ebit": 306.0,
                "bear_mult": 12.0,
                "base_mult": 16.0,
                "bull_mult": 22.0,
            },
            {
                "name": "衍生内容开发与海外全球化业务",
                "ebit": 292.0,
                "bear_mult": 20.0,
                "base_mult": 30.0,
                "bull_mult": 45.0,
            },
        ],
    },
}

# 别名与代码规范化映射
TICKER_ALIASES = {
    "1810": "01810",
    "01810.HK": "01810",
    "700": "00700",
    "00700.HK": "00700",
    "3690": "03690",
    "03690.HK": "03690",
    "9988": "09988",
    "09988.HK": "09988",
    "BABA": "09988",
    "BABA.US": "09988",
    "TSLA.US": "TSLA",
    "AAPL.US": "AAPL",
    "300750.SZ": "300750",
    "9992": "09992",
    "09992.HK": "09992",
}


def get_sotp_preset(ticker: str) -> Optional[Dict[str, Any]]:
    """根据标的代码匹配 SOTP 预置分部，若存在返回其副本。"""
    if not ticker:
        return None
    raw = ticker.strip().upper()
    canonical = TICKER_ALIASES.get(raw, raw)
    # 如果纯数字补零，如 1810 -> 01810
    if canonical.isdigit() and len(canonical) == 4:
        canonical = "0" + canonical
    preset = SOTP_PRESETS.get(canonical)
    if not preset:
        return None
    # 深拷贝避免直接污染
    import copy
    return copy.deepcopy(preset)
