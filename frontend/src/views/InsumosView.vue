<template>
  <div class="insumos-container p-6 bg-slate-50 min-h-screen">
    <!-- Cabecera -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">Gestión de Insumos y Lotes</h1>
        <p class="text-slate-500 text-sm">Administración del catálogo de productos y recepciones de stock</p>
      </div>
      <div class="flex gap-3 items-center">
        <!-- Acciones Carga Masiva y Exportación -->
        <button 
          @click="descargarExcel" 
          class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 border border-slate-300 shadow-sm cursor-pointer"
        >
          <Download class="w-4 h-4" />
          Exportar Excel
        </button>

        <button 
          @click="mostrarModalImportar = true" 
          class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 border border-slate-300 shadow-sm cursor-pointer"
        >
          <Upload class="w-4 h-4" />
          Importar Excel
        </button>

        <!-- Acciones Manuales -->
        <button 
          @click="abrirModalLote()" 
          class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 shadow-sm cursor-pointer"
        >
          <span>+</span> Ingresar Lote
        </button>
        <button 
          @click="abrirModalProducto()" 
          class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 shadow-sm cursor-pointer"
        >
          <span>+</span> Nuevo Insumo
        </button>
      </div>
    </div>

    <!-- Barra de Búsqueda y Filtros -->
    <div class="bg-white p-4 rounded-xl shadow-sm mb-6 flex flex-wrap gap-4 items-center border border-slate-200">
      <input 
        v-model="filtroBusqueda" 
        type="text" 
        placeholder="Buscar por nombre, código o marca..." 
        class="flex-1 min-w-[250px] border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select 
        v-model="filtroCategoria" 
        class="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      >
        <option value="">Todas las Categorías</option>
        <option v-for="cat in store.categorias" :key="cat.id" :value="cat.id">
          {{ cat.nombre }}
        </option>
      </select>
    </div>

    <!-- Mensaje de Carga / Error -->
    <div v-if="store.loading && !store.productos.length" class="text-center py-10 text-slate-500">Cargando inventario...</div>
    <div v-else-if="store.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ store.error }}
    </div>

    <!-- Tabla de Insumos -->
    <div v-else class="bg-white rounded-xl shadow-sm overflow-hidden border border-slate-200">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-slate-100 text-slate-600 text-xs uppercase tracking-wider border-b border-slate-200">
            <th class="py-3 px-4">Código</th>
            <th class="py-3 px-4">Insumo</th>
            <th class="py-3 px-4">Categoría</th>
            <th class="py-3 px-4">U. Medida</th>
            <th class="py-3 px-4 text-center">Stock Actual</th>
            <th class="py-3 px-4 text-center">Stock Mínimo</th>
            <th class="py-3 px-4 text-center">Estado Stock</th>
            <th class="py-3 px-4 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 text-sm">
          <template v-for="prod in productosFiltrados" :key="prod.id">
            <tr class="hover:bg-slate-50 transition">
              <td class="py-3 px-4 font-mono text-xs text-slate-500">{{ prod.codigo_barras }}</td>
              <td class="py-3 px-4 font-semibold text-slate-800">
                {{ prod.nombre }}
                <span v-if="prod.marca" class="block text-xs font-normal text-slate-400">{{ prod.marca }}</span>
              </td>
              <td class="py-3 px-4 text-slate-600">{{ prod.categoria_nombre || 'Sin Categoría' }}</td>
              <td class="py-3 px-4 text-slate-600 capitalize">{{ prod.unidad_medida }}</td>
              <td class="py-3 px-4 text-center font-bold text-slate-800">{{ prod.stock_total }}</td>
              <td class="py-3 px-4 text-center text-slate-500">{{ prod.stock_minimo }}</td>
              <td class="py-3 px-4 text-center">
                <span 
                  :class="prod.stock_total <= prod.stock_minimo ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'"
                  class="px-2 py-1 rounded-full text-xs font-semibold"
                >
                  {{ prod.stock_total <= prod.stock_minimo ? 'Crítico' : 'Normal' }}
                </span>
              </td>
              <td class="py-3 px-4 text-right flex justify-end gap-2 items-center">
                <button 
                  @click="toggleDetalleLotes(prod.id)" 
                  class="text-blue-600 hover:text-blue-800 text-xs font-medium underline cursor-pointer"
                >
                  {{ loteDesplegado === prod.id ? 'Ocultar Lotes' : 'Ver Lotes (' + (prod.lotes ? prod.lotes.length : 0) + ')' }}
                </button>
                <button 
                  @click="abrirModalLote(prod)" 
                  class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-2 py-1 rounded border border-slate-300 cursor-pointer"
                >
                  + Lote
                </button>
              </td>
            </tr>

            <!-- Desglose de Lotes del Producto -->
            <tr v-if="loteDesplegado === prod.id" class="bg-slate-50/70 border-b border-slate-200">
              <td colspan="8" class="p-4">
                <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-inner">
                  <h4 class="text-xs font-bold text-slate-700 uppercase mb-2">Detalle de Lotes Asociados</h4>
                  <table v-if="prod.lotes && prod.lotes.length" class="w-full text-xs text-left">
                    <thead>
                      <tr class="text-slate-400 border-b border-slate-100">
                        <th class="py-1">Nº Lote</th>
                        <th class="py-1">F. Compra</th>
                        <th class="py-1">F. Vencimiento</th>
                        <th class="py-1">Costo Unit.</th>
                        <th class="py-1 text-center">Cant. Inicial</th>
                        <th class="py-1 text-center">Cant. Actual</th>
                        <th class="py-1 text-center">Agotado</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="lote in prod.lotes" :key="lote.id" class="border-b border-slate-50">
                        <td class="py-1.5 font-mono text-slate-600">{{ lote.numero_lote }}</td>
                        <td class="py-1.5 text-slate-600">{{ lote.fecha_compra }}</td>
                        <td class="py-1.5 text-slate-600 font-medium" :class="esPorVencer(lote.fecha_vencimiento) ? 'text-amber-600 font-bold' : ''">
                          {{ lote.fecha_vencimiento }}
                        </td>
                        <td class="py-1.5 text-slate-600">${{ Number(lote.costo_unitario).toLocaleString() }}</td>
                        <td class="py-1.5 text-center text-slate-500">{{ lote.cantidad_inicial }}</td>
                        <td class="py-1.5 text-center font-bold text-slate-700">{{ lote.cantidad_actual }}</td>
                        <td class="py-1.5 text-center">
                          <span :class="lote.agotado ? 'text-red-500 font-semibold' : 'text-emerald-500 font-semibold'">
                            {{ lote.agotado ? 'Sí' : 'No' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <p v-else class="text-xs text-slate-400 italic">No existen lotes registrados para este insumo.</p>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- MODAL NUEVO PRODUCTO -->
    <div v-if="modalProductoOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex justify-center items-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Crear Nuevo Insumo</h2>
        
        <form @submit.prevent="guardarProducto" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Código de Barras *</label>
              <input v-model="formProducto.codigo_barras" type="text" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Nombre Insumo *</label>
              <input v-model="formProducto.nombre" type="text" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Marca</label>
              <input v-model="formProducto.marca" type="text" class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Categoría *</label>
              <select v-model="formProducto.categoria" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-white">
                <option value="" disabled>Seleccione Categoria</option>
                <option v-for="cat in store.categorias" :key="cat.id" :value="cat.id">{{ cat.nombre }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Proveedor Habitual</label>
              <select v-model="formProducto.proveedor_habitual" class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-white">
                <option :value="null">Ninguno / Sin definir</option>
                <option v-for="prov in store.proveedores" :key="prov.id" :value="prov.id">{{ prov.nombre_fantasia }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Unidad de Medida *</label>
              <select v-model="formProducto.unidad_medida" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-white">
                <option value="caja">Caja</option>
                <option value="cartucho">Cartucho</option>
                <option value="frasco">Frasco</option>
                <option value="tubo">Tubo</option>
                <option value="kit">Kit</option>
                <option value="unidad">Unidad</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">Stock Mínimo Crítico *</label>
            <input v-model.number="formProducto.stock_minimo" type="number" min="0" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
          </div>

          <div v-if="errorForm" class="text-xs text-red-600 bg-red-50 border border-red-200 p-2 rounded">
            {{ errorForm }}
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button type="button" @click="modalProductoOpen = false" class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded cursor-pointer">Cancelar</button>
            <button type="submit" :disabled="store.loading" class="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 cursor-pointer">
              {{ store.loading ? 'Guardando...' : 'Guardar Insumo' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL NUEVO LOTE -->
    <div v-if="modalLoteOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex justify-center items-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Ingresar Nuevo Lote de Stock</h2>
        
        <form @submit.prevent="guardarLote" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">Producto / Insumo *</label>
            <select v-model="formLote.producto" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-white">
              <option value="" disabled>Seleccionar Producto</option>
              <option v-for="prod in store.productos" :key="prod.id" :value="prod.id">
                {{ prod.nombre }} ({{ prod.codigo_barras }})
              </option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Número de Lote *</label>
              <input v-model="formLote.numero_lote" type="text" placeholder="EJ: L-2026-001" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Cantidad Inicial *</label>
              <input v-model.number="formLote.cantidad_inicial" type="number" min="1" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Fecha Compra *</label>
              <input v-model="formLote.fecha_compra" type="date" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Fecha Vencimiento *</label>
              <input v-model="formLote.fecha_vencimiento" type="date" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">Costo Unitario ($)</label>
            <input v-model.number="formLote.costo_unitario" type="number" step="0.01" min="0" class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
          </div>

          <div v-if="errorForm" class="text-xs text-red-600 bg-red-50 border border-red-200 p-2 rounded">
            {{ errorForm }}
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button type="button" @click="modalLoteOpen = false" class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded cursor-pointer">Cancelar</button>
            <button type="submit" :disabled="store.loading" class="px-4 py-2 text-sm bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50 cursor-pointer">
              {{ store.loading ? 'Guardando...' : 'Guardar Lote' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL CARGA MASIVA DESDE EXCEL -->
    <div v-if="mostrarModalImportar" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 border border-slate-200">
        <h3 class="text-lg font-bold text-slate-800">Carga Masiva desde Excel</h3>
        <p class="text-xs text-slate-500">Selecciona una plantilla .xlsx con las columnas requeridas: Nombre, Categoria, StockMinimo, Lote, FechaVencimiento, CostoUnitario, CantidadInicial.</p>

        <input 
          type="file" 
          ref="fileInput" 
          accept=".xlsx, .xls" 
          class="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100 cursor-pointer" 
        />

        <div v-if="cargandoImportacion" class="text-xs text-teal-600 font-medium">
          Procesando e importando archivo Excel...
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t border-slate-100">
          <button @click="mostrarModalImportar = false" class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer">Cancelar</button>
          <button @click="subirArchivo" :disabled="cargandoImportacion" class="px-4 py-2 text-sm bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 cursor-pointer">
            {{ cargandoImportacion ? 'Importando...' : 'Subir e Importar' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Download, Upload } from 'lucide-vue-next'
import { useInventoryStore } from '@/stores/inventoryStore'

const store = useInventoryStore()

const filtroBusqueda = ref('')
const filtroCategoria = ref('')
const loteDesplegado = ref(null)

const modalProductoOpen = ref(false)
const modalLoteOpen = ref(false)
const mostrarModalImportar = ref(false)
const cargandoImportacion = ref(false)
const fileInput = ref(null)
const errorForm = ref('')

const formProducto = ref({
  codigo_barras: '',
  nombre: '',
  marca: '',
  categoria: '',
  proveedor_habitual: null,
  unidad_medida: 'unidad',
  stock_minimo: 5
})

const formLote = ref({
  producto: '',
  numero_lote: '',
  fecha_compra: new Date().toISOString().split('T')[0],
  fecha_vencimiento: '',
  costo_unitario: 0,
  cantidad_inicial: 10
})

onMounted(async () => {
  await Promise.all([
    store.fetchProductos(),
    store.fetchCategorias(),
    store.fetchProveedores()
  ])
})

const productosFiltrados = computed(() => {
  return store.productos.filter(p => {
    const coincideNombre = p.nombre.toLowerCase().includes(filtroBusqueda.value.toLowerCase()) ||
                           p.codigo_barras.toLowerCase().includes(filtroBusqueda.value.toLowerCase()) ||
                           (p.marca && p.marca.toLowerCase().includes(filtroBusqueda.value.toLowerCase()))
    
    const coincideCat = filtroCategoria.value === '' || p.categoria === Number(filtroCategoria.value)
    
    return coincideNombre && coincideCat
  })
})

const toggleDetalleLotes = (id) => {
  loteDesplegado.value = loteDesplegado.value === id ? null : id
}

const abrirModalProducto = () => {
  errorForm.value = ''
  formProducto.value = {
    codigo_barras: '',
    nombre: '',
    marca: '',
    categoria: store.categorias.length ? store.categorias[0].id : '',
    proveedor_habitual: null,
    unidad_medida: 'unidad',
    stock_minimo: 5
  }
  modalProductoOpen.value = true
}

const abrirModalLote = (producto = null) => {
  errorForm.value = ''
  formLote.value = {
    producto: producto ? producto.id : (store.productos.length ? store.productos[0].id : ''),
    numero_lote: '',
    fecha_compra: new Date().toISOString().split('T')[0],
    fecha_vencimiento: '',
    costo_unitario: 0,
    cantidad_inicial: 10
  }
  modalLoteOpen.value = true
}

const guardarProducto = async () => {
  try {
    errorForm.value = ''
    await store.crearProducto(formProducto.value)
    modalProductoOpen.value = false
  } catch (err) {
    errorForm.value = err.message || 'Error al guardar el insumo'
  }
}

const guardarLote = async () => {
  try {
    errorForm.value = ''
    await store.crearLote(formLote.value)
    modalLoteOpen.value = false
  } catch (err) {
    errorForm.value = err.message || 'Error al guardar el lote'
  }
}

// NUEVA FUNCIÓN REFACCIONADA: Exportar usando Axios y el Store
const descargarExcel = async () => {
  try {
    await store.exportarExcel()
  } catch (err) {
    alert(err.message || 'Error al exportar inventario.')
  }
}

// NUEVA FUNCIÓN REFACCIONADA: Importar usando Axios y el Store
const subirArchivo = async () => {
  const file = fileInput.value?.files[0]
  if (!file) return alert('Por favor selecciona un archivo Excel (.xlsx).')

  cargandoImportacion.value = true
  
  try {
    const data = await store.importarExcel(file)
    alert(data.message || 'Importación completada con éxito.')
    mostrarModalImportar.value = false
  } catch (err) {
    alert(err.message || 'Error de conexión al importar el archivo Excel.')
  } finally {
    cargandoImportacion.value = false
    if (fileInput.value) {
      fileInput.value.value = '' // Limpiar el input file
    }
  }
}

const esPorVencer = (fechaStr) => {
  if (!fechaStr) return false
  const fecha = new Date(fechaStr)
  const hoy = new Date()
  const limite = new Date()
  limite.setDate(hoy.getDate() + 30)
  return fecha >= hoy && fecha <= limite
}
</script>
