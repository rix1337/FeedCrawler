<script setup>
import {ref} from 'vue'

import "bootstrap/dist/css/bootstrap.min.css"
import 'bootstrap-icons/font/bootstrap-icons.css'

import Head from './components/_Head.vue'
import Log from './components/_Log.vue'
import MyJD from './components/_MyJD.vue'
import Notifications from './components/_Notifications.vue'
import Search from './components/Search.vue'
import Lists from './components/Lists.vue'
import Settings from './components/Settings.vue'
import Help from './components/Help.vue'

let prefix = ref('')

if (import.meta.env.MODE === 'development') {
  prefix = 'http://localhost:9090/feedcrawler/'
}
</script>

<template>
  <main class="text-center">
    <!--- Main Items -->
    <Head :prefix=prefix/>
    <Log/>
    <MyJD/>
    <Notifications/>

    <!--- Offcanvas Items -->
    <Search/>
    <Lists/>
    <Settings/>
    <Help/>
  </main>
</template>

<style>
@import './assets/base.css';
</style>
