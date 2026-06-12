<script setup lang="ts">
import type { ColumnProfile } from '~/types'
import { fmt } from '~/utils/stats'
import { Hash, Type } from 'lucide-vue-next'
defineProps<{ profiles: ColumnProfile[] }>()
defineEmits<{ select: [string] }>()
const { t } = useI18n()
</script>

<template>
  <div class="wrap">
    <table>
      <thead>
        <tr>
          <th>{{ t('prof.field') }}</th><th>{{ t('prof.type') }}</th><th>{{ t('prof.missing') }}</th>
          <th>{{ t('prof.unique') }}</th><th class="dist">{{ t('prof.dist') }}</th><th class="right">{{ t('prof.summary') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in profiles" :key="p.name" @click="$emit('select', p.name)">
          <td class="name">{{ p.name }}</td>
          <td>
            <span class="chip" :class="p.type">
              <Hash v-if="p.type === 'numeric'" :size="11" /><Type v-else :size="11" />
              {{ p.type === 'numeric' ? t('type.numeric') : t('type.categorical') }}
            </span>
          </td>
          <td class="mono" :style="{ color: p.missingPct > 0 ? 'var(--warn)' : 'var(--faint)' }">{{ (p.missingPct * 100).toFixed(1) }}%</td>
          <td class="mono muted">{{ p.unique }}</td>
          <td><MiniDist :profile="p" /></td>
          <td class="right mono small">
            {{ p.type === 'numeric' ? `μ ${fmt(p.mean)} · σ ${fmt(p.std)}` : t('prof.top', { v: p.top?.[0]?.k ?? '—' }) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.wrap { overflow: hidden; border-radius: 11px; border: 1px solid var(--line); }
table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
thead tr { background: var(--surface-2); color: var(--faint); text-align: left; font-size: 12px; }
th { padding: 11px 14px; font-weight: 600; }
th.dist { width: 150px; } th.right, td.right { text-align: right; }
tbody tr { border-top: 1px solid var(--line-soft); cursor: pointer; transition: background 0.12s; }
tbody tr:hover { background: var(--surface-2); }
td { padding: 10px 14px; vertical-align: middle; }
td.name { font-weight: 600; }
.mono { font-family: var(--font-mono); } .muted { color: var(--muted); } .small { font-size: 12px; color: var(--muted); }
.chip { display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px; border-radius: 20px; font-size: 11.5px; font-weight: 600; }
.chip.numeric { background: var(--accent-soft); color: var(--accent-deep); }
.chip.categorical { background: #f1ecfa; color: #5b3fa8; }
</style>
