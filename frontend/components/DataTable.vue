<script setup lang="ts">
import type { Row } from '~/types'
import { fmt, isBlank } from '~/utils/stats'
const props = defineProps<{ rows: Row[]; columns: string[]; limit?: number }>()
const view = computed(() => props.rows.slice(0, props.limit ?? 200))
</script>

<template>
  <div class="wrap">
    <table>
      <thead>
        <tr><th class="idx">#</th><th v-for="c in columns" :key="c">{{ c }}</th></tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in view" :key="i">
          <td class="idx mono">{{ i + 1 }}</td>
          <td v-for="c in columns" :key="c" :class="{ mono: typeof r[c] === 'number' }"
            :style="{ color: isBlank(r[c]) ? 'var(--faint)' : 'var(--ink)' }">
            {{ isBlank(r[c]) ? '—' : typeof r[c] === 'number' ? fmt(r[c] as number) : String(r[c]) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.wrap { overflow: auto; max-height: 560px; border-radius: 11px; border: 1px solid var(--line); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead { position: sticky; top: 0; } thead tr { background: var(--surface-2); }
th { padding: 11px 14px; font-weight: 600; text-align: left; white-space: nowrap; }
td { padding: 10px 14px; white-space: nowrap; }
tbody tr { border-top: 1px solid var(--line-soft); }
.idx { color: var(--faint); } .mono { font-family: var(--font-mono); }
</style>
