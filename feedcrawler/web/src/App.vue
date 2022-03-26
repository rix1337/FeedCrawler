<script setup>
import {useStore} from 'vuex'
import {onMounted} from 'vue'
import "bootstrap/dist/css/bootstrap.min.css"
import 'bootstrap-icons/font/bootstrap-icons.css'
import "bootstrap"

import Head from './components/_Head.vue'
import Log from './components/_Log.vue'
import MyJD from './components/_MyJD.vue'

import Search from './components/Search.vue'
import Lists from './components/Lists.vue'
import Settings from './components/Settings.vue'
import Help from './components/Help.vue'

const store = useStore()

if (import.meta.env.MODE === 'development') {
  store.commit("setPrefix", 'http://localhost:9090/feedcrawler/')
}

store.commit("setNow", Date.now())
store.commit("getCrawlTimes")
store.commit("getHostNames")

onMounted(() => {
  setInterval(store.commit("setNow", Date.now()), 1000)
  setInterval(store.commit("getCrawlTimes"), 5 * 1000)
})
</script>

<template>
  <main class="text-center">
    <!--- Main Items -->
    <Head/>
    <Log/>
    <MyJD/>
    <!-- <Notifications/> -->

    <!-- Off canvas Items -->
    <Settings/>
    <Search/>
    <Lists/>
    <Help/>
  </main>
</template>

<style>
@import './assets/base.css';
</style>
