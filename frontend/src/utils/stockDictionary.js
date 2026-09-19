// 常用与重点上市公司股票代码知识库与专业估值适配建议引擎
export const STOCK_DATABASE = [
  // 港股 (HK)
  {
    ticker: '09992',
    name: '泡泡玛特',
    fullName: '泡泡玛特国际集团有限公司 (POP MART International Group Limited)',
    enName: 'POP MART',
    market: 'HK',
    exchange: '香港联合交易所有限公司 (HKEX 主板)',
    ipoYear: '2020年',
    currency: 'CNY (人民币计价/港币交易)',
    sector: '潮流文化与IP衍生品运营',
    businessModel: '以潮玩IP（如 MOLLY、SKULLPANDA、LABUBU/THE MONSTERS、DIMOO）为核心，涵盖IP孵化、盲盒/手办设计零售、海外直营门店扩张及主题乐园乐园衍生。',
    companyType: '高成长品牌消费与全球化IP运营龙头',
    typeTag: '成长消费/IP出海',
    financialTraits: ['高毛利 (60%+)', '海外收入复合高增', '零有息负债/净现金丰沛', '存货与渠道周转快'],
    advice: {
      primary: { method: 'dcf_exit', name: 'Exit 退出乘数法 (EV/EBITDA)', weight: '40%', reason: '海外高速扩张期资本开支及门店折旧摊销明显，EV/EBITDA能真实还原现金创利能力；兼顾中长期稳态退出倍数。' },
      secondary: { method: 'comps_pe', name: 'P/E 市盈率法 / PEG', weight: '30%', reason: '作为消费品牌标的，同业可比对标（如万代、三丽鸥、乐高及潮玩连锁）受公开市场投资者广泛认可。' },
      tertiary: { method: 'dcf_gordon', name: 'Gordon 永续增长法', weight: '20%', reason: '作为DCF内生价值底线检验，但需注意永续增长率g假设不宜过高，避免高估成熟期规模。' },
      auxiliary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 可比倍数', weight: '10%', reason: '剔除现金储备扰动后的企业价值倍数对比。' },
      caution: { method: 'sotp', name: 'SOTP 分部加总', note: '目前主要围绕潮玩IP与零售单一大主业运营，分拆分部必要性不高，建议赋予较低权重。' }
    }
  },
  {
    ticker: '00700',
    name: '腾讯控股',
    fullName: '腾讯控股有限公司 (Tencent Holdings Limited)',
    enName: 'Tencent',
    market: 'HK',
    exchange: '香港联合交易所 (HKEX 恒生指数核心权重股)',
    ipoYear: '2004年',
    currency: 'RMB (报告币种) / HKD (交易币种)',
    sector: '互联网平台 / 社交与数字娱乐',
    businessModel: '以微信/QQ为国民级流量底座，构建增值服务（网络游戏/社交网络）、网络广告、金融科技与企业服务（微信支付/腾讯云/AI）三驾马车及庞大外部投资版图。',
    companyType: '平台型多元化科技互联网控股集团',
    typeTag: '科技航母/多元控股',
    financialTraits: ['高现金流创造力', '多元业务驱动', '庞大联营公司投资资产', '回购注销力度强'],
    advice: {
      primary: { method: 'sotp', name: 'SOTP 分部加总估值', weight: '40%', reason: '★ 投行首选！游戏、广告、金融科技、腾讯云各业务利润率及成熟度差异极大，且拥有千亿级上市公司对外股权投资，唯有SOTP能公允拆解真实资产价值。' },
      secondary: { method: 'dcf_exit', name: 'DCF 退出乘数法', weight: '30%', reason: '高自由现金流属性匹配自由现金流折现，以Exit Multiple考量成熟互联网巨头终端倍数。' },
      tertiary: { method: 'comps_pe', name: 'P/E 市盈率法', weight: '20%', reason: '主营扣非核心业务市盈率与海外科技巨头横向对标。' },
      auxiliary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 倍数估值', weight: '10%', reason: '企业价值倍数对比。' },
      caution: { method: 'dcf_gordon', name: 'Gordon 永续增长', note: '受宏观及体量基数限制，单一永续模型难以完全反映多元生态价值。' }
    }
  },
  {
    ticker: '03690',
    name: '美团',
    fullName: '美团 (Meituan)',
    enName: 'Meituan',
    market: 'HK',
    exchange: '香港联合交易所 (HKEX 主板)',
    ipoYear: '2018年',
    currency: 'RMB (报告币种) / HKD (交易币种)',
    sector: '本地生活服务 / 即时零售与电商',
    businessModel: '依托庞大即时骑手履约网络与本地商户连接，核心业务为餐饮外卖与到店酒旅业务，创新业务涵盖美团优选、美团买菜（小象超市）与海外扩张（Keeta）。',
    companyType: '本地生活基础设施龙头 / 核心利润+创新拓展',
    typeTag: '即时零售/平台经济',
    financialTraits: ['核心本地商业高经营现金流', '创新业务处于减亏/出海期', '强规模网络效应'],
    advice: {
      primary: { method: 'sotp', name: 'SOTP 分部加总估值', weight: '45%', reason: '核心本地商业已产生丰厚EBIT利润，而新业务及出海仍处于减亏和重投入期，将成熟外卖酒旅与创新业务分拆估值是投行最标准视角。' },
      secondary: { method: 'dcf_exit', name: 'DCF 退出乘数法', weight: '30%', reason: '随新业务亏损收窄，全集团无杠杆自由现金流(UFCF)高速释放，适合现金流折现。' },
      tertiary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 倍数法', weight: '15%', reason: '剔除外卖即时配送重资产摊销扰动。' },
      auxiliary: { method: 'comps_pe', name: 'P/E 市盈率法', weight: '10%', reason: '当期利润受新业务扰动，单一P/E波动较大。' },
      caution: { method: 'dcf_gordon', name: 'Gordon 永续增长', note: '本地商业面临竞争格局演进，需动态推演5年过渡期。' }
    }
  },
  {
    ticker: '09988',
    name: '阿里巴巴',
    fullName: '阿里巴巴集团控股有限公司 (Alibaba Group Holding Limited)',
    enName: 'Alibaba',
    market: 'HK',
    exchange: '香港联合交易所 / 纽交所双重主要上市',
    ipoYear: '2019年 (港股)',
    currency: 'RMB',
    sector: '电子商务 / 阿里云计算 / 海外数字商业',
    businessModel: '淘天集团（国内电商零售/批发现金牛）、阿里云智能集团（云计算与AI底层）、阿里国际数字商业（速卖通/Lazada）、菜鸟集团及本地生活服务。',
    companyType: '电商与云计算超级控股集团',
    typeTag: '电商现金牛+云计算',
    financialTraits: ['年自由现金流超千亿', '账面千亿现金理财', '大规模回购股息率可观'],
    advice: {
      primary: { method: 'sotp', name: 'SOTP 分部加总估值', weight: '50%', reason: '★ 市场公认唯一公允方式！淘天集团(现金牛成熟期)、阿里云(高成长独立估值)、国际商业(高增长跨境电商)，各分部按不同乘数相加。' },
      secondary: { method: 'dcf_gordon', name: 'DCF 现金流折现 (Gordon)', weight: '25%', reason: '千亿级自由现金流底仓价值，适合作为价值底线保护。' },
      tertiary: { method: 'comps_pe', name: 'P/E 市盈率相对估值', weight: '15%', reason: '当前已具备类公用事业高股息特征，P/E估值极具防守反弹参考度。' },
      auxiliary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 倍数法', weight: '10%', reason: '扣除巨大净现金后企业倍数极低。' },
      caution: { method: 'dcf_exit', name: 'Exit 乘数法', note: '需保守设置终值倍数。' }
    }
  },
  {
    ticker: '01810',
    name: '小米集团',
    fullName: '小米集团 (Xiaomi Corporation)',
    enName: 'Xiaomi',
    market: 'HK',
    exchange: '香港联合交易所 (HKEX 主板)',
    ipoYear: '2018年',
    currency: 'RMB',
    sector: '消费电子 / 智能电动车 / 互联网服务',
    businessModel: '“人车家全生态”战略：智能手机高端化出海、AIoT消费电子生态互联、智能电动汽车 (SU7系列) 及高毛利互联网变现服务。',
    companyType: '智能硬件+电动汽车+互联网生态三轮驱动',
    typeTag: '人车家全生态/硬科技',
    financialTraits: ['手机与IoT基本盘高周转', '汽车业务爆发式增长', '千亿现金储备支撑汽车研发'],
    advice: {
      primary: { method: 'sotp', name: 'SOTP 分部加总估值', weight: '45%', reason: '手机IoT成熟硬件(给8~12x PE) + 互联网服务高毛利(给15~20x PE) + 智能汽车业务(按PS或EV/Sales估值)，SOTP为最标准框架。' },
      secondary: { method: 'dcf_exit', name: 'DCF 现金流折现', weight: '30%', reason: '汽车产能爬坡与软件服务中长期释放充沛现金流。' },
      tertiary: { method: 'comps_pe', name: 'P/E 市盈率法', weight: '15%', reason: '对标苹果及全球消费电子巨头。' },
      auxiliary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 倍数', weight: '10%', reason: '衡量综合硬件盈利水平。' },
      caution: { method: 'dcf_gordon', name: 'Gordon 永续法', note: '汽车与芯片研发投入较大，前期现金流存在阶段波动。' }
    }
  },

  // 美股 (US)
  {
    ticker: 'AAPL',
    name: '苹果公司',
    fullName: 'Apple Inc.',
    enName: 'Apple Inc.',
    market: 'US',
    exchange: '美国纳斯达克证券交易所 (NASDAQ: AAPL)',
    ipoYear: '1980年',
    currency: 'USD (美元)',
    sector: '消费电子 / 软件与订阅服务',
    businessModel: '全球领先的消费硬件（iPhone、Mac、iPad、Apple Watch）与强大的闭环生态订阅服务（App Store、iCloud、Apple Music、Apple Pay）。',
    companyType: '软硬件闭环顶级自由现金牛',
    typeTag: '消费电子/高自由现金流',
    financialTraits: ['千亿美元年自由现金流', '巨额股票回购注销', '极强品牌护城河与粘性', '高ROE'],
    advice: {
      primary: { method: 'dcf_gordon', name: 'DCF 现金流折现 (Gordon 永续)', weight: '40%', reason: '★ 股神巴菲特最推崇逻辑！现金流极度充沛稳定，每年大额持续注销股本，Gordon模型最能捕获其永续自由现金流价值。' },
      secondary: { method: 'comps_pe', name: 'P/E 市盈率估值', weight: '30%', reason: '市场对苹果硬件与服务业务的估值乘数认知高度一致（历史多在25x~35x PE）。' },
      tertiary: { method: 'dcf_exit', name: 'DCF 退出乘数法', weight: '20%', reason: '以成熟期高端科技品牌倍数锚定终值。' },
      auxiliary: { method: 'sotp', name: 'SOTP 分部法', weight: '10%', reason: '将硬件（较低倍数）与服务订阅（高倍数）分别定价。' },
      caution: { method: 'comps_ev_ebitda', name: 'EV/EBITDA', note: '可作为交叉参考，但对软件服务高附加值敏感度略低。' }
    }
  },
  {
    ticker: 'NVDA',
    name: '英伟达',
    fullName: 'NVIDIA Corporation',
    enName: 'NVIDIA',
    market: 'US',
    exchange: '美国纳斯达克全球精选市场 (NASDAQ: NVDA)',
    ipoYear: '1999年',
    currency: 'USD (美元)',
    sector: '半导体芯片 / 人工智能计算基础设施',
    businessModel: '全球 GPU 与 AI 算力底座霸主，提供全栈式加速计算硬件（Hopper/Blackwell架构）、网络互联（Infiniband/Spectrum-X）及 CUDA 软件生态。',
    companyType: '全球 AI 算力基础设施核心卖水人',
    typeTag: '硬科技/AI军备竞赛',
    financialTraits: ['爆发式超高增长', '70%+ 超高毛利率', '巨额研发壁垒', '强定价权'],
    advice: {
      primary: { method: 'dcf_exit', name: 'DCF 退出乘数法', weight: '45%', reason: '当前处于 AI 爆发期，超高净现金流将在未来3~5年急剧积累，需重点测算中期现金流及技术换代后的 Exit 倍数。' },
      secondary: { method: 'comps_pe', name: 'P/E / PEG 市盈率相对估值', weight: '30%', reason: '综合考量AI芯片高景气度带来的超预期业绩兑现，结合PEG指标合理化估值溢价。' },
      tertiary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 倍数法', weight: '15%', reason: '对标半导体行业平均水平与算力军备周期。' },
      auxiliary: { method: 'dcf_gordon', name: 'Gordon 永续法', weight: '10%', reason: '需注意芯片行业本身具有周期性，永续g应保持理智保守。' },
      caution: { method: 'sotp', name: 'SOTP 分部法', note: '数据中心算力业务占比超80%，为主导核心，无需复杂分拆。' }
    }
  },
  {
    ticker: 'TSLA',
    name: '特斯拉',
    fullName: 'Tesla, Inc.',
    enName: 'Tesla',
    market: 'US',
    exchange: '美国纳斯达克全球精选市场 (NASDAQ: TSLA)',
    ipoYear: '2010年',
    currency: 'USD (美元)',
    sector: '智能电动汽车 / 储能 / 人形机器人 / FSD AI',
    businessModel: '涵盖智能电动乘用车制造销售（Model 3/Y/CyberTruck）、公用事业与户用储能系统（Megapack/Powerwall）、FSD全自动驾驶订阅、Optimus人形机器人与超级计算平台。',
    companyType: '跨界 AI 具身智能与能源硬件科技领军者',
    typeTag: 'AI+储能+新能源车',
    financialTraits: ['制造业重资产属性但具备软件期权', '全球产销网络', '储能业务高复合爆发'],
    advice: {
      primary: { method: 'sotp', name: 'SOTP 分部加总估值', weight: '50%', reason: '★ 机构分歧最大但最科学方法！必须将整车制造业务（传统车企/新能源倍数）、储能业务（高增长公用事业储能）、FSD软件订阅及机器人创新期权拆开分别加总。' },
      secondary: { method: 'dcf_exit', name: 'DCF 退出乘数法', weight: '30%', reason: '测算长周期全球汽车+储能交付现金流，并赋予中长期科技属性乘数。' },
      tertiary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 相对法', weight: '10%', reason: '对标整车制造业现金创利水平。' },
      auxiliary: { method: 'comps_pe', name: 'P/E 市盈率法', weight: '10%', reason: '静态PE易因季度降价与研发波动出现剧烈起伏，仅供参考。' },
      caution: { method: 'dcf_gordon', name: 'Gordon 永续法', note: '技术迭代剧烈，单一永续模型容易错判中远期机器人等新增长极。' }
    }
  },

  // A股 (CN)
  {
    ticker: '600519',
    name: '贵州茅台',
    fullName: '贵州茅台酒股份有限公司 (Kweichow Moutai Co., Ltd.)',
    enName: 'Kweichow Moutai',
    market: 'CN',
    exchange: '上海证券交易所主板 (SSE: 600519)',
    ipoYear: '2001年',
    currency: 'CNY (人民币)',
    sector: '白酒与高端消费品',
    businessModel: '核心为贵州茅台酒系列产品的生产与销售，拥有顶级独占的地理标志品牌心智护城河，销售渠道涵盖直销渠道（i茅台）、传统经销商、商超电商。',
    companyType: '中国核心资产顶级品牌护城河与永续现金牛',
    typeTag: '顶级护城河/永续分红',
    financialTraits: ['超 90% 极高毛利率', '超 50% 极高净利率', '无有息负债/净现金极厚', '确定性分红'],
    advice: {
      primary: { method: 'dcf_gordon', name: 'DCF Gordon 永续增长法', weight: '45%', reason: '★ 最完美匹配标的！产品生命周期接近无限，商业壁垒几乎不可复制，资本开支平稳，未来几十年现金流高度可预测，Gordon永续模型能完美捕获其内在时间价值。' },
      secondary: { method: 'comps_pe', name: 'P/E 市盈率法', weight: '35%', reason: '国内公募与外资机构最核心定价锚（历史中枢多在 25x~35x PE 波动），具备强大的市场共识。' },
      tertiary: { method: 'dcf_exit', name: 'DCF 退出乘数法', weight: '15%', reason: '作为 5 年稳态回报率测算参照。' },
      auxiliary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 倍数', weight: '5%', reason: '作为去现金化估值校验。' },
      caution: { method: 'sotp', name: 'SOTP 分部法', note: '核心产品高度聚焦白酒主业，无需分拆。' }
    }
  },
  {
    ticker: '300750',
    name: '宁德时代',
    fullName: '宁德时代新能源科技股份有限公司 (Contemporary Amperex Technology Co., Limited)',
    enName: 'CATL',
    market: 'CN',
    exchange: '深圳证券交易所创业板 (SZSE: 300750)',
    ipoYear: '2018年',
    currency: 'CNY (人民币)',
    sector: '新能源动力电池与储能电池制造',
    businessModel: '全球领先的锂离子电池研发与制造企业，涵盖动力电池系统（神行/麒麟电池等）、储能电池系统及电池回收材料循环体系。',
    companyType: '全球动力电池与储能全球制造霸主',
    typeTag: '全球制造龙头/规模效应',
    financialTraits: ['全球市占率超35%', '巨额研发与Capex折旧', '经营性净现金流极其充沛'],
    advice: {
      primary: { method: 'dcf_exit', name: 'DCF 退出乘数法', weight: '40%', reason: '重资产先进制造行业，前期巨额Capex转化为强大制造壁垒与充沛现金流，Exit倍数能平衡制造业成熟期折价与技术溢价。' },
      secondary: { method: 'comps_ev_ebitda', name: 'EV/EBITDA 相对倍数', weight: '30%', reason: '制造业重折旧重投入，EV/EBITDA 剔除折旧摊销与资本结构差异，为全球锂电与新能源材料对标金标准。' },
      tertiary: { method: 'comps_pe', name: 'P/E 市盈率法', weight: '20%', reason: '随产能利用率与盈利释放，以动态PE结合行业景气周期定价。' },
      auxiliary: { method: 'sotp', name: 'SOTP 分部法', weight: '10%', reason: '动力电池主营 vs 储能高增长分拆校验。' },
      caution: { method: 'dcf_gordon', name: 'Gordon 永续法', note: '动力电池面临固态电池等长期技术路线革新，永续增长率g需保守。' }
    }
  }
]

