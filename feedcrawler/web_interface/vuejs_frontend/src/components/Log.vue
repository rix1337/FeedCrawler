<script setup>
import {useStore} from '@/main.js'
import {computed, inject, onMounted, ref} from 'vue'
import axios from 'axios'
import Paginate from "vuejs-paginate-next"

const store = useStore()
const toast = inject('toast')

onMounted(() => {
  getLog()
  setInterval(getLog, 10 * 1000)
})

const log = ref([])


function getLog() {
  axios.get('api/log/')
      .then(function (res) {
        log.value = res.data.log
        store.misc.loaded_log = true
        getLogPages()
      }, function () {
        console.log('Konnte Log nicht abrufen!')
      })
}

const resLengthLog = ref(0)
const pageSizeLog = ref(5)
const currentPageLog = ref(1)
const numberOfPagesLog = ref(0)

function getLogPages() {
  if (typeof log.value !== 'undefined') {
    resLengthLog.value = log.value.length
    if (resLengthLog.value > 0) {
      numberOfPagesLog.value = Math.ceil(resLengthLog.value / pageSizeLog.value)
    } else {
      numberOfPagesLog.value = 1
    }
  }
}

const currentLogPage = computed(() => {
  if (currentPageLog.value > numberOfPagesLog.value) {
    currentPageLog.value = numberOfPagesLog.value
  }
  return log.value.slice((currentPageLog.value - 1) * pageSizeLog.value, currentPageLog.value * pageSizeLog.value)
})

const maxLogItemLength = ref(65)
const longLogItemsAllowed = ref(false)

function longerLog() {
  maxLogItemLength.value = 999
  longLogItemsAllowed.value = true
}

function shorterLog() {
  maxLogItemLength.value = 65
  longLogItemsAllowed.value = false
}

function checkEntryLength(entry) {
  if (entry !== undefined) {
    return (entry.length > 65)
  } else {
    return false
  }
}

function shortenEntry(entry) {
  if (entry !== undefined && !longLogItemsAllowed.value) {
    return entry.substring(0, maxLogItemLength.value)
  } else {
    return entry
  }
}

function deleteLog() {
  spinLog()
  axios.delete('api/log/')
      .then(function () {
        console.log('Log geleert!')
        toast.success('Log geleert!')
        getLog()
      }, function () {
        console.log('Konnte Log nicht leeren!')
        toast.error('Konnte Log nicht leeren!')
      })
}

function deleteLogRow(title) {
  const title_b64 = btoa(title)
  axios.delete('api/log_entry/' + title_b64)
      .then(function () {
        console.log('Log-Eintrag ' + title + ' gelöscht!')
        toast.success('Log-Eintrag ' + title + ' gelöscht!')
        getLog()
      }, function () {
        console.log('Konnte Log-Eintrag ' + title + ' nicht löschen!')
        toast.error('Konnte Log-Eintrag ' + title + '  nicht löschen!')
      })
}

const spin_log = ref(false)

function spinLog() {
  spin_log.value = true
  setTimeout(function () {
    spin_log.value = false
  }, 1000)
}
</script>


