<template>
  <div class="p-8 space-y-6 bg-slate-50 min-h-screen w-full">
    <div>
      <h1 class="text-2xl font-bold text-slate-800">Resumen de Inventario</h1>
      <p class="text-slate-500 text-sm">Estado del stock en tiempo real - Clínica Dental Maró</p>
    </div>

    <!-- Indicador de carga -->
    <div v-if="store.loading" class="text-slate-500 text-sm font-medium">
      Cargando métricas en tiempo real...
    </div>

    <!-- Mensaje de error (si ocurre) -->
    <div v-else-if="store.error" class="p-4 bg-rose-50 text-rose-700 rounded-lg text-sm border border-rose-200">
      {{ store.error }}
    </div>

    <!-- Tarjetas de Métricas Dinámicas -->
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Total Productos -->
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Productos</span>
          <p class="text-3xl font-extrabold text-slate-800 mt-1">{{ totalProductos }}</p>
        </div>
        <div class="p-3 bg-teal-50 rounded-lg text-teal-600">
          <Package class="w-6 h-6" />
        </div>
      </div>

      <!-- Próximos a Vencer -->
      <div class="bg-white p-6 rounded-xl border border-amber-200 shadow-sm flex items-center justify-between">
        <div>
          <span class="text-xs font-semibold text-amber-600 uppercase tracking-wider">Próximos a Vencer</span>
          <p class="text-3xl font-extrabold text-amber-600 mt-1">{{ store.resumenAlertas.por_vencer }}</p>
        </div>
        <div class="p-3 bg-amber-50 rounded-lg text-amber-600">
          <Clock class="w-6 h-6" />
        </div>
      </div>

      <!-- Stock Crítico -->
      <div class="bg-white p-6 rounded-xl border border-rose-200 shadow-sm flex items-center justify-between">
        <div>
          <span class="text-xs font-semibold text-rose-600 uppercase tracking-wider">Stock Crítico</span>
          <p class="text-3xl font-extrabold text-rose-600 mt-1">{{ store.resumenAlertas.stock_critico }}</p>
        </div>
        <div class="p-3 bg-rose-50 rounded-lg text-rose-600">
          <AlertCircle class="w-6 h-6" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Package, Clock, AlertCircle } from 'lucide-vue-next'
import { useInventoryStore } from '@/stores/inventoryStore'
import api from '@/api/axios'

const store = useInventoryStore()
const totalProductos = ref(0)

const fetchTotalProductos = async () => {
  try {
    const response = await api.get('productos/')
    // Si la API usa paginación devuelve count, si no, se usa la longitud del arreglo
    totalProductos.value = response.data.count ?? response.data.length
  } catch (err) {
    console.error('Error al obtener el total de productos:', err)
  }
}

onMounted(() => {
  store.cargarDashboard()
  fetchTotalProductos()
})
</script>
