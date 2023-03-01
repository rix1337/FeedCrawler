<script setup>
import {useStore} from 'vuex'
import {computed, onMounted, ref, watch} from 'vue'
import {useToast} from "vue-toastification"
import Paginate from "vuejs-paginate-next"
import {submitForm} from '@formkit/vue'
import axios from 'axios'


const store = useStore()
const toast = useToast()

const search_movies = ref(true)
const search_shows = ref(true)

onMounted(() => {
  const check_storage_movies = localStorage.getItem("search_movies")
  if (check_storage_movies === null) {
    search_movies.value = true
    localStorage.setItem("search_movies", "true")
  } else {
    search_movies.value = check_storage_movies === "true"
  }

  const check_storage_shows = localStorage.getItem("search_shows")
  if (check_storage_shows === null) {
    search_shows.value = true
    localStorage.setItem("search_shows", "true")
  } else {
    search_shows.value = check_storage_shows === "true"
  }
})

const results = ref(false)

const resLengthResults = ref(0)
const pageSizeResults = ref(10)
const currentPageResults = ref(1)
const numberOfPagesResults = ref(0)

function getResultsPages() {
  if (typeof results.value !== 'undefined') {
    resLengthResults.value = results.value.bl.length
    if (resLengthResults.value > 0) {
      numberOfPagesResults.value = Math.ceil(resLengthResults.value / pageSizeResults.value)
    } else {
      numberOfPagesResults.value = 1
    }
  }
}

const search = ref('')
const spin_search = ref(false)

const movies_only = ref(false)
const shows_only = ref(false)

watch(search_movies, (newVal) => {
  if (newVal === false && search_shows.value === false) {
    search_shows.value = true
  }
  localStorage.setItem("search_movies", newVal.toString())
})

watch(search_shows, (newVal) => {
  if (newVal === false && search_movies.value === false) {
    search_movies.value = true
  }
  localStorage.setItem("search_shows", newVal.toString())
})

watch([search_movies, search_shows], ([movies_value, shows_value]) => {
  if (movies_value === true && shows_value === false) {
    movies_only.value = true
    shows_only.value = false
  } else if (movies_value === false && shows_value === true) {
    movies_only.value = false
    shows_only.value = true
  }
})

function clearResults() {
  results.value = false
  currentPageResults.value = 1
}

function searchNow() {
  clearResults()
  let title = search.value
  spin_search.value = true
  if (search.value) {
    {
      spin_search.value = true
      axios.post('api/search/' + title, {movies_only: movies_only.value, shows_only: shows_only.value})
          .then(function (res) {
            if (results.value) {
              results.value.sj = res.data.results.sj.concat(results.value.sj)
              results.value.bl = res.data.results.bl.concat(results.value.bl)
            } else {
              results.value = res.data.results
            }
            getResultsPages()
            console.log('Nach ' + title + ' gesucht!')
            spin_search.value = false
          }, function () {
            console.log('Konnte ' + title + ' nicht suchen!')
            toast.error('Konnte  ' + title + ' nicht suchen!')
            spin_search.value = false
            results.value = false
            resLengthResults.value = 0
          })
    }
  }
}

const currentResultsPage = computed(() => {
  if (currentPageResults.value > numberOfPagesResults.value) {
    currentPageResults.value = numberOfPagesResults.value
  }
  return results.value.bl.slice((currentPageResults.value - 1) * pageSizeResults.value, currentPageResults.value * pageSizeResults.value)
})

function downloadBL(payload, title) {
  toast.info("Starte Download: " + title)
  axios.post('api/download_bl/' + payload)
      .then(function () {
        console.log('Download gestartet!')
        toast.success('Download gestartet!')
      }, function () {
        console.log('Konnte Download nicht starten!')
        toast.error('Konnte Download nicht starten!')
      })
}

function downloadS(payload, title) {
  toast.info("Starte Download: " + title + " Dieser Vorgang kann etwas dauern!", {
    timeout: 10000
  })
  axios.post('api/download_s/' + payload)
      .then(function () {
        console.log('Download gestartet!')
        toast.success('Download gestartet!')
      }, function () {
        console.log('Konnte Download nicht starten!')
        toast.error('Konnte Download nicht starten!')
      })
}

function submitSearch() {
  submitForm('search')
}
</script>

