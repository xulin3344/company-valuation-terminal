<template>
  <div class="page">
    <div class="page-header">
      <div class="title-wrap">
        <h2 class="page-title">可比公司相对估值 (Comps)</h2>
        <div class="page-sub">基于行业同行标的乘数分布（P/E、EV/EBITDA、EV/EBIT、EV/Sales）测算相对内在价值</div>
      </div>
      <div class="header-badges" v-if="comps">
        <span class="badge badge-consensus">综合目标价: ¥{{ fmt(comps.consensus_price) }}</span>
        <span class="badge">同行样本数: {{ peersList.length }} 家</span>
      </div>
    </div>

    <!-- 四路相对估值结果矩阵 -->
    <div class="grid-2">
      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">四路倍数推导每股估值</div>
          <span class="card-hint">标的行业对标 / 目标价中枢</span>
        </div>
        <table class="data-table" v-if="comps?.methods">
          <thead>
            <tr>
              <th>估值方法</th>
              <th>行业基准倍数</th>
              <th>推导企业价值 EV</th>
              <th>每股隐含价值</th>
              <th>合理区间</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(m, k) in comps.methods"
              :key="k"
              class="method-row"
              :class="{ 'row-focused': isMethodFocused(k) }"
            >
              <td class="font-semibold">
                {{ methodLabel[k] }}
                <span v-if="isMethodFocused(k)" class="focus-pill">● 当前选中</span>
              </td>
              <td class="mono">{{ fmt(m.multiple_used, 2) }}x</td>
              <td class="mono">¥{{ fmt(m.implied_ev) }} M</td>
              <td class="mono accent font-bold">¥{{ fmt(m.implied_price) }}</td>
              <td class="mono text-muted">¥{{ fmt(m.low_price) }} ~ ¥{{ fmt(m.high_price) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="consensus-box" v-if="comps">
          <div class="consensus-title">可比公司加权综合目标价</div>
          <div class="consensus-price">¥{{ fmt(comps.consensus_price) }}</div>
          <div class="consensus-sub">取四路乘数中位数加权推导计算</div>
        </div>
      </div>

      <!-- 倍数统计分位数表 -->
      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">行业估值乘数分位数统计</div>
          <span class="card-hint">Min / P25 / 中位数 / Mean / P75 / Max</span>
        </div>
        <div class="table-scroll">
          <table class="data-table" v-if="comps?.multiples">
            <thead>
              <tr>
                <th>乘数类型</th>
                <th>最小值</th>
                <th>P25</th>
                <th>中位数</th>
                <th>平均值</th>
                <th>P75</th>
                <th>最大值</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(s, k) in comps.multiples" :key="k">
                <td class="font-semibold">{{ multLabel[k] }}</td>
                <td class="mono text-muted">{{ fmt(s.minimum, 2) }}</td>
                <td class="mono">{{ fmt(s.p25, 2) }}</td>
                <td class="mono accent font-bold">{{ fmt(s.median, 2) }}</td>
                <td class="mono">{{ fmt(s.mean, 2) }}</td>
                <td class="mono">{{ fmt(s.p75, 2) }}</td>
                <td class="mono text-muted">{{ fmt(s.maximum, 2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div style="margin-top:14px">
          <BoxPlot :data="boxplotData" />
        </div>
      </div>
    </div>

    <!-- 补全同行可比公司详情清单表 -->
    <div class="card" style="margin-top:20px">
      <div class="card-header-clean">
        <div class="card-title">同行对标样本公司财务及估值全景清单 ({{ peersList.length }} 家)</div>
        <span class="card-hint">单位: 百万 / 来源: {{ state.assumptions?.comps_params?.peers_source || '动态数据池' }}</span>
      </div>
      <div class="table-scroll" v-if="peersList.length > 0">
        <table class="data-table">
          <thead>
            <tr>
              <th style="text-align:left">可比标的名称</th>
              <th>代码</th>
              <th>总市值</th>
              <th>净负债</th>
              <th>营业收入</th>
              <th>EBITDA</th>
              <th>息税前利润 EBIT</th>
              <th>净利润</th>
              <th>P/E</th>
              <th>EV/EBITDA</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in peersList" :key="p.name + p.ticker">
              <td style="text-align:left" class="font-semibold text-accent">{{ p.name }}</td>
              <td class="mono text-muted">{{ p.ticker || '—' }}</td>
              <td class="mono">¥{{ fmt(p.market_cap) }}</td>
              <td class="mono" :class="p.net_debt <= 0 ? 'good' : 'warn'">¥{{ fmt(p.net_debt) }}</td>
              <td class="mono">¥{{ fmt(p.revenue) }}</td>
              <td class="mono">¥{{ fmt(p.ebitda) }}</td>
              <td class="mono">¥{{ fmt(p.ebit) }}</td>
              <td class="mono" :class="p.net_income >= 0 ? 'good' : 'danger'">¥{{ fmt(p.net_income) }}</td>
              <td class="mono accent font-semibold">{{ calcPe(p) }}</td>
              <td class="mono font-semibold">{{ calcEvEbitda(p) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-text">
        暂无可比公司列表，请在假设参数页设置 Peers。
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { state } from '../store.js'
import BoxPlot from '../charts/BoxPlot.vue'
import { formatNumber } from '../utils/financials.js'

const props = defineProps({
  focusMultiple: { type: String, default: '' }
})

const comps = computed(() => state.result?.comps)
const peersList = computed(() => state.assumptions?.comps_params?.peers || [])

function isMethodFocused(k) {
  if (props.focusMultiple === 'comps_pe' && k === 'pe') return true
  if (props.focusMultiple === 'comps_ev_ebitda' && k === 'ev_ebitda') return true
  return false
}

const methodLabel = {
  pe: 'P/E (市盈率法)',
  ev_ebitda: 'EV/EBITDA (企业价值倍数法)',
  ev_ebit: 'EV/EBIT (息税前利润法)',
  ev_sales: 'EV/Sales (市销率法)'
}

const multLabel = {
  pe: 'P/E',
  ev_ebitda: 'EV/EBITDA',
  ev_ebit: 'EV/EBIT',
  ev_sales: 'EV/Sales'
}

const boxplotData = computed(() => {
  const m = comps.value?.multiples
  if (!m) return []
  return Object.entries(m).map(([k, s]) => ({ name: multLabel[k] || k, ...s }))
})

function calcPe(p) {
  if (!p.net_income || p.net_income <= 0) return '亏损'
  return (p.market_cap / p.net_income).toFixed(1) + 'x'
}

function calcEvEbitda(p) {
  if (!p.ebitda || p.ebitda <= 0) return '—'
  const ev = (p.market_cap || 0) + (p.net_debt || 0)
  return (ev / p.ebitda).toFixed(1) + 'x'
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
.badge { padding: 4px 10px; background: var(--bg-2); border-radius: 6px; font-size: 12px; font-weight: 600; color: var(--text-2); border: 1px solid var(--border); font-family: var(--font-mono); }
.badge-consensus { background: var(--accent-dim); color: var(--accent); border-color: var(--accent); }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.card-header-clean { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.card-hint { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
.text-accent { color: var(--accent); }
.text-muted { color: var(--text-3); }
.good { color: var(--good); }
.warn { color: var(--warn); }
.danger { color: var(--danger); }
.accent { color: var(--accent); }

.row-focused {
  background: var(--accent-dim) !important;
}
.row-focused td {
  color: var(--accent) !important;
}
.focus-pill {
  font-size: 9px;
  background: var(--accent);
  color: #ffffff;
  padding: 1px 5px;
  border-radius: 4px;
  margin-left: 6px;
  font-family: var(--font-sans);
  font-weight: 600;
  vertical-align: middle;
}

.consensus-box { margin-top: 16px; padding: 14px; background: var(--bg-2); border-radius: 8px; border: 1px solid var(--border); text-align: center; }
.consensus-title { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.consensus-price { font-size: 26px; font-weight: 800; font-family: var(--font-mono); color: var(--accent); }
.consensus-sub { font-size: 11px; color: var(--text-2); }

.table-scroll { max-height: 400px; overflow: auto; }
.empty-text { text-align: center; padding: 30px; color: var(--text-3); font-size: 13px; }

@media (max-width: 900px) {
  .grid-2 { grid-template-columns: 1fr; }
}
</style>