<template>
  <div class="container">
    <div class="row my-3">
      <div class="col-md-12">
        <div class="card my-3">
          <div class="card-header">
            <h3 class="text-center">
              <i class="bi bi-clock-history"></i> Log
            </h3>
          </div>
          <div class="card-body">
            <div class="row">
              <div v-if="!store.misc.loaded_log" class="text-center">
                <h4>Log wird geladen...</h4>
                <div class="spinner-border text-primary" role="status"></div>
              </div>
              <div v-else class="table-responsive">
                <table class="table table-light table-bordered">
                  <thead>
                  <tr>
                    <th class="text-center" scope="col">Zeitpunkt</th>
                    <th class="text-left" scope="col">Titel</th>
                    <th class="text-center" scope="col">Kategorie</th>
                    <th class="text-center" scope="col">Seite</th>
                    <th class="text-center" scope="col">Größe</th>
                    <th class="text-center" scope="col"><i class="bi bi-link-45deg"></i></th>
                    <th class="text-center" scope="col"><i class="bi bi-trash3"></i></th>
                  </tr>
                  </thead>
                  <tbody v-if="log.length === 0">
                  <tr>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                  </tr>
                  </tbody>
                  <tbody v-else>
                  <tr v-for="x in currentLogPage">
                    <td class="text-center">{{ x[1] }}</td>
                    <td class="text-left">
                      {{ shortenEntry(x[3]) }}<span v-if="!longLogItemsAllowed && checkEntryLength(x[3])"
                                                    class="btn btn-outline-secondary btn-sm mt-0 pt-0 pb-0"
                                                    @click="longerLog()"><i
                        v-tippy="'Titel vollständig anzeigen'"
                        class="bi bi-three-dots"></i></span>
                      <span v-if="longLogItemsAllowed && checkEntryLength(x[3])" v-tippy="'Titel kürzen'"
                            class="btn btn-outline-secondary btn-sm mt-0 pt-0 pb-0"
                            @click="shorterLog()"><i
                          class="bi bi-x-lg"></i></span>
                    </td>
                    <td class="text-center">{{ x[2] }}</td>
                    <td class="text-center">{{ x[4] }}</td>
                    <td class="text-center">{{ x[5] }}<i v-if="!x[5] || x[5] === '' || typeof x[5] === 'undefined'"
                                                         class="bi bi-question-square text-secondary"
                                                         style="color: #6c757d !important; opacity: .65;"></i></td>
                    <td class="text-center">
                      <a v-tippy="'Quelle öffnen'"
                         :class="{
                                    'disabled': (!x[6] || x[6] === '' || typeof x[6] === 'undefined'),
                                    'btn-outline-secondary': (!x[6] || x[6] === '' || typeof x[6] === 'undefined'),
                                    'btn-outline-primary': x[6] && x[6] !== '' && typeof x[6] !== 'undefined'
                                 }"
                         :href="x[6]"
                         class="btn btn-sm mt-0 pt-0 pb-0"
                         target="_blank">
                        <i class="bi bi-link-45deg"></i>
                      </a>
                    </td>
                    <td class="text-center">
                      <button v-tippy="'Log-Eintrag löschen'" class="btn btn-outline-danger btn-sm mt-0 pt-0 pb-0"
                              @click="deleteLogRow(x[3])">
                        <i class="bi bi-trash3"></i></button>
                    </td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <br>
            <div class="row">
              <div class="text-center">
                <div v-if="resLengthLog>5" class="btn-group">
                  <paginate
                      v-model="currentPageLog"
                      :next-text="'>'"
                      :page-count="numberOfPagesLog"
                      :prev-text="'<'"
                  >
                  </paginate>
                </div>
              </div>
              <!-- Modal -->
              <div id="deleteLogModal" aria-hidden="true" aria-labelledby="deleteLogModalLabel" class="modal fade"
                   tabindex="-1">
                <div class="modal-dialog">
                  <div class="modal-content">
                    <div class="modal-header">
                      <h5 id="deleteLogModalLabel" class="modal-title">Log wirklich leeren?</h5>
                      <button aria-label="Close" class="btn-close" data-bs-dismiss="modal" type="button"></button>
                    </div>
                    <div class="modal-body">
                      Hierdurch werden alle Log-Zeilen gelöscht!
                    </div>
                    <div class="modal-footer">
                      <button class="btn btn-outline-secondary" data-bs-dismiss="modal" type="button">Schließen</button>
                      <button class="btn btn-danger" data-bs-dismiss="modal" type="button" @click="deleteLog()">
                        <i class="bi bi-trash3"></i>
                        Log leeren
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="text-center">
                <button class="btn btn-outline-danger" data-bs-target="#deleteLogModal" data-bs-toggle="modal"
                        type="button">
                  <span v-if="spin_log" class="spinner-border spinner-border-sm" role="status"></span>
                  <i v-if="!spin_log" class="bi bi-trash3"></i> Leeren
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* No line break on long log texts */
td {
  white-space: nowrap;
  font-family: var(--bs-font-monospace);
  vertical-align: middle;
}
</style>
