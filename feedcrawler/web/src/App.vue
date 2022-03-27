<script setup>
import {useStore} from 'vuex'

const store = useStore()

if (import.meta.env.MODE === 'development') {
  store.commit("setPrefix", 'http://localhost:9090/feedcrawler/')
}

// ToDo migrate bootstrap tooltips to vue
//$(function () {
//    $('[data-toggle="tooltip"]').tooltip()
//})
</script>

<template>
  <router-view/>
</template>
