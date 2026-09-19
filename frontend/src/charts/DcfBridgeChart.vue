<template>
  <div ref="el" style="width:100%;height:320px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { state } from '../store.js'

const props = defineProps({
  pvUfcf: { type: Number, default: 0 },
  pvTerminal: { type: Number, default: 0 },
  cash: { type: Number, default: 0 },
  debt: { type: Number, default: 0 },
  equityValue: { type: Number, default: 0 }
})

const el = ref(null)
let chart = null

function getThemeColor(varName, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || fallback
}

function render() {
  if (!chart) return

  const textColor = getThemeColor('--text-1', '#cbd5e1')
  const textColorMuted = getThemeColor('--text-3', '#94a3b8')
  const borderColor = getThemeColor('--border', 'rgba(255,255,255,0.08)')
  const accentColor = getThemeColor('--accent', '#3b82f6')
  const goodColor = getThemeColor('--good', '#10b981')
  const dangerColor = getThemeColor('--danger', '#ef4444')

  const categories = ['预测期FCF现值', '终值现值', '企业价值(EV)', '+现金', '-有息负债', '股权价值(Equity)']
  const ev = (props.pvUfcf || 0) + (props.pvTerminal || 0)

  // Pie chart comparing PV of Forecast vs PV of Terminal Value
  const totalEv = Math.max(0.0001, props.pvUfcf + props.pvTerminal)
  const pctForecast = ((props.pvUfcf / totalEv) * 100).toFixed(1)
  const pctTerminal = ((props.pvTerminal / totalEv) * 100).toFixed(1)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = params[0]
        return `<b>${item.name}</b><br/>金额: <b>¥${Number(item.value).toLocaleString()} M</b>`
      }
    },
    grid: { left: '3%', right: '4%', top: '15%', bottom: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: textColor, fontSize: 11, interval: 0, rotate: 15 },
      axisLine: { lineStyle: { color: borderColor } }
    },
    yAxis: {
      type: 'value',
      name: '金额 (百万)',
      nameTextStyle: { color: textColorMuted, fontSize: 11 },
      axisLabel: { color: textColorMuted, fontSize: 11 },
      splitLine: { lineStyle: { color: borderColor, type: 'dashed' } }
    },
    series: [
      {
        name: '估值桥',
        type: 'bar',
        barMaxWidth: 36,
        data: [
          { value: props.pvUfcf, itemStyle: { color: accentColor, borderRadius: [4, 4, 0, 0] } },
          { value: props.pvTerminal, itemStyle: { color: '#8b5cf6', borderRadius: [4, 4, 0, 0] } },
          { value: ev, itemStyle: { color: '#0ea5e9', borderRadius: [4, 4, 0, 0] } },
          { value: props.cash, itemStyle: { color: goodColor, borderRadius: [4, 4, 0, 0] } },
          { value: props.debt, itemStyle: { color: dangerColor, borderRadius: [4, 4, 0, 0] } },
          { value: props.equityValue, itemStyle: { color: '#eab308', borderRadius: [4, 4, 0, 0] } }
        ],
        label: {
          show: true,
          position: 'top',
          color: textColor,
          fontSize: 11,
          formatter: (p) => Math.round(p.value).toLocaleString()
        }
      }
    ]
  }

  chart.setOption(option, true)
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
watch([() => props.pvUfcf, () => props.pvTerminal, () => props.cash, () => props.debt, () => props.equityValue], render)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>
