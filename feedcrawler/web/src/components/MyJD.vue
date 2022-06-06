<script setup xmlns="http://www.w3.org/1999/html">
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
  setInterval(getMyJD, 10 * 1000)
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
        packages_per_myjd_page.value = res.data.packages_per_myjd_page
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

const modalPackage = ref({
  name: '',
  path: '',
  urls: '',
  filenames: ['']
})

function setModalPackage(package_) {
  modalPackage.value = package_
}


const resLengthMyJD = ref(0)
const packages_per_myjd_page = ref(3)
const currentPageMyJD = ref(1)
const numberOfPagesMyJD = ref(1)

function getMyJDPages() {
  if (typeof myjd_packages.value !== 'undefined') {
    resLengthMyJD.value = myjd_packages.value.length
    if (resLengthMyJD.value > 0) {
      numberOfPagesMyJD.value = Math.ceil(resLengthMyJD.value / packages_per_myjd_page.value)
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
  return myjd_packages.value.slice((currentPageMyJD.value - 1) * packages_per_myjd_page.value, currentPageMyJD.value * packages_per_myjd_page.value)
})

const myjd_starting = ref(false)

function myJDstart() {
  myjd_starting.value = true
  axios.post('api/myjd_start/')
      .then(function () {
        getMyJDstate()
        console.log('Download gestartet!')
        myjd_starting.value = false
      }, function () {
        console.log('Konnte Downloads nicht starten!')
        toast.error('Konnte Downloads nicht starten!')
        myjd_starting.value = false
      })
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
        myjd_pausing.value = false
      }, function () {
        console.log('Konnte Downloads nicht fortsetzen!')
        toast.error('Konnte Downloads nicht fortsetzen!')
        myjd_pausing.value = false
      })
}

const myjd_stopping = ref(false)

function myJDstop() {
  myjd_stopping.value = true
  axios.post('api/myjd_stop/')
      .then(function () {
        getMyJDstate()
        console.log('Download angehalten!')
        myjd_stopping.value = false
      }, function () {
        console.log('Konnte Downloads nicht anhalten!')
        toast.error('Konnte Downloads nicht anhalten!')
        myjd_stopping.value = false
      })
}

const myjd_updating = ref(false)

function myJDupdate() {
  myjd_updating.value = true
  axios.post('api/myjd_update/')
      .then(function () {
        getMyJDstate()
        console.log('JDownloader geupdatet!')
      }, function () {
        console.log('Konnte JDownloader nicht updaten!')
        toast.error('Konnte JDownloader nicht updaten!')
        myjd_updating.value = false
      })
}

function getMyJDstate() {
  axios.get('api/myjd_state/')
      .then(function (res) {
        myjd_state.value = res.data.downloader_state
        myjd_grabbing.value = res.data.grabber_collecting
        update_ready.value = res.data.update_ready
        if (update_ready.value === false) {
          myjd_updating.value = false
        }
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
  new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false}).show()
  new Collapse(document.getElementById('collapseSponsorsHelper'), {
    toggle: true
  })
}
</script>


