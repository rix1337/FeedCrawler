<script setup>
import {useStore} from '@/main.js'
import "bootstrap/dist/css/bootstrap.min.css"
import 'bootstrap-icons/font/bootstrap-icons.css'
import "bootstrap"
import "@/assets/scss/app.scss"
import {useDark, useToggle} from "@vueuse/core"

import Head from './components/Head.vue'
import Log from './components/Log.vue'
import MyJD from './components/MyJD.vue'
import Search from './components/Search.vue'
import Lists from './components/Lists.vue'
import Settings from './components/Settings.vue'
import Help from './components/Help.vue'

const store = useStore()

store.setNow(Date.now())
store.getCrawlTimes()
store.getHostNames()
store.getBlockedSites()

const isDark = useDark()
const toggleDark = useToggle(isDark)
</script>

<template>
  <main>
    <!--- Main Items -->
    <Head/>
    <Log/>
    <MyJD/>
    <!-- Offcanvas Items -->
    <Settings/>
    <Search/>
    <Lists/>
    <Help/>
  </main>
  <div class="sticky-bottom float-end">
    <button type="button" class="btn btn-outline-secondary bg-dark m-3 text-warning" @click="toggleDark()">
      <i v-if="isDark" class="bi bi-sun"></i>
      <i v-else class="bi bi-moon-stars"></i>
    </button>
  </div>
</template>
