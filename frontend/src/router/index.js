import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import InsumosView from '@/views/InsumosView.vue'
import MovimientosView from '@/views/MovimientosView.vue'
import OrdenesCompraView from '@/views/OrdenesCompraView.vue'
import ReportesView from '@/views/ReportesView.vue'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true, roles: ['ADMINISTRADOR', 'BODEGA', 'DENTISTA', 'ASISTENTE'] }
    },
    {
      path: '/insumos',
      name: 'insumos',
      component: InsumosView,
      meta: { requiresAuth: true, roles: ['ADMINISTRADOR', 'BODEGA'] }
    },
    {
      path: '/movimientos',
      name: 'movimientos',
      component: MovimientosView,
      meta: { requiresAuth: true, roles: ['ADMINISTRADOR', 'BODEGA', 'DENTISTA', 'ASISTENTE'] }
    },
    {
      path: '/ordenes-compra',
      name: 'ordenes-compra',
      component: OrdenesCompraView,
      meta: { requiresAuth: true, roles: ['ADMINISTRADOR', 'BODEGA'] }
    },
    {
      path: '/reportes',
      name: 'reportes',
      component: ReportesView,
      meta: { requiresAuth: true, roles: ['ADMINISTRADOR', 'BODEGA'] }
    }
  ]
})

// Navigation Guard: Proteger rutas según autenticación y roles RBAC
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const userInfo = JSON.parse(localStorage.getItem('user_info') || 'null')
  const isAuth = !!token
  const userRole = userInfo?.rol || 'ASISTENTE'

  if (to.meta.requiresAuth && !isAuth) {
    next('/login')
  } else if (to.path === '/login' && isAuth) {
    next('/')
  } else if (to.meta.roles && !to.meta.roles.includes(userRole)) {
    // Si no tiene el rol necesario, redirigir al Dashboard principal
    next('/')
  } else {
    next()
  }
})

export default router
