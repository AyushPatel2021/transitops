<template>
  <div class="app-chart-wrapper">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  Chart,
  ArcElement,
  BarElement,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  DoughnutController,
  BarController,
  LineController,
  PieController,
} from 'chart.js'
import { useChartTheme } from '../../composables/useChartTheme'

Chart.register(
  ArcElement, BarElement, LineElement, PointElement,
  CategoryScale, LinearScale,
  Tooltip, Legend,
  DoughnutController, BarController, LineController, PieController,
)

const props = defineProps<{
  /**
   * Chart definition from the backend:
   * {
   *   type: 'bar' | 'line' | 'donut' | 'pie' | 'stacked_bar',
   *   title: string,
   *   labels: string[],
   *   data?: number[],          // single-dataset charts
   *   datasets?: {              // stacked_bar
   *     label: string, data: number[], color: string
   *   }[],
   *   colors: string[],         // semantic: 'primary', 'success', etc.
   * }
   */
  chartDef: Record<string, any>
  /** Increment this prop to force a full re-render (e.g. on theme toggle) */
  themeVersion?: number
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null
const { getColor, getColors, chartDefaults } = useChartTheme()

function resolveColors(keys: string[], count: number): string[] {
  if (keys.length >= count) return getColors(keys.slice(0, count))
  // cycle through provided keys if not enough
  return Array.from({ length: count }, (_, i) => getColor(keys[i % keys.length]))
}

function buildConfig(def: Record<string, any>): any {
  const defaults = chartDefaults()
  const colorKeys: string[] = def.colors ?? ['primary']
  const type = def.type === 'donut' ? 'doughnut' : def.type === 'stacked_bar' ? 'bar' : def.type

  let datasets: any[]

  if (def.type === 'stacked_bar' && Array.isArray(def.datasets)) {
    datasets = def.datasets.map((ds: any) => ({
      label: ds.label,
      data: ds.data,
      backgroundColor: getColor(ds.color ?? 'primary'),
      borderWidth: 0,
    }))
  } else if (type === 'doughnut' || type === 'pie') {
    const colors = resolveColors(colorKeys, (def.data ?? []).length)
    datasets = [{
      data: def.data ?? [],
      backgroundColor: colors,
      borderColor: getColor('bg'),
      borderWidth: 2,
    }]
  } else {
    // bar / line — single dataset
    const color = getColor(colorKeys[0] ?? 'primary')

    // Special case: ROI bar — bars above zero = success, below = danger
    if (def.colors[0] === 'dynamic_roi') {
      const successColor = getColor('success')
      const dangerColor  = getColor('danger')
      datasets = [{
        data: def.data ?? [],
        backgroundColor: (def.data ?? []).map((v: number) => v >= 0 ? successColor : dangerColor),
        borderWidth: 0,
      }]
    } else if (type === 'line') {
      datasets = [{
        data: def.data ?? [],
        borderColor: color,
        backgroundColor: color + '33',
        tension: 0.3,
        pointRadius: 3,
        fill: true,
      }]
    } else {
      datasets = [{
        data: def.data ?? [],
        backgroundColor: color,
        borderWidth: 0,
      }]
    }
  }

  const scales: any = {}
  if (type !== 'doughnut' && type !== 'pie') {
    scales.x = { ticks: { color: getColor('textSec') }, grid: { color: getColor('border') } }
    scales.y = { ticks: { color: getColor('textSec') }, grid: { color: getColor('border') }, beginAtZero: true }
    if (def.type === 'stacked_bar') {
      scales.x.stacked = true
      scales.y.stacked = true
    }
  }

  return {
    type,
    data: { labels: def.labels ?? [], datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,   // fill the parent wrapper, not a fixed ratio
      animation: { duration: 250 },
      plugins: {
        ...defaults.plugins,
        legend: {
          display: type === 'doughnut' || type === 'pie' || def.type === 'stacked_bar',
          labels: { color: getColor('text'), font: { family: 'inherit', size: 11 } },
        },
      },
      scales,
    },
  }
}

function renderChart() {
  if (!canvasRef.value) return
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
  const config = buildConfig(props.chartDef)
  chartInstance = new Chart(canvasRef.value, config)
}

onMounted(() => nextTick(renderChart))

watch(() => props.chartDef, () => nextTick(renderChart), { deep: true })
watch(() => props.themeVersion, () => nextTick(renderChart))

onUnmounted(() => {
  chartInstance?.destroy()
  chartInstance = null
})
</script>

<style scoped>
.app-chart-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.app-chart-wrapper canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
</style>
