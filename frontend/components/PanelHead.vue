<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <div class="ph">
    <h2>{{ title }}</h2>
    <p v-if="subtitle">{{ subtitle }}</p>
  </div>
</template>

<style scoped>
.ph { margin-bottom: 16px; }
h2 { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: 18px; letter-spacing: -0.01em; color: var(--ink); }
p { margin: 4px 0 0; color: var(--muted); font-size: 13.5px; }
</style>
