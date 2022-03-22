<script setup>
import axios from 'axios';
import {onMounted, ref} from 'vue'

const props = defineProps({
  prefix: String
})

onMounted(() => {
  getLog()
  setInterval(getLog, 5 * 1000)
})

const log = ref([])
const numberOfPagesLog = ref(0)

function getLog() {
  axios.get(props.prefix + 'api/log/')
      .then(function (res) {
        log.value = res.data.log;
        getLogPages()
        console.log('Log abgerufen!');
      }, function () {
        console.log('Konnte Log nicht abrufen!');
        // ToDo migrate to vue
        //showDanger('Konnte Log nicht abrufen!');
      });
}

const longlog = ref(false)
const resLengthLog = ref(0)
const currentPageLog = ref(0)
const pageSizeLog = ref(5)

function getLogPages() {
  if (typeof log.value !== 'undefined' && log.value.length > 0) {
    resLengthLog.value = log.value.length;
    numberOfPagesLog.value = Math.ceil(resLengthLog.value / pageSizeLog.value)
    if ((currentPageLog.value > 0) && ((currentPageLog.value + 1) > numberOfPagesLog.value)) {
      currentPageLog.value = numberOfPagesLog - 1
    }
  } else {
    numberOfPagesLog.value = 0
  }
}

function longerLog() {
  console.log("longerLog()");
}

function shorterLog() {
  console.log("shorterLog()");
}

function deleteLog() {
  console.log("deleteLog()");
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
          <!-- ToDo refactor removed AngularJS filters to vue -->
          <td class="text-left d-none d-lg-block">{{ x[1] }}</td>
          <td class="text-left" title="{{ x[3] }}">
            {{ x[3] }}
            <a v-if="!longlog && x[3].length > 65" href='' title="Titel vollständig anzeigen"
               @click="longerLog()">...</a>
            <a v-if="longlog && x[3].length > 65" href='' title="Titel kürzen" @click="shorterLog()"><i
                class="bi bi-x-circle"></i></a>
          </td>
          <td class="text-left">{{ x[2] }}</td>
          <td class="text-left d-none d-lg-block">{{ x[4] }}</td>
          <td class="text-right"><a data-toggle="tooltip" href="" title="Logeintrag löschen"
                                    @click="deleteLogRow(x[3])"><i
              class="bi bi-trash remove"></i></a></td>
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
      <a class="btn btn-dark" href="" @click="deleteLog()">
        <div id="spinner-log" class="spinner-border spinner-border-sm"
             role="status" style="display: none;"></div>
        <i class="bi bi-trash"></i> Leeren</a>
    </div>
  </div>
</template>
