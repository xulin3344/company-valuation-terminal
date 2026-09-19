<template>
  <div class="page">
    <!-- 顶部状态栏与验证徽章 -->
    <div class="page-header">
      <div class="title-wrap">
        <h2 class="page-title">公司基本状况与专业估值适配指引</h2>
        <div class="page-sub">验证目标标的信息，并根据公司商业模式与行业特征获取投行级估值方法建议</div>
      </div>
      <div class="header-badges">
        <span class="verification-badge">
          ✓ 标的上市信息已核验
        </span>
        <span class="badge badge-market">{{ profile.market }} 市场</span>
        <span class="badge badge-type">{{ profile.typeTag }}</span>
      </div>
    </div>

    <!-- 第一部分：公司上市基本状况与标的核对卡片 -->
    <div class="card verification-card">
      <div class="verify-header">
        <div class="company-brand">
          <div class="company-logo">{{ (profile.name || state.ticker).slice(0, 1) }}</div>
          <div class="company-titles">
            <div class="company-main-name">
              {{ profile.name }}
              <span class="ticker-pill mono">{{ profile.ticker }}.{{ profile.market }}</span>
              <span class="curated-tag" v-if="profile.isCurated">官方名录已收录</span>
            </div>
            <div class="company-full-name">{{ profile.fullName }}</div>
          </div>
        </div>
        <div class="company-quick-data">
          <div class="qd-item">
            <span class="qd-label">当前股价</span>
            <span class="qd-val mono accent">¥{{ fmt(currentPrice) }}</span>
          </div>
          <div class="qd-item">
            <span class="qd-label">总股本 (M股)</span>
            <span class="qd-val mono">{{ fmt(shares) }}</span>
          </div>
          <div class="qd-item">
            <span class="qd-label">参考总市值</span>
            <span class="qd-val mono font-bold">¥{{ fmt(marketCap) }} M</span>
          </div>
        </div>
      </div>

      <div class="verify-divider"></div>

      <!-- 核心上市基础属性网格 -->
      <div class="profile-grid">
        <div class="p-item">
          <span class="p-label">挂牌交易所</span>
          <span class="p-val font-semibold">{{ profile.exchange }}</span>
        </div>
        <div class="p-item">
          <span class="p-label">所属核心赛道</span>
          <span class="p-val font-semibold text-accent">{{ profile.sector }}</span>
        </div>
        <div class="p-item">
          <span class="p-label">上市年份/时间</span>
          <span class="p-val mono">{{ profile.ipoYear || '已上市' }}</span>
        </div>
        <div class="p-item">
          <span class="p-label">结算与报表币种</span>
          <span class="p-val mono">{{ profile.currency }}</span>
        </div>
      </div>

      <!-- 商业模式与业务概要 -->
      <div class="business-box">
        <div class="b-title">业务模式与核心竞争力概要 (Business Overview)</div>
        <div class="b-desc">{{ profile.businessModel }}</div>
      </div>

      <!-- 核心财务特征标签 -->
      <div class="traits-wrap" v-if="profile.financialTraits?.length">
        <span class="traits-title">关键基本面财务画像:</span>
        <div class="trait-tags">
          <span v-for="t in profile.financialTraits" :key="t" class="trait-tag">{{ t }}</span>
        </div>
      </div>
    </div>

    <!-- 第二部分：专业估值方法适配诊断与建议 -->
    <div class="card advisory-card" style="margin-top:20px">
      <div class="card-header-clean">
        <div class="advisory-title-wrap">
          <div class="card-title">投行专业估值适配建议：当前标的应如何估值？</div>
          <div class="advisory-sub">
            公司分类诊断: <b class="accent">{{ profile.companyType }}</b>
          </div>
        </div>
        <span class="card-hint">基于 Aswath Damodaran 估值理论与华尔街主流投行框架</span>
      </div>

      <div class="methodology-intro">
        💡 <b>专业投行常识</b>：没有任何单一估值模型能适用于所有公司。例如：
        <b>轻资产高现金流龙头（如茅台）</b>极度契合 Gordon 永续折现；
        <b>高成长出海消费（如泡泡玛特）</b>必须重点看 Exit 退出乘数与海外周转；
        <b>多元化巨头（如腾讯、美团）</b>单看 P/E 会严重低估创新业务，首选 SOTP 分拆；
        <b>重资产制造（如宁德、比亚迪）</b>则需采用 EV/EBITDA 去除折旧扰动。
      </div>

      <!-- 5种方法推荐矩阵 -->
      <div class="advice-matrix">
        <!-- 首选强推模型 -->
        <div class="advice-row primary-row" v-if="profile.advice?.primary">
          <div class="advice-rank">
            <span class="rank-badge rank-primary">⭐⭐⭐⭐⭐ 首选推荐</span>
            <span class="weight-rec">建议权重: <b>{{ profile.advice.primary.weight }}</b></span>
          </div>
          <div class="advice-content">
            <div class="method-title-wrap">
              <span class="method-name">{{ profile.advice.primary.name }}</span>
              <button class="btn btn-xs btn-primary" @click="jumpToModel(profile.advice.primary.method)">
                立即前往此模型 ➔
              </button>
            </div>
            <div class="method-reason">{{ profile.advice.primary.reason }}</div>
          </div>
        </div>

        <!-- 重要参考模型 -->
        <div class="advice-row" v-if="profile.advice?.secondary">
          <div class="advice-rank">
            <span class="rank-badge rank-secondary">⭐⭐⭐⭐ 重要参考</span>
            <span class="weight-rec">建议权重: <b>{{ profile.advice.secondary.weight }}</b></span>
          </div>
          <div class="advice-content">
            <div class="method-title-wrap">
              <span class="method-name">{{ profile.advice.secondary.name }}</span>
              <button class="btn btn-xs" @click="jumpToModel(profile.advice.secondary.method)">
                前往查看 ➔
              </button>
            </div>
            <div class="method-reason">{{ profile.advice.secondary.reason }}</div>
          </div>
        </div>

        <!-- 辅助交叉检验 -->
        <div class="advice-row" v-if="profile.advice?.tertiary">
          <div class="advice-rank">
            <span class="rank-badge rank-tertiary">⭐⭐⭐ 辅助校验</span>
            <span class="weight-rec">建议权重: <b>{{ profile.advice.tertiary.weight }}</b></span>
          </div>
          <div class="advice-content">
            <div class="method-title-wrap">
              <span class="method-name">{{ profile.advice.tertiary.name }}</span>
              <button class="btn btn-xs" @click="jumpToModel(profile.advice.tertiary.method)">
                前往查看 ➔
              </button>
            </div>
            <div class="method-reason">{{ profile.advice.tertiary.reason }}</div>
          </div>
        </div>

        <!-- 谨慎使用/警示 -->
        <div class="advice-row caution-row" v-if="profile.advice?.caution">
          <div class="advice-rank">
            <span class="rank-badge rank-caution">⚠️ 谨慎使用/规避提示</span>
          </div>
          <div class="advice-content">
            <div class="method-name text-warn">{{ profile.advice.caution.name }}</div>
            <div class="method-reason">{{ profile.advice.caution.note }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { state } from '../store.js'
import { getCompanyProfile } from '../utils/stockDictionary.js'
import { formatNumber } from '../utils/financials.js'

const emit = defineEmits(['navigate'])

const currentPrice = computed(() => state.analyzeResult?.standard_financials?.price || 0)
const shares = computed(() => state.analyzeResult?.standard_financials?.balance?.shares_diluted || 0)
const marketCap = computed(() => (currentPrice.value * shares.value))

const profile = computed(() => {
  return getCompanyProfile(
    state.ticker,
    state.market,
    state.analyzeResult?.standard_financials,
    state.analyzeResult
  )
})

function jumpToModel(methodKey) {
  emit('navigate', methodKey)
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

.verification-badge {
  background: rgba(16, 185, 129, 0.15);
  color: var(--good);
  border: 1px solid var(--good);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
}
.badge-market { padding: 4px 8px; background: var(--bg-2); border: 1px solid var(--border); border-radius: 6px; font-weight: 600; }
.badge-type { padding: 4px 8px; background: var(--accent-dim); color: var(--accent); border: 1px solid var(--accent); border-radius: 6px; font-weight: 600; }

/* 身份核验卡片 */
.verification-card {
  background: linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
  border: 1px solid var(--border-strong);
  padding: 22px;
}
.verify-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
.company-brand { display: flex; align-items: center; gap: 14px; }
.company-logo {
  width: 52px; height: 52px;
  background: var(--accent-dim);
  border: 2px solid var(--accent);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 900; color: var(--accent);
  box-shadow: 0 0 16px var(--accent-dim);
}
.company-titles { display: flex; flex-direction: column; gap: 3px; }
.company-main-name { font-size: 20px; font-weight: 800; color: var(--text-0); display: flex; align-items: center; gap: 8px; }
.ticker-pill { font-size: 12px; background: var(--bg-3); color: var(--accent); padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.curated-tag { font-size: 10px; background: rgba(74, 222, 128, 0.15); color: var(--good); border: 1px solid var(--good); padding: 1px 6px; border-radius: 10px; font-weight: 600; }
.company-full-name { font-size: 12px; color: var(--text-3); font-family: var(--font-mono); }

.company-quick-data { display: flex; gap: 20px; background: var(--bg-1); padding: 10px 16px; border-radius: 8px; border: 1px solid var(--border); }
.qd-item { display: flex; flex-direction: column; gap: 2px; }
.qd-label { font-size: 10px; color: var(--text-3); text-transform: uppercase; }
.qd-val { font-size: 15px; }

.verify-divider { height: 1px; background: var(--border); margin: 18px 0; }

.profile-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.p-item { display: flex; flex-direction: column; gap: 3px; }
.p-label { font-size: 11px; color: var(--text-3); }
.p-val { font-size: 13px; color: var(--text-0); }
.font-semibold { font-weight: 600; }
.text-accent { color: var(--accent); }

.business-box {
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 14px;
}
.b-title { font-size: 11px; font-weight: 700; color: var(--text-2); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }
.b-desc { font-size: 13px; color: var(--text-1); line-height: 1.6; }

.traits-wrap { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.traits-title { font-size: 11px; color: var(--text-3); font-weight: 600; }
.trait-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.trait-tag { font-size: 11px; padding: 2px 8px; background: var(--bg-3); border-radius: 4px; color: var(--text-1); }

/* 估值建议卡片 */
.advisory-card { padding: 22px; }
.card-header-clean { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
.advisory-title-wrap { display: flex; flex-direction: column; gap: 2px; }
.advisory-sub { font-size: 13px; color: var(--text-2); }
.card-hint { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.methodology-intro {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-1);
  line-height: 1.6;
  margin-bottom: 20px;
}

.advice-matrix { display: flex; flex-direction: column; gap: 12px; }
.advice-row {
  display: flex;
  gap: 16px;
  padding: 14px 16px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  align-items: flex-start;
  transition: all 0.2s;
}
.advice-row:hover { border-color: var(--border-strong); transform: translateX(2px); }

.primary-row {
  background: linear-gradient(90deg, var(--accent-dim) 0%, var(--bg-2) 100%);
  border-color: var(--accent);
  border-left: 4px solid var(--accent);
}

.caution-row {
  background: rgba(251, 191, 36, 0.05);
  border-left: 4px solid var(--warn);
}

.advice-rank { display: flex; flex-direction: column; gap: 4px; width: 140px; flex-shrink: 0; }
.rank-badge { font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 4px; display: inline-block; width: fit-content; }
.rank-primary { background: var(--accent); color: #ffffff; }
.rank-secondary { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.rank-tertiary { background: var(--bg-3); color: var(--text-2); }
.rank-caution { background: rgba(251, 191, 36, 0.15); color: var(--warn); }
.weight-rec { font-size: 11px; color: var(--text-3); }
.weight-rec b { color: var(--text-0); font-family: var(--font-mono); }

.advice-content { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.method-title-wrap { display: flex; justify-content: space-between; align-items: center; }
.method-name { font-size: 14px; font-weight: 700; color: var(--text-0); }
.method-reason { font-size: 12px; color: var(--text-2); line-height: 1.5; }
.text-warn { color: var(--warn); }

@media (max-width: 900px) {
  .profile-grid { grid-template-columns: 1fr 1fr; }
  .advice-row { flex-direction: column; gap: 8px; }
  .advice-rank { width: 100%; flex-direction: row; justify-content: space-between; }
}
</style>
