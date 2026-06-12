<script setup lang="ts">
defineProps<{ label: string; modelValue: string; options: string[]; blankLabel?: string }>()
defineEmits<{ 'update:modelValue': [string] }>()
</script>

<template>
  <label class="sel">
    <span>{{ label }}</span>
    <select :value="modelValue" @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)">
      <option v-for="o in options" :key="o" :value="o">{{ o === '' ? (blankLabel ?? '—') : o }}</option>
    </select>
  </label>
</template>

<style scoped>
.sel { display: flex; flex-direction: column; gap: 5px; font-size: 12px; color: var(--faint); font-weight: 600; }
select {
  padding: 8px 11px; border-radius: 8px; border: 1px solid var(--line);
  background: var(--surface); font-size: 13px; color: var(--ink); font-weight: 500; min-width: 120px;
}
</style>
