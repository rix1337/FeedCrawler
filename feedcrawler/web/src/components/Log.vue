<script setup>
import {useStore} from 'vuex'
import {computed, onMounted, ref} from 'vue'
import {useToast} from 'vue-toastification'
import axios from 'axios'
import Paginate from "vuejs-paginate-next"

const store = useStore()
const toast = useToast()

onMounted(() => {
  getLog()
  setInterval(getLog, 5 * 1000)
})

const log = ref([])


function getLog() {
  axios.get('api/log/')
      .then(function (res) {
        log.value = res.data.log
        getLogPages()
      }, function () {
        console.log('Konnte Log nicht abrufen!')
        toast.error('Konnte Log nicht abrufen!')
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

const maxLogItemLength = ref(60)
const longLogItemsAllowed = ref(false)

function longerLog() {
  maxLogItemLength.value = 999
  longLogItemsAllowed.value = true
}

function shorterLog() {
  maxLogItemLength.value = 60
  longLogItemsAllowed.value = false
}

function checkEntryLength(entry) {
  if (entry !== undefined) {
    return (entry.length > 60)
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

function copyTitleToClipBoard(title) {
  navigator.clipboard.writeText(title)
  toast.success(title + ' zur Zwischenablage hinzugefügt.')
}
</script>


<template>
  <div class="container">
    <div class="row my-3">
      <div class="col-md-10 offset-md-1">
        <div class="card my-3">
          <div class="card-header">
            <h3 class="text-center">
              <i class="bi bi-clock-history"></i> Log
            </h3>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="table-responsive">
                <table v-if="log.length > 0" class="table table-light table-bordered">
                  <thead>
                  <tr>
                    <th class="text-center" scope="col">Zeitpunkt</th>
                    <th class="text-left" scope="col">Titel</th>
                    <th class="text-center" scope="col"><i class="bi bi-clipboard-fill"></i></th>
                    <th class="text-center" scope="col">Kategorie</th>
                    <th class="text-center" scope="col">Seite</th>
                    <th class="text-center" scope="col"><i class="bi bi-trash-fill"></i></th>
                  </tr>
                  </thead>
                  <tbody id="logbody">
                  <tr v-for="x in currentLogPage">
                    <td class="text-center">{{ x[1] }}</td>
                    <td class="text-left">
                      {{ shortenEntry(x[3]) }}<i v-if="!longLogItemsAllowed && checkEntryLength(x[3])"
                                                 class="bi bi-three-dots text-primary"
                                                 v-tippy="'Titel vollständig anzeigen'"
                                                 @click="longerLog()"></i>
                      <button v-if="longLogItemsAllowed && checkEntryLength(x[3])" v-tippy="'Titel kürzen'"
                              class="btn btn-link btn-sm"
                              @click="shorterLog()"><i
                          class="bi bi-x-circle"></i></button>
                    </td>
                    <td class="text-center">
                      <button class="btn btn-outline-primary btn-sm"
                              v-tippy="'Titel kopieren'"
                              @click="copyTitleToClipBoard(x[3])">
                        <i class="bi bi-clipboard"></i>
                      </button>
                    </td>
                    <td class="text-center">{{ x[2] }}</td>
                    <td class="text-center">{{ x[4] }}</td>
                    <td class="text-center">
                      <button v-tippy="'Log-Eintrag löschen'" class="btn btn-link btn-sm"
                              @click="deleteLogRow(x[3])">
                        <i class="bi bi-trash text-danger"></i></button>
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
              <div class="text-center">
                <button class="btn btn-outline-secondary" @click="deleteLog()">
                  <span v-if="spin_log" class="spinner-border spinner-border-sm" role="status"></span>
                  <i v-if="!spin_log" class="bi bi-trash"></i> Leeren
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
