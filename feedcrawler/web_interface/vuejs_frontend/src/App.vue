<script setup>
import "@/assets/scss/app.scss"
import {useStore} from "vuex"
import {useDark, useToggle} from "@vueuse/core"

const store = useStore()
const isDark = useDark()
const toggleDark = useToggle(isDark)
</script>

<template>
  <router-view/>

  <div class="sticky-bottom float-end">
    <button type="button" class="btn btn-outline-light bg-dark m-3" @click="toggleDark()">
      <i v-if="isDark" class="bi bi-sun"></i>
      <i v-else class="bi bi-moon-stars"></i>
    </button>
  </div>
</template>
