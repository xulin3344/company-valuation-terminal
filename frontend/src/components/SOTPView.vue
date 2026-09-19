<template>
  <div class="page">
    <div class="page-header">
      <div class="title-wrap">
        <div class="title-row">
          <h2 class="page-title">SOTP 分部加总估值 (Sum of the Parts)</h2>
          <span class="ticker-tag" v-if="state.ticker">{{ state.ticker }} ({{ state.market }})</span>
        </div>
        <div class="page-sub">针对多元化集团业务分别按不同行业乘数与估值逻辑加总，推导整体内在价值</div>
      </div>
      <div class="header-actions">
        <!-- 预置模板快速套用下拉框 -->
        <div class="template-selector-wrap">
          <span class="action-label">📋 预置分部模板:</span>
          <select class="field select-field mono" v-model="selectedTemplateId" @change="applySelectedTemplate">
            <option value="" disabled>-- 快速套用投行分部模板 --</option>
            <option v-for="tpl in SOTP_TEMPLATES" :key="tpl.id" :value="tpl.id">
              {{ tpl.name }}
            </option>
          </select>
        </div>
        <button class="btn btn-primary btn-sm" @click="addNewSegment">
          ➕ 添加新分部
        </button>
      </div>
    </div>

    <!-- 空状态引导向导 -->
    <div v-if="!hasSegments" class="card empty-card">
      <div class="empty-icon">🧩</div>
      <div class="empty-title">当前标的尚未配置业务分部</div>
      <div class="empty-desc">
        SOTP 估值法为投行分析多元化集团（如小米、腾讯、美团、阿里、特斯拉等）的首选工具。你可以直接从下方一键载入推荐模板，或创建自定义分部：
      </div>
      <div class="quick-template-grid">
        <button
          v-for="tpl in SOTP_TEMPLATES.slice(0, 6)"
          :key="tpl.id"
          class="quick-tpl-btn"
          @click="loadTemplate(tpl)"
        >
          <span class="tpl-btn-name">{{ tpl.name }}</span>
          <span class="tpl-btn-desc">{{ tpl.description }}</span>
        </button>
      </div>
      <div style="margin-top: 16px;">
        <button class="btn btn-secondary btn-sm" @click="addNewSegment">
          ➕ 手动创建第一个自定义分部
        </button>
      </div>
    </div>

    <template v-else>
      <!-- 三大情景对比卡片 -->
      <div class="grid-3" v-if="sotp">
        <div class="card scenario-card" :class="'scenario-' + s.key" v-for="s in scenarios" :key="s.key">
          <div class="scenario-badge">{{ s.badge }}</div>
          <div class="scenario-title">{{ s.label }}</div>
          <div class="scenario-price">¥{{ fmt(s.implied_price) }}</div>
          <div class="scenario-meta">隐含每股目标价格</div>

          <div class="scenario-divider"></div>

          <div class="result-item">
            <span>各分部加总企业价值 (EV)</span>
            <span class="mono">¥{{ fmt(s.enterprise_value) }} M</span>
          </div>
          <div class="result-item">
            <span>扣除净负债后股权价值</span>
            <span class="mono font-semibold">¥{{ fmt(s.equity_value) }} M</span>
          </div>
        </div>
      </div>

      <!-- 分部贡献明细与环形占比图 -->
      <div class="grid-2" style="margin-top:20px" v-if="sotp?.contributions?.length">
        <div class="card">
          <div class="card-header-clean">
            <div class="card-title">各业务分部价值贡献 (基准 Base 情境)</div>
            <span class="card-hint">各业务线 EV 贡献金额及占比</span>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>分部名称</th>
                <th>估值贡献 EV</th>
                <th>价值占比</th>
                <th>贡献权重条</th>
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

      <!-- 交互式分部参数编辑器表格 -->
      <div class="card" style="margin-top:20px">
        <div class="card-header-clean">
          <div class="editor-header-left">
            <div class="card-title">🧩 分部估值参数互动编辑器</div>
            <span class="card-hint">可直接修改分部名称、EBIT 及三情景倍数，实时联动全局重算</span>
          </div>
          <div class="editor-header-right">
            <button class="btn btn-xs btn-primary" @click="addNewSegment">➕ 添加分部</button>
            <button class="btn btn-xs btn-outline" @click="resetToCurrentStockPreset" v-if="hasStockPreset">
              🔄 恢复当前标的默认模板
            </button>
            <button class="btn btn-xs btn-danger" @click="clearAllSegments">
              🗑️ 清空所有分部
            </button>
          </div>
        </div>

        <div class="table-scroll">
          <table class="data-table segment-edit-table">
            <thead>
              <tr>
                <th style="width: 28%">业务分部名称 (Segment Name)</th>
                <th style="width: 16%">分部 EBIT (百万)</th>
                <th style="width: 13%">悲观倍数 (Bear)</th>
                <th style="width: 13%">基准倍数 (Base)</th>
                <th style="width: 13%">乐观倍数 (Bull)</th>
                <th style="width: 12%">基准 EV (百万)</th>
                <th style="width: 5%; text-align: center">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(seg, idx) in localSegments" :key="idx">
                <td>
                  <input
                    class="field table-input font-semibold"
                    type="text"
                    v-model="seg.name"
                    placeholder="业务板块名称"
                    @input="onSegmentChange"
                  />
                </td>
                <td>
                  <input
                    class="field table-input mono"
                    type="number"
                    step="100"
                    v-model.number="seg.ebit"
                    placeholder="EBIT金额"
                    @input="onSegmentChange"
                  />
                </td>
                <td>
                  <div class="input-with-x">
                    <input
                      class="field table-input mono"
                      type="number"
                      step="0.5"
                      v-model.number="seg.bear_mult"
                      @input="onSegmentChange"
                    />
                    <span class="input-unit">x</span>
                  </div>
                </td>
                <td>
                  <div class="input-with-x highlight-input">
                    <input
                      class="field table-input mono"
                      type="number"
                      step="0.5"
                      v-model.number="seg.base_mult"
                      @input="onSegmentChange"
                    />
                    <span class="input-unit">x</span>
                  </div>
                </td>
                <td>
                  <div class="input-with-x">
                    <input
                      class="field table-input mono"
                      type="number"
                      step="0.5"
                      v-model.number="seg.bull_mult"
                      @input="onSegmentChange"
                    />
                    <span class="input-unit">x</span>
                  </div>
                </td>
                <td class="mono font-bold accent">
                  ¥{{ fmt((Number(seg.ebit) || 0) * (Number(seg.base_mult) || 0)) }} M
                </td>
                <td style="text-align: center">
                  <button class="btn-icon-del" title="删除该分部" @click="removeSegment(idx)">✕</button>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="table-total-row">
                <td class="font-bold">分部加总合计 (Sum of Segments)</td>
                <td class="mono font-bold">¥{{ fmt(totalEbit) }} M</td>
                <td class="mono font-bold text-muted">加权倍数</td>
                <td class="mono font-bold accent">
                  {{ totalEbit > 0 ? (totalBaseEv / totalEbit).toFixed(1) : '-' }}x
                </td>
                <td class="mono font-bold text-muted">-</td>
                <td class="mono font-bold accent" style="font-size: 14px">
                  ¥{{ fmt(totalBaseEv) }} M
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- 过桥参数调节卡片 (Cash, Debt, Shares) -->
      <div class="card" style="margin-top:20px">
        <div class="card-header-clean">
          <div class="card-title">🌉 股权价值过桥参数 (Equity Value Bridge)</div>
          <span class="card-hint">股权价值 = 分部合计 EV + 现金及等价物 - 有息负债；每股价值 = 股权价值 ÷ 稀释股本</span>
        </div>
        <div class="grid-3 bridge-grid">
          <label class="param-box">
            <span class="param-label">现金及等价物 (+Cash, 百万元)</span>
            <input class="field mono" type="number" step="100" v-model.number="bridge.cash" @input="onSegmentChange" />
            <span class="param-hint">货币资金、定期存款与交易性金融资产</span>
          </label>
          <label class="param-box">
            <span class="param-label">有息总负债 (-Total Debt, 百万元)</span>
            <input class="field mono" type="number" step="100" v-model.number="bridge.debt" @input="onSegmentChange" />
            <span class="param-hint">短期借款、长期借款及应付有息债券</span>
          </label>
          <label class="param-box">
            <span class="param-label">完全稀释普通股股本 (Shares, 百万股)</span>
            <input class="field mono" type="number" step="10" v-model.number="bridge.shares" @input="onSegmentChange" />
            <span class="param-hint">包含期权及可转债潜在稀释后的总普通股数</span>
          </label>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue'
