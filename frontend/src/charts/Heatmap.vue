<template>
  <div ref="el" style="width:100%;height:380px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { state } from '../store.js'

const props = defineProps({ data: Object })
const el = ref(null)
let chart = null

function getThemeColor(varName, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || fallback
}

function render() {
  if (!chart || !props.data) return
  const { xLabels, yLabels, matrix } = props.data
  const data = []
  let min = Infinity, max = -Infinity
  for (let i = 0; i < matrix.length; i++) {
    for (let j = 0; j < matrix[i].length; j++) {
      const val = matrix[i][j]
      data.push([j, i, val])
      if (val < min) min = val
      if (val > max) max = val
    }
  }

  const textColor = getThemeColor('--text-1', '#cbd5e1')
  const textColorMuted = getThemeColor('--text-3', '#94a3b8')
  const borderColor = getThemeColor('--border', 'rgba(255,255,255,0.08)')
  const currentPrice = state.analyzeResult?.standard_financials?.price || 0

  chart.setOption({
    tooltip: {
      formatter: p => {
        const priceVal = p.value[2]
        const diffPct = currentPrice > 0 ? (((priceVal - currentPrice) / currentPrice) * 100).toFixed(1) : null
        return `<div style="font-size:12px;padding:4px">
          <div>永续增长率 g: <b>${xLabels[p.value[0]]}</b></div>
          <div>折现率 WACC: <b>${yLabels[p.value[1]]}</b></div>
          <div style="margin-top:4px;font-size:14px;font-weight:bold;color:var(--accent)">推导每股: ¥${priceVal.toFixed(2)}</div>
          ${diffPct ? `<div style="color:${diffPct >= 0 ? 'var(--good)' : 'var(--danger)'}">较现价: ${diffPct >= 0 ? '+' : ''}${diffPct}%</div>` : ''}
        </div>`
      }
    },
    grid: { left: 70, right: 30, top: 30, bottom: 50 },
    xAxis: {
      type: 'category',
      name: '永续增长率 g',
      nameLocation: 'middle',
      nameGap: 28,
      nameTextStyle: { color: textColorMuted, fontSize: 11 },
      data: xLabels,
      axisLabel: { color: textColor, fontSize: 11 },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'category',
      name: '折现率 WACC',
      nameTextStyle: { color: textColorMuted, fontSize: 11 },
      data: yLabels,
      axisLabel: { color: textColor, fontSize: 11 },
      splitLine: { show: false }
    },
    visualMap: {
      min,
      max,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { color: textColorMuted, fontSize: 11 },
      inRange: { color: ['#ef4444', '#f59e0b', '#10b981', '#06b6d4'] }
    },
    series: [{
      type: 'heatmap',
      data,
      label: {
        show: true,
        formatter: p => `¥${p.value[2].toFixed(1)}`,
        color: '#ffffff',
        fontSize: 11,
        fontWeight: 600,
        textShadowColor: 'rgba(0,0,0,0.5)',
        textShadowBlur: 2
      },
      itemStyle: {
        borderColor: borderColor,
        borderWidth: 1
      }
    }]
  })
}

function handleResize() { chart?.resize() }

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
watch(() => props.data, render, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>