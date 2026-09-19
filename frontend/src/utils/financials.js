// 财务科目中文对照及工具函数
export const ACCOUNT_NAMES = {
  revenue: '营业收入 (Revenue)',
  cogs: '营业成本 (COGS)',
  gross_profit: '毛利润 (Gross Profit)',
  selling_expense: '销售费用 (Selling Exp)',
  admin_expense: '管理费用 (Admin Exp)',
  rd_expense: '研发费用 (R&D Exp)',
  ebit: '息税前利润 (EBIT)',
  ebitda: '税息折旧摊销前利润 (EBITDA)',
  pretax_profit: '税前利润 (Pretax Profit)',
  tax_expense: '所得税费用 (Tax Expense)',
  net_income: '净利润 (Net Income)',
  minority_pnl: '少数股东损益 (Minority Interest)',
  da: '折旧与摊销 (D&A)',
  capex: '资本开支 (CapEx)',
  eps_diluted: '稀释每股收益 (EPS)',
  cash: '现金及等价物 (Cash)',
  debt: '有息总负债 (Total Debt)',
  minority_equity: '少数股东权益',
  total_equity: '归母所有者权益 (Total Equity)',
  shares_diluted: '稀释总股本 (Shares)',
  total_assets: '总资产 (Total Assets)'
}

export function getAccountName(key) {
  return ACCOUNT_NAMES[key] || key
}

export function formatNumber(v, digits = 2) {
  if (v == null || isNaN(v)) return '—'
  return Number(v).toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits
  })
}

export function formatPercent(v, digits = 1) {
  if (v == null || isNaN(v)) return '—'
  return (Number(v) * 100).toFixed(digits) + '%'
}

export function formatMoney(v, currency = '¥', digits = 2) {
  if (v == null || isNaN(v)) return '—'
  return `${currency}${formatNumber(v, digits)}`
}
