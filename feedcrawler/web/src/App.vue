<script setup>
import "bootstrap/dist/css/bootstrap.min.css"
import "bootstrap"
import 'bootstrap-icons/font/bootstrap-icons.css'

import Head from './components/_Head.vue'
import Log from './components/_Log.vue'
import MyJD from './components/_MyJD.vue'
import Search from './components/Search.vue'
import Lists from './components/Lists.vue'</script>

<template>
  <main class="text-center">
    <!--- Visible Items -->
    <Head/>
    <Log/>
    <MyJD/>

    <!--- Offcanvas Items -->
    <Search/>
    <Lists/>

    <!-- Disabled for now

    <Settings/>
    <Help/>
    <Notifications/>
     -->

  </main>
</template>

<style>
@import './assets/base.css';
</style>
