<template>
  <div class="flex min-h-screen bg-slate-50">
    <Sidebar v-if="$route.path !== '/login'" />
    <main class="flex-1 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
</script>
