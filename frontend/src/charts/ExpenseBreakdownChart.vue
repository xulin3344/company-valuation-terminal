<template>
  <div ref="el" style="width:100%;height:320px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { state } from '../store.js'

const props = defineProps({
  cogs: { type: Number, default: 0 },
  selling: { type: Number, default: 0 },
  admin: { type: Number, default: 0 },
  rd: { type: Number, default: 0 },
  ebit: { type: Number, default: 0 }
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
  const bg1 = getThemeColor('--bg-1', '#111113')

  const data = [
    { value: Math.max(0, props.cogs || 0), name: '营业成本 (COGS)', itemStyle: { color: '#f87171' } },
    { value: Math.max(0, props.selling || 0), name: '销售费用 (Selling)', itemStyle: { color: '#fb923c' } },
    { value: Math.max(0, props.admin || 0), name: '管理费用 (Admin)', itemStyle: { color: '#facc15' } },
    { value: Math.max(0, props.rd || 0), name: '研发费用 (R&D)', itemStyle: { color: '#a78bfa' } },
    { value: Math.max(0, props.ebit || 0), name: '营业利润 (EBIT)', itemStyle: { color: '#4ade80' } },
  ].filter(d => d.value > 0)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: <br/><b>{c} M</b> ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '2%',
      top: 'center',
      textStyle: { color: textColor, fontSize: 11 }
    },
    series: [
      {
        name: '收入拆解构成',
        type: 'pie',
        radius: ['45%', '72%'],
        center: ['38%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: bg1,
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: 'bold',
            color: textColor,
            formatter: '{b}\n{d}%'
          }
        },
        labelLine: { show: false },
        data: data.length > 0 ? data : [{ value: 1, name: '暂无结构数据', itemStyle: { color: textColorMuted } }]
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
watch([() => props.cogs, () => props.selling, () => props.admin, () => props.rd, () => props.ebit], render)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>
