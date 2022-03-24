<script setup>
import axios from 'axios'
import {onMounted, ref} from 'vue'

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

onMounted(() => {
  getHostNames()
  getCrawlTimes()
  getLists()
  getSettings()
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

const lists = ref({})

function getLists() {
  axios.get(prefix + 'api/lists/')
      .then(function (res) {
        lists.value = res.data.lists
        console.log('Listen abgerufen!')
      }, function () {
        console.log('Konnte Listen nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Listen nicht abrufen!')
      })
}

const settings = ref({
  general: {
    myjd_user: '',
    myjd_pass: '',
    myjd_device: '',
    closed_myjd_tab: false,
    packages_per_myjd_page: 10,
    port: 9090,
  },
  mb: {
    quality: '1080p',
    search: 3,
    regex: false,
    imdb_score: 5,
    imdb_year: 2020,
    force_dl: false,
    retail_only: false,
    cutoff: false,
    hevc_retail: false,
    hoster_fallback: false,
  },
  f: {
    interval: 6,
    search: 3,
  },
  sj: {
    quality: '1080p',
    regex: false,
    retail_only: false,
    hevc_retail: false,
    hoster_fallback: false,
  },
  mbsj: {
    enabled: false,
    quality: '1080p',
    packs: false,
    source: '',
  },
  dj: {
    quality: '1080p',
    regex: false,
    hoster_fallback: false,
  },
  hosters: {
    rapidgator: true,
    turbobit: true,
    uploaded: true,
    zippyshare: true,
    oboom: true,
    ddl: true,
    filefactory: true,
    uptobox: true,
    onefichier: true,
    filer: true,
    nitroflare: true,
    ironfiles: true,
    k2s: true,
  },
  alerts: {
    pushbullet: "",
    pushover: "",
    telegram: "",
  },
  ombi: {
    url: "",
    api: ""
  },
  crawljobs: {
    autostart: false,
    subdir: false,
  }
})
const myjd_connection_error = ref(false)
const pageSizeMyJD = ref(3)

function getSettings() {
  axios.get(prefix + 'api/settings/')
      .then(function (res) {
        settings.value = res.data.settings
        console.log('Einstellungen abgerufen!')
        myjd_connection_error.value = !(settings.value.general.myjd_user && settings.value.general.myjd_device && settings.value.general.myjd_device)
        pageSizeMyJD.value = settings.value.general.packages_per_myjd_page
      }, function () {
        console.log('Konnte Einstellungen nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Einstellungen nicht abrufen!')
      })
}
</script>

<template>
  <main class="text-center">
    <!--- Main Items -->
    <Head :prefix=prefix :crawltimes=crawltimes :starting=starting :now=now></Head>
    <Log :prefix=prefix></Log>
    <MyJD :prefix=prefix></MyJD>
    <!-- <Notifications :prefix=prefix></Notifications> -->

    <!-- Off canvas Items -->
    <Settings :prefix=prefix :hostnames=hostnames :settings=settings :sjbl_enabled=sjbl_enabled
              :getSettings=getSettings></Settings>
    <Search :prefix=prefix></Search>
    <Lists :prefix=prefix :hostnames=hostnames :lists=lists :settings=settings :getLists=getLists></Lists>
    <Help :prefix=prefix :hostnames=hostnames :crawltimes=crawltimes :now=now></Help>
  </main>
</template>

<style>
@import './assets/base.css';
</style>
