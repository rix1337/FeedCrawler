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
  axios.get(store.state.prefix + 'api/log/')
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
  axios.delete(store.state.prefix + 'api/log/')
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
  axios.delete(store.state.prefix + 'api/log_entry/' + title_b64)
      .then(function () {
        console.log('Log-Eintrag ' + title + ' gelöscht!')
        toast.success('Log-Eintrag\n' + title + '\ngelöscht!')
        getLog()
      }, function () {
        console.log('Konnte Log-Eintrag ' + title + ' nicht löschen!')
        toast.error('Konnte Log-Eintrag\n' + title + '\n nicht löschen!')
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
  <div id="log" class="container app col">
    <h3><i class="bi bi-clock-history"></i> Log</h3>
    <div class="card log">
      <table v-if="log.length > 0" class="table">
        <thead>
        <tr>
          <th class="text-left d-none d-lg-block" scope="col">Zeitstempel</th>
          <th class="text-left" scope="col">Release</th>
          <th class="text-left" scope="col">Kategorie</th>
          <th class="text-left d-none d-lg-block" scope="col">Seite</th>
        </tr>
        </thead>
        <tbody id="logbody">
        <tr v-for="x in currentLogPage">
          <td class="text-left d-none d-lg-block">{{ x[1] }}</td>
          <td class="text-left">
            {{ shortenEntry(x[3]) }}
            <button v-if="!longLogItemsAllowed && checkEntryLength(x[3])" class="btn btn-link btn-sm"
                    v-tooltip="'Titel vollständig anzeigen'"
                    @click="longerLog()">...
            </button>
            <button v-if="longLogItemsAllowed && checkEntryLength(x[3])" v-tooltip="'Titel kürzen'"
                    class="btn btn-link btn-sm"
                    @click="shorterLog()"><i
                class="bi bi-x-circle"></i></button>
          </td>
          <td class="text-left">{{ x[2] }}</td>
          <td class="text-left d-none d-lg-block">{{ x[4] }}</td>
          <td class="text-right">
            <button v-tooltip="'Log-Eintrag löschen'" class="btn btn-link btn-sm"
                    @click="deleteLogRow(x[3])">
              <i class="bi bi-trash remove"></i></button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <br>
    <div v-if="resLengthLog>5" class="btn-group">
      <paginate
          v-model="currentPageLog"
          :next-text="'>'"
          :page-count="numberOfPagesLog"
          :prev-text="'<'"
      >
      </paginate>
    </div>
    <div>
      <button class="btn btn-dark" @click="deleteLog()">
        <div v-if="spin_log" class="spinner-border spinner-border-sm" role="status"></div>
        <i v-if="!spin_log" class="bi bi-trash"></i> Leeren
      </button>
    </div>
  </div>
</template>

<style>
.btn-link {
  margin-top: 0 !important;
  padding: 0 !important;
}
</style>