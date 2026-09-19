/**
 * 常用上市公司与行业 SOTP 分部加总估值预置模板库
 */

export const SOTP_TEMPLATES = [
  {
    id: '01810',
    name: '📱 小米集团 (人车家全生态 4大分部)',
    ticker: '01810',
    description: '手机硬件 + IoT消费品 + 互联网服务 + 智能电动汽车',
    segments: [
      { name: '智能手机业务 (高端化与全球出海)', ebit: 16500, bear_mult: 8.0, base_mult: 10.5, bull_mult: 13.0 },
      { name: 'IoT与生活消费产品 (智能家电/穿戴/平板)', ebit: 8200, bear_mult: 11.0, base_mult: 14.0, bull_mult: 17.0 },
      { name: '互联网服务 (高毛利澎湃OS广告与软件分发)', ebit: 23500, bear_mult: 15.0, base_mult: 18.5, bull_mult: 22.0 },
      { name: '智能电动汽车及创新业务 (SU7/YU7放量研发)', ebit: 4500, bear_mult: 18.0, base_mult: 25.0, bull_mult: 32.0 },
    ]
  },
  {
    id: '00700',
    name: '🐧 腾讯控股 (平台生态与投资 4大分部)',
    ticker: '00700',
    description: '增值服务 + 社交广告 + 金融科技云 + 投资资产',
    segments: [
      { name: '增值服务 (网络游戏与社交网络生态)', ebit: 75000, bear_mult: 12.0, base_mult: 15.0, bull_mult: 18.0 },
      { name: '网络广告 (微信视频号/朋友圈/数字媒体)', ebit: 35000, bear_mult: 15.0, base_mult: 18.0, bull_mult: 22.0 },
      { name: '金融科技与企业服务 (微信支付/腾讯云/混元AI)', ebit: 62000, bear_mult: 16.0, base_mult: 20.0, bull_mult: 25.0 },
      { name: '战略联营与对外上市公司股权投资版图', ebit: 25000, bear_mult: 10.0, base_mult: 12.0, bull_mult: 15.0 },
    ]
  },
  {
    id: '03690',
    name: '🛵 美团 (核心本地商业+新业务 2大分部)',
    ticker: '03690',
    description: '餐饮外卖酒旅现金牛 + 小象超市及Keeta出海',
    segments: [
      { name: '核心本地商业 (餐饮外卖/即时闪购/到店酒旅)', ebit: 38500, bear_mult: 13.0, base_mult: 16.5, bull_mult: 20.0 },
      { name: '新业务及其他拓展 (小象超市/快驴供应链/Keeta海外)', ebit: 5000, bear_mult: 10.0, base_mult: 14.0, bull_mult: 18.0 },
    ]
  },
  {
    id: '09988',
    name: '🛍️ 阿里巴巴 (电商现金牛+云计算 4大分部)',
    ticker: '09988',
    description: '淘天集团 + 阿里云智能 + 国际商业 + 菜鸟本地生活',
    segments: [
      { name: '淘天集团 (淘宝/天猫国内电商零售与批发现金牛)', ebit: 125000, bear_mult: 7.5, base_mult: 9.5, bull_mult: 12.0 },
      { name: '阿里云智能集团 (公共云与通义千问AI算力基础设施)', ebit: 15000, bear_mult: 18.0, base_mult: 22.0, bull_mult: 28.0 },
      { name: '阿里国际数字商业 (速卖通Choice/Lazada/Trendyol)', ebit: 8000, bear_mult: 12.0, base_mult: 15.0, bull_mult: 20.0 },
      { name: '菜鸟与本地生活服务 (高德地图/饿了么/菜鸟物流)', ebit: 9500, bear_mult: 10.0, base_mult: 12.5, bull_mult: 16.0 },
    ]
  },
  {
    id: 'TSLA',
    name: '⚡ 特斯拉 (汽车+储能+FSD AI 3大分部)',
    ticker: 'TSLA',
    description: '整车产销 + Megapack储能 + 软件与前瞻期权',
    segments: [
      { name: '电动汽车整车制造与销售交付 (Model 3/Y/CyberTruck)', ebit: 8500, bear_mult: 16.0, base_mult: 22.0, bull_mult: 28.0 },
      { name: '储能与清洁能源系统 (Megapack电网储能与Powerwall)', ebit: 2500, bear_mult: 20.0, base_mult: 28.0, bull_mult: 36.0 },
      { name: 'FSD全自动驾驶软件订阅与Robotaxi前瞻AI期权', ebit: 2000, bear_mult: 25.0, base_mult: 35.0, bull_mult: 48.0 },
    ]
  },
  {
    id: 'AAPL',
    name: '🍎 苹果公司 (硬件+软件订阅 2大分部)',
    ticker: 'AAPL',
    description: '顶级消费硬件 + 高粘性服务订阅',
    segments: [
      { name: '高端硬件产品生态 (iPhone / Mac / iPad / 智能穿戴)', ebit: 82000, bear_mult: 18.0, base_mult: 21.0, bull_mult: 25.0 },
      { name: '高粘性软件与订阅生态 (App Store / iCloud / Apple Pay)', ebit: 45000, bear_mult: 28.0, base_mult: 32.0, bull_mult: 38.0 },
    ]
  },
  {
    id: '300750',
    name: '🔋 宁德时代 (动力+储能+材料 3大分部)',
    ticker: '300750',
    description: '动力电池主营 + 储能高增长 + 材料循环',
    segments: [
      { name: '动力电池系统 (全球新能源乘用车与商用车锂电池)', ebit: 38000, bear_mult: 14.0, base_mult: 18.0, bull_mult: 22.0 },
      { name: '储能电池系统 (全球电网侧与工商业储能电芯)', ebit: 12500, bear_mult: 18.0, base_mult: 24.0, bull_mult: 30.0 },
      { name: '电池关键材料与锂资源回收循环体系', ebit: 3500, bear_mult: 10.0, base_mult: 13.0, bull_mult: 16.0 },
    ]
  },
  {
    id: '09992',
    name: '🧸 泡泡玛特 (IP矩阵与海外体验 5大分部)',
    ticker: '09992',
    description: 'LABUBU超级IP + 经典IP + 乐园与海外',
    segments: [
      { name: 'THE MONSTERS 头部超级IP (LABUBU)', ebit: 7646, bear_mult: 20.0, base_mult: 28.0, bull_mult: 36.0 },
      { name: '经典艺术家核心IP矩阵 (MOLLY/SKULLPANDA/DIMOO)', ebit: 6336, bear_mult: 16.0, base_mult: 22.0, bull_mult: 28.0 },
      { name: '新锐孵化与外部授权合作IP', ebit: 2310, bear_mult: 18.0, base_mult: 25.0, bull_mult: 35.0 },
      { name: '主题乐园与线下沉浸体验零售', ebit: 306, bear_mult: 12.0, base_mult: 16.0, bull_mult: 22.0 },
      { name: '衍生内容开发与海外全球化业务', ebit: 292, bear_mult: 20.0, base_mult: 30.0, bull_mult: 45.0 },
    ]
  },
  {
    id: 'generic_dual',
    name: '⚙️ 通用双业务拆分模板 (成熟主业 + 创新高增长)',
    ticker: 'GENERIC',
    description: '适用于多数具有成熟现金牛与创新第二曲线的控股公司',
    segments: [
      { name: '核心成熟主营业务 (稳健现金牛与防御倍数)', ebit: 10000, bear_mult: 8.0, base_mult: 12.0, bull_mult: 15.0 },
      { name: '高成长创新业务与第二曲线 (溢价估值倍数)', ebit: 3000, bear_mult: 18.0, base_mult: 25.0, bull_mult: 35.0 },
    ]
  },
]

export function getTemplateForTicker(ticker) {
  if (!ticker) return null
  const clean = ticker.replace(/\.(HK|US|SZ|SS)$/i, '').trim().toUpperCase()
  return SOTP_TEMPLATES.find(t => t.id === clean || t.ticker === clean) || null
}
