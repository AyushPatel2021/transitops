<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dash-header">
      <h1 class="dash-title">Dashboard</h1>

      <!-- Date range filter -->
      <div class="period-filter">
        <button
          v-for="p in periods"
          :key="p.value"
          :class="['period-btn', { active: period === p.value }]"
          @click="setPeriod(p.value)"
        >{{ p.label }}</button>

        <!-- Custom range inputs -->
        <template v-if="period === 'custom'">
          <input type="date" v-model="customFrom" class="date-input" @change="loadDashboard" />
          <span class="date-sep">→</span>
          <input type="date" v-model="customTo"   class="date-input" @change="loadDashboard" />
        </template>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="dash-loading">
      <div class="skeleton-row">
        <div class="skeleton-kpi" v-for="i in 4" :key="i"></div>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="dash-error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadDashboard">Retry</button>
    </div>

    <template v-else>
      <!-- KPI Cards -->
      <div class="kpi-grid" v-if="kpis.length">
        <div v-for="kpi in kpis" :key="kpi.key" class="kpi-card">
          <div class="kpi-icon">
            <component :is="getIcon(kpi.icon)" class="icon-lg" />
          </div>
          <div class="kpi-body">
            <span class="kpi-value">
              <span v-if="kpi.prefix" class="kpi-prefix">{{ kpi.prefix }}</span>
              {{ kpi.is_text ? kpi.value : formatKpiValue(kpi.value) }}
              <span v-if="kpi.suffix" class="kpi-suffix">{{ kpi.suffix }}</span>
            </span>
            <span class="kpi-label">{{ kpi.label }}</span>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-grid" v-if="charts.length">
        <template v-for="chart in charts" :key="chart.title">
          <!-- Expiring license table widget — always full row -->
          <div v-if="chart.type === 'table'" class="chart-card span-full">
            <h3 class="chart-title">{{ chart.title }}</h3>
            <div class="compact-table-wrap">
              <table class="compact-table">
                <thead>
                  <tr>
                    <th v-for="col in chart.columns" :key="col">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in chart.rows" :key="i">
                    <td v-for="(cell, j) in row" :key="j">{{ cell }}</td>
                  </tr>
                  <tr v-if="!chart.rows?.length">
                    <td :colspan="chart.columns?.length" class="empty-cell">No records</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Regular chart -->
          <div v-else class="chart-card">
            <h3 class="chart-title">{{ chart.title }}</h3>
            <div class="chart-canvas-wrap">
              <AppChart :chartDef="chart" :themeVersion="themeVersion" />
            </div>
          </div>
        </template>
      </div>

      <div class="dashboard-lower">
        <section class="summary-panel">
          <div class="panel-heading">
            <h2>Fleet Snapshot</h2>
            <span>{{ activePeriodLabel }}</span>
          </div>
          <div class="snapshot-grid">
            <div class="snapshot-item">
              <span class="snapshot-label">Ready Fleet</span>
              <strong>{{ getKpiDisplay('available_vehicles') }}</strong>
            </div>
            <div class="snapshot-item">
              <span class="snapshot-label">Trips In Motion</span>
              <strong>{{ getKpiDisplay('active_trips') }}</strong>
            </div>
            <div class="snapshot-item">
              <span class="snapshot-label">Shop Load</span>
              <strong>{{ getKpiDisplay('vehicles_in_maintenance') }}</strong>
            </div>
            <div class="snapshot-item">
              <span class="snapshot-label">Utilization</span>
              <strong>{{ getKpiDisplay('fleet_utilization_pct') }}</strong>
            </div>
          </div>
        </section>

        <section class="quick-panel">
          <div class="panel-heading">
            <h2>Reports</h2>
          </div>
          <div class="quick-links">
            <RouterLink to="/reports/fuel-efficiency" class="quick-link">
              <Gauge class="quick-icon" />
              <span>Fuel Efficiency</span>
            </RouterLink>
            <RouterLink to="/reports/fleet-utilization" class="quick-link">
              <Activity class="quick-icon" />
              <span>Fleet Utilization</span>
            </RouterLink>
            <RouterLink to="/reports/operational-cost" class="quick-link">
              <TrendingUp class="quick-icon" />
              <span>Operational Cost</span>
            </RouterLink>
            <RouterLink to="/reports/roi" class="quick-link">
              <BadgeDollarSign class="quick-icon" />
              <span>ROI</span>
            </RouterLink>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import * as Icons from 'lucide-vue-next'