/**
 * 模糊搜索标的匹配函数
 */
export function fuzzySearchStocks(query, filterMarket = '') {
  if (!query || !query.trim()) return []
  const q = query.trim().toLowerCase()

  return STOCK_DATABASE.filter(item => {
    if (item.ticker.toLowerCase().includes(q)) return true
    if (item.name.toLowerCase().includes(q)) return true
    if (item.fullName && item.fullName.toLowerCase().includes(q)) return true
    if (item.enName.toLowerCase().includes(q)) return true
    if (item.sector && item.sector.toLowerCase().includes(q)) return true
    return false
  }).slice(0, 8)
}

/**
 * 根据股票代码及财报数据，智能生成公司画像与专业估值适配建议
 */
export function getCompanyProfile(ticker, market, financials, analyzeResult) {
  const normTicker = String(ticker || '').toUpperCase().trim()
  const found = STOCK_DATABASE.find(s => s.ticker.toUpperCase() === normTicker)

  if (found) {
    return {
      isCurated: true,
      ...found
    }
  }

  // 动态启发式合成未知标的档案与专业估值建议
  const price = financials?.price || analyzeResult?.standard_financials?.price || 0
  const currency = analyzeResult?.currency || (market === 'US' ? 'USD' : (market === 'HK' ? 'HKD' : 'CNY'))
  const rev = financials?.income?.revenue?.slice(-1)[0] || 0
  const net = financials?.income?.net_income?.slice(-1)[0] || 0
  const cash = financials?.balance?.cash || 0
  const debt = financials?.balance?.debt || 0
  const netMargin = rev > 0 ? (net / rev) : 0

  let companyType = '通用综合型上市企业'
  let typeTag = '通用标的'
  let primaryMethod = 'dcf_exit'
  let primaryName = 'DCF 现金流折现 (退出乘数法)'
  let primaryReason = '现金流折现法直击企业未来真实创利与去杠杆能力，最适合作为基准内生锚。'

  if (netMargin > 0.35 && debt < cash) {
    companyType = '高毛利轻资产高现金流龙头'
    typeTag = '现金牛型'
    primaryMethod = 'dcf_gordon'
    primaryName = 'Gordon 永续增长法 (DCF)'
    primaryReason = '公司净利率极高且手头现金充裕，经营现金流稳定可预测，Gordon永续模型能最好地衡量其永续现金回报价值。'
  } else if (rev > 50000) {
    companyType = '超大规模集团化成熟企业'
    typeTag = '大型多元集团'
    primaryMethod = 'sotp'
    primaryName = 'SOTP 分部加总估值法'
    primaryReason = '营业额巨大且往往覆盖多业务条线，分部加总能避免单一市盈率低估创新业务或不同利润率资产。'
  } else if (net < 0) {
    companyType = '成长扩张期 / 阶段性盈亏平衡中企业'
    typeTag = '高增长或阶段亏损'
    primaryMethod = 'comps_pe'
    primaryName = '同行可比公司法 (EV/Sales 与 远期DCF)'
    primaryReason = '当前净利润尚未充分释放或为负数，传统P/E失真，建议重点以市销率、企业价值倍数及远期现金流折现为核心。'
  }

  return {
    isCurated: false,
    ticker: ticker,
    name: `${ticker} 上市公司`,
    fullName: `${ticker} (${market} 交易所挂牌证券)`,
    enName: `${ticker} Corporation`,
    market: market,
    exchange: market === 'HK' ? '香港交易所 (HKEX)' : (market === 'US' ? '美国证券市场 (NASDAQ/NYSE)' : '中国A股市场 (SSE/SZSE)'),
    ipoYear: '公开上市',
    currency: currency,
    sector: '公开资本市场挂牌行业',
    businessModel: `标的代码为 ${ticker}，于公开市场进行交易，财报数据源为 ${analyzeResult?.source || '标准化公开接口'}。`,
    companyType: companyType,
    typeTag: typeTag,
    financialTraits: [
      `最新年营业收入: ¥${(rev).toLocaleString()} M`,
      `最新净利润: ¥${(net).toLocaleString()} M`,
      debt > cash ? '存在有息负债杠杆' : '净现金储备健康',
      netMargin > 0.15 ? '盈利能力较强' : '利润率处于行业平均'
    ],
    advice: {
      primary: { method: primaryMethod, name: primaryName, weight: '40%', reason: primaryReason },
      secondary: { method: 'comps_pe', name: 'P/E 市盈率相对估值', weight: '30%', reason: '作为同行横向比对的主流参照标准。' },
      tertiary: { method: 'dcf_exit', name: 'Exit 退出乘数法 (EV/EBITDA)', weight: '20%', reason: '衡量企业价值与未来退出倍数空间。' },
      auxiliary: { method: 'sotp', name: 'SOTP 分部加总估值', weight: '10%', reason: '若存在跨界业务可进一步拆分加总。' },
      caution: { method: 'dcf_gordon', name: '参数敏感度警示', note: '折现率 WACC 与永续增长率 g 变动 0.5% 会引起估值大幅波动，需结合敏感性矩阵参考。' }
    }
  }
}