<template>
  <div class="container">
    <div class="row my-3">
      <div class="col-md-12">
        <div class="card text-center my-3">
          <div class="card-header">
            <h3>
              <i>
                <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px"
                     width="40" height="40"
                     viewBox="0 0 32 32"
                     style=" fill:#000000;">
                  <path
                      d="M 15.40625 4 C 9.066406 4 3.90625 9.160156 3.90625 15.5 C 3.90625 21.839844 9.066406 27 15.40625 27 C 17.21875 27 18.941406 26.5625 20.46875 25.8125 L 18.75 24.375 C 17.710938 24.765625 16.578125 25 15.40625 25 C 14.859375 25 14.332031 24.933594 13.8125 24.84375 C 14.636719 24.375 15.578125 23.734375 16.5625 22.84375 C 18.214844 21.347656 19.960938 19.148438 21.4375 16.03125 C 22.003906 17.609375 22.476563 19.320313 22.75 21.15625 L 19 22 L 25.03125 27 L 28 20 L 24.71875 20.71875 C 24.300781 18.007813 23.5 15.523438 22.5625 13.375 C 22.886719 12.472656 23.167969 11.5 23.4375 10.46875 C 23.9375 11.265625 24.347656 12.128906 24.59375 13.0625 C 25.265625 14.664063 25.847656 16.445313 26.28125 18.34375 L 26.5625 18.28125 C 26.785156 17.390625 26.90625 16.457031 26.90625 15.5 C 26.90625 9.160156 21.746094 4 15.40625 4 Z M 15.40625 6 C 15.460938 6 15.511719 6 15.5625 6 C 15.605469 6.050781 15.695313 6.15625 15.75 6.21875 L 15.1875 6.3125 L 14.71875 7 L 15.46875 8.125 L 15.28125 8.6875 L 15.84375 9.25 L 17.1875 8.0625 C 18.160156 9.398438 19.347656 11.226563 20.40625 13.5 C 19.164063 16.667969 17.601563 18.910156 16.125 20.46875 L 15.6875 20.4375 L 13.9375 19.65625 L 13.28125 20.0625 L 13 19.03125 L 9.34375 17.4375 L 8.21875 17.53125 L 8.375 18.21875 L 7.96875 20.0625 L 8.9375 20.9375 L 9.46875 21.5625 L 11 22.375 L 11.3125 23.21875 L 11.6875 23.6875 C 11.484375 23.773438 11.257813 23.894531 11.125 23.9375 C 11.117188 23.933594 11.101563 23.941406 11.09375 23.9375 C 8.164063 22.425781 6.109375 19.445313 5.9375 15.96875 L 6.71875 16.46875 L 7.75 17.5 L 6.40625 15.4375 L 6.78125 14.3125 L 7.90625 14.25 L 8.90625 15.53125 L 8.9375 14.5 L 10.34375 13.6875 L 11.3125 12.75 L 13.15625 12.1875 L 12.53125 11.78125 L 14.3125 10.90625 L 14.03125 10.125 L 13.15625 9.65625 L 12.28125 10.1875 L 11.6875 11.21875 L 11.09375 11.0625 L 10.9375 10.03125 L 11.53125 9.5 L 13.28125 8.53125 L 11.875 8.4375 L 10.375 8.6875 L 10.84375 8.21875 L 9.90625 7.78125 C 11.460938 6.671875 13.355469 6 15.40625 6 Z M 18.5625 6.53125 C 19.804688 6.96875 20.929688 7.652344 21.875 8.53125 C 21.703125 9.328125 21.519531 10.09375 21.3125 10.8125 C 20.34375 9.027344 19.378906 7.617188 18.5625 6.53125 Z M 8.40625 9.125 L 8.375 9.25 L 7.53125 10.1875 C 7.789063 9.804688 8.097656 9.464844 8.40625 9.125 Z"></path>
                </svg> <!-- Wrapped in <i> so the distance to My JDownloader text matches other headings -->
              </i>My JDownloader
            </h3>
          </div>
          <div class="card-body">
            <div id="accordionMyJD" class="accordion">
              <div class="accordion-item">
                <h2 id="headingMyJd" class="accordion-header">
                  <button aria-controls="collapseMyJd" aria-expanded="false"
                          class="accordion-button collapsed"
                          data-bs-target="#collapseMyJd"
                          data-bs-toggle="collapse" type="button" @click="manualCollapse">
                    Details
                  </button>
                </h2>
                <div id="collapseMyJd" aria-labelledby="headingMyJd" class="accordion-collapse collapse"
                     data-bs-parent="#accordionMyJD">
                  <div class="accordion-body">
                    <div v-if="!store.state.misc.myjd_connection_error">
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
                                  <button type="button" class="btn btn-outline-info m-1" data-bs-toggle="modal"
                                          data-bs-target="#myJdItemModal"
                                          @click="setModalPackage(x)">
                                    <i class="bi bi-info-square"></i> Details
                                  </button>
                                  <button class="btn btn-outline-danger m-1"
                                          @click="myJDremove(x.linkids, x.uuid, x.name)"><i class="bi bi-trash3"></i>
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
                                  <button type="button" class="btn btn-outline-info m-1" data-bs-toggle="modal"
                                          data-bs-target="#myJdItemModal"
                                          @click="setModalPackage(x)">
                                    <i class="bi bi-info-square"></i> Details
                                  </button>
                                  <button class="btn btn-outline-danger m-1"
                                          @click="myJDremove(x.linkids, x.uuid, x.name)"><i class="bi bi-trash3"></i>
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
                                          @click="myJDremove(x.linkids, x.uuid, x.name)"><i class="bi bi-trash3"></i>
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
                                          @click="internalRemove(x[1].name)"><i class="bi bi-trash3"></i>
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
                                          @click="myJDremove(x.linkids, x.uuid, x.name)"><i class="bi bi-trash3"></i>
                                    Löschen
                                  </button>
                                </li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>
                      <!-- Modal -->
                      <div class="modal fade" id="myJdItemModal" tabindex="-1" aria-labelledby="myJdItemModalLabel"
                           aria-hidden="true">
                        <div class="modal-dialog">
                          <div class="modal-content">
                            <div class="modal-header">
                              <h5 class="modal-title" id="myJdItemModalLabel">Details</h5>
                              <button type="button" class="btn-close" data-bs-dismiss="modal"
                                      aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                              <div class="mb-4">
                                <h4>Paketname</h4>
                                {{ modalPackage.name }}
                              </div>
                              <div class="mb-4">
                                <h4>Pfad</h4>
                                {{ modalPackage.path }}
                              </div>
                              <div class="mb-4">
                                <h4>URLs</h4>
                                <button v-for="(url, index) in modalPackage.urls.split(/\r?\n/)"
                                        class="btn btn-outline-info"
                                        :class="{ 'btn-outline-warning': (url.startsWith('file:/') || url.startsWith('filecrypt')),
                                                   'btn-outline-info': !(url.startsWith('file:/') || url.startsWith('filecrypt'))
                                        }">
                                  <a v-if="!(url.startsWith('file:/') || url.startsWith('filecrypt'))" target="_blank" :href="url">
                                    <i class="bi bi-link-45deg"></i> {{ modalPackage.filenames[index] }}</a>
                                  <span v-else
                                        v-tippy="'URL nicht durch My JDownloader abrufbar!'">
                                    {{ modalPackage.filenames[index] }}</span>
                                </button>
                              </div>
                            </div>
                            <div class="modal-footer">
                              <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                Schließen
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                      <!-- Pagination of MyJD items -->
                      <div v-if="resLengthMyJD>3" class="btn-group">
                        <paginate
                            v-model="currentPageMyJD"
                            :next-text="'>'"
                            :page-count="numberOfPagesMyJD"
                            :prev-text="'<'"
                        >
                        </paginate>
                      </div>
                    </div>
                    <!-- General MyJD information and actions -->
                    <div>
                      <div v-if="!myjd_state">
                        <h4 id="initial-loading">Verbinde mit My JDownloader...</h4>
                        <div class="spinner-border text-primary" role="status"></div>
                      </div>
                      <h4 v-if="store.state.misc.myjd_connection_error">
                        Fehler bei Verbindung mit My JDownloader!
                      </h4>
                      <h4 v-if="myjd_state && (myjd_packages.length === 0)">
                        Downloadliste und Linksammler sind leer.
                      </h4>

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
                      <button v-if="update_ready" id="myjd_stop"
                              :disabled="myjd_updating"
                              :class="{ blinking: myjd_updating }"
                              class="btn btn-outline-primary m-1"
                              @click="myJDupdate()">
                        <i v-if="!myjd_updating" v-tippy="'JDownloader updaten'" class="bi bi-wrench"></i>
                        <i v-else class="spinner-border spinner-border-sm" role="status"></i>
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
