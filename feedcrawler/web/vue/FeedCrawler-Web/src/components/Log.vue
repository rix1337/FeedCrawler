<script>
export default {
  // ToDo replace with actual data calls
  data() {
    return {
      longlog: false,
      resLengthLog: 10,
      currentPageLog: 0,
      numberOfPagesLog: 2,
      pageSizeLog: 5,
      log: [
          "Test",
          "Test2",
          "Test3",
          "Test4",
          "Test5",
          "Test6",
          "Test7",
          "Test8",
          "Test9",
          "Test10",
      ]
    }
  }
}
</script>

<template>
  <div id="log" class="container app col">
    <h3><i class="bi bi-clock-history"></i> Log</h3>
    <div class="card log">
      <table class="table" v-if="log.length > 0">
        <thead>
        <tr>
          <th scope="col" class="text-left d-none d-lg-block">Zeitstempel</th>
          <th scope="col" class="text-left">Release</th>
          <th scope="col" class="text-left">Kategorie</th>
          <th scope="col" class="text-left d-none d-lg-block">Seite</th>
        </tr>
        </thead>
        <tbody id="logbody">
        <tr v-for="x in log">
          <!-- ToDo refactor removed AngularJS filters to vue -->
          <td class="text-left d-none d-lg-block">{{ x[1] }}</td>
          <td class="text-left" title="{{ x[3] }}">
            {{ x[3] }}
            <a href='' v-if="!longlog && x[3].length > 65" @click="longerLog()"
               title="Titel vollständig anzeigen">...</a>
            <a href='' v-if="longlog && x[3].length > 65" @click="shorterLog()" title="Titel kürzen"><i
                class="bi bi-x-circle"></i></a>
          </td>
          <td class="text-left">{{ x[2] }}</td>
          <td class="text-left d-none d-lg-block">{{ x[4] }}</td>
          <td class="text-right"><a href="" title="Logeintrag löschen" data-toggle="tooltip"
                                    @click="deleteLogRow(x[3])"><i
              class="bi bi-trash remove"></i></a></td>
        </tr>
        </tbody>
      </table>
    </div>
    <div class="btn-group" v-if="resLengthLog>5">
      <!-- ToDo refactor ng-disable to vue variant -->
      <button class="btn btn-outline-info" :disable="currentPageLog === 0"
              @click="currentPageLog=currentPageLog-1">
        <i class="bi bi-chevron-left"></i>
      </button>
      <button class="btn btn-outline-info disabled">
        {{currentPageLog + 1}} / {{numberOfPagesLog}}
      </button>
      <button class="btn btn-outline-info" :disable="currentPageLog >= resLengthLog/pageSizeLog - 1"
              @click="currentPageLog=currentPageLog+1">
        <i class="bi bi-chevron-right"></i>
      </button>
    </div>
    <div>
      <a href="" @click="deleteLog()" class="btn btn-dark">
        <div id="spinner-log" style="display: none;"
             class="spinner-border spinner-border-sm" role="status"></div>
        <i class="bi bi-trash"></i> Leeren</a>
    </div>
  </div>
</template>
