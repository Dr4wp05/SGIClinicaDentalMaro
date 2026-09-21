<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-100 p-4">
    <div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-200">
      <div class="text-center mb-6">
        <h1 class="text-2xl font-bold text-slate-800">Clínica Dental MARÓ</h1>
        <p class="text-xs text-slate-500 mt-1">Sistema de Gestión de Inventario y Abastecimiento</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-600 mb-1">Nombre de Usuario</label>
          <input 
            v-model="username" 
            type="text" 
            required 
            placeholder="Ej: admin_maro"
            class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-600 mb-1">Contraseña</label>
          <input 
            v-model="password" 
            type="password" 
            required 
            placeholder="••••••••"
            class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div v-if="authStore.error" class="bg-red-50 border border-red-200 text-red-600 text-xs p-3 rounded-lg text-center">
          {{ authStore.error }}
        </div>

        <button 
          type="submit" 
          :disabled="authStore.loading"
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg text-sm transition shadow-sm disabled:opacity-50"
        >
          {{ authStore.loading ? 'Iniciando sesión...' : 'Ingresar al Sistema' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const username = ref('')
const password = ref('')
const authStore = useAuthStore()
const router = useRouter()

const handleLogin = async () => {
  const exito = await authStore.login(username.value, password.value)
  if (exito) {
    router.push('/')
  }
}
</script>