import { state, scheduleRecalculate } from '../store.js'
import SotpPieChart from '../charts/SotpPieChart.vue'
import { formatNumber, formatPercent } from '../utils/financials.js'
import { SOTP_TEMPLATES, getTemplateForTicker } from '../utils/sotpTemplates.js'

const sotp = computed(() => state.result?.sotp)
const selectedTemplateId = ref('')

const localSegments = ref([])
const bridge = reactive({
  cash: 0,
  debt: 0,
  shares: 1,
})

const hasSegments = computed(() => localSegments.value.length > 0)

const hasStockPreset = computed(() => {
  return !!getTemplateForTicker(state.ticker)
})

const totalEbit = computed(() => {
  return localSegments.value.reduce((sum, s) => sum + (Number(s.ebit) || 0), 0)
})

const totalBaseEv = computed(() => {
  return localSegments.value.reduce((sum, s) => sum + ((Number(s.ebit) || 0) * (Number(s.base_mult) || 0)), 0)
})

const scenarios = computed(() => {
  if (!sotp.value) return []
  return [
    { key: 'bear', label: 'Bear 悲观情景', badge: '防御下限', ...sotp.value.bear },
    { key: 'base', label: 'Base 基准情景', badge: '核心中枢', ...sotp.value.base },
    { key: 'bull', label: 'Bull 乐观情景', badge: '成长上限', ...sotp.value.bull },
  ]
})

