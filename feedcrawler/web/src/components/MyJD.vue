<script setup>
import {useStore} from 'vuex'
import {computed, onMounted, ref} from 'vue'
import {useRoute} from "vue-router"
import {useToast} from 'vue-toastification'
import {Collapse, Offcanvas} from 'bootstrap'
import axios from 'axios'
import Paginate from "vuejs-paginate-next"

const route = useRoute()
const store = useStore()
const toast = useToast()

onMounted(() => {
  getContext()
  getMyJD()
  setInterval(getMyJD, 5 * 1000)
})

const context = ref('')

function getContext() {
  context.value = route.path.split('/').slice(-1)[0]
}

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
  axios.get('api/myjd/')
      .then(function (res) {
        store.commit("setMyJDConnectionError", false)
        pageSizeMyJD.value = store.state.misc.pageSizeMyJD
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
        getMyJDPages()
        openMyJDTab()
      }, function () {
        myjd_grabbing.value = null
        myjd_downloads.value = null
        myjd_decrypted.value = null
        myjd_failed.value = null
        store.commit("setMyJDConnectionError", true)
        console.log('Konnte JDownloader nicht erreichen!')
        toast.error('Konnte JDownloader nicht erreichen!')
      })
}


const resLengthMyJD = ref(0)
const pageSizeMyJD = ref(3)
const currentPageMyJD = ref(1)
const numberOfPagesMyJD = ref(1)

function getMyJDPages() {
  if (typeof myjd_packages.value !== 'undefined') {
    resLengthMyJD.value = myjd_packages.value.length
    if (resLengthMyJD.value > 0) {
      numberOfPagesMyJD.value = Math.ceil(resLengthMyJD.value / pageSizeMyJD.value)
    } else {
      numberOfPagesMyJD.value = 1
    }
  }
}

const myjd_collapse_manual = ref(false)

function manualCollapse() {
  myjd_collapse_manual.value = true
}

function openMyJDTab() {
  if (!myjd_collapse_manual.value && resLengthMyJD.value > 0) {
    new Collapse(document.getElementById('collapseMyJd'), {
      toggle: true
    })
    myjd_collapse_manual.value = true
  }
}

const currentMyJDPage = computed(() => {
  if (currentPageMyJD.value > numberOfPagesMyJD.value) {
    currentPageMyJD.value = numberOfPagesMyJD.value
  }
  return myjd_packages.value.slice((currentPageMyJD.value - 1) * pageSizeMyJD.value, currentPageMyJD.value * pageSizeMyJD.value)
})

const myjd_starting = ref(false)

function myJDstart() {
  myjd_starting.value = true
  axios.post('api/myjd_start/')
      .then(function () {
        getMyJDstate()
        console.log('Download gestartet!')
      }, function () {
        console.log('Konnte Downloads nicht starten!')
        toast.error('Konnte Downloads nicht starten!')
      })
  myjd_starting.value = false
}

const myjd_pausing = ref(false)

function myJDpause(pause) {
  myjd_pausing.value = true
  axios.post('api/myjd_pause/' + pause)
      .then(function () {
        getMyJDstate()
        if (pause) {
          console.log('Download pausiert!')
        } else {
          console.log('Download fortgesetzt!')
        }
      }, function () {
        console.log('Konnte Downloads nicht fortsetzen!')
        toast.error('Konnte Downloads nicht fortsetzen!')
      })
  myjd_pausing.value = false
}

const myjd_stopping = ref(false)

function myJDstop() {
  myjd_stopping.value = true
  axios.post('api/myjd_stop/')
      .then(function () {
        getMyJDstate()
        console.log('Download angehalten!')
      }, function () {
        console.log('Konnte Downloads nicht anhalten!')
        toast.error('Konnte Downloads nicht anhalten!')
      })
  myjd_stopping.value = false
}

function getMyJDstate() {
  axios.get('api/myjd_state/')
      .then(function (res) {
        myjd_state.value = res.data.downloader_state
        myjd_grabbing.value = res.data.grabber_collecting
        update_ready.value = res.data.update_ready
        myjd_pausing.value = false
        myjd_stopping.value = false
        myjd_starting.value = false
      }, function () {
        console.log('Konnte JDownloader nicht erreichen!')
        toast.error('Konnte JDownloader nicht erreichen!')
      })
}

function myJDmove(linkids, uuid, name) {
  axios.post('api/myjd_move/' + linkids + "&" + uuid)
      .then(function () {
        toast.success('Download ' + name + ' gestartet!')
        getMyJD()
      }, function () {
        console.log('Konnte Download ' + name + ' nicht starten!')
        toast.error('Konnte Download ' + name + ' nicht starten!')
      })
}

