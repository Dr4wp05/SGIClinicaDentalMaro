<template>
  <div class="p-8 max-w-7xl mx-auto space-y-8">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Reportes de Inventario</h1>
      <p class="text-sm text-slate-500">Métricas financieras, pérdidas por merma y rotación de productos</p>
    </div>

    <!-- Carga inicial -->
    <div v-if="loading" class="text-center py-12">
      <p class="text-slate-500 text-sm">Cargando reporte de inventario...</p>
    </div>

    <template v-else>
      <!-- KPIs Financieros -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wider">Capital Inmovilizado</p>
          <p class="text-3xl font-bold text-slate-900">${{ formatoMoneda(financiero.capital_inmovilizado) }}</p>
          <p class="text-xs text-slate-400">Valor actual en bodega sobre {{ financiero.total_lotes_activos }} lotes activos</p>
        </div>

        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wider">Pérdidas por Merma</p>
          <p class="text-3xl font-bold text-red-600">${{ formatoMoneda(financiero.perdida_mermas) }}</p>
          <p class="text-xs text-slate-400">Costo total por desperdicios y vencimientos</p>
        </div>

        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wider">Eficiencia de Inventario</p>
          <p class="text-3xl font-bold text-teal-600">{{ calcularEficiencia() }}%</p>
          <p class="text-xs text-slate-400">Relación de capital activo vs pérdidas acumuladas</p>
        </div>
      </div>

      <!-- Top Rotación de Insumos -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="p-6 border-b border-slate-100">
          <h2 class="font-bold text-slate-800 text-base">Top 5 Insumos con Mayor Rotación (Consumo)</h2>
        </div>

        <div v-if="rotacion.length === 0" class="p-6 text-center text-slate-400 text-sm">
          No hay consumos registrados para calcular rotación.
        </div>

        <div v-else class="divide-y divide-slate-100">
          <div v-for="(item, index) in rotacion" :key="index" class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
            <div class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full bg-teal-100 text-teal-700 font-bold text-xs flex items-center justify-center">
                {{ index + 1 }}
              </span>
              <span class="font-medium text-slate-800 text-sm">{{ item.producto }}</span>
            </div>
            <span class="text-sm font-semibold text-slate-600">{{ item.total_consumido }} unidades consumidas</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(true)
const financiero = ref({ capital_inmovilizado: 0, perdida_mermas: 0, total_lotes_activos: 0 })
const rotacion = ref([])

const formatoMoneda = (valor) => {
  return Number(valor || 0).toLocaleString('es-CL')
}

const calcularEficiencia = () => {
  const cap = financiero.value.capital_inmovilizado || 0
  const mer = financiero.value.perdida_mermas || 0
  if (cap === 0) return 100
  const ratio = ((cap - mer) / cap) * 100
  return Math.max(0, ratio.toFixed(1))
}

const obtenerDatos = async () => {
  loading.value = true
  const token = localStorage.getItem('access_token')
  const headers = { Authorization: `Bearer ${token}` }

  try {
    const [resFin, resRot] = await Promise.all([
      fetch('/api/reportes/financiero/', { headers }),
      fetch('/api/reportes/rotacion/', { headers })
    ])

    if (resFin.ok) financiero.value = await resFin.json()
    if (resRot.ok) rotacion.value = await resRot.json()
  } catch (e) {
    console.error('Error al cargar datos del reporte:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  obtenerDatos()
})
</script>