// 初始化与同步 assumptions 中的分部数据
watch(() => state.assumptions, (a) => {
  if (!a) return
  if (a.sotp && a.sotp.segments) {
    localSegments.value = JSON.parse(JSON.stringify(a.sotp.segments))
    bridge.cash = a.sotp.cash ?? a.dcf_params?.cash ?? 0
    bridge.debt = a.sotp.debt ?? a.dcf_params?.debt ?? 0
    bridge.shares = a.sotp.shares ?? a.dcf_params?.shares ?? 1
  } else if (a.summary?.sotp_segments?.length) {
    localSegments.value = JSON.parse(JSON.stringify(a.summary.sotp_segments))
    bridge.cash = a.dcf_params?.cash ?? 0
    bridge.debt = a.dcf_params?.debt ?? 0
    bridge.shares = a.dcf_params?.shares ?? 1
  } else {
    // 检查当前标的是否有推荐模板
    const tpl = getTemplateForTicker(state.ticker)
    if (tpl && localSegments.value.length === 0) {
      loadTemplate(tpl, false)
    }
  }
}, { immediate: true })

function onSegmentChange() {
  if (!state.assumptions) return

  if (localSegments.value.length === 0) {
    state.assumptions.sotp = null
    if (state.assumptions.summary) {
      state.assumptions.summary.sotp_segments = []
    }
  } else {
    const formattedSegments = localSegments.value.map(s => ({
      name: s.name || '未命名业务',
      ebit: Number(s.ebit) || 0,
      bear_mult: Number(s.bear_mult) || 1,
      base_mult: Number(s.base_mult) || 1,
      bull_mult: Number(s.bull_mult) || 1,
    }))

    state.assumptions.sotp = {
      segments: formattedSegments,
      cash: Number(bridge.cash) || 0,
      debt: Number(bridge.debt) || 0,
      shares: Number(bridge.shares) || 1,
    }

    if (state.assumptions.summary) {
      state.assumptions.summary.sotp_segments = formattedSegments
      // 确保 SOTP 模型在汇总看板中拥有合理的权重
      const sotpModel = state.assumptions.summary.models?.find(m => m.key === 'sotp')
      if (sotpModel && sotpModel.weight === 0) {
        sotpModel.weight = 0.25
        const rem = 0.75 / 4.0
        state.assumptions.summary.models.forEach(m => {
          if (m.key !== 'sotp') m.weight = rem
        })
      }
    }
  }

  scheduleRecalculate()
}

function addNewSegment() {
  localSegments.value.push({
    name: `新业务分部 ${localSegments.value.length + 1}`,
    ebit: 1000,
    bear_mult: 10.0,
    base_mult: 15.0,
    bull_mult: 20.0,
  })
  onSegmentChange()
}

function removeSegment(index) {
  localSegments.value.splice(index, 1)
  onSegmentChange()
}

function clearAllSegments() {
  if (confirm('确定要清空所有业务分部吗？清空后 SOTP 模型将自动停用并降级。')) {
    localSegments.value = []
    onSegmentChange()
  }
}

function loadTemplate(tpl, trigger = true) {
  if (!tpl) return
  localSegments.value = JSON.parse(JSON.stringify(tpl.segments))
  selectedTemplateId.value = tpl.id
  if (trigger) {
    onSegmentChange()
  }
}

