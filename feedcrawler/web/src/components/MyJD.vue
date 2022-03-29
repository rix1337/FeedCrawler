<script setup>
import {useStore} from 'vuex'
import {computed, onMounted, ref} from 'vue'
import {useToast} from 'vue-toastification'
import {Collapse, Offcanvas} from 'bootstrap'
import axios from 'axios'
import Paginate from "vuejs-paginate-next"

const store = useStore()
const toast = useToast()

onMounted(() => {
  getMyJD()
  setInterval(getMyJD, 5 * 1000)
})

const myjd_state = ref(false)
const myjd_packages = ref([])
const myjd_downloads = ref([])
const myjd_decrypted = ref([])
const myjd_offline = ref([])
const myjd_failed = ref([])
const myjd_grabbing = ref(false)
const to_decrypt = ref([])
const update_ready = ref(false)

function getMyJD() {
  axios.get(store.state.prefix + 'api/myjd/')
      .then(function (res) {
        store.commit("setMyJDConnectionError", false)
        pageSizeMyJD.value = store.state.misc.pageSizeMyJD
        getMyJDPages()
        myjd_state.value = res.data.downloader_state
        myjd_downloads.value = res.data.packages.downloader
        myjd_decrypted.value = res.data.packages.linkgrabber_decrypted
        myjd_offline.value = res.data.packages.linkgrabber_offline
        myjd_failed.value = res.data.packages.linkgrabber_failed
        to_decrypt.value = res.data.packages.to_decrypt

        let uuids = []
        if (myjd_failed.value) {
          for (let existing_package of myjd_failed.value) {
            let uuid = existing_package['uuid']
            uuids.push(uuid)
          }
          const failed_packages = Object.entries(res.data.packages.linkgrabber_failed)
          for (let failed_package of failed_packages) {
            let uuid = failed_package[1]['uuid']
            if (!uuids.includes(uuid)) {
              myjd_failed.value.push(failed_package[1])
            }
          }
        }
        let names = []
        if (to_decrypt.value) {
          for (let existing_package of to_decrypt.value) {
            let name = existing_package['name']
            names.push(name)
          }
          to_decrypt.value = Object.entries(res.data.packages.to_decrypt)
          for (let failed_package of to_decrypt.value) {
            let name = failed_package[1]['name']
            if (!names.includes(name)) {
              to_decrypt.value.push(failed_package[1])
            }
          }
        }
        myjd_grabbing.value = res.data.grabber_collecting
        if (myjd_grabbing.value) {
          if (!myjd_collapse_manual.value && (typeof store.state.settings.general !== 'undefined' && !store.state.settings.general.closed_myjd_tab.value)) {
            // ToDo migrate to vue
            //$("#collapseOne").addClass('show')
            //$("#myjd_collapse").removeClass('collapsed')
          }
        }
        update_ready.value = res.data.update_ready

        myjd_packages.value = []
        if (myjd_failed.value) {
          for (let p of myjd_failed.value) {
            p.type = "failed"
            myjd_packages.value.push(p)
          }
        }
        if (to_decrypt.value) {
          let first = true
          for (let p of to_decrypt.value) {
            p.type = "to_decrypt"
            p.first = first
            first = false
            myjd_packages.value.push(p)
          }
        }
        if (myjd_offline.value) {
          for (let p of myjd_offline.value) {
            p.type = "offline"
            myjd_packages.value.push(p)
          }
        }
        if (myjd_decrypted.value) {
          for (let p of myjd_decrypted.value) {
            p.type = "decrypted"
            myjd_packages.value.push(p)
          }
        }
        if (myjd_downloads.value) {
          for (let p of myjd_downloads.value) {
            p.type = "online"
            myjd_packages.value.push(p)
          }
        }

        if (myjd_packages.value.length === 0 || (typeof store.state.settings.general !== 'undefined' && typeof store.state.settings.general.closed_myjd_tab.value !== 'undefined')) {
          if (!myjd_collapse_manual.value) {
            // ToDo migrate to vue
            //$("#myjd_collapse").addClass('collapsed')
            //$("#collapseOne").removeClass('show')
          }
        } else {
          if (!myjd_collapse_manual.value && (typeof store.state.settings.general !== 'undefined' && typeof store.state.settings.general.closed_myjd_tab.value !== 'undefined')) {
            // ToDo migrate to vue
            //$("#collapseOne").addClass('show')
            //$("#myjd_collapse").removeClass('collapsed')
          }
        }
      }, function () {
        myjd_grabbing.value = null
        myjd_downloads.value = null
        myjd_decrypted.value = null
        myjd_failed.value = null
        store.commit("setMyJDConnectionError", true)
        console.log('Konnte JDownloader nicht erreichen!')
        toast.error('Konnte JDownloader nicht erreichen!', {icon: 'bi bi-exclamation-triangle'})
      })
}


