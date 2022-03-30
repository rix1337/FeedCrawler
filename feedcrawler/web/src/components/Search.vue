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
      numberOfPagesResults.value = 0
    }
  }
}

const search = ref('')
const searching = ref(false)

function searchNow() {
  results.value = false
  currentPageResults.value = 1
  let title = search.value
  searching.value = true
  if (!title) {
    results.value = false
    resLengthResults.value = 0
    searching.value = false
  } else {
    axios.get(store.state.prefix + 'api/search/' + title)
        .then(function (res) {
          results.value = res.data.results
          getResultsPages()
          search.value = ""
          console.log('Nach ' + title + ' gesucht!')
          searching.value = false
        }, function () {
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

function downloadBL(payload) {
  toast.info("Starte Download...")
  axios.post(store.state.prefix + 'api/download_bl/' + payload)
      .then(function () {
        console.log('Download gestartet!')
        toast.success('Download gestartet!')
      }, function () {
        console.log('Konnte Download nicht starten!')
        toast.error('Konnte Download nicht starten!')
      })
}

function downloadSJ(payload) {
  toast.info("Starte Download...")
  axios.post(store.state.prefix + 'api/download_sj/' + payload)
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
  <div id="offcanvasBottomSearch" aria-labelledby="offcanvasBottomSearchLabel" class="offcanvas offcanvas-bottom"
       tabindex="-1">
    <div class="offcanvas-header">
      <h3 id="offcanvasBottomSearchLabel" class="offcanvas-title"><i class="bi bi-search"></i> Web-Suche</h3>
      <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas" type="button"></button>
    </div>
    <div class="offcanvas-body">
      <input v-model="search" aria-label="Search"
             class="form-control mr-sm-2"

             placeholder="Filme und Serien suchen"
             v-tooltip="'Bequeme Suchfunktion für SJ, BY, FX, HW und NK. Bei hellblau hinterlegten Serien werden alle verfügbaren Staffeln/Episoden hinzugefügt. Komplette Serien landen auch in der Suchliste. Alternativ kann eine einzelne Staffel/Episode per Komma am Titel ergänzt werden: \'Serien Titel,S01\' oder \'Serien Titel,S01E01\'. Die jeweilige Auflösung und die Filterliste werden berücksichtigt, aber nicht forciert. Bereits geladene Releases werden hier nicht ignoriert!'"
             @keyup.enter="searchNow()">
      <button v-if="search || (!results.sj && !results.bl)" class="btn btn-dark" type="submit"
              @click="searchNow()">
        <span v-if="searching" id="spinner-search" class="spinner-border spinner-border-sm" role="status"> </span>
        <i v-if="!searching" class="bi bi-search"></i> Suchen
      </button>
      <button v-if="!search && (results.sj || results.bl)" class="btn btn-dark" type="submit"
              @click="searchNow()"><i class="bi bi-x-circle"></i> Leeren
      </button>
      <div v-if="results" class="results">
        <p v-for="x in results.sj">
          <button class="btn btn-outline-info" type="submit" @click="downloadSJ(x.payload)"><i
              class="bi bi-download"></i> Serie: <span v-text="x.title"></span></button>
        </p>
        <p v-for="y in currentResultsPage">
          <button class="btn btn-outline-dark" type="submit" @click="downloadBL(y.payload)"><i
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
</template>
