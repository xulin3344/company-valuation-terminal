<template>
  <div ref="el" style="width:100%;height:320px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { state } from '../store.js'

const props = defineProps({ data: Array })
const el = ref(null)
let chart = null

function getThemeColor(varName, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || fallback
}

function render() {
  if (!chart || !props.data) return
  const cats = props.data.map(d => d.name)
  const boxData = props.data.map(d => [d.minimum, d.p25, d.median, d.p75, d.maximum])

  const textColor = getThemeColor('--text-1', '#cbd5e1')
  const textColorMuted = getThemeColor('--text-3', '#94a3b8')
  const borderColor = getThemeColor('--border', 'rgba(255,255,255,0.08)')
  const accentColor = getThemeColor('--accent', '#3b82f6')
  const accentDim = getThemeColor('--accent-dim', 'rgba(59,130,246,0.15)')

  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (param) => {
        return `<div style="font-size:12px;padding:4px">
          <div style="font-weight:bold;margin-bottom:4px">${param.name} 估值倍数统计</div>
          <div>最大值 (Max): <b>${param.data[5]?.toFixed(2)}</b></div>
          <div>上四分位 (P75): <b>${param.data[4]?.toFixed(2)}</b></div>
          <div style="color:var(--accent)">中位数 (Median): <b>${param.data[3]?.toFixed(2)}</b></div>
          <div>下四分位 (P25): <b>${param.data[2]?.toFixed(2)}</b></div>
          <div>最小值 (Min): <b>${param.data[1]?.toFixed(2)}</b></div>
        </div>`
      }
    },
    grid: { left: 50, right: 30, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: cats,
      axisLabel: { color: textColor, fontSize: 12, fontWeight: 500 },
      axisLine: { lineStyle: { color: borderColor } }
    },
    yAxis: {
      type: 'value',
      name: '估值倍数',
      nameTextStyle: { color: textColorMuted, fontSize: 11 },
      axisLabel: { color: textColorMuted, fontSize: 11 },
      splitLine: { lineStyle: { color: borderColor, type: 'dashed' } }
    },
    series: [{
      name: '倍数分布',
      type: 'boxplot',
      data: boxData,
      itemStyle: {
        color: accentDim,
        borderColor: accentColor,
        borderWidth: 1.5
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