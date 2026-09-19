<template>
  <div class="page">
    <div class="page-header">
      <div class="title-wrap">
        <h2 class="page-title">估值模型核心假设参数</h2>
        <div class="page-sub">实时修改任何参数将触发后台秒级快速重算，并同步更新所有估值模型</div>
      </div>
      <div class="header-badges">
        <div class="preset-group">
          <span class="preset-label">情境模板:</span>
          <button class="btn btn-xs" @click="applyPreset('bull')">🚀 乐观 (Bull)</button>
          <button class="btn btn-xs" @click="applyPreset('base')">⚖️ 基准 (Base)</button>
          <button class="btn btn-xs" @click="applyPreset('bear')">🛡️ 保守 (Bear)</button>
        </div>
        <span class="recalc-pill" v-if="state.recalcTime">
          ⚡ 重算耗时 {{ state.recalcTime.toFixed(0) }}ms
        </span>
      </div>
    </div>

    <!-- WACC 与 核心折现参数 -->
    <div class="grid-2">
      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">WACC 加权平均资本成本参数</div>
          <span class="card-hint">CAPM 资本资产定价模型</span>
        </div>
        <div class="param-grid">
          <label v-for="f in waccFields" :key="f.key" class="param-box">
            <span class="param-label">{{ f.label }}</span>
            <input class="field mono" type="number" step="0.005" v-model.number="wacc[f.key]" @input="recalc" />
            <span class="param-hint">{{ f.hint }}</span>
          </label>
        </div>

        <div class="wacc-summary-box" v-if="state.result?.wacc">
          <div class="wacc-metric">
            <span class="w-label">权益资本成本 (Ke)</span>
            <span class="w-val mono">{{ pct(state.result.wacc.cost_of_equity) }}</span>
          </div>
          <div class="wacc-metric">
            <span class="w-label">税后债务成本 (Kd*(1-t))</span>
            <span class="w-val mono">{{ pct(state.result.wacc.after_tax_cost_of_debt) }}</span>
          </div>
          <div class="wacc-metric highlight">
            <span class="w-label">综合折现率 (WACC)</span>
            <span class="w-val mono accent font-bold">{{ pct(state.result.wacc.wacc) }}</span>
          </div>
        </div>
      </div>

      <!-- DCF 终值与宏观参数 -->
      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">DCF 终值与长期稳态假设</div>
          <span class="card-hint">Gordon 永续模型 & 退出乘数</span>
        </div>
        <div class="param-grid">
          <label class="param-box">
            <span class="param-label">永续增长率 g (Perpetual Growth)</span>
            <input class="field mono" type="number" step="0.005" v-model.number="dcf.g" @input="recalc" />
            <span class="param-hint">通常取 GDP 长期预期 (2% ~ 3.5%)</span>
          </label>
          <label class="param-box">
            <span class="param-label">退出乘数 (Exit Multiple EV/EBITDA)</span>
            <input class="field mono" type="number" step="0.5" v-model.number="dcf.exit_multiple" @input="recalc" />
            <span class="param-hint">第 5 年末企业价值/EBITDA 乘数</span>
          </label>
          <label class="param-box">
            <span class="param-label">预测基准期营业收入 (百万)</span>
            <input class="field mono" type="number" v-model.number="forecast.base_revenue" @input="recalc" />
            <span class="param-hint">起始推演的最新完整年度营收</span>
          </label>
          <label class="param-box">
            <span class="param-label">所得税率 (Effective Tax Rate)</span>
            <input class="field mono" type="number" step="0.01" v-model.number="forecast.tax_rate" @input="recalc" />
            <span class="param-hint">法定或实际有效综合所得税率</span>
          </label>
          <label class="param-box full-span">
            <span class="param-label">营运资金增量比率 (NWC % of ΔRevenue)</span>
            <input class="field mono" type="number" step="0.01" v-model.number="forecast.nwc_pct_of_rev_delta" @input="recalc" />
            <span class="param-hint">每增加 1 元营收所需占用的净营运资金比率</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 5年详细财务预测矩阵 -->
    <div class="card" style="margin-top:20px">
      <div class="card-header-clean">
        <div class="card-title">未来 5 年财务明细假设预测 (Forecast Schedule)</div>
        <span class="card-hint">可直接双击或点击单元格进行修改</span>
      </div>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th style="min-width:180px">核心预测驱动因子</th>
              <th v-for="i in 5" :key="i">Year {{ i }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in forecastRows" :key="row.key">
              <td class="font-semibold">
                {{ row.label }}
                <span class="row-hint">({{ row.unit }})</span>
              </td>
              <td v-for="i in 5" :key="i">
                <input
                  class="field table-input mono"
                  type="number"
                  step="0.01"
                  v-model.number="forecast[row.key][i-1]"
                  @input="recalc"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- SOTP 分部加总快捷配置与状态卡片 -->
    <div class="card" style="margin-top:20px">
      <div class="card-header-clean">
        <div class="card-title">🧩 SOTP 分部加总参数 (Sum of the Parts)</div>
        <span class="card-hint">适用于具有多元业务板块的控股集团</span>
      </div>
      <div class="sotp-summary-row">
        <div class="sotp-status-info">
          <div class="sotp-badge-row">
            <span class="sotp-status-badge" :class="sotpSegmentCount > 0 ? 'active' : 'inactive'">
              {{ sotpSegmentCount > 0 ? `已激活: ${sotpSegmentCount} 个业务分部` : '暂未配置业务分部 (处于自降级状态)' }}
            </span>
            <span class="sotp-price-metric" v-if="state.result?.sotp?.base?.implied_price">
              基准估值中枢: <b class="mono accent">¥{{ state.result.sotp.base.implied_price.toFixed(2) }}</b>
            </span>
          </div>
          <span class="sotp-desc">
            {{ sotpSegmentCount > 0 
              ? '当前标的已通过投行分部模型拆解估值，可在 SOTP 工作台随时编辑分部参数并实时重算。'
              : '针对小米、腾讯、美团、阿里等多元化集团，可前往 SOTP 工作台一键套用标准分部模板并参与加权汇总。' }}
          </span>
        </div>
        <button class="btn btn-sm btn-primary" @click="emit('navigate', 'sotp')">
          前往 SOTP 交互工作台 ➔
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch, computed } from 'vue'
import { state, scheduleRecalculate } from '../store.js'
import { formatPercent } from '../utils/financials.js'

