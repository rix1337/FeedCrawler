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
