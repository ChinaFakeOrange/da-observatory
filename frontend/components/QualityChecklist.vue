<script setup lang="ts">
import type { QualityFlag } from '~/types'
import { ShieldCheck, AlertTriangle } from 'lucide-vue-next'
defineProps<{ flags: QualityFlag[] }>()
const { t } = useI18n()
</script>

<template>
  <div>
    <div class="cap">{{ t('quality.title') }}</div>
    <div v-for="(f, i) in flags" :key="i" class="row" :class="f.level">
      <AlertTriangle v-if="f.level === 'warn'" :size="15" class="ic" />
      <ShieldCheck v-else :size="15" class="ic ok" />
      <span>{{ t('quality.' + f.code, f.params) }}</span>
    </div>
  </div>
</template>

<style scoped>
.cap { font-size: 12px; color: var(--faint); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }
.row { display: flex; gap: 9px; padding: 9px 0; border-top: 1px solid var(--line-soft); font-size: 13px; color: var(--ink); }
.row.warn .ic { color: var(--warn); }
.ic { flex-shrink: 0; margin-top: 1px; }
.ic.ok { color: var(--accent); }
</style>
