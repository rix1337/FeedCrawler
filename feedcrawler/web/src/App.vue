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
        sjbl_enabled.value = !((hostnames.bl.value === not_set && hostnames.s.value !== not_set) || (hostnames.bl.value !== not_set && hostnames.s.value === not_set))
        console.log('Hostnamen abgerufen!')
      }, function () {
        console.log('Konnte Hostnamen nicht abrufen!')
        showDanger('Konnte Hostnamen nicht abrufen!')
      });
}
</script>

<template>
  <main class="text-center">
    <!--- Main Items -->
    <Head :prefix=prefix></Head>
    <Log :prefix=prefix></Log>
    <MyJD :prefix=prefix></MyJD>
    <!-- <Notifications :prefix=prefix></Notifications>

    Off canvas Items
    <Search :prefix=prefix></Search>
    <Lists :prefix=prefix></Lists>
    <Settings :prefix=prefix></Settings> -->
    <Help :prefix=prefix :hostnames=hostnames></Help>
  </main>
</template>

<style>
@import './assets/base.css';
</style>
