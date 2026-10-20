<template>
  <div>
    <!-- VISTA NORMAL DE LA APLICACIÓN (Se oculta al imprimir) -->
    <div class="p-8 space-y-6 bg-slate-50 min-h-screen w-full print:hidden">
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
                  <!-- Botón Exportar PDF -->
                  <button 
                    @click="imprimirOrden(o)"
                    class="px-3 py-1 bg-slate-100 text-slate-600 hover:bg-slate-200 border border-slate-300 rounded-md text-xs font-medium cursor-pointer inline-flex items-center gap-1"
                    title="Exportar documento PDF"
                  >
                    <Printer class="w-3 h-3" /> PDF
                  </button>

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

    <!-- PLANTILLA DE IMPRESIÓN / PDF (Oculta en pantalla, visible al imprimir) -->
    <div v-if="ordenParaImprimir" class="hidden print:block bg-white p-8 font-sans text-slate-800 max-w-[210mm] mx-auto absolute top-0 left-0 w-full min-h-screen">
      <!-- Membrete -->
      <div class="flex justify-between items-start border-b-2 border-slate-800 pb-6 mb-8">
        <div>
          <h1 class="text-3xl font-extrabold tracking-tight text-slate-900 uppercase">Clínica Dental Maró</h1>
          <p class="text-sm text-slate-600 mt-1">Avenida Pablo Neruda 1790, Temuco, Chile</p>
          <p class="text-sm text-slate-600">contacto@maroclinica.cl | Administración de Abastecimiento</p>
        </div>
        <div class="text-right">
          <h2 class="text-2xl font-bold text-teal-700 uppercase">Orden de Compra</h2>
          <p class="text-lg font-mono font-bold mt-1 text-slate-700">N° OC-{{ ordenParaImprimir.id }}</p>
          <p class="text-sm mt-2"><span class="font-semibold">Fecha de Emisión:</span> {{ formatearFecha(ordenParaImprimir.fecha_creacion) }}</p>
          <p class="text-sm"><span class="font-semibold">Estado de la Orden:</span> <span class="capitalize">{{ ordenParaImprimir.estado }}</span></p>
        </div>
      </div>

      <!-- Datos del Proveedor -->
      <div class="mb-8">
        <h3 class="text-base font-bold border-b border-slate-300 mb-3 pb-1 text-slate-700">Destinatario / Proveedor</h3>
        <p class="text-sm"><span class="font-semibold">Razón Social / Fantasía:</span> {{ ordenParaImprimir.proveedor_nombre || 'Proveedor General' }}</p>
        <p class="text-sm"><span class="font-semibold">Emitido por:</span> {{ ordenParaImprimir.creado_por_nombre || 'Sistema de Inventario' }}</p>
      </div>

      <!-- Tabla de Insumos Requeridos -->
      <div class="mb-12">
        <h3 class="text-base font-bold border-b border-slate-300 mb-3 pb-1 text-slate-700">Detalle de Insumos Solicitados</h3>
        <table class="w-full text-left text-sm border-collapse border border-slate-300">
          <thead>
            <tr class="bg-slate-100">
              <th class="py-2 px-4 border border-slate-300 font-bold w-16 text-center">Nº</th>
              <th class="py-2 px-4 border border-slate-300 font-bold">Descripción del Producto</th>
              <th class="py-2 px-4 border border-slate-300 font-bold text-center w-32">Cant. Solicitada</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(lote, index) in ordenParaImprimir.lotes" :key="lote.id" class="border-b border-slate-200">
              <td class="py-2 px-4 border border-slate-300 text-center font-mono text-slate-500">{{ index + 1 }}</td>
              <td class="py-2 px-4 border border-slate-300 font-medium">{{ lote.producto_nombre }}</td>
              <td class="py-2 px-4 border border-slate-300 text-center font-bold">{{ lote.cantidad_inicial }}</td>
            </tr>
            <tr v-if="!ordenParaImprimir.lotes || ordenParaImprimir.lotes.length === 0">
              <td colspan="3" class="py-4 text-center italic text-slate-500 border border-slate-300">
                No hay desglose de insumos en esta orden.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Firmas -->
      <div class="mt-24 flex justify-between px-16">
        <div class="text-center border-t border-slate-400 w-56 pt-2">
          <p class="text-xs font-bold text-slate-800">Firma Autorizada</p>
          <p class="text-xs text-slate-500">Clínica Dental Maró</p>
        </div>
        <div class="text-center border-t border-slate-400 w-56 pt-2">
          <p class="text-xs font-bold text-slate-800">Recepción Conforme</p>
          <p class="text-xs text-slate-500">Firma y Timbre Proveedor</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Sparkles, Printer } from 'lucide-vue-next'
import { useInventoryStore } from '@/stores/inventoryStore'

const store = useInventoryStore()
const generando = ref(false)
const ordenParaImprimir = ref(null)

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

// Función que carga los datos en la plantilla y abre el diálogo de impresión del SO
const imprimirOrden = async (orden) => {
  ordenParaImprimir.value = orden
  // nextTick asegura que Vue actualice el DOM con los datos antes de lanzar la ventana de impresión
  await nextTick()
  window.print()
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

<style>
/* 
  Reglas CSS globales específicas para la impresión. 
  Aseguran que los márgenes del navegador se eliminen 
  y se use formato A4 estándar.
*/
@media print {
  @page {
    margin: 0;
    size: A4;
  }
  body {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
</style>