import { Activity, BadgeDollarSign, Gauge, TrendingUp } from 'lucide-vue-next'
import api from '../core/api'
import AppChart from '../components/charts/AppChart.vue'
import { useDashboardTheme } from '../composables/useDashboardTheme'

const { themeVersion } = useDashboardTheme()

// ── Period filter ───────────────────────────────────────────────────────────
const periods = [
  { value: 'this_month',   label: 'This Month'   },
  { value: 'this_quarter', label: 'This Quarter' },
  { value: 'all_time',     label: 'All Time'     },
  { value: 'custom',       label: 'Custom'       },
]
const period     = ref('this_month')
const customFrom = ref('')
const customTo   = ref('')

// ── Data ────────────────────────────────────────────────────────────────────
const loading = ref(false)
const error   = ref('')
const kpis    = ref<any[]>([])
const charts  = ref<any[]>([])

function setPeriod(p: string) {
  period.value = p
  if (p !== 'custom') loadDashboard()
}

async function loadDashboard() {
  loading.value = true
  error.value   = ''
  try {
    const params: Record<string, string> = { period: period.value }
    if (period.value === 'custom') {
      params.date_from = customFrom.value
      params.date_to   = customTo.value
    }
    const resp = await api.get('/dashboard/data', { params })
    if (resp.data.success) {
      kpis.value   = resp.data.data.kpis   ?? []
      charts.value = resp.data.data.charts ?? []
    } else {
      error.value = resp.data.error ?? 'Unknown error'
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to load dashboard'
  } finally {
    loading.value = false
  }
}

function formatKpiValue(val: any): string {
  if (typeof val === 'number') {
    return val % 1 === 0 ? val.toString() : val.toFixed(1)
  }
  return String(val ?? '—')
}

function getIcon(name: string) {
  return (Icons as any)[name] || Icons.LayoutDashboard
}

const activePeriodLabel = computed(() => periods.find(p => p.value === period.value)?.label ?? 'Current Period')

function getKpiDisplay(key: string): string {
  const kpi = kpis.value.find(item => item.key === key)
  if (!kpi) return '—'
  const value = kpi.is_text ? String(kpi.value ?? '—') : formatKpiValue(kpi.value)
  return `${kpi.prefix ?? ''}${value}${kpi.suffix ?? ''}`
}

onMounted(loadDashboard)
</script>

<style lang="scss" scoped>
@use '../styles/variables' as v;

.dashboard {
  padding: 1.25rem 1.5rem 2rem;
  width: 100%;
  box-sizing: border-box;
}

// ── Header ──────────────────────────────────────────────────────────────────
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.dash-title {
  font-size: 1.375rem;
  font-weight: 700;
  color: v.$text-primary;
  margin: 0;
}
.period-filter {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}
.period-btn {
  padding: 0.3rem 0.7rem;
  border-radius: 6px;
  border: 1px solid v.$border-color;
  background: v.$bg-secondary;
  color: v.$text-secondary;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
  &:hover  { background: v.$bg-tertiary; color: v.$text-primary; }
  &.active { background: v.$primary-color; color: #fff; border-color: v.$primary-color; }
}
.date-input {
  padding: 0.275rem 0.5rem;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  background: v.$bg-secondary;
  color: v.$text-primary;
  font-size: 0.8rem;
}
.date-sep { color: v.$text-tertiary; font-size: 0.8rem; }

// ── Loading skeleton ─────────────────────────────────────────────────────────
.dash-loading { padding: 1rem 0; }
.skeleton-row { display: flex; gap: 1rem; flex-wrap: wrap; }
.skeleton-kpi {
  flex: 1 1 140px;
  height: 80px;
  background: v.$bg-tertiary;
  border-radius: 10px;
  animation: shimmer 1.2s infinite;
}
@keyframes shimmer {
  0%, 100% { opacity: 1 }
  50%       { opacity: 0.5 }
}
.dash-error { text-align: center; padding: 3rem; color: v.$danger-color; }

// ── KPI Grid ──────────────────────────────────────────────────────────────────
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.kpi-card {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.875rem 1rem;
  background: v.$bg-secondary;
  border: 1px solid v.$border-color;
  border-radius: 10px;
  box-shadow: v.$shadow-sm;
}
.kpi-icon { color: v.$primary-color; flex-shrink: 0; }
.kpi-icon :deep(svg) { width: 22px; height: 22px; }
.kpi-body { display: flex; flex-direction: column; line-height: 1.25; min-width: 0; }
.kpi-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: v.$text-primary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-prefix, .kpi-suffix { font-size: 0.8rem; font-weight: 400; color: v.$text-secondary; }
.kpi-label  { font-size: 0.7rem; color: v.$text-secondary; margin-top: 0.1rem; }

// ── Charts Grid ───────────────────────────────────────────────────────────────
.charts-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}
.chart-card {
  background: v.$bg-secondary;
  border: 1px solid v.$border-color;
  border-radius: 10px;
  padding: 1rem 1.125rem;
  box-shadow: v.$shadow-sm;
  min-width: 0;    // prevent chart overflow

  &.span-full { grid-column: 1 / -1; }
}
.chart-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: v.$text-primary;
  margin: 0 0 0.75rem;
}
// Constrain chart canvas so it never fills full screen
.chart-canvas-wrap {
  position: relative;
  width: 100%;
  height: 220px;    // fixed height — chart uses this container
  canvas { width: 100% !important; height: 100% !important; }
}

