<template>
  <div class="p-8 space-y-6 bg-slate-50 min-h-screen w-full">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">Órdenes de Compra</h1>
        <p class="text-slate-500 text-sm">Gestión de abastecimiento y pedidos a proveedores - Clínica Dental Maró</p>
      </div>
      <button 
        @click="generarSugerencias"
        :disabled="generando"
        class="inline-flex items-center justify-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-medium text-sm transition-colors shadow-sm cursor-pointer disabled:opacity-50"
      >
        <Sparkles class="w-4 h-4" />
        {{ generando ? 'Analizando Stock...' : 'Generar Sugerencia de Compra' }}
      </button>
    </div>

    <!-- Indicador de Carga -->
    <div v-if="store.loading && !generando" class="text-slate-500 text-sm font-medium">
      Cargando órdenes de compra...
    </div>

    <!-- Tabla de Órdenes -->
    <div v-else class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-600">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-xs">
            <tr>
              <th class="px-6 py-4">N° Orden</th>
              <th class="px-6 py-4">Proveedor</th>
              <th class="px-6 py-4">Estado</th>
              <th class="px-6 py-4">Fecha Creación</th>
              <th class="px-6 py-4">Fecha Recepción</th>
              <th class="px-6 py-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="o in store.ordenesCompra" :key="o.id" class="hover:bg-slate-50 transition-colors">
              <td class="px-6 py-4 font-mono font-bold text-slate-800">
                #OC-{{ o.id }}
              </td>
              <td class="px-6 py-4 font-semibold text-slate-700">
                {{ o.proveedor_nombre || 'Proveedor General' }}
              </td>
              <td class="px-6 py-4">
                <span :class="getBadgeClass(o.estado)" class="px-2.5 py-1 rounded-full text-xs font-semibold capitalize">
                  {{ o.estado }}
                </span>
              </td>
              <td class="px-6 py-4 text-xs font-mono text-slate-500">
                {{ formatearFecha(o.fecha_creacion) }}
              </td>
              <td class="px-6 py-4 text-xs font-mono text-slate-500">
                {{ formatearFecha(o.fecha_recepcion) }}
              </td>
              <td class="px-6 py-4 text-right space-x-2">
                <button 
                  v-if="o.estado === 'borrador'"
                  @click="cambiarEstado(o.id, 'enviada')"
                  class="px-3 py-1 bg-sky-50 text-sky-600 hover:bg-sky-100 border border-sky-200 rounded-md text-xs font-medium cursor-pointer"
                >
                  Marcar Enviada
                </button>
                <button 
                  v-if="o.estado === 'enviada'"
                  @click="cambiarEstado(o.id, 'recibida')"
                  class="px-3 py-1 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200 rounded-md text-xs font-medium cursor-pointer"
                >
                  Recibir Insumos
                </button>
                <button 
                  v-if="o.estado !== 'recibida' && o.estado !== 'cancelada'"
                  @click="cambiarEstado(o.id, 'cancelada')"
                  class="px-3 py-1 bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200 rounded-md text-xs font-medium cursor-pointer"
                >
                  Cancelar
                </button>
              </td>
            </tr>
            <tr v-if="store.ordenesCompra.length === 0">
              <td colspan="6" class="px-6 py-8 text-center text-slate-400">
                No hay órdenes de compra registradas. Haz clic en "Generar Sugerencia de Compra".
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import { useInventoryStore } from '@/stores/inventoryStore'

const store = useInventoryStore()
const generando = ref(false)

const generarSugerencias = async () => {
  generando.value = true
  try {
    await store.generarSugerenciasCompra()
  } catch (err) {
    alert(err.message)
  } finally {
    generando.value = false
  }
}

const cambiarEstado = async (id, estado) => {
  try {
    await store.cambiarEstadoOrden(id, estado)
  } catch (err) {
    alert(err.message)
  }
}

const formatearFecha = (strFecha) => {
  if (!strFecha) return '—'
  return new Date(strFecha).toLocaleString('es-CL', {
    day: '2-digit', month: '2-digit', year: 'numeric'
  })
}

const getBadgeClass = (estado) => {
  switch (estado) {
    case 'borrador': return 'bg-slate-100 text-slate-700 border border-slate-300'
    case 'enviada': return 'bg-sky-100 text-sky-800 border border-sky-300'
    case 'recibida': return 'bg-emerald-100 text-emerald-800 border border-emerald-300'
    case 'cancelada': return 'bg-rose-100 text-rose-800 border border-rose-300'
    default: return 'bg-slate-100 text-slate-800'
  }
}

onMounted(() => {
  store.fetchOrdenesCompra()
})
</script>
