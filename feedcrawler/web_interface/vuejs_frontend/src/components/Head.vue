<script setup>
import {useStore} from '@/main.js'
import {computed, inject, onMounted, ref} from 'vue'
import {Collapse, Offcanvas} from "bootstrap"
import axios from 'axios'

const store = useStore()
const toast = inject('toast')

onMounted(() => {
  getVersion()
  setInterval(getVersion, 300 * 1000)
  setInterval(updateCrawlTimes, 10 * 1000)
})

function updateCrawlTimes() {
  store.getCrawlTimes()
}

const version = ref("")
const update = ref(false)

function openReleaseNotes() {
  window.open("https://github.com/rix1337/FeedCrawler/releases/latest", "_blank")
}

function getVersion() {
  axios.get('api/version/')
      .then(function (res) {
        version.value = res.data.version.ver
        console.info("%c FeedCrawler %c ".concat(version.value, " "), "color: white; background: #303030; font-weight: 700; font-size: 24px; font-family: Monospace;", "color: #303030; background: white; font-weight: 700; font-size: 24px; font-family: Monospace;");
        console.info("%c ❤ Projekt unterstützen %c ".concat("https://github.com/sponsors/rix1337 ❤", " "), "color: white; background: #dc3545; font-weight: 700;", "color: #dc3545; background: white; font-weight: 700;")
        update.value = res.data.version.update_ready
        store.setDocker(res.data.version.docker)
        store.setHelperActive(res.data.version.helper_active)
        if (update.value) {
          scrollingTitle("FeedCrawler - Update verfügbar! - ")
          console.log('Update steht bereit! Weitere Informationen unter https://github.com/rix1337/FeedCrawler/releases/latest')
          toast.info("Update steht bereit! Hier klicken für weitere Informationen...", {
            duration: 15000,
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
  if (store.crawltimes.active) {
    setTimeout(() => {
      store.setNow(Date.now())
      countUp()
    }, 1000)
  }
}

const currentDuration = computed(() => {
  countUp()
  let duration = store.misc.now - store.crawltimes.start_time
  if (duration < 0) {
    duration = 0
  }
  return new Date(duration).toISOString().substr(11, 8)
})

function startNow() {
  toast.info('Starte Suchlauf...')
  store.setStarting(true)
  axios.post('api/start_now/')
      .then(function () {
        store.setStarting(false)
        toast.success('Suchlauf gestartet!')
        console.log('Suchlauf gestartet!')
      }, function () {
        store.setStarting(false)
        console.log('Konnte Suchlauf nicht starten!')
        toast.error('Konnte Suchlauf nicht starten!')
      })
}

function getBlockedSites() {
  store.getBlockedSites()
}

function getLists() {
  getSettings()
  store.getLists()
}

function getSettings() {
  store.getSettings()
}

function showSiteStatusHelp() {
  getBlockedSites()
  new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false}).show()
  new Collapse(document.getElementById('collapseSiteStatus'), {
    toggle: true
  })
}
</script>


<template>
  <div class="container">
    <div class="row my-3">
      <div class="col-md-6 offset-md-3">
        <div class="card text-center shadow my-3">
          <div class="card-header">
            <h1>
              <i class="bi bi-reception-4"></i> FeedCrawler
            </h1>
            <p>Projekt von
              <a href="https://github.com/rix1337/FeedCrawler/releases/latest" target="_blank">RiX</a> {{ version }}
              <span v-if="update"> (Update verfügbar!)</span>
            </p>
          </div>
          <div class="card-body">
            <div v-if="Object.keys(store.crawltimes).length !== 0">
              <div v-if="store.crawltimes.active&& !isNaN(store.crawltimes.start_time)">
                Suchlauf gestartet: {{ getTimestamp(store.crawltimes.start_time) }} (Dauer:
                {{ currentDuration }})
              </div>
              <div v-if="!store.crawltimes.active&& !isNaN(store.crawltimes.next_start)">
                Start des nächsten Suchlaufs: {{ getTimestamp(store.crawltimes.next_start) }}
                <i v-if="!store.misc.starting" v-tippy="'Suchlauf direkt starten'"
                   class="bi bi-skip-end-fill text-primary"
                   @click="startNow()"></i>
                <div v-if="store.misc.starting" class="spinner-border spinner-border-sm" role="status"></div>
              </div>
              <div
                  v-if="store.crawltimes.next_cloudflare_run && store.hostnames.cloudflare_shorthands !== 'Nicht gesetzt!'">
                Wartezeit ({{ store.hostnames.cloudflare_shorthands }}) bis: {{
                  getTimestamp(store.crawltimes.next_cloudflare_run)
                }}
              </div>
              <div v-if="typeof store.crawltimes.total_time === 'string'">
                Dauer des letzten Suchlaufs: {{ store.crawltimes.total_time }}
              </div>
            </div>
            <div v-else>
              <div class="spinner-border spinner-border-sm" role="status"></div>
            </div>

            <div class="border-top mt-2"></div>

            <div class="row justify-content-center mt-2">
              <div v-if="store.hostnames.search !== 'Nicht gesetzt!'" class="col-md-auto p-1">
                <button aria-controls="offcanvasBottomSearch" class="btn btn-outline-primary"
                        data-bs-target="#offcanvasBottomSearch"
                        data-bs-toggle="offcanvas"
                        type="button"><i class="bi bi-search"></i> Web-Suche
                </button>
              </div>

              <div class="col-md-auto p-1">
                <button aria-controls="offcanvasBottomLists" class="btn btn-outline-primary"
                        data-bs-target="#offcanvasBottomLists"
                        data-bs-toggle="offcanvas"
                        type="button"
                        @click='getLists'><i class="bi bi-text-left"></i>
                  Feed-Suche
                </button>
              </div>

              <div class="col-md-auto p-1">
                <button aria-controls="offcanvasBottomSettings" class="btn btn-outline-primary"
                        data-bs-target="#offcanvasBottomSettings"
                        data-bs-toggle="offcanvas"
                        type="button"
                        @click='getSettings'><i class="bi bi-gear"></i> Einstellungen
                </button>
              </div>

              <div class="col-md-auto p-1">
                <button aria-controls="offcanvasBottomHelp" class="btn btn-outline-primary"
                        data-bs-target="#offcanvasBottomHelp"
                        data-bs-toggle="offcanvas"
                        type="button"
                        @click='getBlockedSites'><i class="bi bi-question-diamond"></i> Hilfe
                </button>
              </div>
            </div>

            <div class="row justify-content-center">
              <div class="col-md-auto p-1">
                <button
                    :class="{ 'btn-outline-success': store.misc.no_site_blocked === 0,
                              'btn-outline-warning': store.misc.no_site_blocked === 1,
                              'btn-outline-danger': store.misc.no_site_blocked === 2
                    }"
                    class="btn"
                    type="button" @click="showSiteStatusHelp">
                  <i class="bi bi-bar-chart"></i>
                  Seitenstatus
                </button>
              </div>

              <div class="col-md-auto p-1">
                <a v-if="!store.misc.helper_active"
                   v-tippy="'Bitte unterstütze die Weiterentwicklung über eine aktive GitHub Sponsorship!'"
                   class="btn btn-outline-danger"
                   href="https://github.com/users/rix1337/sponsorship"
                   target="_blank"><i id="no-heart" class="bi bi-emoji-frown"></i> Kein
                  aktiver
                  Sponsor</a>
                <a v-else v-tippy="'Vielen Dank für die aktive GitHub Sponsorship!'" class="btn btn-outline-success"
                   href="https://github.com/users/rix1337/sponsorship"
                   target="_blank"><i id="heart" class="bi bi-heart"></i> Aktiver
                  Sponsor</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
