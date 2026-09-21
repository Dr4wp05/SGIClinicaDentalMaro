import { defineStore } from 'pinia'
import api from '@/api/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
    user: JSON.parse(localStorage.getItem('user_info') || 'null'),
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.rol || 'ASISTENTE',
    userName: (state) => state.user ? `${state.user.first_name || state.user.username}` : 'Usuario'
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const response = await api.post('token/', { username, password })
        this.token = response.data.access
        this.refreshToken = response.data.refresh
        this.user = response.data.user

        localStorage.setItem('access_token', this.token)
        localStorage.setItem('refresh_token', this.refreshToken)
        localStorage.setItem('user_info', JSON.stringify(this.user))

        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Credenciales inválidas o usuario inactivo.'
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.token = null
      this.refreshToken = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
      window.location.href = '/login'
    }
  }
})
