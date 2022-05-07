<script setup>
import {useStore} from 'vuex'
import {computed, ref} from 'vue'
import {useToast} from "vue-toastification"
import axios from 'axios'
import Paginate from "vuejs-paginate-next"

const store = useStore()
const toast = useToast()

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
const searching = ref(false)
const slow_ready = ref(false)

function clearResults() {
  results.value = false
  currentPageResults.value = 1
}

function searchNow() {
  clearResults()
  let title = search.value
  searching.value = true
  slow_ready.value = false
  if (!title) {
    results.value = false
    resLengthResults.value = 0
    searching.value = false
  } else {
    axios.post('api/search/' + title, {slow_only: false, fast_only: true})
        .then(function (res) {
          results.value = res.data.results
          getResultsPages()
          search.value = ""
          console.log('Nach ' + title + ' gesucht (schnelle Seiten)!')
          searching.value = false
        }, function () {
          console.log('Konnte ' + title + ' nicht suchen!')
          toast.error('Konnte  ' + title + ' nicht suchen!')
          results.value = false
          resLengthResults.value = 0
          searching.value = false
        })
    axios.post('api/search/' + title, {slow_only: true, fast_only: false})
        .then(function (res) {
          slow_ready.value = true
          if (results.value) {
            results.value.sj = res.data.results.sj.concat(results.value.sj)
            results.value.bl = res.data.results.bl.concat(results.value.bl)
          } else {
            results.value = res.data.results
          }
          getResultsPages()
          search.value = ""
          console.log('Nach ' + title + ' gesucht (langsame Seiten)!')
          searching.value = false
        }, function () {
          slow_ready.value = true
          console.log('Konnte ' + title + ' nicht suchen!')
          toast.error('Konnte  ' + title + ' nicht suchen!')
          results.value = false
          resLengthResults.value = 0
          searching.value = false
        })
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
  toast.info("Starte Download:\n" + title + "\nDieser Vorgang kann etwas dauern!", {
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
        <input v-model="search" aria-label="Search"
               class="form-control mr-sm-2"
               minlength="3"
               placeholder="Film- oder Serientitel eingeben"
               v-tippy="'Bequeme Suchfunktion für ' + store.state.hostnames.search_shorthands + '. Bei hellblau hinterlegten Serien werden alle verfügbaren Staffeln/Episoden hinzugefügt.\nKomplette Serien landen auch in der Suchliste.\nAlternativ kann eine einzelne Staffel/Episode per Komma am Titel ergänzt werden: \'Serien Titel,S01\' oder \'Serien Titel,S01E01\'.\nDie jeweilige Auflösung und die Filterliste werden berücksichtigt, aber nicht forciert.\nBereits geladene Releases werden hier nicht ignoriert!'"
               @keyup.enter="searchNow()">
        <button v-if="search.length > 2" class="btn btn-primary mt-2" type="submit"
                @click="searchNow()">
          <span v-if="searching" id="spinner-search" class="spinner-border spinner-border-sm" role="status"> </span>
          <i v-if="!searching" class="bi bi-search"></i> Suchen
        </button>
        <div v-else v-tippy="'Bitte zunächst einen Suchtitel (mehr als 3 Zeichen) eingeben!'">
          <button class="btn btn-danger disabled mt-2">
            <i class="bi bi-search"></i> Suchen
          </button>
        </div>
        <div v-if="results && !slow_ready" class="btn btn-warning disabled mt-2">
          <span class="spinner-border spinner-border-sm"></span> Suche auf langsamen Seiten läuft noch...
        </div>
        <div v-if="results" class="results mt-2">
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
          <p v-for="y in currentResultsPage">
            <button class="btn btn-outline-dark" type="submit" @click="downloadBL(y.payload, y.title)"><i
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
</template>