const resLengthMyJD = ref(0)
const pageSizeMyJD = ref(3)
const currentPageMyJD = ref(1)
const numberOfPagesMyJD = ref(0)

function getMyJDPages() {
  if (typeof myjd_packages.value !== 'undefined') {
    resLengthMyJD.value = myjd_packages.value.length
    if (resLengthMyJD.value > 0) {
      numberOfPagesMyJD.value = Math.ceil(resLengthMyJD.value / pageSizeMyJD.value)
    } else {
      numberOfPagesMyJD.value = 0
    }
  }
}

const currentMyJDPage = computed(() => {
  return myjd_packages.value.slice((currentPageMyJD.value - 1) * pageSizeMyJD.value, currentPageMyJD.value * pageSizeMyJD.value)
})

function myJDstart() {
  // ToDo migrate to vue
  //$('#myjd_start').addClass('blinking').addClass('isDisabled')
  axios.post(store.state.prefix + 'api/myjd_start/')
      .then(function () {
        getMyJDstate()
        console.log('Download gestartet!')
      }, function () {
        console.log('Konnte Downloads nicht starten!')
        toast.error('Konnte Downloads nicht starten!', {icon: 'bi bi-exclamation-triangle'})
      })
}

function myJDpause(pause) {
  // ToDo migrate to vue
  //$('#myjd_pause').addClass('blinking').addClass('isDisabled')
  //$('#myjd_unpause').addClass('blinking').addClass('isDisabled')
  axios.post(store.state.prefix + 'api/myjd_pause/' + pause)
      .then(function () {
        getMyJDstate()
        if (pause) {
          console.log('Download pausiert!')
        } else {
          console.log('Download fortgesetzt!')
        }
      }, function () {
        console.log('Konnte Downloads nicht fortsetzen!')
        toast.error('Konnte Downloads nicht fortsetzen!', {icon: 'bi bi-exclamation-triangle'})
      })
}

function myJDstop() {
  // ToDo migrate to vue
  //$('#myjd_stop').addClass('blinking').addClass('isDisabled')
  axios.post(store.state.prefix + 'api/myjd_stop/')
      .then(function () {
        getMyJDstate()
        console.log('Download angehalten!')
      }, function () {
        console.log('Konnte Downloads nicht anhalten!')
        toast.error('Konnte Downloads nicht anhalten!', {icon: 'bi bi-exclamation-triangle'})
      })
}

function getMyJDstate() {
  axios.get(store.state.prefix + 'api/myjd_state/')
      .then(function (res) {
        myjd_state.value = res.data.downloader_state
        myjd_grabbing.value = res.data.grabber_collecting
        update_ready.value = res.data.update_ready
        // ToDo migrate to vue
        //$('#myjd_start').removeClass('blinking').removeClass('isDisabled')
        //$('#myjd_pause').removeClass('blinking').removeClass('isDisabled')
        //$('#myjd_unpause').removeClass('blinking').removeClass('isDisabled')
        //$('#myjd_stop').removeClass('blinking').removeClass('isDisabled')
        //$('#myjd_update').removeClass('blinking').removeClass('isDisabled')
      }, function () {
        console.log('Konnte JDownloader nicht erreichen!')
        toast.error('Konnte JDownloader nicht erreichen!', {icon: 'bi bi-exclamation-triangle'})
      })
}

function myJDmove(linkids, uuid) {
  toast.success("Starte Download...", {icon: 'bi bi-check-circle-fill'})
  axios.post(store.state.prefix + 'api/myjd_move/' + linkids + "&" + uuid)
      .then(function () {
        getMyJD()
      }, function () {
        console.log('Konnte Download nicht starten!')
        toast.error('Konnte Download nicht starten!', {icon: 'bi bi-exclamation-triangle'})
      })
}

