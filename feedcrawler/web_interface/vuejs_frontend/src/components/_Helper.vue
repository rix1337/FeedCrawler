<script setup>
import {useStore} from 'vuex'
import {onMounted, ref} from 'vue'
import axios from 'axios'

import "bootstrap/dist/css/bootstrap.min.css"
import 'bootstrap-icons/font/bootstrap-icons.css'
import "bootstrap"

const store = useStore()

onMounted(() => {
  getContext()
  sponsorCheck()
  updateToDecrypt()
  setInterval(updateToDecrypt, 30 * 1000)
})

function updateToDecrypt() {
  spinHelper()
  getAntiGate()
  getFBlocked()
  getToDecrypt()
}

const context = ref('')

function getContext() {
  // this enables the use of path prefix in production (else the sponsors_helper will only work in vue dev)
  let get_context_from_window = window.location.pathname.split("/").slice(-1)[0]
  if (get_context_from_window.length > 0) {
    context.value = get_context_from_window
  } else {
    context.value = '.'
  }
}

const sponsor = ref(false)

function sponsorCheck() {
  if (window.location.search.includes('sponsor=active')) {
    sponsor.value = true
  }
}

const antigate_active = ref(false)
const antigate_available = ref(false)

function getAntiGate() {
  if (sponsor.value) {
    axios.get("http://127.0.0.1:9700/status")
        .then(function (res) {
          antigate_active.value = res.data
          antigate_available.value = true
        }, function () {
          antigate_available.value = false
          console.log('[FeedCrawler Sponsors Helper] Konnte AntiGate Status nicht abrufen!')
        })
  }
}

const current_to_decrypt = ref('')
const wnd_to_decrypt = ref(false)

const previous_attempts = ref({})

function countPreviousAttempts(url) {
  if (previous_attempts.value[url]) {
    previous_attempts.value[url]++
  } else {
    previous_attempts.value[url] = 1
  }
  console.log('[FeedCrawler Sponsors Helper] ' + url + ' wurde ' + previous_attempts.value[url] + ' mal versucht.')
}

const max_attempts = ref(3)

function tooManyAttempts(url, name) {
  if (antigate_active.value === false) {
    countPreviousAttempts(url)
  }
  if (previous_attempts.value[url] > max_attempts.value) {
    console.log('[FeedCrawler Sponsors Helper] ' + name + ' wurde bereits ' + max_attempts.value + 'x versucht. Lösche Paket...')
    removeFromToDecrypt(name)
    return true
  } else {
    return false
  }
}

const to_decrypt = ref({
  name: '',
  url: false
})

function getToDecrypt() {
  if (sponsor.value) {
    axios.get(context.value + '/api/to_decrypt/')
        .then(function (res) {
          to_decrypt.value = res.data.to_decrypt
          max_attempts.value = to_decrypt.value.max_attempts
          startToDecrypt()
        }, function () {
          console.log('[FeedCrawler Sponsors Helper] Konnte Pakete zum Entschlüsseln nicht abrufen!')
        })
  }
}

function removeFromToDecrypt(name) {
  if (sponsor.value) {
    axios.delete(context.value + '/api/to_decrypt/' + name)
        .then(function (res) {
          console.log('[FeedCrawler Sponsors Helper] ' + name + ' wurde entfernt!')
        }, function () {
          console.log('[FeedCrawler Sponsors Helper] Konnte ' + name + ' nicht entfernen!')
        })
  }
}

function startToDecrypt() {
  if (sponsor.value) {
    if (to_decrypt.value.name !== current_to_decrypt.value) {
      if (wnd_to_decrypt.value) {
        wnd_to_decrypt.value.close()
      }
      if (to_decrypt.value.name && to_decrypt.value.url) {
        if (!tooManyAttempts(to_decrypt.value.url, to_decrypt.value.name)) {
          current_to_decrypt.value = to_decrypt.value.name
          if (antigate_available.value) {
            if (antigate_active.value === false) {
              if (to_decrypt.value.url.includes("filecrypt.") || (to_decrypt.value.url.includes("tolink."))) {
                let clean_url = to_decrypt.value.url
                if (to_decrypt.value.url.includes("#")) {
                  clean_url = to_decrypt.value.url.split('#')[0]
                }
                let title = to_decrypt.value.name
                let password = to_decrypt.value.password
                let payload = btoa(decodeURIComponent(encodeURIComponent((clean_url + "|" + title + "|" + password))))
                console.log('[FeedCrawler Sponsors Helper] Entschlüsselung von ' + title + ' gestartet...')
                wnd_to_decrypt.value = window.open("http://127.0.0.1:9700/?payload=" + payload)
              } else {
                console.log('[FeedCrawler Sponsors Helper] Entschlüsselung von ' + to_decrypt.value.name + ' gestartet...')
                wnd_to_decrypt.value = window.open(to_decrypt.value.url)
              }
            } else {
              console.log('[FeedCrawler Sponsors Helper] Entschlüsselung ist noch aktiv!')
            }
          }
        }
      }
    } else {
      if (wnd_to_decrypt.value && wnd_to_decrypt.value.closed) {
        current_to_decrypt.value = ''
      }
    }
  }
}

function getTimestamp(ms) {
  const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s)
  const d = new Date(ms)

  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const spin_helper = ref(false)

function spinHelper() {
  spin_helper.value = true
  setTimeout(function () {
    spin_helper.value = false
  }, 1000)
}
</script>

<template>
  <main class="text-center">
    <!--- Main Items -->
    <div class="container">
      <div class="row my-3">
        <div class="col-md-6 offset-md-3">
          <div class="card text-center shadow my-3">
            <div class="card-header">
              <h1>
                <i class="bi bi-reception-4"></i> FeedCrawler Sponsors Helper</h1>
            </div>
            <div class=card-body>
            </div>
            <div v-if="!sponsor" class="card-body">
              FeedCrawler Sponsors Helper ist nicht aktuell. Bitte auf neue Version updaten!
            </div>
            <div v-else class="card-body">
              <span v-if="!to_decrypt.url && !to_decrypt.name" class="btn btn-outline-success disabled">Keine verschlüsselten Links vorhanden</span>

              <span v-if="antigate_active === 'true'" class="btn btn-outline-success disabled">Automatische Entschlüsselung ist aktiv!</span><br
                v-if="antigate_active === 'true'">

              <a v-if="to_decrypt.url && to_decrypt.name" :href="to_decrypt.url" class="btn btn-outline-danger"
                 target="_blank">{{
                  to_decrypt.name
                }}</a>
              <br>
              <div v-tippy="'Helper neu laden'"
                   class="btn btn-outline-primary mt-2" @click="updateToDecrypt()">
                <div v-if="spin_helper" class="spinner-border spinner-border-sm" role="status"></div>
                <i v-if="!spin_helper" class="bi bi-arrow-counterclockwise"></i></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
