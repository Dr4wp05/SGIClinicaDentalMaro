import { defineStore } from 'pinia'
import api from '@/api/axios'

export const useInventoryStore = defineStore('inventory', {
  state: () => ({
    productos: [],
    categorias: [],
    proveedores: [],
    movimientos: [],
    ordenesCompra: [],
    resumenAlertas: {
      stock_critico: 0,
      por_vencer: 0,
      total_alertas: 0
    },
    // Nuevos estados para el módulo BI
    reporteFinanciero: { capital_inmovilizado: 0, perdida_mermas: 0, total_lotes_activos: 0 },
    reporteRotacion: [],
    alertasVencimientos: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchProductos() {
      this.loading = true
      try {
        const response = await api.get('productos/')
        this.productos = response.data.results || response.data
      } catch (err) {
        this.error = 'Error al cargar productos'
        console.error(err)
      } finally {
        this.loading = false
      }
    },

    async fetchCategorias() {
      try {
        const response = await api.get('categorias/')
        this.categorias = response.data.results || response.data
      } catch (err) {
        console.error('Error al cargar categorias:', err)
      }
    },

    async fetchProveedores() {
      try {
        const response = await api.get('proveedores/')
        this.proveedores = response.data.results || response.data
      } catch (err) {
        console.error('Error al cargar proveedores:', err)
      }
    },

    async crearProducto(payloadProducto) {
      this.loading = true
      try {
        const response = await api.post('productos/', payloadProducto)
        await this.fetchProductos()
        await this.fetchResumenAlertas()
        return response.data
      } catch (err) {
        let msg = 'Error al crear el producto'
        if (err.response?.data) {
          if (typeof err.response.data === 'object') {
            msg = Object.entries(err.response.data)
              .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
              .join(' | ')
          } else {
            msg = err.response.data
          }
        }
        console.error('Error en crearProducto:', err.response?.data)
        throw new Error(msg)
      } finally {
        this.loading = false
      }
    },

    async crearLote(payloadLote) {
      this.loading = true
      try {
        const cantInicial = Number(payloadLote.cantidad_inicial) || 0
        const data = {
          ...payloadLote,
          cantidad_inicial: cantInicial,
          cantidad_actual: cantInicial,
          agotado: cantInicial <= 0
        }
        const response = await api.post('lotes/', data)
        await this.fetchProductos()
        await this.fetchResumenAlertas()
        return response.data
      } catch (err) {
        let msg = 'Error al crear el lote'
        if (err.response?.data) {
          if (typeof err.response.data === 'object') {
            msg = Object.entries(err.response.data)
              .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
              .join(' | ')
          } else {
            msg = err.response.data
          }
        }
        console.error('Error en crearLote:', err.response?.data)
        throw new Error(msg)
      } finally {
        this.loading = false
      }
    },

    async fetchResumenAlertas() {
      try {
        const response = await api.get('alertas/resumen/')
        this.resumenAlertas = response.data
      } catch (err) {
        console.error('Error al cargar alertas:', err)
      }
    },

    async fetchMovimientos() {
      this.loading = true
      try {
        const response = await api.get('movimientos/')
        this.movimientos = response.data.results || response.data
      } catch (err) {
        this.error = 'Error al cargar el historial de movimientos'
        console.error(err)
      } finally {
        this.loading = false
      }
    },

    async fetchOrdenesCompra() {
      this.loading = true
      try {
        const response = await api.get('ordenes-compra/')
        this.ordenesCompra = response.data.results || response.data
      } catch (err) {
        this.error = 'Error al cargar las órdenes de compra'
        console.error(err)
      } finally {
        this.loading = false
      }
    },

    async generarSugerenciasCompra() {
      this.loading = true
      try {
        const response = await api.post('ordenes-compra/generar-sugerencias/')
        await this.fetchOrdenesCompra()
        return response.data
      } catch (err) {
        const msg = err.response?.data?.error || 'Error al generar sugerencias de compra'
        throw new Error(msg)
      } finally {
        this.loading = false
      }
    },

    async cambiarEstadoOrden(idOrden, nuevoEstado) {
      try {
        const response = await api.post(`ordenes-compra/${idOrden}/cambiar_estado/`, { estado: nuevoEstado })
        await this.fetchOrdenesCompra()
        await this.fetchProductos()
        await this.fetchResumenAlertas()
        return response.data
      } catch (err) {
        const msg = err.response?.data?.error || 'Error al actualizar estado de la orden'
        throw new Error(msg)
      }
    },

    async registrarMovimiento(datosMovimiento) {
      try {
        const response = await api.post('movimientos/', datosMovimiento)
        await this.fetchMovimientos()
        await this.fetchProductos()
        await this.fetchResumenAlertas()
        return response.data
      } catch (err) {
        const msg = err.response?.data?.error || 'Error al registrar movimiento'
        throw new Error(msg)
      }
    },

    async cargarDashboard() {
      this.loading = true
      this.error = null
      try {
        await this.fetchResumenAlertas()
      } catch (err) {
        this.error = 'Error al cargar datos del dashboard'
      } finally {
        this.loading = false
      }
    },

    // NUEVA ACCIÓN BI: Trae todo lo necesario para la vista de Reportes
    async fetchReportesBI() {
      this.loading = true
      this.error = null
      try {
        // Ejecutamos las peticiones en paralelo para mayor velocidad
        const [resFinanciero, resRotacion, resVencimientos] = await Promise.all([
          api.get('reportes/financiero/'),
          api.get('reportes/rotacion/'),
          api.get('alertas/vencimientos/')
        ])
        
        this.reporteFinanciero = resFinanciero.data
        this.reporteRotacion = resRotacion.data.results || resRotacion.data
        this.alertasVencimientos = resVencimientos.data.results || resVencimientos.data
      } catch (err) {
        this.error = 'Error al cargar los reportes analíticos'
        console.error(err)
      } finally {
        this.loading = false
      }
    },
    async exportarExcel() {
          try {
            const response = await api.get('carga-masiva/exportar-inventario/', {
              responseType: 'blob' // Fundamental para recibir archivos binarios
            })
            
            // Crear un enlace temporal para forzar la descarga
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const a = document.createElement('a')
            a.href = url
            a.download = 'inventario_clinica_maro.xlsx'
            document.body.appendChild(a)
            a.click()
            a.remove()
            window.URL.revokeObjectURL(url)
          } catch (err) {
            console.error('Error al exportar inventario:', err)
            throw new Error('Error al generar el archivo Excel de inventario.')
          }
        },
    
        // NUEVA ACCIÓN: Importar Inventario desde Excel
        async importarExcel(file) {
          this.loading = true
          try {
            const formData = new FormData()
            formData.append('file', file)
            
            const response = await api.post('carga-masiva/importar-excel/', formData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            })
            
            // Recargar datos tras una importación exitosa
            await this.fetchProductos()
            await this.fetchResumenAlertas()
            
            return response.data
          } catch (err) {
            const msg = err.response?.data?.error || 'Error al importar el archivo Excel.'
            console.error('Error en importarExcel:', msg)
            throw new Error(msg)
          } finally {
            this.loading = false
          }
        },
        async consumirKit(idKit, motivo) {
              try {
                const response = await api.post(`kits/${idKit}/consumir/`, { motivo_perdida: motivo })
                await this.fetchMovimientos()
                await this.fetchProductos()
                await this.fetchResumenAlertas()
                return response.data
              } catch (err) {
                const msg = err.response?.data?.error || 'Error al consumir el kit.'
                throw new Error(msg)
              }
            }
  }
})
