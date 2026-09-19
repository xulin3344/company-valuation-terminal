<template>
  <div class="page">
    <div class="page-header">
      <div class="title-wrap">
        <h2 class="page-title">综合估值汇总决策看板</h2>
        <div class="page-sub">多模型（内在估值 DCF + 相对估值 Comps + 分部加总 SOTP）多维度交叉加权决断</div>
      </div>
      <div class="header-badges" v-if="summary">
        <span class="badge badge-rating" :class="ratingClass">{{ summary.rating }}</span>
        <span class="badge badge-upside" :class="upsideClass">
          {{ summary.upside >= 0 ? '+' : '' }}{{ pct(summary.upside) }} 空间
        </span>
      </div>
    </div>

    <!-- 顶部核心决策大卡片 -->
    <div class="grid-summary">
      <!-- 估值中枢与评级大卡 -->
      <div class="card summary-main-card">
        <div class="center-tag">综合合理价值中枢</div>
        <div class="center-price-wrap">
          <span class="currency-sym">¥</span>
          <span class="center-price accent">{{ fmt(summary?.fair_value) }}</span>
          <span class="center-unit">{{ state.analyzeResult?.currency || 'CNY' }} / 股</span>
        </div>

        <div class="price-contrast-bar">
          <div class="contrast-item">
            <span class="c-label">当前市场价格</span>
            <span class="c-val mono">¥{{ fmt(currentPrice) }}</span>
          </div>
          <div class="contrast-arrow">➔</div>
          <div class="contrast-item">
            <span class="c-label">潜在空间 (Upside)</span>
            <span class="c-val mono" :class="upsideClass">{{ summary?.upside >= 0 ? '+' : '' }}{{ pct(summary?.upside) }}</span>
          </div>
          <div class="contrast-divider"></div>
          <div class="contrast-item">
            <span class="c-label">综合评级</span>
            <span class="c-val font-bold" :class="ratingClass">{{ summary?.rating }}</span>
          </div>
        </div>

        <div class="range-boxes">
          <div class="range-box">
            <span class="r-title">核心加权区间 (Weighted Range)</span>
            <span class="r-val mono">¥{{ fmt(summary?.weighted_low) }} ~ ¥{{ fmt(summary?.weighted_high) }}</span>
          </div>
          <div class="range-box">
            <span class="r-title">全模型包络区间 (Envelope Range)</span>
            <span class="r-val mono">¥{{ fmt(summary?.full_low) }} ~ ¥{{ fmt(summary?.full_high) }}</span>
          </div>
        </div>
      </div>

      <!-- 参与计算的模型权重分配 -->
      <div class="card">
        <div class="card-header-clean">
          <div class="card-title">估值模型明细与权重</div>
          <span class="card-hint">各子模型可用性与贡献度</span>
        </div>
        <table class="data-table" v-if="summary">
          <thead>
            <tr>
              <th>模型名称</th>
              <th>测算每股价值</th>
              <th>合理区间</th>
              <th>加权占比</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in summary.models" :key="m.key" :class="{ disabled: !m.available }">
              <td class="font-semibold">
                <span class="status-dot" :class="m.available ? 'dot-active' : 'dot-inactive'"></span>
                {{ m.label }}
              </td>
              <td class="mono" :class="m.available ? 'accent font-bold' : 'text-muted'">
                {{ m.available ? '¥' + fmt(m.price) : '—' }}
              </td>
              <td class="mono font-sm">
                {{ m.available ? '¥' + fmt(m.low) + ' ~ ¥' + fmt(m.high) : ('排除: ' + m.exclude_reason) }}
              </td>
              <td>
                <div class="weight-cell" v-if="m.available">
                  <span class="mono">{{ pct(m.weight) }}</span>
                  <div class="weight-bar-bg">
                    <div class="weight-bar-fill" :style="{ width: ((m.weight || 0) * 100) + '%' }"></div>
                  </div>
                </div>
                <span v-else class="text-muted font-sm">未纳入</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 经典足球场图 (Football Field Chart) -->
    <div class="card" style="margin-top:20px" v-if="summary">
      <div class="card-header-clean">
        <div class="card-title">估值区间足球场图 (Football Field Range Chart)</div>
        <span class="card-hint">红色虚线: 当前市价 · 青色虚线: 加权中枢</span>
      </div>
      <div style="padding: 10px 0">
        <FootballField :data="footballData" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { state } from '../store.js'
