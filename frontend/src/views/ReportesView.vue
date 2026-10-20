<template>
  <div class="p-8 max-w-7xl mx-auto space-y-8">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Reportes de Inventario</h1>
      <p class="text-sm text-slate-500">Métricas financieras, pérdidas por merma y rotación de productos</p>
    </div>

    <!-- Carga inicial -->
    <div v-if="store.loading" class="text-center py-12">
      <p class="text-slate-500 text-sm">Cargando reporte de inventario...</p>
    </div>

    <template v-else>
      <!-- KPIs Financieros -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wider">Capital Inmovilizado</p>
          <p class="text-3xl font-bold text-slate-900">${{ formatoMoneda(store.reporteFinanciero.capital_inmovilizado) }}</p>
          <p class="text-xs text-slate-400">Valor actual en bodega sobre {{ store.reporteFinanciero.total_lotes_activos }} lotes activos</p>
        </div>

        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wider">Pérdidas por Merma</p>
          <p class="text-3xl font-bold text-red-600">${{ formatoMoneda(store.reporteFinanciero.perdida_mermas) }}</p>
          <p class="text-xs text-slate-400">Costo total por desperdicios y vencimientos</p>
        </div>

        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wider">Eficiencia de Inventario</p>
          <p class="text-3xl font-bold text-teal-600">{{ calcularEficiencia }}%</p>
          <p class="text-xs text-slate-400">Relación de capital activo vs pérdidas acumuladas</p>
        </div>
      </div>

      <!-- Tableros Secundarios -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <!-- Top Rotación de Insumos -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
          <div class="p-6 border-b border-slate-100">
            <h2 class="font-bold text-slate-800 text-base">Top 5 Mayor Rotación (Consumo)</h2>
          </div>

          <div v-if="store.reporteRotacion.length === 0" class="p-6 text-center text-slate-400 text-sm flex-grow flex items-center justify-center">
            No hay consumos registrados para calcular rotación.
          </div>

          <div v-else class="divide-y divide-slate-100 flex-grow">
            <div v-for="(item, index) in store.reporteRotacion" :key="index" class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
              <div class="flex items-center gap-3">
                <span class="w-6 h-6 rounded-full bg-teal-100 text-teal-700 font-bold text-xs flex items-center justify-center">
                  {{ index + 1 }}
                </span>
                <span class="font-medium text-slate-800 text-sm">{{ item.producto }}</span>
              </div>
              <span class="text-sm font-semibold text-slate-600">{{ item.total_consumido }} unidades</span>
            </div>
          </div>
        </div>

        <!-- Proyección de Vencimientos -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
          <div class="p-6 border-b border-slate-100 flex justify-between items-center">
            <h2 class="font-bold text-slate-800 text-base">Próximos a Vencer (30 días)</h2>
            <span class="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded-full">
              {{ store.alertasVencimientos.length }} Lotes
            </span>
          </div>

          <div v-if="store.alertasVencimientos.length === 0" class="p-6 text-center text-slate-400 text-sm flex-grow flex items-center justify-center">
            No hay insumos próximos a vencer en los siguientes 30 días.
          </div>

          <div v-else class="divide-y divide-slate-100 flex-grow max-h-80 overflow-y-auto">
            <div v-for="lote in store.alertasVencimientos" :key="lote.id" class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
              <div class="flex items-center gap-3">
                <div class="w-2 h-2 rounded-full bg-amber-500"></div>
                <div>
                  <p class="font-medium text-slate-800 text-sm">{{ lote.producto_nombre }}</p>
                  <p class="text-xs text-slate-500 font-mono">Lote: {{ lote.numero_lote }}</p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-sm font-semibold text-slate-700">{{ lote.cantidad_actual }} un.</p>
                <p class="text-xs text-amber-600 font-medium">Vence: {{ formatoFecha(lote.fecha_vencimiento) }}</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useInventoryStore } from '@/stores/inventoryStore'

const store = useInventoryStore()

const formatoMoneda = (valor) => {
  return Number(valor || 0).toLocaleString('es-CL')
}

// Formateamos para que "YYYY-MM-DD" no sufra desfase de zona horaria
const formatoFecha = (strFecha) => {
  if (!strFecha) return '—'
  const [year, month, day] = strFecha.split('-')
  return `${day}/${month}/${year}`
}

const calcularEficiencia = computed(() => {
  const cap = store.reporteFinanciero.capital_inmovilizado || 0
  const mer = store.reporteFinanciero.perdida_mermas || 0
  if (cap === 0) return 100
  const ratio = ((cap - mer) / cap) * 100
  return Math.max(0, ratio).toFixed(1)
})

onMounted(() => {
  store.fetchReportesBI()
})
</script>
