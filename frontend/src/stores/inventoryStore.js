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
    }
  }
})