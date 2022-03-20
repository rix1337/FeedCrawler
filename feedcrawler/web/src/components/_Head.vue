<script>
export default {
  // ToDo replace with actual data calls
  data() {
    return {
      now: Date.now(),
      version: "0.0.1",
      crawltimes: {
        active: true,
        start_time: "123000",
        next_start: "234000",
        total_time: "90000",
        next_f_run: "345000",
      }
    }
  }, methods: {
    // ToDo replace with actual functions
    startNow() {
      console.log("startNow()");
    },
    getLists() {
      console.log("getLists()");
    },
    getSettings() {
      console.log("getSettings()");
    },
    getBlockedSites() {
      console.log("getBlockedSites()");
    }
  }
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

    <!-- ToDo refactor removed AngularJS filters to vue -->
    <div v-if="crawltimes">
      <div v-if="crawltimes.active">
        Suchlauf gestartet: {{ crawltimes.start_time }} (Dauer: {{
          (now - crawltimes.start_time) / 1000
        }})
      </div>
      <div v-if="!crawltimes.active">
        Start des nächsten Suchlaufs: {{ crawltimes.next_start }}
        <i id="start_now" class="bi bi-skip-end-fill" title="Suchlauf direkt starten" data-toggle="tooltip"
           v-if="!starting"
           @click="startNow()"></i>
        <div v-if="starting" class="spinner-border spinner-border-sm" role="status"></div>
      </div>
      <div v-if="crawltimes.next_f_run">
        Keine SF/FF-Suchläufe bis: {{ crawltimes.next_f_run }}
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
              v-on:click="getLists()"><i class="bi bi-text-left"></i> Suchlisten
      </button>

      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomSettings"
              aria-controls="offcanvasBottomSettings"
              v-on:click="getSettings()"><i class="bi bi-gear"></i> Einstellungen
      </button>

      <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasBottomHelp"
              aria-controls="offcanvasBottomHelp"
              v-on:click="getBlockedSites()"><i class="bi bi-question-diamond"></i> Hilfe
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
