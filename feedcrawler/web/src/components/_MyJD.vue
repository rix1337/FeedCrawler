<script>
export default {
  // ToDo replace with actual data calls
  data() {
    return {}
  }
}
</script>

<template>
  <div id="myjd" class="container app col">
    <h3><i class="bi bi-cloud-arrow-down"></i> My JDownloader</h3>
    <div id="accordionMyJD" class="accordion">
      <div class="accordion-item myjdheader">
        <h2 id="headingOne" class="accordion-header">
          <button id="myjd_collapse" aria-controls="collapseOne" aria-expanded="false"
                  class="accordion-button collapsed"
                  data-bs-target="#collapseOne"
                  data-bs-toggle="collapse" type="button" @click="manualCollapse()">
            Details
          </button>
        </h2>
        <div id="collapseOne" aria-labelledby="headingOne" class="accordion-collapse collapse"
             data-bs-parent="#accordionMyJD">
          <div class="accordion-body">
            <!-- ToDo refactor removed AngularJS filters to vue -->
            <div v-for="x in myjd_packages" class="myjd-items">
              <div class="myjd-downloads">
                <div v-if="x.type=='online'" class="card bg-success" title="In der Downloadliste">
                  <div class="card-header">
                    <strong v-text="x.name"></strong> (<span v-text="x.links"></span>)
                  </div>
                  <ul class="list-group list-group-flush">
                    <li class="list-group-item"><span v-text="x.done"></span> / <span
                        v-text="x.size"></span>
                    </li>
                    <li class="list-group-item">
                      <div class="progress">
                        <div :class="{'bg-info': x.eta_ext, 'bg-warning': (!x.speed && !x.eta_ext)}"
                             :style="{ 'width': x.percentage + '%' }"
                             aria-valuemax="100" aria-valuemin="0" aria-valuenow="x.percentage"
                             class="progress-bar progress-bar-striped progress-bar-animated"
                             role="progressbar">
                          <div id="percentage"><span v-text="x.percentage"></span> %</div>
                        </div>
                      </div>
                    </li>
                    <li v-if="x.speed || x.eta_ext" class="list-group-item">
                      <span v-text="x.speed"></span>
                      <span v-if="x.eta_ext">Entpacken</span>
                      <span> - </span>
                      <span v-text="x.eta"></span>
                      <span v-if="x.eta_ext" v-text="x.eta_ext"></span>
                    </li>
                    <li v-if="!x.speed && !x.eta_ext" class="list-group-item">
                      <span v-if="x.percentage===100">Wartet auf Entpacken</span>
                      <span v-if="x.percentage!==100">Wartet auf Download</span>
                    </li>
                  </ul>
                  <ul class="list-group list-group-flush">
                    <li class="list-group-item">
                      <a class="btn btn-outline-danger" data-toggle="tooltip" href=""
                         title="Löschen"
                         @click="myJDremove(x.linkids, x.uuid)"><i class="bi bi-trash"></i>
                        Löschen</a>
                    </li>
                  </ul>
                </div>
              </div>

              <div class="myjd-decrypted">
                <div v-if="x.type=='decrypted'" class="card bg-warning" title="Im Linksammler">
                  <div class="card-header">
                    <strong v-text="x.name"></strong> (<span v-text="x.links"></span>)
                  </div>
                  <ul class="list-group list-group-flush">
                    <li v-if="cnl_active" class="list-group-item">
                            <span class="cnl-spinner" data-toggle="tooltip"
                                  title="Warte auf hinzugefügte Links!">
                                <span class="spinner-border spinner-border-sm" role="status"></span> Warte auf hinzugefügte Links!</span>
                    </li>
                    <li v-if="x.size" class="list-group-item"><span v-text="x.size"></span></li>
                    <li v-if="!cnl_active" class="list-group-item cnl-blockers">
                      <a class="btn btn-outline-success" data-toggle="tooltip" href=""
                         title="Download starten"
                         @click="myJDmove(x.linkids, x.uuid)"><i class="bi bi-play"></i>
                        Download
                        starten</a>
                      <a class="btn btn-outline-danger" data-toggle="tooltip" href=""
                         title="Löschen"
                         @click="myJDremove(x.linkids, x.uuid)"><i class="bi bi-trash"></i>
                        Löschen</a>
                    </li>
                  </ul>
                </div>
              </div>

              <div class="myjd-failed">
                <div v-if="x.type=='failed'" class="card bg-danger" title="Fehler im Linksammler">
                  <span>Entschlüsselung im JDownloader fehlgeschlagen. Paket wird in Kürze aus dem JDownloader zurück in den FeedCrawler überführt...</span>
                  <a v-if="!cnl_active" class="btn btn-outline-danger" data-toggle="tooltip"
                     href=""
                     title="Löschen"
                     @click="myJDremove(x.linkids, x.uuid)"><i class="bi bi-trash"></i>
                    Löschen</a>
                </div>
              </div>

              <div class="myjd-to-decrypt">
                <div v-if="x.type=='to_decrypt'" class="card bg-danger" title="Fehler im Linksammler">
                  <div class="card-header">
                    <strong v-text="x.name"></strong>
                  </div>
                  <ul class="list-group list-group-flush">
                    <li v-if="x.url" class="list-group-item">
                      <a v-if="helper_active && helper_available && x.first && !cnl_active"
                         :href="x.url + '#' + x.name"
                         class="cnl-button btn btn-outline-success"
                         target="_blank"
                         title="Da der Click'n'Load des FeedCrawler Sponsors Helper verfügbar ist, kann die Click'n'Load Automatik hiermit umgangen werden."
                         type="submit">Sponsors Helper Click'n'Load</a>
                      <span
                          v-if="( hostnames.sj && x.url.includes(hostnames.sj.toLowerCase().replace('www.', '')) ) && helper_active && helper_available && x.first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_sponsors_helper_sj.user.js"
                                           target="_blank">FeedCrawler Sponsors Helper (SJ)</a> installieren!
                                    </span>
                      <span
                          v-if="( hostnames.dj && x.url.includes(hostnames.dj.toLowerCase().replace('www.', '')) ) && helper_active && helper_available && x.first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_sponsors_helper_sj.user.js"
                                           target="_blank">FeedCrawler Sponsors Helper (DJ)</a> installieren!
                                    </span>
                      <span
                          v-if="( x.url.includes('filecrypt') || ( hostnames.ww && x.url.includes(hostnames.ww.toLowerCase().replace('www.', '')) ) ) && helper_active && helper_available && x.first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_sponsors_helper_fc.user.js"
                                           target="_blank">FeedCrawler Sponsors Helper (FC)</a> installieren!
                                    </span>
                      <a v-if="!myjd_grabbing && !cnl_active"
                         :href="x.url + '#' + x.name"
                         class="cnl-button btn btn-secondary"
                         data-toggle="tooltip" target="_blank"
                         title="Click'n'Load innerhalb einer Minute auslösen!"
                         type="submit"
                         @click="internalCnl(x.name, x.password)">Click'n'Load-Automatik</a>
                      <span v-if="!myjd_grabbing">Setzt voraus, dass Port 9666 des JDownloaders durch diese Browsersitzung erreichbar ist.</span>
                      <span v-if="hostnames.sj && x.url.includes(hostnames.sj.toLowerCase())"><br>Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_helper_sj.user.js"
                                           target="_blank">FeedCrawler Helper (SJ)</a> installieren!
                                    </span>
                      <span v-if="hostnames.dj && x.url.includes(hostnames.dj.toLowerCase())"><br>Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_helper_sj.user.js"
                                           target="_blank">FeedCrawler Helper (DJ)</a> installieren!
                                    </span>
                      <span v-if="!helper_active"><br>
                                        <mark>Genervt davon, CAPTCHAs manuell zu lösen? Jetzt <a
                                            data-toggle="tooltip" href="https://github.com/users/rix1337/sponsorship"
                                            target="_blank"
                                            title="Bitte unterstütze die Weiterentwicklung über eine aktive Github Sponsorship!">Sponsor werden</a> und den <a
                                            href="#" @click="showSponsorsHelp()">den Sponsors Helper</a> für dich arbeiten lassen.</mark>
                                    </span>
                      <span v-if="myjd_grabbing"><br>Die Click'n'Load-Automatik funktioniert nicht bei aktivem Linkgrabber.</span>
                      <span v-if="cnl_active" class="cnl-spinner"
                            data-toggle="tooltip"
                            title="Warte noch {{time}} {{time == 1 ?'Sekunde':'Sekunden'}} auf hinzugefügte Links!"><br>
                                        <span class="spinner-border spinner-border-sm" role="status"></span> <strong>Warte noch {{
                            time
                          }} {{ time == 1 ? 'Sekunde' : 'Sekunden' }} auf hinzugefügte Links!</strong>
                                    </span>
                    </li>
                    <li v-if="!cnl_active" class="list-group-item cnl-blockers">
                      <a v-if="!cnl_active" class="btn btn-outline-danger" data-toggle="tooltip"
                         href=""
                         title="Löschen"
                         @click="internalRemove(x.name)"><i class="bi bi-trash"></i>
                        Löschen</a>
                    </li>
                  </ul>
                </div>
              </div>

              <div class="myjd-offline">
                <div v-if="x.type=='offline'" class="card bg-danger" title="Links offline">
                  <div class="card-header">
                    <strong v-text="x.name"></strong>
                  </div>
                  <ul class="list-group list-group-flush">
                    <li class="list-group-item">
                      <a v-if="!cnl_active" class="btn btn-outline-info" data-toggle="tooltip"
                         href=""
                         title="Erneut hinzufügen"
                         @click="myJDretry(x.linkids, x.uuid, x.urls)"><i
                          class="bi bi-arrow-counterclockwise"></i>
                        Erneut
                        hinzufügen</a>
                      <a class="btn btn-outline-danger" data-toggle="tooltip" href=""
                         title="Löschen"
                         @click="myJDremove(x.linkids, x.uuid)"><i class="bi bi-trash"></i>
                        Löschen</a>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div v-if="resLengthMyJD>3" class="btn-group">
              <button :disable="currentPageMyJD == 0" class="btn btn-outline-info"
                      @click="currentPageMyJD=currentPageMyJD-1">
                <i class="bi bi-chevron-left"></i>
              </button>
              <button :disable="true" class="btn btn-outline-info">
                {{ currentPageMyJD + 1 }} / {{ numberOfPagesMyJD() }}
              </button>
              <button :disable="currentPageMyJD >= resLengthMyJD/pageSizeMyJD - 1"
                      class="btn btn-outline-info"
                      @click="currentPageMyJD=currentPageMyJD+1">
                <i class="bi bi-chevron-right"></i>
              </button>
            </div>

            <div v-if="!myjd_state" class="myjd_connection_state">
              <p id="initial-loading">Verbinde mit My JDownloader...</p>
              <div id="spinner-myjd" class="spinner-border text-primary" role="status"></div>
            </div>
            <div v-if="myjd_connection_error" id="myjd_no_login" class="myjd_connection_state">Fehler bei
              Verbindung mit My
              JDownloader!
            </div>
            <div v-if="myjd_state && (myjd_packages.length == 0)" id="myjd_no_packages"
                 class="myjd_connection_state">
              Downloadliste und Linksammler sind leer.
            </div>

            <div v-if="myjd_downloads" id="myjd_state">
              <a v-if="myjd_state=='STOPPED_STATE' || myjd_state=='STOPPING'" id="myjd_start"
                 href=""
                 @click="myJDstart()"><i class="bi bi-play" data-toggle="tooltip"
                                         title="Downloads starten"></i></a>
              <a v-if="myjd_state=='RUNNING'" id="myjd_pause" href="" @click="myJDpause(true)"><i
                  class="bi bi-pause" data-toggle="tooltip"
                  title="Downloads pausieren"></i></a>
              <a v-if="myjd_state=='PAUSE'" id="myjd_unpause" href=""
                 @click="myJDpause(false)"><i
                  class="bi bi-skip-end-fill"
                  data-toggle="tooltip"
                  title="Downloads fortsetzen"></i></a>
              <a v-if="myjd_state=='RUNNING' || myjd_state=='PAUSE'" id="myjd_stop" href=""
                 @click="myJDstop()"><i
                  class="bi bi-stop" data-toggle="tooltip"
                  title="Downloads anhalten"></i></a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
