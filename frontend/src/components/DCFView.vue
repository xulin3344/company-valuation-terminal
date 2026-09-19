<template>
  <div class="page">
    <div class="page-header">
      <div class="title-wrap">
        <h2 class="page-title">DCF 现金流折现估值</h2>
        <div class="page-sub">基于未来 5 年无杠杆自由现金流 (UFCF) 与加权平均资本成本 (WACC) 的内在价值推算</div>
      </div>
      <div class="header-badges">
        <span class="badge">WACC: {{ formatPercent(state.result?.wacc?.wacc, 2) }}</span>
        <span class="badge">永续 g: {{ formatPercent(state.assumptions?.dcf_params?.g, 1) }}</span>
        <span class="badge">退出乘数: {{ state.assumptions?.dcf_params?.exit_multiple }}x</span>
      </div>
    </div>

    <!-- 两种方法并排对比卡片 (支持根据二级菜单焦点高亮) -->
    <div class="grid-2">
      <div class="card dcf-card" :class="{ 'card-focused': focusMethod === 'dcf_gordon' }">
        <div class="dcf-badge" :class="{ 'badge-active': focusMethod === 'dcf_gordon' }">
          {{ focusMethod === 'dcf_gordon' ? '● 当前聚焦 · 永续增长模型' : '永续增长模型' }}
        </div>
        <div class="card-title">Gordon 永续增长法 (Perpetual Growth)</div>
        <div v-if="dcf?.gordon" class="result-grid">
          <div class="result-item"><span>预测期现金流现值 PV(UFCF)</span><span class="mono">¥{{ fmt(dcf.pv_forecast_cashflows) }} M</span></div>
          <div class="result-item"><span>终值 Terminal Value (TV)</span><span class="mono">¥{{ fmt(dcf.gordon.terminal_value) }} M</span></div>
          <div class="result-item"><span>终值现值 PV(Terminal Value)</span><span class="mono">¥{{ fmt(dcf.gordon.pv_terminal_value) }} M</span></div>
          <div class="result-item"><span>企业价值 (Enterprise Value)</span><span class="mono font-semibold">¥{{ fmt(dcf.gordon.enterprise_value) }} M</span></div>
          <div class="result-item"><span>+ 现金及等价物</span><span class="mono good">+¥{{ fmt(dcfParams?.cash) }} M</span></div>
          <div class="result-item"><span>- 有息总负债</span><span class="mono danger">-¥{{ fmt(dcfParams?.debt) }} M</span></div>
          <div class="result-item"><span>= 股权价值 (Equity Value)</span><span class="mono font-semibold">¥{{ fmt(dcf.gordon.equity_value) }} M</span></div>
          <div class="result-item highlight">
            <span class="highlight-label">每股隐含价值 (Gordon)</span>
            <span class="mono highlight-price accent">¥{{ fmt(dcf.gordon.implied_price) }}</span>
          </div>
        </div>
      </div>

      <div class="card dcf-card" :class="{ 'card-focused': focusMethod === 'dcf_exit' }">
        <div class="dcf-badge dcf-badge-exit" :class="{ 'badge-active': focusMethod === 'dcf_exit' }">
          {{ focusMethod === 'dcf_exit' ? '● 当前聚焦 · 退出乘数模型' : '乘数终值模型' }}
        </div>
        <div class="card-title">Exit 退出乘数法 (EV / EBITDA)</div>
        <div v-if="dcf?.exit" class="result-grid">
          <div class="result-item"><span>预测期现金流现值 PV(UFCF)</span><span class="mono">¥{{ fmt(dcf.pv_forecast_cashflows) }} M</span></div>
          <div class="result-item"><span>退出乘数 (Exit Multiple)</span><span class="mono">{{ dcfParams?.exit_multiple }}x</span></div>
          <div class="result-item"><span>终值现值 PV(Terminal Value)</span><span class="mono">¥{{ fmt(dcf.exit.pv_terminal_value) }} M</span></div>
          <div class="result-item"><span>企业价值 (Enterprise Value)</span><span class="mono font-semibold">¥{{ fmt(dcf.exit.enterprise_value) }} M</span></div>
          <div class="result-item"><span>+ 现金及等价物</span><span class="mono good">+¥{{ fmt(dcfParams?.cash) }} M</span></div>
          <div class="result-item"><span>- 有息总负债</span><span class="mono danger">-¥{{ fmt(dcfParams?.debt) }} M</span></div>
          <div class="result-item"><span>= 股权价值 (Equity Value)</span><span class="mono font-semibold">¥{{ fmt(dcf.exit.equity_value) }} M</span></div>
          <div class="result-item highlight">
            <span class="highlight-label">每股隐含价值 (Exit Multiple)</span>
            <span class="mono highlight-price" style="color:#8b5cf6">¥{{ fmt(dcf.exit.implied_price) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- EV 价值桥梁与价值拆解图 -->
    <div class="card" style="margin-top:20px" v-if="dcf?.gordon">
      <div class="card-header-clean">
        <div class="card-title">企业价值 EV → 股权价值 Equity Value 价值桥梁构成</div>
        <span class="card-hint">单位: 百万 (Gordon 永续模型拆解)</span>
      </div>
      <DcfBridgeChart
        :pvUfcf="dcf.pv_forecast_cashflows"
        :pvTerminal="dcf.gordon.pv_terminal_value"
        :cash="dcfParams?.cash"
        :debt="dcfParams?.debt"
        :equityValue="dcf.gordon.equity_value"
      />
    </div>

    <!-- 预测期 5 年现金流测算全明细表 -->
    <div class="card" style="margin-top:20px">
      <div class="card-header-clean">
        <div class="card-title">预测期 5 年无杠杆现金流 (UFCF) 测算明细表</div>
        <span class="card-hint">单位: 百万 / 折现基准期: 5年</span>
      </div>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th style="text-align:left">科目 / 年份</th>
              <th v-for="i in 5" :key="i">Y{{ i }} (预测第{{ i }}年)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="forecast?.revenue">
              <td>预测营业收入 (Revenue)</td>
              <td v-for="(v, i) in forecast.revenue" :key="i">{{ fmt(v) }}</td>
            </tr>
            <tr v-if="forecast?.ebit">
              <td>息税前利润 (EBIT)</td>
              <td v-for="(v, i) in forecast.ebit" :key="i">{{ fmt(v) }}</td>
            </tr>
            <tr v-if="forecast?.nopat">
              <td>税后净营业利润 (NOPAT)</td>
              <td v-for="(v, i) in forecast.nopat" :key="i">{{ fmt(v) }}</td>
            </tr>
            <tr v-if="forecast?.da">
              <td>+ 折旧与摊销 (D&A)</td>
              <td v-for="(v, i) in forecast.da" :key="i" class="good">+{{ fmt(v) }}</td>
            </tr>
            <tr v-if="forecast?.capex">
              <td>- 资本开支 (CapEx)</td>
              <td v-for="(v, i) in forecast.capex" :key="i" class="danger">-{{ fmt(v) }}</td>
            </tr>
            <tr v-if="forecast?.nwc_delta">
              <td>- 营运资金增量 (ΔNWC)</td>
              <td v-for="(v, i) in forecast.nwc_delta" :key="i">-{{ fmt(v) }}</td>
            </tr>
            <tr class="highlight-row-accent" v-if="forecast?.ufcf">
              <td><b>= 无杠杆自由现金流 (UFCF)</b></td>
              <td v-for="(v, i) in forecast.ufcf" :key="i"><b>¥{{ fmt(v) }}</b></td>
            </tr>
            <tr v-if="dcf?.discount_factors">
              <td>折现因子 (1 / (1+WACC)^t)</td>
              <td v-for="(v, i) in dcf.discount_factors" :key="i">{{ fmt(v, 4) }}</td>
            </tr>
            <tr class="highlight-row-bold" v-if="dcf?.pv_of_ufcf">
              <td><b>= UFCF 折现值 (PV)</b></td>
              <td v-for="(v, i) in dcf.pv_of_ufcf" :key="i" class="accent"><b>¥{{ fmt(v) }}</b></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="table-footer-sum">
        <span>预测期 5 年现值累计合计: <b class="accent">¥{{ fmt(dcf?.pv_forecast_cashflows) }} M</b></span>
      </div>
    </div>

    <!-- 敏感性热力矩阵图 -->
    <div class="card" style="margin-top:20px" v-if="dcf?.sensitivity">
      <div class="card-header-clean">
        <div class="card-title">二维双变量敏感性矩阵 (WACC × 永续增长率 g → 每股价值)</div>
        <span class="card-hint">横轴为永续增长率，纵轴为折现率，色块展示不同情景下的每股价值</span>
      </div>
      <Heatmap :data="heatmapData" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { state } from '../store.js'
import Heatmap from '../charts/Heatmap.vue'
import DcfBridgeChart from '../charts/DcfBridgeChart.vue'
import { formatNumber, formatPercent } from '../utils/financials.js'

const props = defineProps({
  focusMethod: { type: String, default: '' }
})

const dcf = computed(() => state.result?.dcf)
const forecast = computed(() => state.result?.forecast)
const dcfParams = computed(() => state.assumptions?.dcf_params)

const heatmapData = computed(() => {
  const s = dcf.value?.sensitivity
  if (!s) return null
  return {
    xLabels: s.g_list.map(g => (g * 100).toFixed(1) + '%'),
    yLabels: s.wacc_list.map(w => (w * 100).toFixed(1) + '%'),
    matrix: s.matrix
  }
})

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
.badge { padding: 4px 10px; background: var(--bg-2); border-radius: 6px; font-size: 12px; font-weight: 600; color: var(--accent); border: 1px solid var(--border); font-family: var(--font-mono); }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.dcf-card { position: relative; overflow: hidden; padding-top: 24px; transition: all 0.25s; }
.card-focused {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px var(--accent-dim), var(--shadow-md) !important;
  transform: translateY(-2px);
}
.badge-active {
  background: var(--accent) !important;
  color: #ffffff !important;
  box-shadow: 0 0 8px var(--accent) !important;
}
.dcf-badge { position: absolute; top: 12px; right: 14px; font-size: 10px; padding: 2px 8px; border-radius: 4px; background: var(--accent-dim); color: var(--accent); font-weight: 600; text-transform: uppercase; transition: all 0.2s; }
.dcf-badge-exit { background: rgba(139, 92, 246, 0.15); color: #8b5cf6; }

.result-grid { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.result-item { display: flex; justify-content: space-between; font-size: 13px; color: var(--text-1); padding: 3px 0; }
.result-item.highlight { padding-top: 10px; margin-top: 4px; border-top: 1px dashed var(--border-strong); align-items: center; }
.highlight-label { font-weight: 600; color: var(--text-0); font-size: 14px; }
.highlight-price { font-size: 22px; font-weight: 700; }

.font-semibold { font-weight: 600; color: var(--text-0); }
.good { color: var(--good); }
.danger { color: var(--danger); }
.accent { color: var(--accent); }

.card-header-clean { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.card-hint { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.table-scroll { max-height: 380px; overflow: auto; }
.highlight-row-accent { background: var(--accent-dim); }
.highlight-row-bold { background: var(--bg-2); }

.table-footer-sum { margin-top: 12px; padding: 10px 14px; background: var(--bg-2); border-radius: 6px; font-size: 13px; text-align: right; border: 1px solid var(--border); }

@media (max-width: 900px) {
  .grid-2 { grid-template-columns: 1fr; }
}
</style>