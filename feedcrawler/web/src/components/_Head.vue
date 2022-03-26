<script setup>
import {useStore} from 'vuex'
import {onMounted, ref} from 'vue'
import axios from 'axios'

const store = useStore()

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
  axios.get(store.state.prefix + 'api/version/')
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
  let duration = store.state.misc.now - ms
  return new Date(duration).toISOString().substr(11, 8)
}

function startNow() {
  // ToDo migrate to vue
  //showInfoLong("Starte Suchlauf...")
  store.commit('setStarting', true)
  axios.post(store.state.prefix + 'api/start_now/')
      .then(function () {
        // ToDo migrate to vue
        //$(".alert-info").slideUp(1500)
        console.log('Suchlauf gestartet!')
      }, function () {
        store.commit('setStarting', false)
        console.log('Konnte Suchlauf nicht starten!')
        // ToDo migrate to vue
        //showDanger('Konnte Suchlauf nicht starten!')
        //(".alert-info").slideUp(1500)
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

    <div v-if="store.state.crawltimes">
      <div v-if="store.state.crawltimes.active">
        Suchlauf gestartet: {{ getTimestamp(store.state.crawltimes.start_time) }} (Dauer:
        {{ getDuration(store.state.crawltimes.start_time) }})
      </div>
      <div v-if="!store.state.crawltimes.active">
        Start des nächsten Suchlaufs: {{ getTimestamp(store.state.crawltimes.next_start) }}
        <i id="start_now" class="bi bi-skip-end-fill" title="Suchlauf direkt starten" data-toggle="tooltip"
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
              @click='store.commit("getLists")'><i class="bi bi-text-left"></i> Suchlisten
      </button>

      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomSettings"
              aria-controls="offcanvasBottomSettings"
              @click='store.commit("getSettings")'><i class="bi bi-gear"></i> Einstellungen
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
