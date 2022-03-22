<script setup>
import {ref} from 'vue'

import "bootstrap/dist/css/bootstrap.min.css"
import 'bootstrap-icons/font/bootstrap-icons.css'

import Head from './components/_Head.vue'

let prefix = ref('')

if (import.meta.env.MODE === 'development') {
  prefix = 'http://localhost:9090/feedcrawler/'
}
</script>

<template>
  <main class="text-center">
    <!--- Main Items -->
    <Head :prefix=prefix></Head>
    <!-- <Log :prefix=prefix></Log>
    <MyJD :prefix=prefix></MyJD>
    <Notifications :prefix=prefix></Notifications>

    Off canvas Items
    <Search :prefix=prefix></Search>
    <Lists :prefix=prefix></Lists>
    <Settings :prefix=prefix></Settings>
    <Help :prefix=prefix></Help> -->
  </main>
</template>

<style>
@import './assets/base.css';
</style>
