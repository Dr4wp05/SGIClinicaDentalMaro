<template>
  <div class="p-8 space-y-6 bg-slate-50 min-h-screen w-full">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">Movimientos de Inventario</h1>
        <p class="text-slate-500 text-sm">Historial de entradas, salidas y mermas - Clínica Dental Maró</p>
      </div>
      <button 
        @click="abrirModal = true"
        class="inline-flex items-center justify-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-medium text-sm transition-colors shadow-sm cursor-pointer"
      >
        <ArrowLeftRight class="w-4 h-4" />
        Registrar Movimiento
      </button>
    </div>

    <!-- Indicador de Carga -->
    <div v-if="store.loading" class="text-slate-500 text-sm font-medium">
      Cargando historial de movimientos...
    </div>

    <!-- Tabla Histórica -->
    <div v-else class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-600">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-xs">
            <tr>
              <th class="px-6 py-4">Fecha y Hora</th>
              <th class="px-6 py-4">Tipo</th>
              <th class="px-6 py-4">Responsable</th>
              <th class="px-6 py-4">Insumo</th>
              <th class="px-6 py-4">Lote</th>
              <th class="px-6 py-4">Cantidad</th>
              <th class="px-6 py-4">Detalle / Motivo</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="m in store.movimientos" :key="m.id" class="hover:bg-slate-50 transition-colors">
              <td class="px-6 py-4 text-xs font-mono text-slate-500">
                {{ formatearFecha(m.fecha_hora) }}
              </td>
              <td class="px-6 py-4">
                <span :class="getBadgeClass(m.tipo_movimiento)" class="px-2.5 py-1 rounded-full text-xs font-semibold">
                  {{ m.tipo_movimiento }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="flex flex-col">
                  <span class="font-semibold text-slate-800 text-xs">{{ m.usuario_nombre || 'Sistema' }} {{ m.usuario_apellido || '' }}</span>
                  <span class="text-[10px] text-slate-500 uppercase">{{ m.usuario_rol || 'N/A' }}</span>
                </div>
              </td>
              <td class="px-6 py-4 font-semibold text-slate-800">
                {{ m.lote_detalle?.producto_nombre || '—' }}
              </td>
              <td class="px-6 py-4 text-xs font-mono text-slate-600">
                {{ m.lote_detalle?.numero_lote || m.lote }}
              </td>
              <td class="px-6 py-4 font-bold" :class="m.tipo_movimiento === 'ENTRADA' ? 'text-teal-600' : 'text-rose-600'">
                {{ m.tipo_movimiento === 'ENTRADA' ? '+' : '-' }}{{ m.cantidad }}
              </td>
              <td class="px-6 py-4 text-xs text-slate-500">
                {{ m.motivo_perdida || 'Sin especificación' }}
              </td>
            </tr>
            <tr v-if="store.movimientos.length === 0">
              <td colspan="7" class="px-6 py-8 text-center text-slate-400">
                No hay movimientos registrados en la bitácora.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Registrar Movimiento -->
    <div v-if="abrirModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full p-6 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-lg font-bold text-slate-800">Nuevo Movimiento</h3>
          <button @click="cerrarModal" class="text-slate-400 hover:text-slate-600 text-lg font-bold cursor-pointer">&times;</button>
        </div>

        <form @submit.prevent="guardarMovimiento" class="space-y-4">
          <!-- Seleccionar Producto -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Producto</label>
            <select v-model="productoSeleccionadoId" @change="alCambiarProducto" required class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none">
              <option value="" disabled>Seleccione un producto...</option>
              <option v-for="p in store.productos" :key="p.id" :value="p.id">
                {{ p.nombre }}
              </option>
            </select>
          </div>

          <!-- Seleccionar Lote -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Lote de Origen/Destino</label>
            <select v-model="form.lote" :disabled="!lotesDisponibles.length" required class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none disabled:bg-slate-100">
              <option value="" disabled>Seleccione un lote...</option>
              <option v-for="l in lotesDisponibles" :key="l.id" :value="l.id">
                Lote: {{ l.numero_lote }} (Disponible: {{ l.cantidad_actual }})
              </option>
            </select>
          </div>

          <!-- Tipo Movimiento -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Tipo de Operación</label>
            <select v-model="form.tipo_movimiento" required class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none">
              <option value="CONSUMO">Consumo en Procedimiento / Box</option>
              <option value="MERMA_PERDIDA">Pérdida / Extravío / Dañado</option>
              <option value="MERMA_VENCIMIENTO">Vencimiento</option>
              <option value="ENTRADA">Entrada / Reposición</option>
            </select>
          </div>

          <!-- Cantidad -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Cantidad</label>
            <input type="number" min="1" v-model.number="form.cantidad" required class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none" />
          </div>

          <!-- Motivo -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Observación / Motivo</label>
            <textarea v-model="form.motivo_perdida" rows="2" placeholder="Detalles opcionales..." class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"></textarea>
          </div>

          <!-- Mensaje Error Form -->
          <p v-if="errorForm" class="text-xs text-rose-600 font-medium">{{ errorForm }}</p>

          <!-- Botones -->
          <div class="flex items-center justify-end gap-3 pt-2">
            <button type="button" @click="cerrarModal" class="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer">Cancelar</button>
            <button type="submit" :disabled="guardando" class="px-4 py-2 text-sm font-medium bg-teal-600 hover:bg-teal-700 text-white rounded-lg transition-colors cursor-pointer">
              {{ guardando ? 'Guardando...' : 'Confirmar Registro' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ArrowLeftRight } from 'lucide-vue-next'
import { useInventoryStore } from '@/stores/inventoryStore'

const store = useInventoryStore()
const abrirModal = ref(false)
const guardando = ref(false)
const errorForm = ref('')

const productoSeleccionadoId = ref('')
const form = ref({
  lote: '',
  tipo_movimiento: 'CONSUMO',
  cantidad: 1,
  motivo_perdida: ''
})

const lotesDisponibles = computed(() => {
  if (!productoSeleccionadoId.value) return []
  const prod = store.productos.find(p => p.id === productoSeleccionadoId.value)
  return prod ? prod.lotes || [] : []
})

const alCambiarProducto = () => {
  form.value.lote = ''
}

const cerrarModal = () => {
  abrirModal.value = false
  errorForm.value = ''
  productoSeleccionadoId.value = ''
  form.value = { lote: '', tipo_movimiento: 'CONSUMO', cantidad: 1, motivo_perdida: '' }
}

const guardarMovimiento = async () => {
  errorForm.value = ''
  guardando.value = true
  try {
    await store.registrarMovimiento(form.value)
    cerrarModal()
  } catch (err) {
    errorForm.value = err.message
  } finally {
    guardando.value = false
  }
}

const formatearFecha = (strFecha) => {
  if (!strFecha) return '—'
  return new Date(strFecha).toLocaleString('es-CL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

const getBadgeClass = (tipo) => {
  switch (tipo) {
    case 'ENTRADA': return 'bg-teal-100 text-teal-800'
    case 'CONSUMO': return 'bg-sky-100 text-sky-800'
    case 'MERMA_PERDIDA': return 'bg-rose-100 text-rose-800'
    case 'MERMA_VENCIMIENTO': return 'bg-amber-100 text-amber-800'
    default: return 'bg-slate-100 text-slate-800'
  }
}

onMounted(() => {
  store.fetchMovimientos()
  store.fetchProductos()
})
</script>
