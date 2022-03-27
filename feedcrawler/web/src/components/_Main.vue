<script setup>
import {useStore} from 'vuex'
import {onMounted} from 'vue'

import "bootstrap/dist/css/bootstrap.min.css"
import 'bootstrap-icons/font/bootstrap-icons.css'
import "bootstrap"

import Head from './Head.vue'
import Log from './Log.vue'
import MyJD from './MyJD.vue'

import Search from './Search.vue'
import Lists from './Lists.vue'
import Settings from './Settings.vue'
import Help from './Help.vue'

const store = useStore()

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
@import '.././assets/base.css';
</style>