function myJDremove(linkids, uuid) {
  toast.success("Lösche Download...", {icon: 'bi bi-check-circle-fill'})
  axios.post(store.state.prefix + 'api/myjd_remove/' + linkids + "&" + uuid)
      .then(function () {
        if (myjd_failed.value) {
          for (let failed_package of myjd_failed.value) {
            let existing_uuid = failed_package['uuid']
            if (uuid === existing_uuid) {
              let index = myjd_failed.value.indexOf(failed_package)
              myjd_failed.value.splice(index, 1)
            }
          }
        }
        getMyJD()
      }, function () {
        console.log('Konnte Download nicht löschen!')
        toast.error('Konnte Download nicht löschen!', {icon: 'bi bi-exclamation-triangle'})
      })
}

function internalRemove(name) {
  toast.success("Lösche Download...", {icon: 'bi bi-check-circle-fill'})
  axios.post(store.state.prefix + 'api/internal_remove/' + name)
      .then(function () {
        if (to_decrypt.value) {
          for (let failed_package of to_decrypt.value) {
            let existing_name = failed_package['name']
            if (name === existing_name) {
              let index = to_decrypt.value.indexOf(failed_package)
              to_decrypt.value.splice(index, 1)
            }
          }
        }
        getMyJD()
      }, function () {
        console.log('Konnte Download nicht löschen!')
        toast.error('Konnte Download nicht löschen!', {icon: 'bi bi-exclamation-triangle'})
      })
}

function myJDretry(linkids, uuid, links) {
  toast.success("Füge Download erneut hinzu...", {icon: 'bi bi-check-circle-fill'})
  links = btoa(links)
  axios.post(store.state.prefix + 'api/myjd_retry/' + linkids + "&" + uuid + "&" + links)
      .then(function () {
        if (myjd_failed.value) {
          for (let failed_package of myjd_failed.value) {
            let existing_uuid = failed_package['uuid']
            if (uuid === existing_uuid) {
              let index = myjd_failed.value.indexOf(failed_package)
              myjd_failed.value.splice(index, 1)
            }
          }
        }
        getMyJD()
      }, function () {
        console.log('Konnte Download nicht erneut hinzufügen!')
        toast.error('Konnte Download nicht erneut hinzufügen!', {icon: 'bi bi-exclamation-triangle'})
      })
}

const cnl_active = ref(false)
const time = ref(0)

function internalCnl(name, password) {
  toast.warning("Warte auf Click'n'Load...", {
    timeout: 60000,
    icon: 'bi bi-exclamation-circle',
    closeOnClick: false,
    closeButton: false,
    pauseOnFocusLoss: false,
    pauseOnHover: false,
  })
  cnl_active.value = true
  time.value = 60
  countDown()
  axios.post(store.state.prefix + 'api/internal_cnl/' + name + "&" + password)
      .then(function () {
        if (to_decrypt.value) {
          for (let failed_package of to_decrypt.value) {
            let existing_name = failed_package['name']
            if (name === existing_name) {
              let index = to_decrypt.value.indexOf(failed_package)
              to_decrypt.value.splice(index, 1)
            }
          }
        }
        getMyJD()
        cnl_active.value = false
        time.value = 0
      }).catch(function () {
    toast.error("Click'n'Load nicht durchgeführt!", {icon: 'bi bi-exclamation-triangle'})
    cnl_active.value = false
    time.value = 0
  })
}

function countDown() {
  if (time.value > 0) {
    setTimeout(() => {
      time.value -= 1
      countDown()
    }, 1000)
  }
}

const myjd_collapse_manual = ref(false)

function manualCollapse() {
  myjd_collapse_manual.value = true
}

