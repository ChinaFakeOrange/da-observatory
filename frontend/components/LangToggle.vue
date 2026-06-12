<script setup lang="ts">
const { locale, setLocale } = useI18n()
</script>

<template>
  <div class="lang" role="group" aria-label="Language">
    <button :class="{ on: locale === 'zh' }" @click="setLocale('zh')">中</button>
    <button :class="{ on: locale === 'en' }" @click="setLocale('en')">EN</button>
  </div>
</template>

<style scoped>
.lang { display: inline-flex; border: 1px solid var(--line); border-radius: 9px; overflow: hidden; }
.lang button {
  padding: 8px 12px; background: var(--surface); border: none; font-size: 13px;
  color: var(--muted); font-weight: 600; min-width: 38px; transition: background 0.15s, color 0.15s;
}
.lang button.on { background: var(--accent); color: #fff; }
.lang button + button { border-left: 1px solid var(--line); }
</style>
