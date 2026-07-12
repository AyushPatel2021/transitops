<template>
  <ReportLayout
    title="Fleet Utilization"
    icon="Activity"
    :loading="loading"
    :error="error"
    :rows="rows"
    :columns="columns"
    :charts="chartList"
    v-model:modelPeriod="period"
    v-model:modelDateFrom="dateFrom"
    v-model:modelDateTo="dateTo"
    :themeVersion="themeVersion"
    @export="exportCsv"
    @reload="load"
  >
    <template #filters>
      <select v-model="vehicleType" class="filter-select" @change="load">
        <option value="">All Types</option>
        <option value="Van">Van</option>
        <option value="Truck">Truck</option>
        <option value="Trailer">Trailer</option>
        <option value="Bike">Bike</option>
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

const period      = ref('all_time')
const dateFrom    = ref('')
const dateTo      = ref('')
const vehicleType = ref('')

const loading  = ref(false)
const error    = ref('')
const rows     = ref<any[]>([])
const columns  = ref<string[]>([])
const chartList = ref<any[]>([])

async function load() {
  loading.value = true
  error.value   = ''
  try {
    const params: any = { period: period.value, vehicle_type: vehicleType.value || undefined }
    if (period.value === 'custom') { params.date_from = dateFrom.value; params.date_to = dateTo.value }
    const resp = await api.get('/reports/fleet-utilization', { params })
    if (resp.data.success) {
      rows.value     = resp.data.data.rows    ?? []
      columns.value  = resp.data.data.columns ?? []
      chartList.value = resp.data.data.charts ?? []
    } else { error.value = resp.data.error ?? 'Error' }
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to load report'
  } finally { loading.value = false }
}

async function exportCsv() {
  const params: Record<string, string> = { period: period.value }
  if (vehicleType.value) params.vehicle_type = vehicleType.value
  if (period.value === 'custom') { params.date_from = dateFrom.value; params.date_to = dateTo.value }
  const query = new URLSearchParams(params).toString()
  const token = localStorage.getItem('token') ?? ''
  const base = (api.defaults.baseURL ?? '').replace(/\/$/, '')
  window.open(`${base}/reports/fleet-utilization/csv?${query}&token=${token}`, '_blank')
}

watch([period, dateFrom, dateTo], load)
onMounted(load)
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