const emit = defineEmits(['navigate'])

const sotpSegmentCount = computed(() => {
  return state.assumptions?.sotp?.segments?.length || state.result?.sotp?.contributions?.length || 0
})

const waccFields = [
  { key: 'rf', label: '无风险利率 (Rf)', hint: '通常取10年期国债收益率' },
  { key: 'beta', label: '股票 Beta 系数 (β)', hint: '相对大盘波动敏感度' },
  { key: 'erp', label: '股权风险溢价 (ERP)', hint: '市场超额回报预期 (5%~7%)' },
  { key: 'kd', label: '债务融资成本 (Kd)', hint: '银行贷款或发债综合利率' },
  { key: 'weight_equity', label: '股权资本权重 (We)', hint: '股权资本在总资本结构占比' },
  { key: 'tax_rate', label: '利息抵税税率 (t)', hint: '用于计算税后债务成本' },
]

const wacc = reactive({})
const forecast = reactive({
  growth: [],
  gross_margin: [],
  selling_ratio: [],
  admin_ratio: [],
  da_pct: [],
  capex_pct: [],
  base_revenue: 0,
  tax_rate: 0.25,
  nwc_pct_of_rev_delta: 0.1
})
const dcf = reactive({ g: 0.03, exit_multiple: 15.0 })

const forecastRows = [
  { key: 'growth', label: '营业收入增长率', unit: '小数, 如 0.15' },
  { key: 'gross_margin', label: '综合毛利率', unit: '小数, 如 0.45' },
  { key: 'selling_ratio', label: '销售费用率', unit: '占营收比例' },
  { key: 'admin_ratio', label: '管理费用率', unit: '占营收比例' },
  { key: 'da_pct', label: '折旧与摊销 (D&A) 占比', unit: '占营收比例' },
  { key: 'capex_pct', label: '资本开支 (CapEx) 占比', unit: '占营收比例' },
]

let originalSnapshot = null

watch(() => state.assumptions, (a) => {
  if (!a) return
  if (!originalSnapshot) {
    originalSnapshot = JSON.parse(JSON.stringify(a))
  }
  Object.assign(wacc, a.wacc_inputs || {})
  Object.assign(forecast, a.forecast_assumptions || {})
  if (a.dcf_params) {
    dcf.g = a.dcf_params.g
    dcf.exit_multiple = a.dcf_params.exit_multiple
  }
}, { immediate: true })

function recalc() {
  state.assumptions.wacc_inputs = { ...wacc }
  state.assumptions.forecast_assumptions = { ...forecast }
  if (state.assumptions.dcf_params) {
    state.assumptions.dcf_params.g = dcf.g
    state.assumptions.dcf_params.exit_multiple = dcf.exit_multiple
  }
  scheduleRecalculate()
}

