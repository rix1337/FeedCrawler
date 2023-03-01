<script setup>
import {useStore} from 'vuex'
import {computed, ref} from 'vue'
import {useToast} from "vue-toastification"
import {submitForm} from '@formkit/vue'
import {Collapse, Offcanvas} from 'bootstrap'
import axios from 'axios'

const store = useStore()
const toast = useToast()

const mb_search = [
  {value: '1', label: '1 Seite'},
  {value: '3', label: '3 Seiten'},
  {value: '5', label: '5 Seiten'},
  {value: '10', label: '10 Seiten'},
  {value: '15', label: '15 Seiten'},
  {value: '30', label: '30 Seiten'}
]

const resolutions = [
  {value: '480p', label: '480p (SD)'},
  {value: '720p', label: '720p (HD)'},
  {value: '1080p', label: '1080p (Full-HD)'},
  {value: '2160p', label: '2160p (4K)'}
]

const sources = [
  {value: 'hdtv|hdtvrip|tvrip', label: 'HDTV'},
  {value: 'web|web-dl|webrip|webhd|netflix*|amazon*|itunes*', label: 'WEB'},
  {value: 'hdtv|hdtvrip|tvrip|web|web-dl|webrip|webhd|netflix*|amazon*|itunes*', label: 'HDTV/WEB'},
  {value: 'bluray|bd|bdrip', label: 'BluRay'},
  {value: 'web|web-dl|webrip|webhd|netflix*|amazon*|itunes*|bluray|bd|bdrip', label: 'Web/BluRay'},
  {
    value: 'hdtv|hdtvrip|tvrip|web|web-dl|webrip|webhd|netflix*|amazon*|itunes*|bluray|bd|bdrip',
    label: 'HDTV/WEB/BluRay'
  },
  {
    value: 'web.*-(tvs|4sj|tvr)|web-dl.*-(tvs|4sj|tvr)|webrip.*-(tvs|4sj|tvr)|webhd.*-(tvs|4sj|tvr)|netflix.*-(tvs|4sj|tvr)|amazon.*-(tvs|4sj|tvr)|itunes.*-(tvs|4sj|tvr)|bluray|bd|bdrip',
    label: 'BluRay/WebRetail (TVS/4SJ/TvR)'
  }
]

function saveSettings() {
  spin_settings.value = true
  axios.post('api/settings/', store.state.settings)
      .then(function () {
        console.log('Einstellungen gespeichert! Neustart des FeedCrawlers wird dringend empfohlen!')
        toast.success('Einstellungen gespeichert! Neustart des FeedCrawlers wird dringend empfohlen!')
        store.commit("getSettings")
        spin_settings.value = false
      }, function () {
        store.commit("getSettings")
        spin_settings.value = false
        console.log('Konnte Einstellungen nicht speichern! Bitte die angegebenen Werte auf Richtigkeit prüfen.')
        toast.error('Konnte Einstellungen nicht speichern! Bitte die angegebenen Werte auf Richtigkeit prüfen.')
      })
}

const spin_settings = ref(false)

function showMultiHosterHelp() {
  new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false}).show()
  new Collapse(document.getElementById('collapseMultiHoster'), {
    toggle: true
  })
}

const password_changed = computed(() => (store.state.settings.general.auth_hash.length > 0))

function submitSettings() {
  submitForm('settings')
}

function showWikiHelp() {
  new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false}).show()
  new Collapse(document.getElementById('collapsePlexDirect'), {
    toggle: true
  })
}
</script>


