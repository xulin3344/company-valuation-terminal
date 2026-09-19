<template>
  <div ref="el" style="width:100%;height:400px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { state } from '../store.js'

const props = defineProps({ data: Object })
const el = ref(null)
let chart = null

function getThemeColor(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || '#000'
}

function render() {
  if (!chart || !props.data) return
  const { models, currentPrice, fairValue } = props.data
  const cats = models.map(m => m.name)
  const ranges = models.map(m => [m.low, m.high])
  const avgs = models.map(m => m.price)

  const allVals = [...ranges.flat(), currentPrice, fairValue].filter(v => v != null)
  const min = Math.min(...allVals) * 0.95
  const max = Math.max(...allVals) * 1.05

  const textColor = getThemeColor('--text-1')
  const textColorDim = getThemeColor('--text-2')
  const splitColor = getThemeColor('--border')
  const accentColor = getThemeColor('--accent')
  const accentDimColor = getThemeColor('--accent-dim')
  const dangerColor = getThemeColor('--danger')

  const markLines = []
  if (currentPrice) markLines.push({ yAxis: currentPrice, name: '现价', lineStyle: { color: dangerColor, type: 'dashed' }, label: { formatter: '现价 ¥{c}', color: dangerColor } })
  if (fairValue) markLines.push({ yAxis: fairValue, name: '中枢', lineStyle: { color: accentColor, type: 'dashed' }, label: { formatter: '中枢 ¥{c}', color: accentColor } })

  chart.setOption({
    tooltip: { trigger: 'item', formatter: p => {
      if (p.componentSubType === 'custom') return `${p.name}<br/>区间 ¥${p.value[1].toFixed(1)} ~ ¥${p.value[2].toFixed(1)}<br/>中枢 ¥${p.value[3].toFixed(1)}`
      return `${p.name}: ¥${p.value.toFixed(1)}`
    }},
    grid: { left: 120, right: 40, top: 20, bottom: 30 },
    xAxis: { type: 'value', min, max, axisLabel: { color: textColorDim, fontSize: 11, formatter: v => '¥' + v.toFixed(0) }, splitLine: { lineStyle: { color: splitColor } } },
    yAxis: { type: 'category', data: cats, axisLabel: { color: textColor, fontSize: 11 }, splitLine: { show: false } },
    series: [{
      type: 'custom',
      renderItem: (params, api) => {
        const cat = api.value(0)
        const low = api.coord([api.value(1), cat])
        const high = api.coord([api.value(2), cat])
        const mid = api.coord([api.value(3), cat])
        return {
          type: 'group',
          children: [
            { type: 'rect', shape: { x: low[0], y: low[1] - 8, width: high[0] - low[0], height: 16 }, style: { fill: accentDimColor, stroke: accentColor, lineWidth: 1 } },
            { type: 'circle', shape: { cx: mid[0], cy: low[1], r: 4 }, style: { fill: accentColor } }
          ]
        }
      },
      data: models.map((m, i) => [i, m.low, m.high, m.price]),
      markLine: { symbol: 'none', data: markLines.map(ml => ({ yAxis: ml.yAxis, lineStyle: ml.lineStyle, label: { formatter: ml.label.formatter, color: ml.label.color, position: 'end', fontSize: 11 } })) }
    }]
  })
}

onMounted(() => {
  chart = echarts.init(el.value)
  render()
  window.addEventListener('resize', () => chart?.resize())
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
  window.removeEventListener('resize', () => chart?.resize())
  chart?.dispose()
})
</script>