<script setup>
import {useStore} from 'vuex'
import {computed, onMounted, ref} from 'vue'
import {useToast} from 'vue-toastification'
import {Collapse, Offcanvas} from "bootstrap"
import axios from 'axios'

const store = useStore()
const toast = useToast()

onMounted(() => {
  getVersion()
  setInterval(getVersion, 300 * 1000)
  setInterval(updateCrawlTimes, 5 * 1000)
})

function updateCrawlTimes() {
  store.commit("getCrawlTimes")
}

const version = ref("")
const update = ref(false)
const helper_active = ref(false)
const helper_available = ref(false)

function openReleaseNotes() {
  window.open("https://github.com/rix1337/FeedCrawler/releases/latest", "_blank")
}

function getVersion() {
  axios.get(store.state.prefix + 'api/version/')
      .then(function (res) {
        version.value = res.data.version.ver
        console.info("%c FeedCrawler %c ".concat(version.value, " "), "color: white; background: #303030; font-weight: 700; font-size: 24px; font-family: Monospace;", "color: #303030; background: white; font-weight: 700; font-size: 24px; font-family: Monospace;");
        console.info("%c ❤ Projekt unterstützen %c ".concat("https://github.com/sponsors/rix1337 ❤", " "), "color: white; background: #dc3545; font-weight: 700;", "color: #dc3545; background: white; font-weight: 700;")
        update.value = res.data.version.update_ready
        store.commit('setDocker', res.data.version.docker)
        helper_active.value = res.data.version.helper_active
        if (helper_active.value) {
          axios.get("http://127.0.0.1:9666/")
              .then(function (res) {
                store.commit('setHelperActive', true)
                helper_available.value = (res.data === 'JDownloader')
                if (helper_available.value) {
                  store.commit('setHelperAvailable', true)
                  console.log("Click'n'Load des FeedCrawler Sponsors Helper ist verfügbar!")
                }
              })
        }
        if (update.value) {
          scrollingTitle("FeedCrawler - Update verfügbar! - ")
          console.log('Update steht bereit! Weitere Informationen unter https://github.com/rix1337/FeedCrawler/releases/latest')
          toast.info("Update steht bereit! Weitere Informationen unter:\nhttps://github.com/rix1337/FeedCrawler/releases/latest", {
            timeout: 15000,
            onClick: openReleaseNotes,
          })
        }
      }, function () {
        console.log('Konnte Version nicht abrufen!')
        toast.error('Konnte Version nicht abrufen!')
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

function countUp() {
  if (store.state.crawltimes.active) {
    setTimeout(() => {
      store.commit("setNow", Date.now())
      countUp()
    }, 1000)
  }
}

const currentDuration = computed(() => {
  countUp()
  let duration = store.state.misc.now - store.state.crawltimes.start_time
  if (duration < 0) {
    duration = 0
  }
  return new Date(duration).toISOString().substr(11, 8)
})

function startNow() {
  toast.info('Starte Suchlauf...')
  store.commit('setStarting', true)
  axios.post(store.state.prefix + 'api/start_now/')
      .then(function () {
        store.commit('setStarting', false)
        toast.success('Suchlauf gestartet!')
        console.log('Suchlauf gestartet!')
      }, function () {
        store.commit('setStarting', false)
        console.log('Konnte Suchlauf nicht starten!')
        toast.error('Konnte Suchlauf nicht starten!')
      })
}

function getLists() {
  getSettings()
  store.commit("getLists")
}

function getSettings() {
  store.commit("getSettings")
}

function showSiteStatusHelp() {
  let offcanvas = new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false})
  offcanvas.show()
  new Collapse(document.getElementById('collapseSiteStatus'), {
    toggle: true
  })
  sessionStorage.setItem('fromNav', '')
  window.location.href = "#collapseSiteStatus"
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

    <div v-if="store.state.crawltimes">
      <div v-if="store.state.crawltimes.active">
        Suchlauf gestartet: {{ getTimestamp(store.state.crawltimes.start_time) }} (Dauer:
        {{ currentDuration }})
      </div>
      <div v-if="!store.state.crawltimes.active">
        Start des nächsten Suchlaufs: {{ getTimestamp(store.state.crawltimes.next_start) }}
        <i id="start_now" v-tooltip="'Suchlauf direkt starten'" class="bi bi-skip-end-fill"
           v-if="!store.state.misc.starting"
           @click="startNow()"></i>
        <div v-if="store.state.misc.starting" class="spinner-border spinner-border-sm" role="status"></div>
      </div>
      <div v-if="store.state.crawltimes.next_f_run">
        Keine SF/FF-Suchläufe bis: {{ getTimestamp(store.state.crawltimes.next_f_run) }}
      </div>
      Dauer des letzten Suchlaufs: {{ store.state.crawltimes.total_time }}
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
              @click='getLists'><i class="bi bi-text-left"></i>
        Suchlisten
      </button>

      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomSettings"
              aria-controls="offcanvasBottomSettings"
              @click='getSettings'><i class="bi bi-gear"></i> Einstellungen
      </button>

      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomHelp"
              aria-controls="offcanvasBottomHelp"><i class="bi bi-question-diamond"></i> Hilfe
      </button>
    </div>

    <div>
      <button class="btn btn-outline-secondary" type="button" @click="showSiteStatusHelp">
        <i class="bi bi-bar-chart"></i>
        Seitenstatus
      </button>
      <a v-if="!helper_active" href="https://github.com/users/rix1337/sponsorship" target="_blank"
         v-tooltip="'Bitte unterstütze die Weiterentwicklung über eine aktive Github Sponsorship!'"
         class="btn btn-outline-danger"><i id="no-heart" class="bi bi-emoji-frown"></i> Kein
        aktiver
        Sponsor</a>
      <a v-else href="https://github.com/users/rix1337/sponsorship" target="_blank"
         v-tooltip="'Vielen Dank für die aktive Github Sponsorship!'"
         class="btn btn-outline-success"><i id="heart" class="bi bi-heart"></i> Aktiver
        Sponsor</a>
    </div>
  </div>


</template>