// ── Compact table widget ──────────────────────────────────────────────────────
.compact-table-wrap { overflow-x: auto; }
.compact-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
  th, td { padding: 0.45rem 0.75rem; text-align: left; border-bottom: 1px solid v.$border-color; }
  th { background: v.$bg-tertiary; color: v.$text-secondary; font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.03em; }
  td { color: v.$text-primary; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: v.$bg-tertiary; }
  .empty-cell { text-align: center; color: v.$text-tertiary; padding: 1.5rem; }
}

// ── Lower Dashboard Band ─────────────────────────────────────────────────────
.dashboard-lower {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 1rem;
}
.summary-panel,
.quick-panel {
  background: v.$bg-secondary;
  border: 1px solid v.$border-color;
  border-radius: 10px;
  padding: 1rem 1.125rem;
  box-shadow: v.$shadow-sm;
  min-width: 0;
}
.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.875rem;

  h2 {
    color: v.$text-primary;
    font-size: 0.95rem;
    font-weight: 700;
    margin: 0;
  }

  span {
    color: v.$text-secondary;
    font-size: 0.75rem;
  }
}
.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
}
.snapshot-item {
  border: 1px solid v.$border-color;
  border-radius: 8px;
  padding: 0.8rem;
  background: v.$bg-main;
  min-width: 0;

  strong {
    display: block;
    color: v.$text-primary;
    font-size: 1.15rem;
    line-height: 1.2;
    margin-top: 0.25rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
.snapshot-label {
  color: v.$text-secondary;
  font-size: 0.72rem;
}
.quick-links {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.625rem;
}
.quick-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: v.$text-primary;
  text-decoration: none;
  border: 1px solid v.$border-color;
  border-radius: 8px;
  padding: 0.75rem;
  background: v.$bg-main;
  min-width: 0;
  transition: background 0.15s, border-color 0.15s;

  &:hover {
    background: v.$bg-tertiary;
    border-color: v.$primary-color;
  }

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
.quick-icon {
  color: v.$primary-color;
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
}

// ── Mobile ────────────────────────────────────────────────────────────────────
@media (max-width: 640px) {
  .dashboard { padding: 1rem; }
  .dash-header { flex-direction: column; align-items: flex-start; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
  .dashboard-lower,
  .snapshot-grid,
  .quick-links { grid-template-columns: 1fr; }
  .chart-canvas-wrap { height: 180px; }
}

@media (min-width: 641px) and (max-width: 1180px) {
  .charts-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dashboard-lower,
  .snapshot-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
