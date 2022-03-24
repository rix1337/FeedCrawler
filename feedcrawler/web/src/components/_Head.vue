<script setup>
import axios from 'axios'
import {onMounted, ref} from 'vue'

const props = defineProps({
  prefix: String,
  crawltimes: Object,
  starting: Boolean,
  now: Number
})

onMounted(() => {
  getVersion()
  setInterval(getVersion, 300 * 1000)
})

const version = ref("")
const update = ref(false)
const docker = ref(false)
const helper_active = ref(false)
const helper_available = ref(false)

function getVersion() {
  axios.get(props.prefix + 'api/version/')
      .then(function (res) {
        version.value = res.data.version.ver
        console.log('Dies ist der FeedCrawler ' + version.value + ' von https://github.com/rix1337')
        update.value = res.data.version.update_ready
        docker.value = res.data.version.docker
        helper_active.value = res.data.version.helper_active
        if (helper_active.value) {
          axios.get("http://127.0.0.1:9666/")
              .then(function (res) {
                helper_available.value = (res.data === 'JDownloader')
                if (helper_available.value) {
                  console.log("Click'n'Load des FeedCrawler Sponsors Helper ist verfügbar!")
                }
              })
        }
        if (update.value) {
          scrollingTitle("FeedCrawler - Update verfügbar! - ")
          console.log('Update steht bereit! Weitere Informationen unter https://github.com/rix1337/FeedCrawler/releases/latest')
          // ToDo migrate to vue
          //showInfo('Update steht bereit! Weitere Informationen unter <a href="https://github.com/rix1337/FeedCrawler/releases/latest" target="_blank">github.com</a>.')
        }
        console.log('Version abgerufen!')
      }, function () {
        console.log('Konnte Version nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Version nicht abrufen!')
      })
}

function scrollingTitle(titleText) {
  document.title = titleText
  setTimeout(function () {
    scrollingTitle(titleText.substr(1) + titleText.substr(0, 1))
  }, 200)
}

function getTimestamp(ms) {
  const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s)
  const d = new Date(ms)

  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function getDuration(ms) {
  let duration = now.value - ms
  return new Date(duration).toISOString().substr(11, 8)
}

function startNow() {
  // ToDo migrate to vue
  //showInfoLong("Starte Suchlauf...")
  starting.value = true
  axios.post(props.prefix + 'api/start_now/')
      .then(function () {
        // ToDo migrate to vue
        //$(".alert-info").slideUp(1500)
        console.log('Suchlauf gestartet!')
      }, function () {
        starting.value = false
        console.log('Konnte Suchlauf nicht starten!')
        // ToDo migrate to vue
        //showDanger('Konnte Suchlauf nicht starten!')
        //(".alert-info").slideUp(1500)
      })
}

// ToDo move this to Lists.vue
const lists = ref({})

function getLists() {
  axios.get(props.prefix + 'api/lists/')
      .then(function (res) {
        lists.value = res.data.lists
        console.log('Listen abgerufen!')
      }, function () {
        console.log('Konnte Listen nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Listen nicht abrufen!')
      })
}

const settings = ref({})
const myjd_connection_error = ref(false)
// ToDo hand this over from Settings.vue to _MyJD.vue
const pageSizeMyJD = ref(3)

// ToDo move this to Settings.vue
function getSettings() {
  axios.get(props.prefix + 'api/settings/')
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
  <div id="head" class="container app col">
    <h1>
      <i class="bi bi-reception-4"></i> FeedCrawler</h1>
    <p id="headtitle">Projekt von
      <a href="https://github.com/rix1337/FeedCrawler/releases/latest" target="_blank">RiX</a> {{ version }}
      <span v-if="update"> (Update verfügbar!)</span>
    </p>

    <div class="border-top"></div>

    <div v-if="crawltimes">
      <div v-if="crawltimes.active">
        Suchlauf gestartet: {{ getTimestamp(crawltimes.start_time) }} (Dauer: {{ getDuration(crawltimes.start_time) }})
      </div>
      <div v-if="!crawltimes.active">
        Start des nächsten Suchlaufs: {{ getTimestamp(crawltimes.next_start) }}
        <i id="start_now" class="bi bi-skip-end-fill" title="Suchlauf direkt starten" data-toggle="tooltip"
           v-if="!starting"
           @click="startNow()"></i>
        <div v-if="starting" class="spinner-border spinner-border-sm" role="status"></div>
      </div>
      <div v-if="crawltimes.next_f_run">
        Keine SF/FF-Suchläufe bis: {{ getTimestamp(crawltimes.next_f_run) }}
      </div>
      Dauer des letzten Suchlaufs: {{ crawltimes.total_time }}
    </div>

    <div class="border-top"></div>

    <div>
      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomSearch"
              aria-controls="offcanvasBottomSearch"><i class="bi bi-search"></i> Web-Suche
      </button>

      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomLists"
              aria-controls="offcanvasBottomLists"
              @click="getLists()"><i class="bi bi-text-left"></i> Suchlisten
      </button>

      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomSettings"
              aria-controls="offcanvasBottomSettings"
              @click="getSettings()"><i class="bi bi-gear"></i> Einstellungen
      </button>

      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomHelp"
              aria-controls="offcanvasBottomHelp"><i class="bi bi-question-diamond"></i> Hilfe
      </button>
    </div>

    <div>
      <a v-if="!helper_active" href="https://github.com/users/rix1337/sponsorship" target="_blank"
         title="Bitte unterstütze die Weiterentwicklung über eine aktive Github Sponsorship!"
         class="btn btn-outline-danger" data-toggle="tooltip"><i id="no-heart" class="bi bi-emoji-frown"></i> Kein
        aktiver
        Sponsor</a>
      <a v-if="helper_active" href="https://github.com/users/rix1337/sponsorship" target="_blank"
         title="Vielen Dank für die aktive Github Sponsorship!"
         class="btn btn-outline-success" data-toggle="tooltip"><i id="heart" class="bi bi-heart"></i> Aktiver
        Sponsor</a>
    </div>
  </div>


</template>
