<script setup>
import axios from 'axios';
import {onMounted, ref} from 'vue'

const now = ref(Date.now())
let version = ref("0.0.1")
let starting = ref(false)
let crawltimes = ref({})

onMounted(() => {
  getVersion()
  getCrawlTimes()
  runEveryXSeconds(getCrawlTimes, 15)
  runEveryXSeconds(getVersion, 300)
})

function getCrawlTimes() {
  axios.get('api/crawltimes/')
      .then(function (res) {
        starting = false;
        crawltimes.value = res.data.crawltimes;
        console.log('Laufzeiten abgerufen!');
      }, function () {
        console.log('Konnte Laufzeiten nicht abrufen!');
        //showDanger('Konnte Laufzeiten nicht abrufen!');
      });
}

function runEveryXSeconds(toRun, seconds) {
  setTimeout(function () {
    toRun();
    runEveryXSeconds();
  }, seconds * 1000);
}

function getVersion() {
  // ToDo
  console.log("Version: " + version.value);
}

function getTimestamp() {
  const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s);
  const d = new Date();

  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

// ToDo replace with actual functions
function startNow() {
  console.log("startNow()");
}

function getLists() {
  console.log("getLists()");
}

function getSettings() {
  console.log("getSettings()");
}

function getBlockedSites() {
  console.log("getBlockedSites()");
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
        Suchlauf gestartet: {{ getTimestamp(crawltimes.start_time) }} (Dauer: {{
          (now - crawltimes.start_time) / 1000
        }})
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
      Dauer des letzten Suchlaufs: {{ getTimestamp(crawltimes.total_time) }}
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
              aria-controls="offcanvasBottomHelp"
              @click="getBlockedSites()"><i class="bi bi-question-diamond"></i> Hilfe
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
