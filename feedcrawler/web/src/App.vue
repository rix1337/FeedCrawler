<script setup>
import {useStore} from 'vuex'
import {onMounted} from 'vue'
import axios from 'axios'
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

onMounted(() => {
  getHostNames()
  getCrawlTimes()
  setInterval(store.commit("setNow"), 1000)
  setInterval(getCrawlTimes, 5 * 1000)
})

if (import.meta.env.MODE === 'development') {
  store.commit("setPrefix", 'http://localhost:9090/feedcrawler/')
}

function getHostNames() {
  axios.get(store.state.prefix + 'api/hostnames/')
      .then(function (res) {
        store.commit('setHostNames', res.data.hostnames)
        let not_set = 'Nicht gesetzt!'
        store.commit("setSjBlEnabled", !((store.state.hostnames.bl === not_set && store.state.hostnames.s !== not_set) || (store.state.hostnames.bl !== not_set && store.state.hostnames.s === not_set)))
        console.log('Hostnamen abgerufen!')
      }, function () {
        console.log('Konnte Hostnamen nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Hostnamen nicht abrufen!')
      })
}

function getCrawlTimes() {
  axios.get(store.state.prefix + 'api/crawltimes/')
      .then(function (res) {
        store.commit('setStarting', false)
        store.commit("setCrawlTimes", res.data.crawltimes)
        console.log('Laufzeiten abgerufen!')
      }, function () {
        console.log('Konnte Laufzeiten nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Laufzeiten nicht abrufen!')
      })
}
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
