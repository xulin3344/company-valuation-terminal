<template>
  <div ref="el" style="width:100%;height:320px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { state } from '../store.js'

const props = defineProps({
  periods: { type: Array, default: () => [] },
  revenue: { type: Array, default: () => [] },
  netIncome: { type: Array, default: () => [] },
  grossProfit: { type: Array, default: () => [] }
})

const el = ref(null)
let chart = null

function getThemeColor(varName, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || fallback
}

function render() {
  if (!chart || !props.periods || props.periods.length === 0) return

  const textColor = getThemeColor('--text-1', '#cbd5e1')
  const textColorMuted = getThemeColor('--text-3', '#94a3b8')
  const borderColor = getThemeColor('--border', 'rgba(255,255,255,0.08)')
  const accentColor = getThemeColor('--accent', '#3b82f6')
  const goodColor = getThemeColor('--good', '#10b981')
  const warnColor = getThemeColor('--warn', '#f59e0b')

  // Calculate margins
  const netMargins = props.periods.map((_, i) => {
    const rev = props.revenue?.[i]
    const ni = props.netIncome?.[i]
    if (rev && ni != null) return ((ni / rev) * 100).toFixed(1)
    return null
  })

  const grossMargins = props.periods.map((_, i) => {
    const rev = props.revenue?.[i]
    const gp = props.grossProfit?.[i]
    if (rev && gp != null) return ((gp / rev) * 100).toFixed(1)
    return null
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', crossStyle: { color: textColorMuted } },
      formatter: (params) => {
        let title = `<div style="font-weight:600;margin-bottom:6px;border-bottom:1px solid ${borderColor};padding-bottom:4px">${params[0]?.name || ''} 财报数据</div>`
        let lines = params.map(p => {
          let valStr = p.seriesType === 'line' ? `${p.value}%` : `${Number(p.value).toLocaleString()} M`
          return `<div style="display:flex;justify-content:space-between;gap:16px;font-size:12px;margin:2px 0;">
            <span style="display:flex;align-items:center;gap:6px">${p.marker} <span>${p.seriesName}</span></span>
            <span style="font-family:monospace;font-weight:600">${valStr}</span>
          </div>`
        }).join('')
        return `<div style="padding:4px 6px">${title}${lines}</div>`
      }
    },
    legend: {
      data: ['营业收入', '净利润', '毛利率', '净利率'],
      textStyle: { color: textColor, fontSize: 11 },
      top: 0
    },
    grid: { left: '3%', right: '4%', top: '16%', bottom: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: props.periods,
      axisLabel: { color: textColor, fontSize: 11 },
      axisLine: { lineStyle: { color: borderColor } }
    },
    yAxis: [
      {
        type: 'value',
        name: '金额 (M)',
        nameTextStyle: { color: textColorMuted, fontSize: 11 },
        axisLabel: { color: textColorMuted, fontSize: 11 },
        splitLine: { lineStyle: { color: borderColor, type: 'dashed' } }
      },
      {
        type: 'value',
        name: '利润率 (%)',
        nameTextStyle: { color: textColorMuted, fontSize: 11 },
        axisLabel: { color: textColorMuted, formatter: '{value}%', fontSize: 11 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '营业收入',
        type: 'bar',
        yAxisIndex: 0,
        data: props.revenue,
        itemStyle: { color: accentColor, borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 32
      },
      {
        name: '净利润',
        type: 'bar',
        yAxisIndex: 0,
        data: props.netIncome,
        itemStyle: { color: goodColor, borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 32
      },
      {
        name: '毛利率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: grossMargins,
        lineStyle: { width: 2, color: warnColor },
        itemStyle: { color: warnColor },
        symbolSize: 6
      },
      {
        name: '净利率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: netMargins,
        lineStyle: { width: 2, color: '#38bdf8' },
        itemStyle: { color: '#38bdf8' },
        symbolSize: 6
      }
    ]
  }

  chart.setOption(option, true)
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  chart = echarts.init(el.value)
  render()
  window.addEventListener('resize', handleResize)
})

watch(() => state.theme, () => {
  if (chart) {
    chart.dispose()
    chart = echarts.init(el.value)
    render()
  }
})
watch(() => state.accent, render)
watch([() => props.periods, () => props.revenue, () => props.netIncome], render, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>
