<template>
  <div ref="el" style="width:100%;height:300px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { state } from '../store.js'

const props = defineProps({
  contributions: { type: Array, default: () => [] }
})

const el = ref(null)
let chart = null

function getThemeColor(varName, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || fallback
}

function render() {
  if (!chart) return

  const textColor = getThemeColor('--text-1', '#cbd5e1')
  const bg1 = getThemeColor('--bg-1', '#111113')

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']
  const data = props.contributions.map((c, i) => ({
    value: c.ev,
    name: c.name,
    itemStyle: { color: colors[i % colors.length] }
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: <b>¥{c} M</b> ({d}%)'
    },
    legend: {
      bottom: '5%',
      left: 'center',
      textStyle: { color: textColor, fontSize: 11 }
    },
    series: [
      {
        name: '业务分部 EV 贡献',
        type: 'pie',
        radius: ['42%', '70%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: bg1,
          borderWidth: 2
        },
        label: {
          show: true,
          color: textColor,
          formatter: '{b}: {d}%'
        },
        data: data.length > 0 ? data : [{ value: 1, name: '暂无分部', itemStyle: { color: '#64748b' } }]
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
watch(() => props.contributions, render, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>
