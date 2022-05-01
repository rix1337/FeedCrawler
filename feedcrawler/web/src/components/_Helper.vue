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

const antigate_available_and_active = ref(false)

function getAntiGate() {
  axios.get("http://127.0.0.1:9700/status")
      .then(function (res) {
        antigate_available_and_active.value = res.data
      }, function () {
        console.log('[FeedCrawler Sponsors Helper] Konnte AntiGate Status nicht abrufen!')
      })
}

const to_decrypt = ref({
  name: '',
  url: false
})

function getToDecrypt() {
  axios.get(context.value + '/api/to_decrypt/')
      .then(function (res) {
        to_decrypt.value = res.data.to_decrypt
        startToDecrypt()
      }, function () {
        console.log('[FeedCrawler Sponsors Helper] Konnte Pakete zum Entschlüsseln nicht abrufen!')
      })
}

const f_blocked = ref(false)
const sf_hostname = ref('')
const ff_hostname = ref('')
const next_jf_run = ref(0)

function getFBlocked() {
  axios.get(context.value + '/api/f_blocked/False')
      .then(function (res) {
        f_blocked.value = res.data.blocked_sites.sf_ff
        sf_hostname.value = res.data.blocked_sites.sf_hostname
        ff_hostname.value = res.data.blocked_sites.ff_hostname
        next_jf_run.value = res.data.blocked_sites.next_jf_run
      }, function () {
        console.log('[FeedCrawler Sponsors Helper] Konnte Block-Status von SF/FF nicht abrufen!')
      })
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

function tooManyAttempts(url, name) {
  countPreviousAttempts(url)
  if (previous_attempts.value[url] > 3) {
    console.log('[FeedCrawler Sponsors Helper] ' + name + ' wurde bereits 3x versucht. Lösche Paket...')
    removeFromToDecrypt(name)
  } else {
    return false
  }
}

function removeFromToDecrypt(name) {
  axios.delete(context.value + '/api/to_decrypt/' + name)
      .then(function (res) {
        console.log('[FeedCrawler Sponsors Helper] ' + name + ' wurde entfernt!')
      }, function () {
        console.log('[FeedCrawler Sponsors Helper] Konnte ' + name + ' nicht entfernen!')
      })
}

function startToDecrypt() {
  if (to_decrypt.value.name !== current_to_decrypt.value) {
    if (wnd_to_decrypt.value) {
      wnd_to_decrypt.value.close()
    }
    if (to_decrypt.value.name && to_decrypt.value.url) {
      if (!tooManyAttempts(to_decrypt.value.url, to_decrypt.value.name)) {
        current_to_decrypt.value = to_decrypt.value.name
        if (f_blocked.value && sf_hostname.value && to_decrypt.value.url.includes(sf_hostname.value)) {
          console.log('[FeedCrawler Sponsors Helper] SF ist derzeit geblockt!')
        } else if (f_blocked.value && ff_hostname.value && to_decrypt.value.url.includes(ff_hostname.value)) {
          console.log('[FeedCrawler Sponsors Helper] FF ist derzeit geblockt!')
        } else if (antigate_available_and_active.value && to_decrypt.value.url.includes("filecrypt.")) {
          if (antigate_available_and_active.value === "false") {
            let clean_url = to_decrypt.value.url
            console.log(clean_url)
            if (to_decrypt.value.url.includes("#")) {
              clean_url = to_decrypt.value.url.split('#')[0]
            }
            console.log(clean_url)
            let password = to_decrypt.value.password
            let payload = window.btoa(decodeURIComponent(encodeURIComponent((clean_url + "|" + password))))
            wnd_to_decrypt.value = window.open("http://127.0.0.1:9700/?payload=" + payload)
          }
        } else {
          wnd_to_decrypt.value = window.open(to_decrypt.value.url)
        }
      }
    }
  } else {
    if (wnd_to_decrypt.value && wnd_to_decrypt.value.closed) {
      current_to_decrypt.value = ''
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
    <div class="container app col">
      <h1>
        <i class="bi bi-reception-4"></i> FeedCrawler Sponsors Helper</h1>
      <span v-if="!to_decrypt.url && !to_decrypt.name" class="btn btn-outline-success disabled">Keine verschlüsselten Links vorhanden</span>

      <span v-if="antigate_available_and_active === 'true'" class="btn btn-outline-success disabled">Automatische Entschlüsselung von Filecrypt ist aktiv!</span><br
        v-if="antigate_available_and_active === 'true'">

      <span v-if="f_blocked === true" class="btn btn-outline-danger disabled">
        SF/FF haben derzeit die Entschlüsselung gesperrt! Start des nächsten Versuchs: {{
          getTimestamp(next_jf_run)
        }}</span>
      <br v-if="f_blocked === true">

      <a v-if="to_decrypt.url && to_decrypt.name" :href="to_decrypt.url" class="btn btn-outline-danger"
         target="_blank">{{
          to_decrypt.name
        }}</a>
      <br>
      <div v-tippy="'Helper neu laden'"
           class="btn btn-outline-dark" @click="updateToDecrypt()">
        <div v-if="spin_helper" class="spinner-border spinner-border-sm" role="status"></div>
        <i v-if="!spin_helper" class="bi bi-arrow-counterclockwise"></i></div>
    </div>
  </main>
</template>
