import { reactive, ref, watch } from 'vue'
import { analyze as apiAnalyze, recalculate } from './api.js'

export const state = reactive({
  ticker: '',
  companyName: '',
  market: 'HK',
  loading: false,
  error: null,
  analyzeResult: null,
  dataVerification: null,
  assumptions: null,
  result: null,
  recalcTime: 0,
  updateTime: 0,
  theme: localStorage.getItem('valuation-theme') || 'dark',
  accent: localStorage.getItem('valuation-accent') || 'teal',
})

// Watch theme changes to apply to DOM
watch(() => state.theme, (val) => {
  document.documentElement.setAttribute('data-theme', val)
  localStorage.setItem('valuation-theme', val)
}, { immediate: true })

watch(() => state.accent, (val) => {
  document.documentElement.setAttribute('data-accent', val)
  localStorage.setItem('valuation-accent', val)
}, { immediate: true })

export async function runAnalyze(ticker, market) {
  state.loading = true
  state.error = null
  try {
    console.log('[runAnalyze] requesting', ticker, market)
    const data = await apiAnalyze(ticker, market)
    console.log('[runAnalyze] got', data.ticker, 'rev=', data.standard_financials?.income?.revenue?.slice(-1))
    state.ticker = data.ticker
    state.companyName = data.company_name || data.ticker
    state.market = data.market
    state.analyzeResult = data
    state.dataVerification = data.data_verification
    state.assumptions = data.assumptions
    state.result = data.result
    state.updateTime = Date.now()
  } catch (e) {


    state.error = e.response?.data?.detail || e.message
    console.error('[runAnalyze] error', e)
  } finally {
    state.loading = false
  }
}

let recalcTimer = null
export function scheduleRecalculate() {
  if (recalcTimer) clearTimeout(recalcTimer)
  recalcTimer = setTimeout(doRecalculate, 300)
}

async function doRecalculate() {
  if (!state.assumptions) return
  const t0 = performance.now()
  try {
    const res = await recalculate(state.assumptions)
    state.result = res
    state.recalcTime = performance.now() - t0
  } catch (e) {
    state.error = e.response?.data?.detail || e.message
  }
}