function applyPreset(type) {
  if (!originalSnapshot) return
  const baseAssump = JSON.parse(JSON.stringify(originalSnapshot))

  if (type === 'base') {
    Object.assign(wacc, baseAssump.wacc_inputs)
    Object.assign(forecast, baseAssump.forecast_assumptions)
    dcf.g = baseAssump.dcf_params?.g || 0.03
    dcf.exit_multiple = baseAssump.dcf_params?.exit_multiple || 15.0
  } else if (type === 'bull') {
    forecast.growth = (baseAssump.forecast_assumptions.growth || []).map(g => Number((g * 1.2 + 0.02).toFixed(3)))
    forecast.gross_margin = (baseAssump.forecast_assumptions.gross_margin || []).map(m => Number((m * 1.05).toFixed(3)))
    dcf.g = Number((baseAssump.dcf_params?.g + 0.005).toFixed(3))
    dcf.exit_multiple = Number((baseAssump.dcf_params?.exit_multiple * 1.15).toFixed(1))
    wacc.rf = Math.max(0.02, Number((wacc.rf - 0.005).toFixed(3)))
  } else if (type === 'bear') {
    forecast.growth = (baseAssump.forecast_assumptions.growth || []).map(g => Number((g * 0.7 - 0.02).toFixed(3)))
    forecast.gross_margin = (baseAssump.forecast_assumptions.gross_margin || []).map(m => Number((m * 0.95).toFixed(3)))
    dcf.g = Math.max(0.01, Number((baseAssump.dcf_params?.g - 0.008).toFixed(3)))
    dcf.exit_multiple = Math.max(6, Number((baseAssump.dcf_params?.exit_multiple * 0.8).toFixed(1)))
    wacc.rf = Number((wacc.rf + 0.005).toFixed(3))
  }
  recalc()
}

function pct(v, d = 2) { return formatPercent(v, d) }
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.title-wrap { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 20px; font-weight: 700; color: var(--text-0); }
.page-sub { font-size: 12px; color: var(--text-3); }
.header-badges { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

.preset-group { display: flex; align-items: center; gap: 6px; background: var(--bg-2); padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border); }
.preset-label { font-size: 11px; color: var(--text-3); }
.btn-xs { padding: 3px 8px; font-size: 11px; border-radius: 4px; }

.recalc-pill { font-size: 11px; color: var(--accent); font-family: var(--font-mono); background: var(--accent-dim); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--accent); }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.card-header-clean { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.card-hint { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.param-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.param-box { display: flex; flex-direction: column; gap: 4px; }
.param-box.full-span { grid-column: span 2; }
.param-label { font-size: 11px; color: var(--text-2); font-weight: 500; }
.param-hint { font-size: 10px; color: var(--text-3); }

.wacc-summary-box {
  margin-top: 16px;
  padding: 12px 16px;
  background: var(--bg-2);
  border-radius: 8px;
  border: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.wacc-metric { display: flex; flex-direction: column; gap: 2px; }
.wacc-metric.highlight { text-align: right; }
.w-label { font-size: 11px; color: var(--text-3); }
.w-val { font-size: 15px; font-weight: 600; color: var(--text-0); }
.w-val.accent { color: var(--accent); font-size: 18px; }

.table-scroll { max-height: 380px; overflow: auto; }
.table-input { width: 100%; min-width: 80px; padding: 6px 8px; font-size: 12px; border-radius: 4px; }
.row-hint { font-size: 11px; color: var(--text-3); font-weight: normal; margin-left: 4px; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }

.sotp-summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-2);
  border-radius: 8px;
  border: 1px solid var(--border);
  flex-wrap: wrap;
  gap: 16px;
}
.sotp-status-info { display: flex; flex-direction: column; gap: 6px; }
.sotp-badge-row { display: flex; align-items: center; gap: 12px; }
.sotp-status-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.sotp-status-badge.active {
  background: var(--accent-dim);
  color: var(--accent);
  border: 1px solid var(--accent);
}
.sotp-status-badge.inactive {
  background: var(--bg-3);
  color: var(--text-3);
  border: 1px solid var(--border);
}
.sotp-price-metric { font-size: 13px; color: var(--text-1); }
.sotp-desc { font-size: 12px; color: var(--text-3); max-width: 600px; line-height: 1.4; }

@media (max-width: 900px) {
  .grid-2 { grid-template-columns: 1fr; }
  .param-grid { grid-template-columns: 1fr; }
  .param-box.full-span { grid-column: span 1; }
  .sotp-summary-row { flex-direction: column; align-items: flex-start; }
}
</style>