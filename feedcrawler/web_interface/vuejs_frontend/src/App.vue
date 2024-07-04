<script setup>
import {useStore} from '@/main.js'
import {ref, watchEffect} from 'vue'
import "bootstrap/dist/css/bootstrap.min.css"
import 'bootstrap-icons/font/bootstrap-icons.css'
import "bootstrap"
import "@/assets/scss/app.scss"
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

const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
  isDarkMode.value = event.matches
})

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
}

watchEffect(() => {
  if (isDarkMode.value) {
    document.body.classList.add('dark')
  } else {
    document.body.classList.remove('dark')
  }
})
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
    <button class="btn btn-outline-secondary bg-dark m-3 text-warning" type="button" @click="toggleDarkMode()">
      <i v-if="isDarkMode" class="bi bi-sun"></i>
      <i v-else class="bi bi-moon-stars"></i>
    </button>
  </div>
</template>
