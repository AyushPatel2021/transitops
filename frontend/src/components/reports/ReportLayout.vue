<template>
  <div class="report-layout">
    <!-- Header bar -->
    <div class="report-header">
      <div class="report-title-section">
        <component :is="getIcon(icon)" class="report-icon" />
        <h1 class="report-title">{{ title }}</h1>
      </div>

      <div class="report-controls">
        <!-- Period filter -->
        <div class="period-filter">
          <button
            v-for="p in periods"
            :key="p.value"
            :class="['period-btn', { active: modelPeriod === p.value }]"
            @click="$emit('update:modelPeriod', p.value)"
          >{{ p.label }}</button>

          <template v-if="modelPeriod === 'custom'">
            <input type="date" :value="modelDateFrom" @change="(e: any) => $emit('update:modelDateFrom', e.target.value)" class="date-input" />
            <span class="date-sep">→</span>
            <input type="date" :value="modelDateTo" @change="(e: any) => $emit('update:modelDateTo', e.target.value)" class="date-input" />
          </template>
        </div>

        <!-- Extra filters slot -->
        <slot name="filters" />

        <!-- CSV export -->
        <button class="export-btn" @click="$emit('export')" :disabled="loading">
          <Download class="icon-xs" />
          Export CSV
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="report-loading">
      <div class="skeleton-bar" v-for="i in 6" :key="i"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="report-error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="$emit('reload')">Retry</button>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- KPI stat cards -->
      <div class="report-kpi-row" v-if="kpis && kpis.length">
        <div v-for="kpi in kpis" :key="kpi.key" class="report-kpi-card">
          <component :is="getIcon(kpi.icon)" class="report-kpi-icon" />
          <div class="report-kpi-body">
            <span class="report-kpi-value">
              <span v-if="kpi.prefix" class="report-kpi-affix">{{ kpi.prefix }}</span>
              {{ kpi.value }}
              <span v-if="kpi.suffix" class="report-kpi-affix">{{ kpi.suffix }}</span>
            </span>
            <span class="report-kpi-label">{{ kpi.label }}</span>
          </div>
        </div>
      </div>

      <!-- Charts row -->
      <div class="report-charts" :class="chartGridClass" v-if="charts && charts.length">
        <div
          v-for="chart in charts"
          :key="chart.title"
          class="report-chart-card"
        >
          <h3 class="chart-title">{{ chart.title }}</h3>
          <div class="chart-canvas-wrap">
            <AppChart :chartDef="chart" :themeVersion="themeVersion" />
          </div>
        </div>
      </div>

      <!-- Single chart shorthand -->
      <div class="report-charts charts-single" v-else-if="chart">
        <div class="report-chart-card">
          <h3 class="chart-title">{{ chart.title }}</h3>
          <div class="chart-canvas-wrap">
            <AppChart :chartDef="chart" :themeVersion="themeVersion" />
          </div>
        </div>
      </div>

      <!-- Table -->
      <div class="report-table-wrap">
        <table class="report-table">
          <thead>
            <tr>
              <th v-for="col in columns" :key="col">{{ formatHeader(col) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in rows" :key="i">
              <td v-for="col in columns" :key="col">{{ formatCell(col, row[col]) }}</td>
            </tr>
            <tr v-if="!rows.length">
              <td :colspan="columns.length" class="empty-cell">No data for the selected period / filters.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as Icons from 'lucide-vue-next'
import { Download } from 'lucide-vue-next'
import AppChart from '../charts/AppChart.vue'

const props = defineProps<{
  title: string
  icon: string
  loading: boolean
  error: string
  rows: any[]
  columns: string[]
  chart?: any          // single chart
  charts?: any[]       // multiple charts
  kpis?: any[]         // KPI stat cards
  modelPeriod: string
  modelDateFrom?: string
  modelDateTo?: string
  themeVersion?: number
}>()

defineEmits(['update:modelPeriod', 'update:modelDateFrom', 'update:modelDateTo', 'export', 'reload'])

const periods = [
  { value: 'this_month',   label: 'This Month'   },
  { value: 'this_quarter', label: 'This Quarter' },
  { value: 'all_time',     label: 'All Time'     },
  { value: 'custom',       label: 'Custom'       },
]

const chartGridClass = computed(() => {
  const count = props.charts?.length ?? 0
  if (count === 1) return 'charts-single'
  if (count === 2) return 'charts-two'
  return 'charts-multi'
})

function getIcon(name: string) {
  return (Icons as any)[name] || Icons.BarChart3
}

const CURRENCY_COLS = ['fuel_cost', 'maintenance_cost', 'total_cost', 'revenue', 'acquisition_cost', 'amount']
const PERCENT_COLS  = ['roi_pct', 'utilization_pct']

function formatHeader(col: string): string {
  if (col === 'utilization_pct') return 'Utilization % (as of now)'
  return col.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatCell(col: string, val: any): string {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'string' && !CURRENCY_COLS.includes(col) && !PERCENT_COLS.includes(col)) return val
  if (CURRENCY_COLS.includes(col) && typeof val === 'number') {
    return '₹ ' + val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
  if (PERCENT_COLS.includes(col) && typeof val === 'number') {
    return val.toFixed(2) + '%'
  }
  return String(val)
}
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as v;

.report-layout {
  padding: 1.25rem 1.5rem 2rem;
  width: 100%;
  box-sizing: border-box;
}

// ── Header ──────────────────────────────────────────────────────────────────
.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.report-title-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.report-icon { width: 22px; height: 22px; color: v.$primary-color; }
.report-title { font-size: 1.25rem; font-weight: 700; color: v.$text-primary; margin: 0; }

.report-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.period-filter {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  flex-wrap: wrap;
}
.period-btn {
  padding: 0.28rem 0.6rem;
  border-radius: 6px;
  border: 1px solid v.$border-color;
  background: v.$bg-secondary;
  color: v.$text-secondary;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.15s;
  &:hover  { background: v.$bg-tertiary; color: v.$text-primary; }
  &.active { background: v.$primary-color; color: #fff; border-color: v.$primary-color; }
}
.date-input {
  padding: 0.25rem 0.45rem;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  background: v.$bg-secondary;
  color: v.$text-primary;
  font-size: 0.78rem;
}
.date-sep { color: v.$text-tertiary; font-size: 0.8rem; }

.export-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.78rem;
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
  border: 1px solid v.$border-color;
  background: v.$bg-secondary;
  color: v.$text-secondary;
  cursor: pointer;
  transition: all 0.15s;
  &:hover:not(:disabled) { background: v.$bg-tertiary; color: v.$text-primary; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
.icon-xs { width: 13px; height: 13px; }

// ── Loading ─────────────────────────────────────────────────────────────────
.report-loading { display: flex; flex-direction: column; gap: 0.5rem; padding: 1rem 0; }
.skeleton-bar {
  height: 30px;
  background: v.$bg-tertiary;
  border-radius: 6px;
  animation: shimmer 1.2s infinite;
}
@keyframes shimmer {
  0%, 100% { opacity: 1 } 50% { opacity: 0.5 }
}
.report-error { text-align: center; padding: 3rem; color: v.$danger-color; }

// ── KPI Stat Cards ──────────────────────────────────────────────────────────
.report-kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.report-kpi-card {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.75rem 1rem;
  background: v.$bg-secondary;
  border: 1px solid v.$border-color;
  border-radius: 10px;
  box-shadow: v.$shadow-sm;
}
.report-kpi-icon {
  color: v.$primary-color;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}
.report-kpi-body {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
  min-width: 0;
}
.report-kpi-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: v.$text-primary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.report-kpi-affix {
  font-size: 0.75rem;
  font-weight: 400;
  color: v.$text-secondary;
}
.report-kpi-label {
  font-size: 0.68rem;
  color: v.$text-secondary;
  margin-top: 0.1rem;
}

// ── Charts ──────────────────────────────────────────────────────────────────
.report-charts {
  display: grid;
  gap: 1rem;
  margin-bottom: 1.25rem;

  &.charts-single {
    grid-template-columns: minmax(0, 1fr);
  }
  &.charts-two {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  &.charts-multi {
    grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  }
}
.report-chart-card {
  background: v.$bg-secondary;
  border: 1px solid v.$border-color;
  border-radius: 10px;
  padding: 1rem 1.125rem;
  box-shadow: v.$shadow-sm;
  min-width: 0;
  overflow: hidden;
}
.chart-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: v.$text-primary;
  margin: 0 0 0.75rem;
}
// Fixed-height canvas container
.chart-canvas-wrap {
  position: relative;
  width: 100%;
  height: 320px;
  min-height: 0;
  canvas { width: 100% !important; height: 100% !important; }
}

// ── Table ───────────────────────────────────────────────────────────────────
.report-table-wrap {
  overflow-x: auto;
  background: v.$bg-secondary;
  border: 1px solid v.$border-color;
  border-radius: 10px;
  box-shadow: v.$shadow-sm;
}
.report-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;

  th, td {
    padding: 0.55rem 0.875rem;
    text-align: left;
    border-bottom: 1px solid v.$border-color;
    white-space: nowrap;
  }
  th {
    background: v.$bg-tertiary;
    color: v.$text-secondary;
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    position: sticky;
    top: 0;
    z-index: 1;
  }
  td { color: v.$text-primary; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: v.$bg-tertiary; }
  .empty-cell { text-align: center; color: v.$text-tertiary; padding: 2rem; }
}

// ── Mobile ──────────────────────────────────────────────────────────────────
@media (max-width: 768px) {
  .report-layout { padding: 1rem; }
  .report-header { flex-direction: column; align-items: flex-start; }
  .report-charts {
    &.charts-two { grid-template-columns: 1fr; }
    &.charts-multi { grid-template-columns: 1fr; }
  }
  .report-kpi-row { grid-template-columns: repeat(2, 1fr); }
  .chart-canvas-wrap { height: 220px; }
}
</style>
