<template>
  <div class="page">
    <div class="page-header">
      <div class="title-wrap">
        <h2 class="page-title">SOTP 分部加总估值 (Sum of the Parts)</h2>
        <div class="page-sub">针对多元化集团业务分别按不同行业乘数与估值逻辑加总，推导整体内在价值</div>
      </div>
      <div class="header-badges" v-if="sotp">
        <span class="badge">基准中枢: ¥{{ fmt(sotp.base?.implied_price) }}</span>
        <span class="badge">分部数量: {{ sotp.contributions?.length || 0 }} 个</span>
      </div>
    </div>

    <div v-if="!sotp" class="card empty-card">
      <div class="empty-icon">🧩</div>
      <div class="empty-title">暂无分部加总配置</div>
      <div class="empty-desc">当前标的尚未配置多业务线分部数据。可在假设参数页添加分部后实时计算。</div>
    </div>

    <template v-else>
      <!-- 三大情景对比卡片 -->
      <div class="grid-3">
        <div class="card scenario-card" :class="'scenario-' + s.key" v-for="s in scenarios" :key="s.key">
          <div class="scenario-badge">{{ s.badge }}</div>
          <div class="scenario-title">{{ s.label }}</div>
          <div class="scenario-price">¥{{ fmt(s.implied_price) }}</div>
          <div class="scenario-meta">隐含每股价格</div>

          <div class="scenario-divider"></div>

          <div class="result-item">
            <span>分部合计 EV</span>
            <span class="mono">¥{{ fmt(s.enterprise_value) }} M</span>
          </div>
          <div class="result-item">
            <span>对应股权价值</span>
            <span class="mono font-semibold">¥{{ fmt(s.equity_value) }} M</span>
          </div>
        </div>
      </div>

      <!-- 分部贡献明细与环形占比图 -->
      <div class="grid-2" style="margin-top:20px">
        <div class="card">
          <div class="card-header-clean">
            <div class="card-title">各业务分部价值贡献 (基准 Base 情境)</div>
            <span class="card-hint">EV 贡献金额及占比</span>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>分部名称</th>
                <th>估值贡献 EV</th>
                <th>价值占比</th>
                <th>权重贡献条</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(c, i) in sotp.contributions" :key="i">
                <td class="font-semibold">{{ c.name }}</td>
                <td class="mono accent">¥{{ fmt(c.ev) }} M</td>
                <td class="mono font-bold">{{ pct(c.pct) }}</td>
                <td>
                  <div class="progress-track">
                    <div class="progress-bar" :style="{ width: ((c.pct || 0) * 100) + '%' }"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card">
          <div class="card-header-clean">
            <div class="card-title">业务板块估值结构占比分布</div>
            <span class="card-hint">各分部对总企业价值支撑度</span>
          </div>
          <SotpPieChart :contributions="sotp.contributions" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { state } from '../store.js'
import SotpPieChart from '../charts/SotpPieChart.vue'
import { formatNumber, formatPercent } from '../utils/financials.js'

const sotp = computed(() => state.result?.sotp)

const scenarios = computed(() => {
  if (!sotp.value) return []
  return [
    { key: 'bear', label: 'Bear 悲观情景', badge: '防御下限', ...sotp.value.bear },
    { key: 'base', label: 'Base 基准情景', badge: '核心中枢', ...sotp.value.base },
    { key: 'bull', label: 'Bull 乐观情景', badge: '成长上限', ...sotp.value.bull },
  ]
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
.badge { padding: 4px 10px; background: var(--bg-2); border-radius: 6px; font-size: 12px; font-weight: 600; color: var(--text-2); border: 1px solid var(--border); font-family: var(--font-mono); }

.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.scenario-card { position: relative; padding: 20px; text-align: center; border-top: 3px solid var(--accent); }
.scenario-bear { border-top-color: #f87171; }
.scenario-base { border-top-color: var(--accent); }
.scenario-bull { border-top-color: #4ade80; }

.scenario-badge { position: absolute; top: 12px; right: 14px; font-size: 10px; padding: 2px 6px; border-radius: 4px; background: var(--bg-2); color: var(--text-2); }
.scenario-title { font-size: 14px; font-weight: 600; color: var(--text-1); margin-bottom: 8px; }
.scenario-price { font-size: 28px; font-weight: 800; font-family: var(--font-mono); color: var(--text-0); margin-bottom: 2px; }
.scenario-base .scenario-price { color: var(--accent); }
.scenario-meta { font-size: 11px; color: var(--text-3); }

.scenario-divider { height: 1px; background: var(--border); margin: 14px 0; }
.result-item { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-2); margin-bottom: 6px; }
.font-semibold { font-weight: 600; color: var(--text-0); }

.card-header-clean { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.card-hint { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.progress-track { width: 100%; height: 6px; background: var(--bg-3); border-radius: 3px; overflow: hidden; }
.progress-bar { height: 100%; background: var(--accent); border-radius: 3px; }

.empty-card { text-align: center; padding: 60px 20px; }
.empty-icon { font-size: 48px; margin-bottom: 10px; }
.empty-title { font-size: 16px; font-weight: 600; color: var(--text-1); margin-bottom: 6px; }
.empty-desc { font-size: 13px; color: var(--text-3); max-width: 360px; margin: 0 auto; }

@media (max-width: 900px) {
  .grid-3 { grid-template-columns: 1fr; }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>