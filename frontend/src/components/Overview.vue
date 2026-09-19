<template>
  <div class="page">
    <div class="page-header">
      <div class="title-wrap">
        <h2 class="page-title">财务与数据全景总览</h2>
        <div class="page-sub">全面透视历史财报、关键财务比率与数据质量健康度</div>
      </div>
      <div class="header-badges">
        <span class="badge badge-market">{{ state.market }} 市场</span>
        <span class="badge badge-accent">{{ state.ticker }}</span>
        <span class="badge badge-curr">{{ state.analyzeResult?.currency || 'CNY' }}</span>
        <span class="tag" :class="healthTag">{{ state.analyzeResult?.health }} 健康</span>
      </div>
    </div>

    <!-- 核心指标 KPI Grid -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">最新营业收入</div>
        <div class="kpi-value accent">{{ fmt(latestRev) }} <span class="kpi-unit">M</span></div>
        <div class="kpi-sub">历史趋势见右侧图表</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">最新净利润</div>
        <div class="kpi-value" :class="(latestNet || 0) >= 0 ? 'good' : 'danger'">
          {{ fmt(latestNet) }} <span class="kpi-unit">M</span>
        </div>
        <div class="kpi-sub">净利率 {{ latestNetMargin }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">最新毛利率</div>
        <div class="kpi-value warn">{{ latestGrossMargin }}</div>
        <div class="kpi-sub">毛利润: {{ fmt(latestGrossProfit) }} M</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">营业利润 (EBIT)</div>
        <div class="kpi-value info">{{ fmt(latestEbit) }} <span class="kpi-unit">M</span></div>
        <div class="kpi-sub">EBIT 利润率 {{ latestEbitMargin }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">现金储备 (Cash)</div>
        <div class="kpi-value good">{{ fmt(balance.cash) }} <span class="kpi-unit">M</span></div>
        <div class="kpi-sub">货币资金与高流动性资产</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">有息总负债 (Debt)</div>
        <div class="kpi-value" :class="(balance.debt || 0) > 0 ? 'danger' : 'good'">
          {{ fmt(balance.debt) }} <span class="kpi-unit">M</span>
        </div>
        <div class="kpi-sub">短长期有息借款合计</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">净负债 (Net Debt)</div>
        <div class="kpi-value" :class="netDebt <= 0 ? 'good' : 'warn'">
          {{ fmt(netDebt) }} <span class="kpi-unit">M</span>
        </div>
        <div class="kpi-sub">{{ netDebt <= 0 ? '净现金充裕 🛡️' : '存在净负债杠杆' }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">当前股价与总股本</div>
        <div class="kpi-value">{{ fmt(sf?.price) }} <span class="kpi-unit">{{ state.analyzeResult?.currency }}</span></div>
        <div class="kpi-sub">总股本: {{ fmt(balance.shares_diluted, 1) }} M 股</div>
      </div>
    </div>

    <!-- 核心图表行：营收净利趋势 + 成本费用拆解 -->
    <div class="grid-2" style="margin-top:20px">
      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">历年营收与净利趋势 (含毛利率/净利率)</div>
          <span class="card-hint">双轴对比 / 百万</span>
        </div>
        <IncomeChart
          :periods="periods"
          :revenue="income.revenue"
          :netIncome="income.net_income"
          :grossProfit="income.gross_profit"
        />
      </div>

      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">最新期成本与费用结构占比</div>
          <span class="card-hint">COGS vs 运营费用 vs 营业利润</span>
        </div>
        <ExpenseBreakdownChart
          :cogs="latestCogs"
          :selling="latestSelling"
          :admin="latestAdmin"
          :rd="latestRd"
          :ebit="latestEbit"
        />
      </div>
    </div>

    <!-- 数据质量与清洗报告 -->
    <div class="card" style="margin-top:20px" v-if="q">
      <div class="card-header-clean">
        <div class="card-title">财报数据校验与清洗报告</div>
        <span class="card-hint">数据源: {{ state.analyzeResult?.source }} · 抓取耗时: {{ state.analyzeResult?.elapsed_seconds }}s</span>
      </div>
      <div class="quality-grid">
        <div v-if="q.missing && Object.keys(q.missing).length" class="quality-item">
          <div class="quality-label">缺失科目 (已启用安全降级或补零)</div>
          <div class="tags">
            <span v-for="k in Object.keys(q.missing)" :key="k" class="tag tag-warn">{{ getAccountName(k) }}</span>
          </div>
        </div>
        <div v-if="q.derived_accounts?.length" class="quality-item">
          <div class="quality-label">自动推导补全科目 (基于勾稽关系)</div>
          <div class="tags">
            <span v-for="k in q.derived_accounts" :key="k" class="tag tag-good">{{ getAccountName(k) }}</span>
          </div>
        </div>
        <div v-if="q.warnings?.length" class="quality-item full-width">
          <div class="quality-label">模型质量预警</div>
          <div v-for="w in q.warnings" :key="w" class="warning-text">⚠ {{ w }}</div>
        </div>
        <div v-if="!q.missing?.length && !q.warnings?.length" class="quality-success">
          ✓ 财报数据完全平衡，勾稽校验 100% 通过
        </div>
      </div>
    </div>

    <!-- 损益表与资产负债表 -->
    <div class="grid-2" style="margin-top:20px">
      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">标准利润表 (百万, 历史周期)</div>
          <span class="card-hint">单位: {{ state.analyzeResult?.currency || 'CNY' }}</span>
        </div>
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th style="min-width:140px">科目名称</th>
                <th v-for="(p, i) in periods" :key="i">{{ p }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="acc in incomeRows" :key="acc" :class="{ 'highlight-row': isImportantAccount(acc) }">
                <td class="acc-cell">
                  <span class="acc-name">{{ getAccountName(acc) }}</span>
                  <span class="acc-key">{{ acc }}</span>
                </td>
                <td v-for="(v, i) in income[acc]" :key="i" class="mono font-val">
                  {{ fmt(v) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">资产负债表关键科目 (最新期)</div>
          <span class="card-hint">单位: {{ state.analyzeResult?.currency || 'CNY' }}</span>
        </div>
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th>科目名称</th>
                <th>最新账面价值</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(v, k) in balance" :key="k" :class="{ 'highlight-row': isImportantAccount(k) }">
                <td class="acc-cell">
                  <span class="acc-name">{{ getAccountName(k) }}</span>
                  <span class="acc-key">{{ k }}</span>
                </td>
                <td class="mono font-val accent">
                  {{ fmt(v) }} M
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { state } from '../store.js'
import IncomeChart from '../charts/IncomeChart.vue'
import ExpenseBreakdownChart from '../charts/ExpenseBreakdownChart.vue'
import { getAccountName, formatNumber, formatPercent } from '../utils/financials.js'

const sf = computed(() => state.analyzeResult?.standard_financials)
const income = computed(() => sf.value?.income || {})
const balance = computed(() => sf.value?.balance || {})
const periods = computed(() => sf.value?.periods || [])
const q = computed(() => state.analyzeResult?.quality)

const incomeRows = computed(() => Object.keys(income.value).filter(k => Array.isArray(income.value[k])))

function getLastVal(arr) {
  if (!arr || !arr.length) return null
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] != null) return arr[i]
  }
  return null
}

const latestRev = computed(() => getLastVal(income.value?.revenue))
const latestNet = computed(() => getLastVal(income.value?.net_income))
const latestGrossProfit = computed(() => getLastVal(income.value?.gross_profit))
const latestEbit = computed(() => getLastVal(income.value?.ebit))
const latestCogs = computed(() => getLastVal(income.value?.cogs))
const latestSelling = computed(() => getLastVal(income.value?.selling_expense))
const latestAdmin = computed(() => getLastVal(income.value?.admin_expense))
const latestRd = computed(() => getLastVal(income.value?.rd_expense))

const latestGrossMargin = computed(() => {
  if (latestRev.value && latestGrossProfit.value != null) {
    return formatPercent(latestGrossProfit.value / latestRev.value)
  }
  return '—'
})

const latestNetMargin = computed(() => {
  if (latestRev.value && latestNet.value != null) {
    return formatPercent(latestNet.value / latestRev.value)
  }
  return '—'
})

const latestEbitMargin = computed(() => {
  if (latestRev.value && latestEbit.value != null) {
    return formatPercent(latestEbit.value / latestRev.value)
  }
  return '—'
})

const netDebt = computed(() => {
  const debt = balance.value?.debt || 0
  const cash = balance.value?.cash || 0
  return debt - cash
})

const healthTag = computed(() => {
  const h = state.analyzeResult?.health
  if (h === 'good') return 'tag-good'
  if (h === 'partial') return 'tag-warn'
  return 'tag-danger'
})

function isImportantAccount(acc) {
  return ['revenue', 'gross_profit', 'ebit', 'net_income', 'cash', 'debt', 'shares_diluted'].includes(acc)
}

function fmt(v, d = 2) {
  return formatNumber(v, d)
}
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.title-wrap { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 20px; font-weight: 700; color: var(--text-0); }
.page-sub { font-size: 12px; color: var(--text-3); }
.header-badges { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.badge { padding: 4px 10px; background: var(--bg-2); border-radius: 6px; font-size: 12px; font-weight: 600; color: var(--text-1); border: 1px solid var(--border); }
.badge-market { color: var(--text-2); }
.badge-accent { background: var(--accent-dim); color: var(--accent); border-color: var(--accent); }
.badge-curr { font-family: var(--font-mono); color: var(--warn); }

/* KPI Grid */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.kpi-card { background: var(--bg-1); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; display: flex; flex-direction: column; gap: 4px; transition: transform 0.2s, box-shadow 0.2s; }
.kpi-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: var(--border-strong); }
.kpi-label { font-size: 11px; color: var(--text-3); font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
.kpi-value { font-size: 22px; font-weight: 700; font-family: var(--font-mono); color: var(--text-0); }
.kpi-unit { font-size: 12px; font-weight: normal; color: var(--text-3); margin-left: 2px; }
.kpi-sub { font-size: 11px; color: var(--text-2); margin-top: 2px; }

.kpi-value.accent { color: var(--accent); }
.kpi-value.good { color: var(--good); }
.kpi-value.warn { color: var(--warn); }
.kpi-value.danger { color: var(--danger); }
.kpi-value.info { color: #38bdf8; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.card-header-clean { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.card-hint { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.quality-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.quality-item { display: flex; flex-direction: column; gap: 8px; }
.quality-item.full-width { grid-column: span 2; }
.quality-label { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.warning-text { color: var(--warn); font-size: 12px; padding: 6px 10px; background: rgba(251, 191, 36, 0.1); border-radius: 4px; border-left: 3px solid var(--warn); margin-bottom: 4px; }
.quality-success { color: var(--good); font-size: 13px; font-weight: 500; padding: 12px 0; }

.table-scroll { max-height: 420px; overflow: auto; }
.acc-cell { display: flex; flex-direction: column; gap: 2px; }
.acc-name { font-weight: 500; color: var(--text-0); }
.acc-key { font-size: 10px; color: var(--text-3); font-family: var(--font-mono); }
.font-val { font-size: 13px; }
.highlight-row { background: var(--bg-2); }
.highlight-row .acc-name { color: var(--accent); font-weight: 600; }

@media (max-width: 900px) {
  .grid-2 { grid-template-columns: 1fr; }
}
</style>