function myJDremove(linkids, uuid, name) {
  axios.post('api/myjd_remove/' + linkids + "&" + uuid)
      .then(function () {
        toast.success('Download ' + name + ' gelöscht!')
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
        console.log('Konnte Download ' + name + ' nicht löschen!')
        toast.error('Konnte Download ' + name + ' nicht löschen!')
      })
}

function myJDreset(linkids, uuid, name) {
  axios.post('api/myjd_reset/' + linkids + "&" + uuid)
      .then(function () {
        toast.success('Paket ' + name + ' zurückgesetzt!')
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
        console.log('Konnte Paket ' + name + ' nicht zurücksetzen!')
        toast.error('Konnte Paket ' + name + ' nicht zurücksetzen!')
      })
}

function internalRemove(name) {
  axios.post('api/internal_remove/' + name)
      .then(function () {
        toast.success('Download ' + name + ' gelöscht!')
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
        console.log('Konnte Download ' + name + ' nicht löschen!')
        toast.error('Konnte Download ' + name + ' nicht löschen!')
      })
}

function myJDretry(linkids, uuid, links, name) {
  links = btoa(links)
  axios.post('api/myjd_retry/' + linkids + "&" + uuid + "&" + links)
      .then(function () {
        toast.success('Download ' + name + ' erneut hinzugefügt!')
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
        console.log('Konnte Download ' + name + ' nicht erneut hinzufügen!')
        toast.error('Konnte Download ' + name + ' nicht erneut hinzufügen!')
      })
}

const cnl_active = ref(false)
const time = ref(0)

