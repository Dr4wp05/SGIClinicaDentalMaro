<template>
  <aside class="w-64 bg-slate-900 min-h-screen text-slate-300 flex flex-col justify-between p-4 border-r border-slate-800">
    <div class="space-y-6">
      <!-- Brand Header -->
      <div class="flex items-center gap-3 px-2 pt-2">
        <div class="p-2 bg-teal-500/10 rounded-lg border border-teal-500/20 text-teal-400">
          <Activity class="w-6 h-6" />
        </div>
        <div>
          <h2 class="font-bold text-white tracking-wide text-sm">Clínica Maró</h2>
          <p class="text-xs text-slate-500">Gestión de Inventario</p>
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="space-y-1">
        <router-link
          to="/"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path === '/' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'"
        >
          <LayoutDashboard class="w-4 h-4" />
          Dashboard
        </router-link>

        <router-link
          to="/insumos"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path === '/insumos' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'"
        >
          <Package class="w-4 h-4" />
          Insumos y Lotes
        </router-link>

        <router-link
          to="/movimientos"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path === '/movimientos' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'"
        >
          <ArrowLeftRight class="w-4 h-4" />
          Movimientos
        </router-link>

        <router-link
          to="/ordenes-compra"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path === '/ordenes-compra' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'"
        >
          <ShoppingCart class="w-4 h-4" />
          Órdenes de Compra
        </router-link>

        <router-link
          to="/reportes"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path === '/reportes' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'"
        >
          <FileBarChart class="w-4 h-4" />
          Reportes
        </router-link>
      </nav>
    </div>

    <!-- Footer Profile Info & Logout -->
    <div class="pt-4 border-t border-slate-800 space-y-3">
      <div v-if="authStore.isAuthenticated" class="px-2 space-y-2">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-slate-200 truncate">{{ authStore.userName }}</p>
            <span class="inline-block px-1.5 py-0.5 text-[9px] font-semibold bg-teal-950 text-teal-300 border border-teal-800/60 rounded">
              {{ authStore.userRole }}
            </span>
          </div>
          <button
            @click="authStore.logout()"
            title="Cerrar Sesión"
            class="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>
      </div>

      <div class="px-2 text-[11px] text-slate-500 space-y-0.5">
        <p class="font-medium text-slate-400">Sistema Clínico v1.0</p>
        <p>Inacap - Proyecto Integrado</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { 
  Activity, 
  LayoutDashboard, 
  Package, 
  ArrowLeftRight, 
  ShoppingCart, 
  FileBarChart,
  LogOut
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
</script>
