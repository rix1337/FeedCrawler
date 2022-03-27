<script setup>
import {useStore} from 'vuex'
import {onMounted, ref} from 'vue'
import axios from 'axios'

const store = useStore()

onMounted(() => {
  getLog()
  setInterval(getLog, 5 * 1000)
})

const log = ref([])
const numberOfPagesLog = ref(0)

function getLog() {
  axios.get(store.state.prefix + 'api/log/')
      .then(function (res) {
        log.value = res.data.log
        getLogPages()
      }, function () {
        console.log('Konnte Log nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Log nicht abrufen!')
      })
}

const resLengthLog = ref(0)
const currentPageLog = ref(0)
const pageSizeLog = ref(5)

function getLogPages() {
  if (typeof log.value !== 'undefined' && log.value.length > 0) {
    resLengthLog.value = log.value.length
    numberOfPagesLog.value = Math.ceil(resLengthLog.value / pageSizeLog.value)
    if ((currentPageLog.value > 0) && ((currentPageLog.value + 1) > numberOfPagesLog.value)) {
      currentPageLog.value = numberOfPagesLog - 1
    }
  } else {
    numberOfPagesLog.value = 0
  }
}

const loglength = ref(65)
const longlog = ref(false)

function longerLog() {
  loglength.value = 999
  longlog.value = true
}

function shorterLog() {
  loglength.value = 65
  longlog.value = false
}

function deleteLog() {
  spinLog()
  axios.delete(store.state.prefix + 'api/log/')
      .then(function () {
        console.log('Log geleert!')
        // ToDo migrate to vue
        //showSuccess('Log geleert!')
        getLog()
      }, function () {
        console.log('Konnte Log nicht leeren!')
        // ToDo migrate to vue
        //showDanger('Konnte Log nicht leeren!')
      })
}

function deleteLogRow(title) {
  title = btoa(title)
  axios.delete(store.state.prefix + 'api/log_entry/' + title)
      .then(function () {
        console.log('Logeintrag gelöscht!')
        // ToDo migrate to vue
        //showSuccess('Logeintrag gelöscht!')
        getLog()
      }, function () {
        console.log('Konnte Logeintrag nicht löschen!')
        // ToDo migrate to vue
        //showDanger('Konnte Logeintrag nicht löschen!')
      })
}

const spin_log = ref(false)

function spinLog() {
  spin_log.value = true
  setTimeout(function () {
    spin_log.value = false
  }, 1000)
}

function checkEntryLength(entry) {
  if (entry !== undefined) {
    return (entry.length > 65)
  } else {
    return false
  }
}

function shortenEntry(entry) {
  if (entry !== undefined && !longlog.value) {
    return entry.substring(0, loglength.value)
  } else {
    return entry
  }

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
        <tr v-for="x in log">
          <!-- ToDo refactor removed AngularJS pagination filters to vue -->
          <td class="text-left d-none d-lg-block">{{ x[1] }}</td>
          <td class="text-left" title="{{ x[3] }}">
            {{ shortenEntry(x[3]) }}
            <!-- ToDo for some reason x[3] is undefined here-->
            <button v-if="!longlog && checkEntryLength(x[3])" class="btn btn-link btn-sm" href=''
                    title="Titel vollständig anzeigen"
                    @click="longerLog()">...
            </button>
            <button v-if="longlog && checkEntryLength(x[3])" class="btn btn-link btn-sm" href='' title="Titel kürzen"
                    @click="shorterLog()"><i
                class="bi bi-x-circle"></i></button>
          </td>
          <td class="text-left">{{ x[2] }}</td>
          <td class="text-left d-none d-lg-block">{{ x[4] }}</td>
          <td class="text-right">
            <button class="btn btn-link btn-sm" data-toggle="tooltip" href="" title="Logeintrag löschen"
                    @click="deleteLogRow(x[3])">
              <i class="bi bi-trash remove"></i></button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <div v-if="resLengthLog>5" class="btn-group">
      <!-- ToDo refactor ng-disable to vue variant -->
      <button :disable="currentPageLog === 0" class="btn btn-outline-info"
              @click="currentPageLog=currentPageLog-1">
        <i class="bi bi-chevron-left"></i>
      </button>
      <button class="btn btn-outline-info disabled">
        {{ currentPageLog + 1 }} / {{ numberOfPagesLog }}
      </button>
      <button :disable="currentPageLog >= resLengthLog/pageSizeLog - 1" class="btn btn-outline-info"
              @click="currentPageLog=currentPageLog+1">
        <i class="bi bi-chevron-right"></i>
      </button>
    </div>
    <div>
      <button class="btn btn-dark" href="" @click="deleteLog()">
        <div v-if="spin_log" class="spinner-border spinner-border-sm" role="status"></div>
        <i class="bi bi-trash"></i> Leeren
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