function internalCnl(name, password) {
  toast.warning("Warte auf Click'n'Load für " + name, {
    timeout: 60000,
    closeOnClick: false,
    closeButton: false,
    pauseOnFocusLoss: false,
    pauseOnHover: false,
  })
  cnl_active.value = true
  time.value = 60
  countDown()
  axios.post('api/internal_cnl/' + name + "&" + password)
      .then(function () {
        toast.success("Click'n'Load für " + name + " erfolgreich!")
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
    console.log("Click'n'Load für " + name + " icht durchgeführt!")
    toast.error("Click'n'Load für " + name + " icht durchgeführt!")
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

function showSponsorsHelp() {
  let offcanvas = new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false})
  offcanvas.show()
  new Collapse(document.getElementById('collapseSponsorsHelper'), {
    toggle: true
  })
  sessionStorage.setItem('fromNav', '')
  window.location.href = "#collapseSponsorsHelper"
}
</script>


<template>
  <div class="container">
    <div class="row my-3">
      <div class="col-md-10 offset-md-1">
        <div class="card text-center my-3">
          <div class="card-header">
            <h3><i class="bi bi-cloud-arrow-down"></i> My JDownloader</h3>
          </div>
          <div class="card-body">
            <div id="accordionMyJD" class="accordion">
              <div class="accordion-item">
                <h2 id="headingMyJd" class="accordion-header">
                  <button id="myjd_collapse" aria-controls="collapseMyJd" aria-expanded="false"
                          class="accordion-button collapsed"
                          data-bs-target="#collapseMyJd"
                          data-bs-toggle="collapse" type="button" @click="manualCollapse">
                    Details
                  </button>
                </h2>
                <div id="collapseMyJd" aria-labelledby="headingMyJd" class="accordion-collapse collapse"
                     data-bs-parent="#accordionMyJD">
                  <div class="accordion-body">
                    <div v-for="x in currentMyJDPage" class="myjd-items">
                      <div class="row m-2">
                        <div class="myjd-downloads">
                          <div v-if="x.type=='online'" class="card bg-success">
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
                                <button class="btn btn-outline-danger m-1"
                                        @click="myJDremove(x.linkids, x.uuid, x.name)"><i class="bi bi-trash"></i>
                                  Löschen
                                </button>
                              </li>
                            </ul>
                          </div>
                        </div>

                        <div class="myjd-decrypted">
                          <div v-if="x.type=='decrypted'" class="card bg-warning">
                            <div class="card-header">
                              <strong>{{ x.name }}</strong> (<span v-text="x.links"></span>)
                            </div>
                            <ul class="list-group list-group-flush">
                              <li v-if="cnl_active" class="list-group-item">
                            <span v-tippy="'Warte auf hinzugefügte Links!'"
                                  class="cnl-spinner">
                                <span class="spinner-border spinner-border-sm" role="status"></span> Warte auf hinzugefügte Links!</span>
                              </li>
                              <li v-if="x.size" class="list-group-item"><span v-text="x.size"></span></li>
                              <li v-if="!cnl_active" class="list-group-item cnl-blockers">
                                <button v-tippy="'Download starten'"
                                        class="btn btn-outline-success m-1"
                                        @click="myJDmove(x.linkids, x.uuid, x.name)"><i class="bi bi-play"></i>
                                  Download
                                  starten
                                </button>
                                <button class="btn btn-outline-danger m-1"
                                        @click="myJDremove(x.linkids, x.uuid, x.name)"><i class="bi bi-trash"></i>
                                  Löschen
                                </button>
                              </li>
                            </ul>
                          </div>
                        </div>

                        <div class="myjd-failed">
                          <div v-if="x.type=='failed'" class="card bg-danger">
                            <div class="card-header">
                              <strong>{{ x.name }}</strong>
                            </div>
                            <ul class="list-group list-group-flush">
                              <li class="list-group-item">
                      <span
                          v-tippy="'Dies tritt auf, wenn das Entpacken fehlschlägt, oder Teile des Paketes offline sind.'">
                        Download fehlgeschlagen!
                      </span>
                              </li>
                              <li class="list-group-item">
                                <button v-if="!cnl_active" class="btn btn-outline-danger m-1"
                                        @click="myJDreset(x.linkids, x.uuid, x.name)"><i
                                    class="bi bi-arrow-clockwise"></i>
                                  Zurücksetzen
                                </button>
                                <button v-if="!cnl_active" class="btn btn-outline-danger m-1"
                                        @click="myJDremove(x.linkids, x.uuid, x.name)"><i class="bi bi-trash"></i>
                                  Löschen
                                </button>
                              </li>
                            </ul>
                          </div>
                        </div>

                        <div class="myjd-to-decrypt">
                          <div v-if="x.type=='to_decrypt'" class="card bg-danger">
                            <div class="card-header">
                              <strong>{{ x[1].name }}</strong>
                            </div>
                            <ul class="list-group list-group-flush">
                              <li v-if="x[1].url" class="list-group-item">
                                <div class="row m-1">
                                  <a v-if="store.state.misc.helper_active && store.state.misc.helper_available && x.first && !cnl_active"
                                     :href="x[1].url + '#' + x[1].name"
                                     class="cnl-button btn btn-outline-success"
                                     target="_blank"
                                     v-tippy="'Da der Click\'n\'Load des FeedCrawler Sponsors Helper verfügbar ist, kann die Click\'n\'Load Automatik hiermit umgangen werden.'"
                                     type="submit">Sponsors Helper Click'n'Load
                                  </a>
                                </div>
                                <span
                                    v-if="( store.state.hostnames.sj && x[1].url.includes(store.state.hostnames.sj.toLowerCase().replace('www.', '')) ) && store.state.misc.helper_active && store.state.misc.helper_available && x.first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a :href="context + './sponsors_helper/feedcrawler_sponsors_helper_sj.user.js'"
                                           target="_blank">FeedCrawler Sponsors Helper (SJ)</a> installieren!
                                    </span>
                                <span
                                    v-if="( store.state.hostnames.dj && x[1].url.includes(store.state.hostnames.dj.toLowerCase().replace('www.', '')) ) && store.state.misc.helper_active && store.state.misc.helper_available && x.first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a :href="context + './sponsors_helper/feedcrawler_sponsors_helper_sj.user.js'"
                                           target="_blank">FeedCrawler Sponsors Helper (DJ)</a> installieren!
                                    </span>
                                <span
                                    v-if="( x[1].url.includes('filecrypt') || ( store.state.hostnames.ww && x[1].url.includes(store.state.hostnames.ww.toLowerCase().replace('www.', '')) ) ) && store.state.misc.helper_active && store.state.misc.helper_available && x.first">Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a :href="context + './sponsors_helper/feedcrawler_sponsors_helper_fc.user.js'"
                                           target="_blank">FeedCrawler Sponsors Helper (FC)</a> installieren!
                                    </span>
                                <div class="row m-1">
                                  <a v-if="!myjd_grabbing && !cnl_active"
                                     :href="x[1].url + '#' + x[1].name"
                                     class="cnl-button btn btn-outline-secondary"
                                     v-tippy="'Click\'n\'Load innerhalb einer Minute auslösen!'"
                                     target="_blank"
                                     type="submit"
                                     @click="internalCnl(x[1].name, x[1].password)">Click'n'Load-Automatik
                                  </a>
                                </div>
                                <span v-if="!myjd_grabbing">Setzt voraus, dass Port 9666 des JDownloaders durch diese Browsersitzung erreichbar ist.</span>
                                <span
                                    v-if="store.state.hostnames.sj && x[1].url.includes(store.state.hostnames.sj.toLowerCase())"><br>Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a :href="context + './sponsors_helper/feedcrawler_helper_sj.user.js'"
                                           target="_blank">FeedCrawler Helper (SJ)</a> installieren!
                                    </span>
                                <span
                                    v-if="store.state.hostnames.dj && x[1].url.includes(store.state.hostnames.dj.toLowerCase())"><br>Bitte zuerst
                                        <a href="https://www.tampermonkey.net/" target="_blank">Tampermonkey</a> und dann
                                        <a :href="context + './sponsors_helper/feedcrawler_helper_sj.user.js'"
                                           target="_blank">FeedCrawler Helper (DJ)</a> installieren!
                                    </span>
                                <span v-if="!store.state.misc.helper_active"><br>
                                        <div class="">Genervt davon, CAPTCHAs manuell zu lösen? Jetzt <a
                                            v-tippy="'Bitte unterstütze die Weiterentwicklung über eine aktive Github Sponsorship!'"
                                            target="_blank"
                                            href="https://github.com/users/rix1337/sponsorship">Sponsor werden</a> und den <a
                                            href="#" @click="showSponsorsHelp()">den Sponsors Helper</a> für dich arbeiten lassen.</div>
                                    </span>
                                <span v-if="myjd_grabbing"><br>Die Click'n'Load-Automatik funktioniert nicht bei aktivem Linkgrabber.</span>
                                <span v-if="cnl_active" class="cnl-spinner"><br>
                                        <span class="spinner-border spinner-border-sm" role="status"></span> <strong>Warte noch {{
                                      time
                                    }} {{ time == 1 ? 'Sekunde' : 'Sekunden' }} auf hinzugefügte Links!</strong>
                                    </span>
                              </li>
                              <li v-if="!cnl_active" class="list-group-item cnl-blockers">
                                <button v-if="!cnl_active" class="btn btn-outline-danger"
                                        @click="internalRemove(x[1].name)"><i class="bi bi-trash"></i>
                                  Löschen
                                </button>
                              </li>
                            </ul>
                          </div>
                        </div>

                        <div class="myjd-offline">
                          <div v-if="x.type=='offline'" class="card bg-danger">
                            <div class="card-header">
                              <strong>{{ x.name }}</strong>
                            </div>
                            <ul class="list-group list-group-flush">
                              <li class="list-group-item">
                                <button v-if="!cnl_active" v-tippy="'Erneut hinzufügen'"
                                        class="btn btn-outline-info m-1"
                                        @click="myJDretry(x.linkids, x.uuid, x.urls, x.name)"><i
                                    class="bi bi-arrow-counterclockwise"></i>
                                  Erneut
                                  hinzufügen
                                </button>
                                <button class="btn btn-outline-danger m-1"
                                        @click="myJDremove(x.linkids, x.uuid, x.name)"><i class="bi bi-trash"></i>
                                  Löschen
                                </button>
                              </li>
                            </ul>
                          </div>
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
                    <div v-if="store.state.misc.myjd_connection_error" id="myjd_no_login"
                         class="myjd_connection_state">
                      Fehler bei Verbindung mit My JDownloader!
                    </div>
                    <div v-if="myjd_state && (myjd_packages.length == 0)" id="myjd_no_packages"
                         class="myjd_connection_state">
                      Downloadliste und Linksammler sind leer.
                    </div>

                    <div v-if="myjd_downloads" id="myjd_state">
                      <button v-if="myjd_state==='STOPPED_STATE' || myjd_state==='STOPPING'" id="myjd_start"
                              :disabled="myjd_starting"
                              :class="{ blinking: myjd_starting }"
                              class="btn btn-outline-primary m-1"
                              @click="myJDstart()">
                        <i v-tippy="'Downloads starten'" class="bi bi-play"></i>
                      </button>
                      <button v-if="myjd_state==='RUNNING'" id="myjd_pause"
                              :disabled="myjd_pausing"
                              :class="{ blinking: myjd_pausing }"
                              class="btn btn-outline-primary m-1"
                              @click="myJDpause(true)">
                        <i v-tippy="'Downloads pausieren'" class="bi bi-pause"></i>
                      </button>
                      <button v-if="myjd_state==='PAUSE'" id="myjd_unpause"
                              :disabled="myjd_pausing"
                              :class="{ blinking: myjd_pausing }"
                              class="btn btn-outline-primary m-1"
                              @click="myJDpause(false)">
                        <i v-tippy="'Downloads fortsetzen'" class="bi bi-skip-end-fill"></i>
                      </button>
                      <button v-if="myjd_state==='RUNNING' || myjd_state==='PAUSE'" id="myjd_stop"
                              :disabled="myjd_stopping"
                              :class="{ blinking: myjd_stopping }"
                              class="btn btn-outline-primary m-1"
                              @click="myJDstop()">
                        <i v-tippy="'Downloads anhalten'" class="bi bi-stop"></i>
                      </button>

                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Blink Animation */
.blinking {
  animation: blink 1s linear infinite;
}

@keyframes blink {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