<template>
  <div class="text-center">
    <div id="offcanvasBottomSearch" aria-labelledby="offcanvasBottomSearchLabel" class="offcanvas offcanvas-bottom"
         tabindex="-1">
      <div class="offcanvas-header">
        <h3 id="offcanvasBottomSearchLabel" class="offcanvas-title"><i class="bi bi-search"></i> Web-Suche</h3>
        <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas" type="button"
                @click="clearResults()"></button>
      </div>
      <div class="offcanvas-body">
        <div
            v-tippy="'Bequeme Suchfunktion für ' + store.state.hostnames.search_shorthands + '. Bei hellblau hinterlegten Serien werden alle verfügbaren Staffeln/Episoden hinzugefügt. Komplette Serien landen auch in der Suchliste. Alternativ kann eine einzelne Staffel/Episode per Komma am Titel ergänzt werden: \'Serien Titel,S01\' oder \'Serien Titel,S01E01\'. Die für die Feed-Suche gesetzte Auflösung und Filterliste werden berücksichtigt, aber nicht forciert. Bereits geladene Releases werden hier nicht ignoriert!'"
            class="row">
          <FormKit id="search" #default="{ value }"
                   :actions="false"
                   incomplete-message="Das Suchfeld muss korrekt befüllt werden!"
                   messages-class="text-danger"
                   type="form"
                   @submit="searchNow()"
          >
            <FormKit v-model="search" help-class="text-muted"
                     input-class="form-control bg-light mb-2"
                     label="Suchbegriff"
                     messages-class="text-danger"
                     placeholder="Film- oder Serien-Titel eingeben"
                     type="text"
                     validation="required|length:3"/>
          </FormKit>
        </div>
        <div class="row justify-content-center mx-2">
          <div class="col-sm-1 form-check form-check-inline form-switch">
            <input class="form-check-input" type="checkbox" id="flexSwitchMovies" v-model="search_movies">
            <label class="form-check-label" for="flexSwitchMovies">Filme</label>
          </div>
          <div class="col-sm-1 form-check form-check-inline form-switch">
            <input class="form-check-input" type="checkbox" id="flexSwitchShows" v-model="search_shows">
            <label class="form-check-label" for="flexSwitchShows">Serien</label>
          </div>
        </div>
        <div class="row justify-content-center">
          <div class="col-sm-1">
            <button class="btn btn-primary mb-2" type="submit"
                    @click="submitSearch">
              <span v-if="spin_search" id="spinner-search" class="spinner-border spinner-border-sm"
                    role="status"> </span>
              <i v-if="!spin_search" class="bi bi-search"></i> Suchen
            </button>
          </div>
        </div>
        <div class="row justify-content-center" v-if="store.state.misc.no_site_blocked === 1 && spin_search">
          <div class="col-sm-4">
            <mark>
              Aufgrund aktiver Cloudflare-Blockaden dauert die Suche etwas länger!
            </mark>
          </div>
        </div>

        <div class="row">
          <div v-if="results" class="results">
            <div class="border-top mt-2 mb-2" v-if="results.sf.length > 0 || results.sj.length > 0"></div>
            <p v-for="x in results.sf">
              <button class="btn btn-outline-info" type="submit" @click="downloadS(x.payload, x.title)"><i
                  class="bi bi-download"></i> Serie: <span v-text="x.title"></span> (SF)
              </button>
            </p>
            <p v-for="x in results.sj">
              <button class="btn btn-outline-info" type="submit" @click="downloadS(x.payload, x.title)"><i
                  class="bi bi-download"></i> Serie: <span v-text="x.title"></span> (SJ)
              </button>
            </p>
            <div class="border-top mt-2 mb-2"></div>
            <p v-for="y in currentResultsPage">
              <button class="btn btn-outline-secondary" type="submit" @click="downloadBL(y.payload, y.title)"><i
                  class="bi bi-download"></i> <span v-text="y.title"></span></button>
            </p>
            <div v-if="resLengthResults>10" class="btn-group">
              <paginate
                  v-model="currentPageResults"
                  :next-text="'>'"
                  :page-count="numberOfPagesResults"
                  :prev-text="'<'"
              >
              </paginate>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Required for responsiveness of search results */
.btn {
  margin-top: 0.5em;
  margin-right: 0.1em;
  margin-left: 0.1em;
  white-space: inherit;
  word-break: break-all;
}
</style>