import FootballField from '../charts/FootballField.vue'
import { formatNumber, formatPercent } from '../utils/financials.js'

const summary = computed(() => state.result?.summary)
const currentPrice = computed(() => state.analyzeResult?.standard_financials?.price || 0)

const footballData = computed(() => {
  if (!summary.value) return null
  return {
    models: summary.value.models.filter(m => m.available).map(m => ({
      name: m.label,
      low: m.low,
      high: m.high,
      price: m.price
    })),
    currentPrice: currentPrice.value,
    fairValue: summary.value.fair_value,
  }
})

const upsideClass = computed(() => {
  const u = summary.value?.upside
  if (u == null) return ''
  if (u > 0.15) return 'good'
  if (u < -0.1) return 'danger'
  return 'warn'
})

const ratingClass = computed(() => {
  const r = summary.value?.rating || ''
  if (r.includes('显著低估') || r.includes('低估')) return 'good'
  if (r.includes('高估')) return 'danger'
  return 'accent'
})

function fmt(v, d = 2) { return formatNumber(v, d) }
function pct(v, d = 1) { return formatPercent(v, d) }
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.title-wrap { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 20px; font-weight: 700; color: var(--text-0); }
.page-sub { font-size: 12px; color: var(--text-3); }
.header-badges { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.badge { padding: 5px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; border: 1px solid var(--border); font-family: var(--font-mono); }
.badge-rating.good { background: rgba(74, 222, 128, 0.15); color: var(--good); border-color: var(--good); }
.badge-rating.danger { background: rgba(248, 113, 113, 0.15); color: var(--danger); border-color: var(--danger); }
.badge-rating.accent { background: var(--accent-dim); color: var(--accent); border-color: var(--accent); }
.badge-upside { background: var(--bg-2); }

.grid-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.summary-main-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px;
  background: linear-gradient(135deg, var(--bg-1) 0%, var(--bg-2) 100%);
  border: 1px solid var(--border-strong);
}

.center-tag { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-3); font-weight: 600; margin-bottom: 6px; }
.center-price-wrap { display: flex; align-items: baseline; gap: 4px; margin-bottom: 18px; }
.currency-sym { font-size: 24px; font-weight: 700; color: var(--accent); }
.center-price { font-size: 46px; font-weight: 900; font-family: var(--font-mono); line-height: 1; }
.center-unit { font-size: 13px; color: var(--text-3); margin-left: 4px; }

.price-contrast-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--bg-1);
  border-radius: 8px;
  border: 1px solid var(--border);
  margin-bottom: 18px;
}
.contrast-item { display: flex; flex-direction: column; gap: 2px; }
.contrast-arrow { color: var(--text-3); font-size: 14px; }
.contrast-divider { width: 1px; height: 28px; background: var(--border); margin: 0 4px; }
.c-label { font-size: 11px; color: var(--text-3); }
.c-val { font-size: 15px; font-weight: 600; }

.range-boxes { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.range-box { padding: 10px 12px; background: var(--bg-1); border-radius: 6px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 4px; }
.r-title { font-size: 10px; color: var(--text-3); text-transform: uppercase; }
.r-val { font-size: 13px; font-weight: 600; color: var(--text-0); }

.card-header-clean { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.card-hint { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.status-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 6px; }
.dot-active { background: var(--accent); box-shadow: 0 0 6px var(--accent); }
.dot-inactive { background: var(--text-3); }

.weight-cell { display: flex; align-items: center; gap: 8px; }
.weight-bar-bg { width: 50px; height: 6px; background: var(--bg-3); border-radius: 3px; overflow: hidden; }
.weight-bar-fill { height: 100%; background: var(--accent); border-radius: 3px; }

.disabled { opacity: 0.45; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
.font-sm { font-size: 11px; }
.good { color: var(--good); }
.warn { color: var(--warn); }
.danger { color: var(--danger); }
.accent { color: var(--accent); }
.text-muted { color: var(--text-3); }

@media (max-width: 900px) {
  .grid-summary { grid-template-columns: 1fr; }
}
</style>