<template>
  <ReportLayout
    title="Vehicle ROI"
    icon="BadgeDollarSign"
    :loading="loading"
    :error="error"
    :rows="rows"
    :columns="columns"
    :chart="chartDef"
    v-model:modelPeriod="period"
    v-model:modelDateFrom="dateFrom"
    v-model:modelDateTo="dateTo"
    :themeVersion="themeVersion"
    @export="exportCsv"
    @reload="load"
  >
    <template #filters>
      <select v-model="vehicleId" class="filter-select" @change="load">
        <option value="">All Vehicles</option>
        <option v-for="v in vehicleOptions" :key="v.id" :value="String(v.id)">
          {{ v.registration_number }}
        </option>
      </select>
    </template>
  </ReportLayout>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import api from '../../core/api'
import ReportLayout from '../../components/reports/ReportLayout.vue'
import { useDashboardTheme } from '../../composables/useDashboardTheme'

const { themeVersion } = useDashboardTheme()

const period    = ref('all_time')
const dateFrom  = ref('')
const dateTo    = ref('')
const vehicleId = ref('')

const loading        = ref(false)
const error          = ref('')
const rows           = ref<any[]>([])
const columns        = ref<string[]>([])
const chartDef       = ref<any>(null)
const vehicleOptions = ref<any[]>([])

async function loadVehicles() {
  try {
    const resp = await api.get('/models/vehicle', { params: { limit: 200 } })
    vehicleOptions.value = resp.data.items ?? []
  } catch { /* ignore */ }
}

async function load() {
  loading.value = true
  error.value   = ''
  try {
    const params: any = {
      period:     period.value,
      vehicle_id: vehicleId.value || undefined,
    }
    if (period.value === 'custom') { params.date_from = dateFrom.value; params.date_to = dateTo.value }
    const resp = await api.get('/reports/roi', { params })
    if (resp.data.success) {
      rows.value    = resp.data.data.rows    ?? []
      columns.value = resp.data.data.columns ?? []
      chartDef.value = resp.data.data.chart  ?? null
    } else { error.value = resp.data.error ?? 'Error' }
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to load report'
  } finally { loading.value = false }
}

async function exportCsv() {
  const params: Record<string, string> = { period: period.value }
  if (vehicleId.value) params.vehicle_id = vehicleId.value
  if (period.value === 'custom') { params.date_from = dateFrom.value; params.date_to = dateTo.value }
  const query = new URLSearchParams(params).toString()
  const token = localStorage.getItem('token') ?? ''
  const base = (api.defaults.baseURL ?? '').replace(/\/$/, '')
  window.open(`${base}/reports/roi/csv?${query}&token=${token}`, '_blank')
}

watch([period, dateFrom, dateTo], load)
onMounted(() => { loadVehicles(); load() })
</script>

<style scoped>
.filter-select {
  padding: 0.3rem 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.8rem;
}
</style>