<template>
  <div class="text-center">
    <div id="offcanvasBottomSettings" aria-labelledby="offcanvasBottomSettingsLabel" class="offcanvas offcanvas-bottom"
         tabindex="-1">
      <div class="offcanvas-header">
        <h3 id="offcanvasBottomSettingsLabel" class="offcanvas-title"><i class="bi bi-gear"></i> Einstellungen</h3>
        <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas" type="button"></button>
      </div>
      <div class="offcanvas-body">
        <h4 v-if="!store.state.misc.loaded_settings">Einstellungen werden geladen...</h4>
        <div v-if="store.state.misc.loaded_settings" id="accordionSettings" class="accordion">
          <FormKit id="settings" #default="{ value }"
                   :actions="false"
                   incomplete-message="Es müssen alle Felder korrekt ausgefüllt werden! Fehler sind rot markiert."
                   messages-class="text-danger mt-4"
                   type="form"
                   @submit="saveSettings()"
          >
            <div class="accordion-item">
              <h2 id="headingSettingsMyJd" class="accordion-header">
                <button aria-controls="collapseSettingsMyJd" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsMyJd"
                        data-bs-toggle="collapse" type="button">
                  My JDownloader
                </button>
              </h2>
              <div id="collapseSettingsMyJd" aria-labelledby="headingSettingsMyJd" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.general.myjd_user"
                           help="Hier die E-Mail Adresse des Kontos bei My JDownloader angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="E-Mail Adresse"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. name@mail.com"
                           type="email"
                           validation="required|length:5|*email"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.general.myjd_pass"
                           help="Hier das Passwort von My JDownloader angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Passwort"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. ●●●●●●●●"
                           type="password"
                           validation="required"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.general.myjd_device"
                           help="Hier den Gerätenamen des mit dem obigen My JDownloader-Konto verbundenen JDownloaders angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Gerätename"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. JDownloader@Server"
                           type="text"/>
                  <h5>Autostart</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.crawljobs.autostart"
                             help="Wenn aktiviert, werden Downloads automatisch gestartet, sobald diese entschlüsselt vorliegen."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Automatische Updates</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.myjd_auto_update"
                             help="Wenn aktiviert, wird am Ende jedes Suchlaufs geprüft, ob ein Update verfügbar ist. Verfügbare Updates werden bei inaktivem JDownloader sofort ausgeführt und der JDownloader dafür neugestartet."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Unterordner bei Download</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.crawljobs.subdir"
                             :validation="value.subdir_type ? 'accepted' : ''"
                             :validation-messages="{
                              accepted: 'Unterordner nach Typ setzt voraus, dass Unterordner bei Download aktiviert ist!'
                             }"
                             help="Wenn aktiviert, werden Downloads in passende Unterordner sortiert - Empfohlen für die Weiterverarbeitung per Script!"
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"
                             validation-visibility="live"/>
                  </label>
                  <h5>Unterordner nach Typ</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.crawljobs.subdir_by_type"
                             help="Wenn aktiviert, werden Serien und Filme in getrennte Unterordner sortiert"
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             name="subdir_type"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <FormKit v-model="store.state.settings.general.packages_per_myjd_page"
                           help="Pakete ab dieser Anzahl werden auf Folgeseiten umgebrochen, was unnötiges Scrollen verhindert."
                           help-class="text-muted"
                           input-class=" form-control bg-light mb-2"
                           label="Pakete pro Seite"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. 3"
                           type="number"
                           validation="required|between:3,30"
                           validation-visibility="live"/>
                </div>
              </div>
            </div>
            <div class="accordion-item">
              <h2 id="headingGeneral" class="accordion-header">
                <button aria-controls="collapseGeneral" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseGeneral"
                        data-bs-toggle="collapse" type="button">
                  Allgemein
                </button>
              </h2>
              <div id="collapseGeneral" aria-labelledby="headingGeneral" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <div v-if="!store.state.misc.docker">
                    <FormKit v-model="store.state.settings.general.port"
                             help="Hier den Port des Webservers wählen."
                             help-class="text-muted"
                             input-class="form-control bg-light mb-2"
                             label="Port"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             placeholder="Bspw. 9090"
                             type="number"
                             validation="required|between:1024,65535"
                             validation-visibility="live"/>
                  </div>
                  <FormKit v-model="store.state.settings.general.prefix"
                           help="Hier den Prefix des Webservers wählen (nützlich für Reverse-Proxies)."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Prefix"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. feedcrawler"
                           type="text"
                           validation="alpha"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.general.auth_user"
                           :validation="value.auth_hash ? 'required' : ''"
                           help="Hier den Nutzernamen für FeedCrawler eingeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Nutzername"
                           messages-class="text-danger"
                           name="auth_user"
                           outer-class="mb-4"
                           placeholder="Bspw. rix1337"
                           type="text"/>
                  <FormKit v-model="store.state.settings.general.auth_hash"
                           :validation="(password_changed && value.auth_user) ? 'required|length:6' : ''"
                           help="Hier das Passwort für FeedCrawler angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Passwort"
                           messages-class="text-danger"
                           name="auth_hash"
                           outer-class="mb-4"
                           placeholder="Bspw. ●●●●●●●●"
                           type="password"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.general.interval"
                           help="Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren. Aus Sicherheitsgründen wird das Intervall zufällig um bis zu 25% erhöht."
                           help-class="text-muted"
                           input-class=" form-control bg-light mb-2"
                           label="Suchintervall (Allgemein)"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. 60"
                           type="number"
                           validation="required|between:5,1440"
                           validation-visibility="live"/>
                  <h5>Wartezeit ({{ store.state.hostnames.jf }})</h5> <!-- Setting variables in label is unsupported -->
                  <FormKit v-model="store.state.settings.jf.wait_time"
                           help="Die Wartezeit in Stunden sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren."
                           help-class="text-muted"
                           input-class=" form-control bg-light mb-2"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. 12"
                           type="number"
                           validation="required|between:6,24"
                           validation-visibility="live"/>
                  <h5>Ein Mirror genügt</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.one_mirror_policy"
                             help="Wenn aktiviert, und sofern mindestens ein entschlüsselter Link im Paket vorhanden ist, werden vor dem Download alle Links aus einem Paket entfernt die offline oder verschlüsselt sind. Das ermöglicht den sofortigen Start ohne Click'n'Load-Automatik - betrifft aber alle Pakete im JDownloader!"
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Filterliste in Web-Suche erzwingen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.force_ignore_in_web_search"
                             help="Die Web-Suche erlaubt, wenn keine anderen Releases verfügbar sind, auch Releases, die nicht der für die Feed-Suche gesetzten Filterliste entsprechen. Wenn aktiviert, werden betroffene Releases, analog zur Feed-Suche ignoriert."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Englische Releases hinzufügen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.english"
                             help="Wenn aktiviert, werden auch englischsprachige Titel gesucht."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Mehrkanalton erzwingen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.surround"
                             help="Wenn aktiviert, werden ausschließlich Titel mit Mehrkanalton-Tags hinzugefügt."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                </div>
              </div>
            </div>
            <div class="accordion-item">
              <h2 id="headingSolvers" class="accordion-header">
                <button aria-controls="collapseSolvers" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseSolvers"
                        data-bs-toggle="collapse" type="button">
                  Cloudfare-Umgehung
                </button>
              </h2>
              <div id="collapseSolvers" aria-labelledby="headingSolvers" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.general.sponsors_helper"
                           help="Hier die URL des durch FeedCrawler erreichbaren Sponsors Helpers (Port 9700) angeben. Der Sponsors Helper wird für jede Seite genutzt, auf der eine Blockade durch Cloudflare erkannt wurde."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Sponsors-Helper-URL"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. http://192.168.0.1:9700"
                           type="url"
                           validation="url"
                           validation-visibility="live"/>
                  <mark>
                    Die zuverlässigste Möglichkeit, Cloudflare-Blockaden zu umgehen, ist dafür zu bezahlen.<br>
                    Über den Sponsors Helper ist es möglich, vor dem Suchlauf erkannte Cloudflare-Blockaden zu umgehen.
                    Dabei wird pro blockierter Seite ein kurzfristig gültiger Cloudflare-Cookie erzeugt, der dann für
                    den Suchlauf verwendet wird. Die Kosten pro Seite und Suchlauf liegen im Sub-Cent-Bereich.<br>
                    Um Kosten zu sparen, kann parallel ein FlareSolverr betrieben werden.
                  </mark>
                  <FormKit v-model="store.state.settings.general.flaresolverr"
                           help="Hier die URL eines durch FeedCrawler erreichbaren FlareSolverrs angeben. FlareSolverr wird für jede Seite genutzt, auf der eine Blockade durch Cloudflare erkannt wurde."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="FlareSolverr-URL"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. http://192.168.0.1:8191"
                           type="url"
                           validation="url"
                           validation-visibility="live"/>
                  <mark>
                    FlareSolverr ist ein lokaler Proxy-Server zur kostenlosen Umgehung von Cloudflare-Blockaden.<br>
                    Die Umgehung funktioniert nicht immer zuverlässig, da Cloudflare die Blockaden immer wieder ändert.
                    In unregelmäßigen Abständen vorgeschaltete CAPTCHAs werden durch FlareSolverr nicht umgangen.<br>
                    Wird bevorzugt genutzt, da die Coudflare-Umgehung mit FlareSolverr kostenlos ist.<br>
                    Damit FeedCrawler und FlareSolverr die selbe IP benutzen, muss im FlareSolverr IPv6 deaktiviert
                    werden.<br>
                    Dafür den FlareSolverr-Container mit --sysctl net.ipv6.conf.all.disable_ipv6=1 starten.
                  </mark>
                </div>
              </div>
            </div>
            <div class="accordion-item">
              <h2 id="headingHosters" class="accordion-header">
                <button aria-controls="collapseHosters" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseHosters"
                        data-bs-toggle="collapse" type="button">
                  Hoster
                </button>
              </h2>
              <div id="collapseHosters" aria-labelledby="headingHosters" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div
                    v-tippy="'Für jeden gewählten Hoster werden Links hinzugefügt, sofern verfügbar. Der damit einhergehende CAPTCHA-Bedarf sollte beachtet werden! Ist kein gewählter Hoster am Release verfügbar, wird dieses übersprungen!'"
                    class="accordion-body">
                  <div class="row">
                    <div class="col-sm">
                      <h5>DDownload</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.ddl"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>Rapidgator</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.rapidgator"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>1Fichier</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.onefichier"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>Turbobit</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.turbobit"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                    </div>
                    <div class="col-sm">
                      <h5>Uploaded</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.uploaded"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>FileFactory</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.filefactory"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>Uptobox</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.uptobox"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>Filer</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.filer"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>Zippyshare</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.zippyshare"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                    </div>
                    <div class="col-sm">
                      <h5>Nitroflare</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.nitroflare"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>Keep2Share</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.k2s"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>KatFile</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.katfile"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                      <h5>IronFiles</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.ironfiles"
                                 help-class="text-muted"
                                 input-class="form-check-input"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 type="checkbox"/>
                      </label>
                    </div>
                    <div class="row mb-4">
                      <mark>Als Multihoster unterstützt <a href="#" @click="showMultiHosterHelp()">LinkSnappy</a>
                        die meisten hier aktivierbaren Hoster.
                      </mark>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="accordion-item">
              <h2 id="headingNotifications" class="accordion-header">
                <button aria-controls="collapseNotifications" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseNotifications"
                        data-bs-toggle="collapse" type="button">
                  Benachrichtigungen
                </button>
              </h2>
              <div id="collapseNotifications" aria-labelledby="headingNotifications" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.alerts.discord"
                           :validation="[['matches', /^\d+?,\S+?$/]]"
                           :validation-messages="{
                              matches: 'Bitte die Webhook-ID und dann kommagetrennt den Webhook-Token eines Discord-Kanals angeben (ohne Leerzeichen).'
                           }"
                           help="Hier kommagetrennt die Webhook-ID und danach den Webhook-Token angeben. Beide sind Teil der Webhook-URL: https://discord.com/api/webhooks/[Webhook-ID]/[Webhook-Token]"
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Discord"
                           messages-class="text-danger"
                           outer-class="mb-2"
                           placeholder="Bspw. 1041924765142156906,JxxhatQggSXPcyOpSefXwtoXpSEYLLDwXYCgzuSulcHADQLhJflSCVQhLOmOYRTaazrY"
                           type="text"
                           validation-visibility="live"/>
                  <div class="mb-4">
                    <mark>Discord ist der beste Weg, Benachrichtigungen zu versenden. Webhooks sind sehr einfach
                      einzurichten und Discord unterstützt den Versand von Postern.
                    </mark>
                  </div>
                  <FormKit v-model="store.state.settings.alerts.telegram"
                           :validation="[['matches', /^\d+?:[^\s]+?,\d+?$/]]"
                           :validation-messages="{
                              matches: 'Bitte den Token des eigenen Bots und dann kommagetrennt die Chat-ID des Ziel-Chats angeben (ohne Leerzeichen).'
                           }"
                           help="Hier kommagetrennt den Token des eigenen Bots und danach die Chat-ID des Ziel-Chats angeben. Beide werden im Chat mit BotFather angelegt."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Telegram"
                           messages-class="text-danger"
                           outer-class="mb-2"
                           placeholder="Bspw. 123456789:sYV4B-Ez5yTh3heyFquV4QgQSW2XSBLF9Xj,987654321"
                           type="text"
                           validation-visibility="live"/>
                  <div class="mb-4">
                    <mark>Telegram unterstützt ebenfalls den Versand von Postern.</mark>
                  </div>
                  <FormKit v-model="store.state.settings.alerts.pushbullet"
                           :validation="[['matches', /^o\.[A-Za-z0-9]+$/]]"
                           :validation-messages="{
                              matches: 'Bitte einen validen Access-Token angeben.'
                           }"
                           help="Access-Token auf Pushbullet.com anlegen und hier angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Pushbullet"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. o.12345ABCBCQJMmfhpWkkNFby7Z7qd6Rj"
                           type="text"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.alerts.pushover"
                           :validation="[['matches', /^[A-Za-z0-9]{30},[A-Za-z0-9]{30}$/]]"
                           :validation-messages="{
                              matches: 'Bitte den User-Key und dann kommagetrennt einen API-Token angeben (ohne Leerzeichen).'
                           }"
                           help="Hier kommagetrennt den User-Key und danach einen API-Token angeben. Letzteren zunächst auf Pushover.net anlegen."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Pushover"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. uQiRzpo4DXghDmr9QzzfQu27cmVRsG,azGDORePK8gMaC0QOYAMyEEuzJnyUi"
                           type="text"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.alerts.homeassistant"
                           help="Hier kommagetrennt die URL zur API und danach das Passwort angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Home Assistant"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. http://192.168.0.1:8080,Passwort"
                           type="url"
                           validation="url"
                           validation-visibility="live"/>
                </div>
              </div>
            </div>
            <div class="accordion-item">
              <h2 id="headingRequestManagement" class="accordion-header">
                <button aria-controls="collapseRequestManagement" aria-expanded="false"
                        class="accordion-button collapsed"
                        data-bs-target="#collapseRequestManagement"
                        data-bs-toggle="collapse" type="button">
                  Anfrage-Verwaltung
                </button>
              </h2>
              <div id="collapseRequestManagement" aria-labelledby="headingRequestManagement"
                   class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.plex.url"
                           :validation="[['matches', /^https:\/\/.*\.plex.direct:\d{1,6}$/]]"
                           :validation-messages="{
                              matches: 'Bitte die Plex-Direct-URL inklusive https:// und Port angeben!'
                           }"
                           help="Hier die Plex-Direct-URL des eigenen Plex-Servers angeben, inklusive https:// und Port."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Plex-Direct-URL"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. https://192-168-0-1.a1bcd234abc123456c7891011def12g9.plex.direct:32400"
                           type="url"
                           validation="url"
                           validation-visibility="live"/>
                  <div class="mb-4">
                    <span>Wie eine Plex-Direct-URL ermittelt wird, ist im <a href="#" @click="showWikiHelp()">Wiki</a>
                      beschrieben.
                    </span>
                  </div>
                  <h5>Plex Integration</h5>
                  <div class="mb-4">
                    <div v-if="store.state.settings.plex.url !== ''">
                      <div v-if="!store.state.settings.plex.api">
                        <mark>
                          <a href="./api/plex_auth/">Hier</a> authentifizieren.
                        </mark>
                      </div>
                      <div v-else>
                        <span class="text-success">
                          Erfolgreich authentifiziert.
                        </span>
                      </div>
                    </div>
                    <div v-else>
                      <span class="text-danger">
                        Bitte zuerst eine valide Plex URL eintragen und <strong>speichern</strong>!
                      </span>
                    </div>
                  </div>
                  <FormKit v-model="store.state.settings.overseerr.url"
                           :validation="value.overseerr_api ? 'required|url' : 'url'"
                           help="Hier die URL von Overseerr angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Overseerr URL"
                           messages-class="text-danger"
                           name="overseerr_url"
                           outer-class="mb-4"
                           placeholder="Bspw. http://192.168.0.1:5055"
                           type="url"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.overseerr.api"
                           :validation="value.overseerr_url ? 'required|length:10' : 'length:10'"
                           :validation-messages="{
                              matches: 'Bitte einen validen API-Key angeben.'
                           }"
                           help="Hier den API-Key von Overseerr angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Overseerr API-Key"
                           messages-class="text-danger"
                           name="overseerr_api"
                           outer-class="mb-4"
                           placeholder="Bspw. V2hhdCB3ZXJlIHlvdSBsb29raW5nIGZvcj8KV2h5IGFyZSB5b3UgZXZlbiBoZXJlPw=="
                           type="text"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.ombi.url"
                           :validation="value.ombi_api ? 'required|url' : 'url'"
                           help="Hier die URL von Ombi angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Ombi URL"
                           messages-class="text-danger"
                           name="ombi_url"
                           outer-class="mb-4"
                           placeholder="Bspw. http://192.168.0.1:5000/ombi"
                           type="url"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.ombi.api"
                           :validation="value.ombi_url ? 'required|length:10' : 'length:10'"
                           :validation-messages="{
                              matches: 'Bitte einen validen API-Key angeben.'
                           }"
                           help="Hier den API-Key von Ombi angeben."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Ombi API-Key"
                           messages-class="text-danger"
                           name="ombi_api"
                           outer-class="mb-4"
                           placeholder="Bspw. UQ6oVaEuPR3CyyhEfi2uT32PrRJfitfv3WG"
                           type="text"
                           validation-visibility="live"/>
                </div>
              </div>
            </div>
            <div v-if="store.state.hostnames.bl !== 'Nicht gesetzt!'" class="accordion-item">
              <h2 id="headingSettingsBl" class="accordion-header">
                <button aria-controls="collapseSettingsBl" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsBl"
                        data-bs-toggle="collapse" type="button">
                  {{ store.state.hostnames.bl }}
                </button>
              </h2>
              <div id="collapseSettingsBl" aria-labelledby="headingSettingsBl" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.mb.quality"
                           help="Die Release-Auflösung, nach der gesucht wird."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Auflösung"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           type="select">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.mb.search"
                           help="Hier wählen, wie weit die Suche in die Vergangenheit gehen soll (Je weiter, desto länger dauert der Suchlauf)!"
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Suchtiefe"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           type="select">
                    <option v-for="option in mb_search" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.mb.ignore"
                           help="Releases mit diesen Begriffen werden nicht durch die Feed-Suche hinzugefügt (kommagetrennt)."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Filterliste"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. cam,subbed,xvid,dvdr,untouched,remux,mpeg2,avc,pal,md,ac3md,mic,xxx"
                           type="text"/>
                  <h5>Auch per RegEx suchen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.regex"
                             help="Wenn aktiviert, werden Filme aus der Filme (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <FormKit v-model="store.state.settings.mb.imdb_score"
                           help="Alle Filme die im Feed über der genannten Wertung auftauchen, werden hinzugefügt - Wert unter 6,5 nicht empfehlenswert, 0 zum Deaktivieren."
                           help-class="text-muted"
                           input-class=" form-control bg-light mb-2"
                           label="Ab IMDb-Wertung hinzufügen"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. 6,5"
                           required
                           step="0.1"
                           type="number"
                           validation="required|between:0.0,10.0"
                           validation-visibility="live"/>
                  <FormKit v-model="store.state.settings.mb.imdb_year"
                           help="Berücksichtige Filme bei IMDb-Suche erst ab diesem Erscheinungsjahr."
                           help-class="text-muted"
                           input-class=" form-control bg-light mb-2"
                           label="IMDb hinzufügen ab Erscheinungsjahr"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. 2020"
                           type="number"
                           validation="between:1900,2099"
                           validation-visibility="live"/>
                  <h5>Zweisprachige Releases erzwingen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.force_dl"
                             help="Wenn aktiviert, sucht das Script zu jedem nicht zweisprachigen Release (kein DL-Tag im Titel), das nicht O-Ton Deutsch ist, ein passendes Release in 1080p mit DL-Tag. Findet das Script kein Release wird dies im DEBUG-Log vermerkt. Bei der nächsten Ausführung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nützlich um (durch späteres Remuxen) eine zweisprachige Bibliothek in 720p zu erhalten."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Nur Retail hinzufügen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.retail_only"
                             help="Wenn aktiviert, werden nur Retail-Releases hinzugefügt."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Listeneintrag bei Retail streichen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.cutoff"
                             help="Wenn aktiviert, werden Filme aus der Filme-Liste gestrichen, sobald ein Retail-Release gefunden wurde."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>1080p-HEVC bevorzugen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.hevc_retail"
                             help="Wenn aktiviert, werden Retail-Releases von Filmen in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen. Entspricht außerdem ein beliebiges Filmrelease den Retail-Kriterien, wir ad hoc nach einem Retail-Release in 1080p mit den Tags HEVC, h265 oder x265 gesucht. Wird ein solches gefunden, wird nur dieses hinzugefügt (das andere ignoriert). Für alle anderen Releases greifen die Einstellungen der Auflösung und Filterliste."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Hoster-Fallback</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.hoster_fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <div v-if="store.state.hostnames.s === 'Nicht gesetzt!'">
                    <h5>Staffeln suchen</h5> <!-- Checkbox labels are not placed above -->
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.enabled"
                               help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                               help-class="text-muted"
                               input-class="form-check-input"
                               messages-class="text-danger"
                               outer-class="mb-4"
                               type="checkbox"/>
                    </label>
                    <FormKit v-model="store.state.settings.mbsj.quality"
                             help="Die Release-Auflösung der Staffeln, nach der gesucht wird."
                             help-class="text-muted"
                             input-class="form-control bg-light mb-2"
                             label="Auflösung der Staffeln"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="select">
                      <option v-for="option in resolutions" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
                    <h5>Staffelpakete erlauben</h5> <!-- Checkbox labels are not placed above -->
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.packs"
                               help="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                               help-class="text-muted"
                               input-class="form-check-input"
                               messages-class="text-danger"
                               outer-class="mb-4"
                               type="checkbox"/>
                    </label>
                    <FormKit v-model="store.state.settings.mbsj.source"
                             help="Die Quellart der Staffeln, nach der gesucht wird."
                             help-class="text-muted"
                             input-class="form-control bg-light mb-2"
                             label="Quellart der Staffeln"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="select">
                      <option v-for="option in sources" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="store.state.hostnames.s !== 'Nicht gesetzt!'" class="accordion-item">
              <h2 id="headingSettingsS" class="accordion-header">
                <button aria-controls="collapseSettingsS" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsS"
                        data-bs-toggle="collapse" type="button">
                  {{ store.state.hostnames.s }}
                </button>
              </h2>
              <div id="collapseSettingsS" aria-labelledby="headingSettingsS" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.sj.quality"
                           help="Die Release-Auflösung, nach der gesucht wird."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Auflösung"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           type="select">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.sj.ignore"
                           help="Releases mit diesen Begriffen werden nicht durch die Feed-Suche hinzugefügt (kommagetrennt)."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Filterliste"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. XviD,Subbed,HDTV"
                           type="text"/>
                  <h5>Auch per RegEx suchen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.regex"
                             help="Wenn aktiviert, werden Serien aus der Serien (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Nur Retail hinzufügen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.retail_only"
                             help="Wenn aktiviert, werden nur Retail-Releases hinzugefügt."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>1080p-HEVC bevorzugen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.hevc_retail"
                             help="Wenn aktiviert, werden Retail-Releases von Serien in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Hoster-Fallback</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.hoster_fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <div v-if="store.state.hostnames.bl === 'Nicht gesetzt!'">
                    <h5>Staffeln suchen</h5> <!-- Checkbox labels are not placed above -->
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.enabled"
                               help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                               help-class="text-muted"
                               input-class="form-check-input"
                               messages-class="text-danger"
                               outer-class="mb-4"
                               type="checkbox"/>
                    </label>
                    <FormKit v-model="store.state.settings.mbsj.quality"
                             help="Die Release-Auflösung der Staffeln, nach der gesucht wird."
                             help-class="text-muted"
                             input-class="form-control bg-light mb-2"
                             label="Auflösung der Staffeln"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="select">
                      <option v-for="option in resolutions" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
                    <h5>Staffelpakete erlauben</h5> <!-- Checkbox labels are not placed above -->
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.packs"
                               help="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                               help-class="text-muted"
                               input-class="form-check-input"
                               messages-class="text-danger"
                               outer-class="mb-4"
                               type="checkbox"/>
                    </label>
                    <FormKit v-model="store.state.settings.mbsj.source"
                             help="Die Quellart der Staffeln, nach der gesucht wird."
                             help-class="text-muted"
                             input-class="form-control bg-light mb-2"
                             label="Quellart der Staffeln"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="select">
                      <option v-for="option in sources" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
                    <div
                        v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f === store.state.hostnames.s">
                      <FormKit v-model="store.state.settings.f.search"
                               help="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren."
                               help-class="text-muted"
                               input-class=" form-control bg-light mb-2"
                               label="Suchtiefe"
                               messages-class="text-danger"
                               outer-class="mb-4"
                               placeholder="Bspw. 3"
                               type="number"
                               validation="required|between:1,7"
                               validation-visibility="live"/>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div
                v-if="store.state.hostnames.sjbl !== 'Nicht gesetzt!' && store.state.settings.mbsj.enabled && store.state.misc.sjbl_enabled"
                class="accordion-item">
              <h2 id="headingSettingsSjBl" class="accordion-header">
                <button aria-controls="collapseSettingsSjBl" aria-expanded="false"
                        class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsSjBl"
                        data-bs-toggle="collapse" type="button">
                  {{ store.state.hostnames.sjbl }}
                </button>
              </h2>
              <div id="collapseSettingsSjBl" aria-labelledby="headingSettingsSjBl"
                   class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <h5>Staffeln suchen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mbsj.enabled"
                             help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <FormKit v-model="store.state.settings.mbsj.quality"
                           help="Die Release-Auflösung der Staffeln, nach der gesucht wird."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Auflösung der Staffeln"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           type="select">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <h5>Staffelpakete erlauben</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mbsj.packs"
                             help="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <FormKit v-model="store.state.settings.mbsj.source"
                           help="Die Quellart der Staffeln, nach der gesucht wird."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Quellart der Staffeln"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           type="select">
                    <option v-for="option in sources" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <div
                      v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f === store.state.hostnames.sjbl">
                    <FormKit v-model="store.state.settings.f.search"
                             help="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren."
                             help-class="text-muted"
                             input-class=" form-control bg-light mb-2"
                             label="Suchtiefe"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             placeholder="Bspw. 3"
                             type="number"
                             validation="required|between:1,7"
                             validation-visibility="live"/>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="store.state.hostnames.dj !== 'Nicht gesetzt!'" class="accordion-item">
              <h2 id="headingSettingsDj" class="accordion-header">
                <button aria-controls="collapseSettingsDj" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsDj"
                        data-bs-toggle="collapse" type="button">
                  {{ store.state.hostnames.dj }}
                </button>
              </h2>
              <div id="collapseSettingsDj" aria-labelledby="headingSettingsDj" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.dj.quality"
                           help="Die Release-Auflösung, nach der gesucht wird."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Auflösung"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           type="select">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.dj.ignore"
                           help="Releases mit diesen Begriffen werden nicht durch die Feed-Suche hinzugefügt (kommagetrennt)."
                           help-class="text-muted"
                           input-class="form-control bg-light mb-2"
                           label="Filterliste"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. XviD,Subbed,HDTV"
                           type="text"/>
                  <h5>Auch per RegEx suchen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.dj.regex"
                             help="Wenn aktiviert, werden Serien aus der Dokus (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                  <h5>Hoster-Fallback</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.dj.hoster_fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                </div>
              </div>
            </div>
            <div v-if="store.state.hostnames.dd !== 'Nicht gesetzt!'" class="accordion-item">
              <h2 id="headingSettingsDd" class="accordion-header">
                <button aria-controls="collapseSettingsDd" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsDd"
                        data-bs-toggle="collapse" type="button">
                  {{ store.state.hostnames.dd }}
                </button>
              </h2>
              <div id="collapseSettingsDd" aria-labelledby="headingSettingsDd" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <h5>Hoster-Fallback</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.dd.hoster_fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                </div>
              </div>
            </div>
            <div
                v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f !== store.state.hostnames.sjbl"
                class="accordion-item">
              <h2 id="headingSettingsF" class="accordion-header">
                <button aria-controls="collapseSettingsF" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsF"
                        data-bs-toggle="collapse" type="button">
                  {{ store.state.hostnames.f }}
                </button>
              </h2>
              <div id="collapseSettingsF" aria-labelledby="headingSettingsF" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.f.search"
                           help="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren."
                           help-class="text-muted"
                           input-class=" form-control bg-light mb-2"
                           label="Suchtiefe"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. 3"
                           type="number"
                           validation="required|between:1,7"
                           validation-visibility="live"/>
                </div>
              </div>
            </div>
            <div
                v-if="store.state.misc.helper_active"
                class="accordion-item">
              <h2 id="headingSettingsHelper" class="accordion-header">
                <button aria-controls="collapseSettingsHelper" aria-expanded="false"
                        class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsHelper"
                        data-bs-toggle="collapse" type="button">
                  FeedCrawler Sponsors Helper
                </button>
              </h2>
              <div id="collapseSettingsHelper" aria-labelledby="headingSettingsHelper"
                   class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <FormKit v-model="store.state.settings.sponsors_helper.max_attempts"
                           help="Um keine CAPTCHA-Credits zu verschwenden, löscht der FeedCrawler Sponsor Helper ein Paket, nachdem dieser Schwellwert erreicht wurde."
                           help-class="text-muted"
                           input-class=" form-control bg-light mb-2"
                           label="Erlaubte Fehlversuche"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           placeholder="Bspw. 3"
                           type="number"
                           validation="required|between:1,10"
                           validation-visibility="live"/>
                  <h5>Spenden-Banner automatisch ausblenden</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sponsors_helper.hide_donation_banner"
                             help="Wenn aktiviert, wird das Spenden-Banner im JDownloader automatisch ausgeblendet!"
                             help-class="text-muted"
                             input-class="form-check-input"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             type="checkbox"/>
                  </label>
                </div>
              </div>
            </div>
          </FormKit>
        </div>
        <div>
          <button v-if="store.state.misc.loaded_settings" class="btn btn-primary mt-4" type="submit"
                  @click="submitSettings">
            <span v-if="spin_settings" class="spinner-border spinner-border-sm" role="status"></span>
            <i v-if="!spin_settings" class="bi bi-save"></i> Speichern
          </button>
          <button v-else class="btn btn-dark disabled">
            <span class="spinner-border spinner-border-sm" role="status"></span> Lädt...
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Center Selects */
select {
  max-width: 720px;
  margin-left: auto;
  margin-right: auto;
  text-align-last: center;
}
</style>