function showSponsorsHelp() {
  let offcanvas = new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false})
  offcanvas.show()
  new Collapse(document.getElementById('collapseOneZero'), {
    toggle: true
  })
  sessionStorage.setItem('fromNav', '')
  window.location.href = "#collapseOneZero"
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
            <div v-for="x in currentMyJDPage" class="myjd-items">
              <div class="myjd-downloads">
                <div v-if="x.type=='online'" v-tooltip="'In der Downloadliste'" class="card bg-success">
                  <div class="card-header">
                    <strong>{{ x.name }}</strong> (<span v-text="x.links"></span>)
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
                      <button v-tooltip="'Löschen'"
                              class="btn btn-outline-danger"
                              @click="myJDremove(x.linkids, x.uuid)"><i class="bi bi-trash"></i>
                        Löschen
                      </button>
                    </li>
                  </ul>
                </div>
              </div>

              <div class="myjd-decrypted">
                <div v-if="x.type=='decrypted'" v-tooltip="'Im Linksammler'" class="card bg-warning">
                  <div class="card-header">
                    <strong>{{ x.name }}</strong> (<span v-text="x.links"></span>)
                  </div>
                  <ul class="list-group list-group-flush">
                    <li v-if="cnl_active" class="list-group-item">
                            <span v-tooltip="'Warte auf hinzugefügte Links!'"
                                  class="cnl-spinner">
                                <span class="spinner-border spinner-border-sm" role="status"></span> Warte auf hinzugefügte Links!</span>
                    </li>
                    <li v-if="x.size" class="list-group-item"><span v-text="x.size"></span></li>
                    <li v-if="!cnl_active" class="list-group-item cnl-blockers">
                      <button v-tooltip="'Download starten'"
                              class="btn btn-outline-success"
                              @click="myJDmove(x.linkids, x.uuid)"><i class="bi bi-play"></i>
                        Download
                        starten
                      </button>
                      <button v-tooltip="'Löschen'"
                              class="btn btn-outline-danger"
                              @click="myJDremove(x.linkids, x.uuid)"><i class="bi bi-trash"></i>
                        Löschen
                      </button>
                    </li>
                  </ul>
                </div>
              </div>

              <div class="myjd-failed">
                <div v-if="x.type=='failed'" v-tooltip="'Fehler im Linksammler'" class="card bg-danger">
                  <span>Entschlüsselung im JDownloader fehlgeschlagen. Paket wird in Kürze aus dem JDownloader zurück in den FeedCrawler überführt...</span>
                  <button v-if="!cnl_active" v-tooltip="'Löschen'" class="btn btn-outline-danger"
                          @click="myJDremove(x.linkids, x.uuid)"><i class="bi bi-trash"></i>
                    Löschen
                  </button>
                </div>
              </div>

              <div class="myjd-to-decrypt">
                <div v-if="x.type=='to_decrypt'" v-tooltip="'CAPTCHA zu lösen'" class="card bg-danger">
                  <div class="card-header">
                    <strong>{{ x[1].name }}</strong>
                  </div>
                  <ul class="list-group list-group-flush">
                    <li v-if="x[1].url" class="list-group-item">
                      <a v-if="store.state.misc.helper_active && store.state.misc.helper_available && x[1].first && !cnl_active"
                         :href="x[1].url + '#' + x[1].name"
                         class="cnl-button btn btn-outline-success"
                         target="_blank"
                         v-tooltip="'Da der Click\'n\'Load des FeedCrawler Sponsors Helper verfügbar ist, kann die Click\'n\'Load Automatik hiermit umgangen werden.'"
                         type="submit">Sponsors Helper Click'n'Load
                      </a>
                      <span
                          v-if="( store.state.hostnames.sj && x[1].url.includes(store.state.hostnames.sj.toLowerCase().replace('www.', '')) ) && store.state.misc.helper_active && store.state.misc.helper_available && x[1].first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_sponsors_helper_sj.user.js"
                                           target="_blank">FeedCrawler Sponsors Helper (SJ)</a> installieren!
                                    </span>
                      <span
                          v-if="( store.state.hostnames.dj && x[1].url.includes(store.state.hostnames.dj.toLowerCase().replace('www.', '')) ) && store.state.misc.helper_active && store.state.misc.helper_available && x[1].first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_sponsors_helper_sj.user.js"
                                           target="_blank">FeedCrawler Sponsors Helper (DJ)</a> installieren!
                                    </span>
                      <span
                          v-if="( x[1].url.includes('filecrypt') || ( store.state.hostnames.ww && x[1].url.includes(store.state.hostnames.ww.toLowerCase().replace('www.', '')) ) ) && store.state.misc.helper_active && store.state.misc.helper_available && x[1].first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_sponsors_helper_fc.user.js"
                                           target="_blank">FeedCrawler Sponsors Helper (FC)</a> installieren!
                                    </span>
                      <a v-if="!myjd_grabbing && !cnl_active"
                         :href="x[1].url + '#' + x[1].name"
                         class="cnl-button btn btn-secondary"
                         v-tooltip="'Click\'n\'Load innerhalb einer Minute auslösen!'"
                         target="_blank"
                         type="submit"
                         @click="internalCnl(x[1].name, x[1].password)">Click'n'Load-Automatik
                      </a>
                      <span v-if="!myjd_grabbing">Setzt voraus, dass Port 9666 des JDownloaders durch diese Browsersitzung erreichbar ist.</span>
                      <span
                          v-if="store.state.hostnames.sj && x[1].url.includes(store.state.hostnames.sj.toLowerCase())"><br>Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_helper_sj.user.js"
                                           target="_blank">FeedCrawler Helper (SJ)</a> installieren!
                                    </span>
                      <span
                          v-if="store.state.hostnames.dj && x[1].url.includes(store.state.hostnames.dj.toLowerCase())"><br>Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a href="./sponsors_helper/feedcrawler_helper_sj.user.js"
                                           target="_blank">FeedCrawler Helper (DJ)</a> installieren!
                                    </span>
                      <span v-if="!store.state.misc.helper_active"><br>
                                        <mark>Genervt davon, CAPTCHAs manuell zu lösen? Jetzt <a
                                            v-tooltip="'Bitte unterstütze die Weiterentwicklung über eine aktive Github Sponsorship!'"
                                            target="_blank"
                                            href="https://github.com/users/rix1337/sponsorship">Sponsor werden</a> und den <a
                                            href="#" @click="showSponsorsHelp()">den Sponsors Helper</a> für dich arbeiten lassen.</mark>
                                    </span>
                      <span v-if="myjd_grabbing"><br>Die Click'n'Load-Automatik funktioniert nicht bei aktivem Linkgrabber.</span>
                      <span v-if="cnl_active" class="cnl-spinner"><br>
                                        <span class="spinner-border spinner-border-sm" role="status"></span> <strong>Warte noch {{
                            time
                          }} {{ time == 1 ? 'Sekunde' : 'Sekunden' }} auf hinzugefügte Links!</strong>
                                    </span>
                    </li>
                    <li v-if="!cnl_active" class="list-group-item cnl-blockers">
                      <button v-if="!cnl_active" v-tooltip="'Löschen'" class="btn btn-outline-danger"
                              @click="internalRemove(x[1].name)"><i class="bi bi-trash"></i>
                        Löschen
                      </button>
                    </li>
                  </ul>
                </div>
              </div>

              <div class="myjd-offline">
                <div v-if="x.type=='offline'" v-tooltip="'Links offline'" class="card bg-danger">
                  <div class="card-header">
                    <strong>{{ x.name }}</strong>
                  </div>
                  <ul class="list-group list-group-flush">
                    <li class="list-group-item">
                      <button v-if="!cnl_active" v-tooltip="'Erneut hinzufügen'"
                              class="btn btn-outline-info"
                              @click="myJDretry(x.linkids, x.uuid, x.urls)"><i
                          class="bi bi-arrow-counterclockwise"></i>
                        Erneut
                        hinzufügen
                      </button>
                      <button v-tooltip="'Löschen'"
                              class="btn btn-outline-danger"
                              @click="myJDremove(x.linkids, x.uuid)"><i class="bi bi-trash"></i>
                        Löschen
                      </button>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div v-if="resLengthMyJD>3" class="btn-group">
              <paginate
                  v-model="currentPageMyJD"
                  :next-text="'>'"
                  :page-count="numberOfPagesMyJD"
                  :prev-text="'<'"
              >
              </paginate>
            </div>

            <div v-if="!myjd_state" class="myjd_connection_state">
              <p id="initial-loading">Verbinde mit My JDownloader...</p>
              <div id="spinner-myjd" class="spinner-border text-primary" role="status"></div>
            </div>
            <div v-if="store.state.misc.myjd_connection_error" id="myjd_no_login" class="myjd_connection_state">Fehler
              bei
              Verbindung mit My
              JDownloader!
            </div>
            <div v-if="myjd_state && (myjd_packages.length == 0)" id="myjd_no_packages"
                 class="myjd_connection_state">
              Downloadliste und Linksammler sind leer.
            </div>

            <div v-if="myjd_downloads" id="myjd_state">
              <span v-if="myjd_state=='STOPPED_STATE' || myjd_state=='STOPPING'" id="myjd_start" @click="myJDstart()">
                <i v-tooltip="'Downloads starten'" class="bi bi-play"></i></span>
              <span v-if="myjd_state=='RUNNING'" id="myjd_pause" @click="myJDpause(true)"><i
                  v-tooltip="'Downloads pausieren'" class="bi bi-pause"></i></span>
              <span v-if="myjd_state=='PAUSE'" id="myjd_unpause" @click="myJDpause(false)"><i
                  v-tooltip="'Downloads fortsetzen'" class="bi bi-skip-end-fill"></i></span>
              <span v-if="myjd_state=='RUNNING' || myjd_state=='PAUSE'" id="myjd_stop" @click="myJDstop()"><i
                  v-tooltip="'Downloads anhalten'"
                  class="bi bi-stop"></i></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
