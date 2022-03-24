<script setup>
import axios from 'axios'
import {onMounted, ref} from 'vue'

import "bootstrap/dist/css/bootstrap.min.css"
import 'bootstrap-icons/font/bootstrap-icons.css'
import "bootstrap"

import Head from './components/_Head.vue'
import Log from './components/_Log.vue'
import MyJD from './components/_MyJD.vue'

import Help from './components/Help.vue'

onMounted(() => {
  getHostNames()
  getCrawlTimes()
  setInterval(updateTime, 1000)
  setInterval(getCrawlTimes, 5 * 1000)
})

let prefix = ''
if (import.meta.env.MODE === 'development') {
  prefix = 'http://localhost:9090/feedcrawler/'
}

const hostnames = ref({
  sj: 'Nicht gesetzt!',
  dj: 'Nicht gesetzt!',
  sf: 'Nicht gesetzt!',
  by: 'Nicht gesetzt!',
  fx: 'Nicht gesetzt!',
  nk: 'Nicht gesetzt!',
  ww: 'Nicht gesetzt!',
  bl: 'Nicht gesetzt!',
  s: 'Nicht gesetzt!',
  sjbl: 'Nicht gesetzt!'
})
const sjbl_enabled = ref(true)

function getHostNames() {
  axios.get(prefix + 'api/hostnames/')
      .then(function (res) {
        hostnames.value = res.data.hostnames
        let not_set = 'Nicht gesetzt!'
        sjbl_enabled.value = !((hostnames.value.bl === not_set && hostnames.value.s !== not_set) || (hostnames.value.bl !== not_set && hostnames.value.s === not_set))
        console.log('Hostnamen abgerufen!')
      }, function () {
        console.log('Konnte Hostnamen nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Hostnamen nicht abrufen!')
      });
}

const starting = ref(false)
const crawltimes = ref({})

function getCrawlTimes() {
  axios.get(prefix + 'api/crawltimes/')
      .then(function (res) {
        starting.value = false
        crawltimes.value = res.data.crawltimes
        console.log('Laufzeiten abgerufen!')
      }, function () {
        console.log('Konnte Laufzeiten nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Laufzeiten nicht abrufen!')
      })
}

const now = ref(Date.now())

function updateTime() {
  now.value = Date.now()
}
</script>

<template>
  <main class="text-center">
    <!--- Main Items -->
    <Head :prefix=prefix :crawltimes=crawltimes :starting=starting :now=now></Head>
    <Log :prefix=prefix></Log>
    <MyJD :prefix=prefix></MyJD>
    <!-- <Notifications :prefix=prefix></Notifications>

    Off canvas Items
    <Search :prefix=prefix></Search>
    <Lists :prefix=prefix></Lists>
    <Settings :prefix=prefix></Settings> -->
    <Help :prefix=prefix :hostnames=hostnames :crawltimes=crawltimes :now=now></Help>
  </main>
</template>

<style>
@import './assets/base.css';
</style>