function applySelectedTemplate() {
  const tpl = SOTP_TEMPLATES.find(t => t.id === selectedTemplateId.value)
  if (tpl) {
    loadTemplate(tpl)
  }
}

function resetToCurrentStockPreset() {
  const tpl = getTemplateForTicker(state.ticker)
  if (tpl) {
    loadTemplate(tpl)
  }
}

function fmt(v, d = 2) { return formatNumber(v, d) }
function pct(v, d = 1) { return formatPercent(v, d) }
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.title-wrap { display: flex; flex-direction: column; gap: 4px; }
.title-row { display: flex; align-items: center; gap: 10px; }
.page-title { font-size: 20px; font-weight: 700; color: var(--text-0); }
.ticker-tag { font-size: 12px; padding: 2px 8px; border-radius: 4px; background: var(--accent-dim); color: var(--accent); font-family: var(--font-mono); font-weight: 600; }
.page-sub { font-size: 12px; color: var(--text-3); }

.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.template-selector-wrap { display: flex; align-items: center; gap: 6px; }
.action-label { font-size: 11px; color: var(--text-3); }
.select-field { font-size: 12px; padding: 4px 8px; border-radius: 6px; background: var(--bg-1); color: var(--text-1); border: 1px solid var(--border); }

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
.font-bold { font-weight: 700; color: var(--text-0); }

.card-header-clean { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text-0); }
.card-hint { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.editor-header-left { display: flex; flex-direction: column; gap: 2px; }
.editor-header-right { display: flex; gap: 8px; align-items: center; }

.progress-track { width: 100%; height: 6px; background: var(--bg-3); border-radius: 3px; overflow: hidden; }
.progress-bar { height: 100%; background: var(--accent); border-radius: 3px; }

.table-scroll { max-height: 480px; overflow: auto; }
.table-input { width: 100%; padding: 6px 8px; font-size: 12px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg-1); }
.table-input:focus { border-color: var(--accent); outline: none; }

.input-with-x { display: flex; align-items: center; gap: 4px; }
.input-unit { font-size: 12px; color: var(--text-3); font-family: var(--font-mono); }
.highlight-input input { border-color: var(--accent); font-weight: 600; }

.table-total-row td { background: var(--bg-2); border-top: 2px solid var(--border); padding: 10px 8px; }
.btn-icon-del { background: none; border: none; color: #f87171; cursor: pointer; font-size: 14px; padding: 4px 8px; border-radius: 4px; }
.btn-icon-del:hover { background: rgba(248, 113, 113, 0.15); }

.bridge-grid { margin-top: 8px; }
.param-box { display: flex; flex-direction: column; gap: 4px; }
.param-label { font-size: 11px; color: var(--text-2); font-weight: 500; }
.param-hint { font-size: 10px; color: var(--text-3); }

.empty-card { text-align: center; padding: 40px 20px; }
.empty-icon { font-size: 48px; margin-bottom: 10px; }
.empty-title { font-size: 18px; font-weight: 700; color: var(--text-0); margin-bottom: 8px; }
.empty-desc { font-size: 13px; color: var(--text-2); max-width: 580px; margin: 0 auto 24px auto; line-height: 1.6; }

.quick-template-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; max-width: 800px; margin: 0 auto; }
.quick-tpl-btn { display: flex; flex-direction: column; gap: 4px; padding: 12px; background: var(--bg-1); border: 1px solid var(--border); border-radius: 8px; text-align: left; cursor: pointer; transition: all 0.2s; }
.quick-tpl-btn:hover { border-color: var(--accent); background: var(--bg-2); transform: translateY(-2px); }
.tpl-btn-name { font-size: 13px; font-weight: 600; color: var(--text-0); }
.tpl-btn-desc { font-size: 11px; color: var(--text-3); line-height: 1.3; }

.btn-xs { padding: 3px 8px; font-size: 11px; border-radius: 4px; }
.btn-outline { background: var(--bg-2); border: 1px solid var(--border); color: var(--text-1); cursor: pointer; }
.btn-outline:hover { border-color: var(--accent); }
.btn-danger { background: rgba(248, 113, 113, 0.12); border: 1px solid #f87171; color: #f87171; cursor: pointer; }
.btn-danger:hover { background: rgba(248, 113, 113, 0.25); }

@media (max-width: 900px) {
  .grid-3 { grid-template-columns: 1fr; }
  .grid-2 { grid-template-columns: 1fr; }
  .quick-template-grid { grid-template-columns: 1fr; }
}
</style>