<script setup>
import {useStore} from 'vuex'
import {ref} from 'vue'
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


function submitSettings() {
  submitForm('settings')
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
          <FormKit type="form" #default="{ value }"
                   id="settings"
                   :actions="false"
                   messages-class="text-danger mt-4"
                   incomplete-message="Es müssen alle Felder korrekt ausgefüllt werden! Fehler sind rot markiert."
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
                           label="E-Mail Adresse"
                           help="Hier die E-Mail Adresse des Kontos bei My JDownloader angeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. name@mail.com"
                           validation="required|length:5|*email"
                           validation-visibility="live"
                           type="email"/>
                  <FormKit v-model="store.state.settings.general.myjd_pass"
                           label="Passwort"
                           help="Hier das Passwort von My JDownloader angeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. ●●●●●●●●"
                           validation="required"
                           validation-visibility="live"
                           type="password"/>
                  <FormKit v-model="store.state.settings.general.myjd_device" help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           label="Gerätename"
                           help="Hier den Gerätenamen des mit dem obigen My JDownloader-Konto verbundenen JDownloaders angeben."
                           placeholder="Bspw. JDownloader@Server"
                           type="text"/>
                  <h5>Autostart</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.crawljobs.autostart"
                             help="Wenn aktiviert, werden Downloads automatisch gestartet, sobald diese entschlüsselt vorliegen."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Automatische Updates</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.myjd_auto_update"
                             help="Wenn aktiviert, wird am Ende jedes Suchlaufs geprüft, ob ein Update verfügbar ist. Verfügbare Updates werden bei inaktivem JDownloader sofort ausgeführt und der JDownloader dafür neugestartet."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Unterordner bei Download</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.crawljobs.subdir"
                             help="Wenn aktiviert, werden Downloads in passende Unterordner sortiert - Empfohlen für die Weiterverarbeitung per Script!"
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <FormKit v-model="store.state.settings.general.packages_per_myjd_page"
                           label="Pakete pro Seite"
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class=" form-control bg-light mb-2"
                           help="Pakete ab dieser Anzahl werden auf Folgeseiten umgebrochen, was unnötiges Scrollen verhindert."
                           placeholder="Bspw. 3"
                           validation="required|between:3,30"
                           validation-visibility="live"
                           type="number"/>
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
                             label="Port"
                             help="Hier den Port des Webservers wählen."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-control bg-light mb-2"
                             placeholder="Bspw. 9090"
                             validation="required|between:1024,65535"
                             validation-visibility="live"
                             type="number"/>
                  </div>
                  <FormKit v-model="store.state.settings.general.prefix"
                           label="Prefix"
                           help="Hier den Prefix des Webservers wählen (nützlich für Reverse-Proxies)."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. feedcrawler"
                           validation="alpha"
                           validation-visibility="live"
                           type="text"/>
                  <FormKit v-model="store.state.settings.general.auth_user"
                           label="Nutzername"
                           name="auth_user"
                           help="Hier den Nutzernamen für FeedCrawler eingeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. rix1337"
                           :validation="value.auth_hash ? 'required' : ''"
                           type="text"/>
                  <FormKit v-model="store.state.settings.general.auth_hash"
                           label="Passwort"
                           name="auth_hash"
                           help="Hier das Passwort für FeedCrawler angeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. ●●●●●●●●"
                           :validation="value.auth_user ? 'required' : ''"
                           validation-visibility="live"
                           type="password"/>
                  <FormKit v-model="store.state.settings.general.interval"
                           label="Suchintervall (Allgemein)"
                           help="Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren. Aus Sicherheitsgründen wird das Intervall zufällig um bis zu 25% erhöht."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class=" form-control bg-light mb-2"
                           placeholder="Bspw. 60"
                           validation="required|between:5,1440"
                           validation-visibility="live"
                           type="number"/>
                  <h5>Wartezeit ({{ store.state.hostnames.jf }})</h5> <!-- Setting variables in label is unsupported -->
                  <FormKit v-model="store.state.settings.jf.wait_time"
                           help="Die Wartezeit in Stunden sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class=" form-control bg-light mb-2"
                           placeholder="Bspw. 12"
                           validation="required|between:6,24"
                           validation-visibility="live"
                           type="number"/>
                  <FormKit v-model="store.state.settings.general.flaresolverr"
                           label="FlareSolverr-URL"
                           help="Hier die URL eines durch FeedCrawler erreichbaren FlareSolverrs angeben. FlareSolverr ist ein Proxy-Server zur Umgehung des Cloudflare-Schutzes von Seiten wie SF oder WW. FlareSolverr wird nur dann genutzt, wenn eine Blockade durch Cloudflare erkannt wurde."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. http://192.168.0.1:8191"
                           :validation="value.flaresolverr_proxy ? 'required|url' : 'url'"
                           validation-visibility="live"
                           type="url"/>
                  <FormKit v-model="store.state.settings.general.flaresolverr_proxy"
                           label="FlareSolverr-Proxy-URL"
                           name="flaresolverr_proxy"
                           help="Hier optional die URL eines durch FlareSolverr erreichbaren ungeschützten HTTP-Proxies (ohne Nutzername/Passwort) angeben. FlareSolverr nutzt den hinterlegten Proxy-Server zum Seitenaufruf, wenn eine Blockade der normalen IP durch Cloudflare erkannt wurde."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. http://192.168.0.1:8080"
                           validation="url"
                           validation-visibility="live"
                           type="url"/>
                  <h5>Ein Mirror genügt</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.one_mirror_policy"
                             help="Wenn aktiviert, und sofern mindestens ein entschlüsselter Link im Paket vorhanden ist, werden vor dem Download alle Links aus einem Paket entfernt die offline oder verschlüsselt sind. Das ermöglicht den sofortigen Start ohne Click'n'Load-Automatik - betrifft aber alle Pakete im JDownloader!"
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Englische Releases hinzufügen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.english"
                             help="Wenn aktiviert, werden auch englischsprachige Titel gesucht."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Mehrkanalton erzwingen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.surround"
                             help="Wenn aktiviert, werden ausschließlich Titel mit Mehrkanalton-Tags hinzugefügt."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
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
                <div class="accordion-body"
                     v-tippy="'Für jeden gewählten Hoster werden Links hinzugefügt, sofern verfügbar. Der damit einhergehende CAPTCHA-Bedarf sollte beachtet werden! Ist kein gewählter Hoster am Release verfügbar, wird dieses übersprungen!'">
                  <div class="row">
                    <div class="col-sm">
                      <h5>DDownload</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.ddl"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>Rapidgator</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.rapidgator"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>1Fichier</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.onefichier"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>Turbobit</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.turbobit"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                    </div>
                    <div class="col-sm">
                      <h5>Uploaded</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.uploaded"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>FileFactory</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.filefactory"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>Uptobox</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.uptobox"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>Filer</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.filer"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>Zippyshare</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.zippyshare"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                    </div>
                    <div class="col-sm">
                      <h5>Nitroflare</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.nitroflare"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>Keep2Share</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.k2s"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>KatFile</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.katfile"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
                                 type="checkbox"/>
                      </label>
                      <h5>IronFiles</h5> <!-- Checkbox labels are not placed above -->
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.ironfiles"
                                 help-class="text-muted"
                                 messages-class="text-danger"
                                 outer-class="mb-4"
                                 input-class="form-check-input"
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
                  <FormKit v-model="store.state.settings.alerts.telegram"
                           label="Telegram"
                           help="Hier kommagetrennt den Token des eigenen Bots und danach die Chat-ID des Ziel-Chats angeben. Beide werden im Chat mit BotFather angelegt."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-2"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. 123456789:sYV4B-Ez5yTh3heyFquV4QgQSW2XSBLF9Xj,987654321"
                           :validation="[['matches', /^\d+?:[^\s]+?,\d+?$/]]"
                           validation-visibility="live"
                           :validation-messages="{
                              matches: 'Bitte den Token des eigenen Bots und dann kommagetrennt die Chat-ID des Ziel-Chats angeben (ohne Leerzeichen).'
                           }"
                           type="text"/>
                  <div class="mb-4">
                    <mark>Telegram ist der offiziell empfohlene Weg, Benachrichtigungen zu versenden.</mark>
                  </div>
                  <FormKit v-model="store.state.settings.alerts.pushbullet"
                           label="Pushbullet"
                           help="Access-Token auf Pushbullet.com anlegen und hier angeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. o.12345ABCBCQJMmfhpWkkNFby7Z7qd6Rj"
                           :validation="[['matches', /^o\.[A-Za-z0-9]+$/]]"
                           validation-visibility="live"
                           :validation-messages="{
                              matches: 'Bitte einen validen Access-Token angeben.'
                           }"
                           type="text"/>
                  <FormKit v-model="store.state.settings.alerts.pushover"
                           label="Pushover"
                           help="Hier kommagetrennt den User-Key und danach einen API-Token angeben. Letzteren zunächst auf Pushover.net anlegen."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. uQiRzpo4DXghDmr9QzzfQu27cmVRsG,azGDORePK8gMaC0QOYAMyEEuzJnyUi"
                           :validation="[['matches', /^[A-Za-z0-9]{30},[A-Za-z0-9]{30}$/]]"
                           validation-visibility="live"
                           :validation-messages="{
                              matches: 'Bitte den User-Key und dann kommagetrennt einen API-Token angeben (ohne Leerzeichen).'
                           }"
                           type="text"/>
                  <FormKit v-model="store.state.settings.alerts.homeassistant" help-class="text-muted"
                           label="Home Assistant"
                           help="Hier kommagetrennt die URL zur API und danach das Passwort angeben."
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. http://192.168.0.1:8080,Passwort"
                           validation="url"
                           validation-visibility="live"
                           type="url"/>
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
                  <FormKit v-model="store.state.settings.overseerr.url"
                           label="Overseerr URL"
                           name="overseerr_url"
                           help="Hier die URL von Overseerr angeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. http://192.168.0.1:5055"
                           :validation="value.overseerr_api ? 'required|url' : 'url'"
                           validation-visibility="live"
                           type="url"/>
                  <FormKit v-model="store.state.settings.overseerr.api"
                           label="Overseerr API-Key"
                           name="overseerr_api"
                           help="Hier den API-Key von Overseerr angeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. V2hhdCB3ZXJlIHlvdSBsb29raW5nIGZvcj8KV2h5IGFyZSB5b3UgZXZlbiBoZXJlPw=="
                           :validation="value.overseerr_url ? 'required|length:10' : 'length:10'"
                           validation-visibility="live"
                           :validation-messages="{
                              matches: 'Bitte einen validen API-Key angeben.'
                           }"
                           type="text"/>
                  <FormKit v-model="store.state.settings.ombi.url"
                           label="Ombi URL"
                           name="ombi_url"
                           help="Hier die URL von Ombi angeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. http://192.168.0.1:5000/ombi"
                           :validation="value.ombi_api ? 'required|url' : 'url'"
                           validation-visibility="live"
                           type="url"/>
                  <FormKit v-model="store.state.settings.ombi.api"
                           label="Ombi API-Key"
                           name="ombi_api"
                           help="Hier den API-Key von Ombi angeben."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. UQ6oVaEuPR3CyyhEfi2uT32PrRJfitfv3WG"
                           :validation="value.ombi_url ? 'required|length:10' : 'length:10'"
                           validation-visibility="live"
                           :validation-messages="{
                              matches: 'Bitte einen validen API-Key angeben.'
                           }"
                           type="text"/>
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
                           label="Auflösung"
                           help="Die Release-Auflösung, nach der gesucht wird."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           type="select">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.mb.search"
                           label="Suchtiefe"
                           help="Hier wählen, wie weit die Suche in die Vergangenheit gehen soll (Je weiter, desto länger dauert der Suchlauf)!"
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           type="select">
                    <option v-for="option in mb_search" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.mb.ignore"
                           label="Filterliste"
                           help="Releases mit diesen Begriffen werden nicht hinzugefügt (kommagetrennt)."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. cam,subbed,xvid,dvdr,untouched,remux,mpeg2,avc,pal,md,ac3md,mic,xxx"
                           type="text"/>
                  <h5>Auch per RegEx suchen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.regex"
                             help="Wenn aktiviert, werden Filme aus der Filme (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <FormKit v-model="store.state.settings.mb.imdb_score"
                           label="Ab IMDb-Wertung hinzufügen"
                           help="Alle Filme die im Feed über der genannten Wertung auftauchen, werden hinzugefügt - Wert unter 6,5 nicht empfehlenswert, 0 zum Deaktivieren."
                           required
                           step="0.1"
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class=" form-control bg-light mb-2"
                           placeholder="Bspw. 6,5"
                           validation="required|between:0.0,10.0"
                           validation-visibility="live"
                           type="number"/>
                  <FormKit v-model="store.state.settings.mb.imdb_year"
                           label="IMDb hinzufügen ab Erscheinungsjahr"
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class=" form-control bg-light mb-2"
                           help="Berücksichtige Filme bei IMDb-Suche erst ab diesem Erscheinungsjahr."
                           placeholder="Bspw. 2020"
                           validation="between:1900,2099"
                           validation-visibility="live"
                           type="number"/>
                  <h5>Zweisprachige Releases erzwingen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.force_dl"
                             help="Wenn aktiviert, sucht das Script zu jedem nicht zweisprachigen Release (kein DL-Tag im Titel), das nicht O-Ton Deutsch ist, ein passendes Release in 1080p mit DL-Tag. Findet das Script kein Release wird dies im DEBUG-Log vermerkt. Bei der nächsten Ausführung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nützlich um (durch späteres Remuxen) eine zweisprachige Bibliothek in 720p zu erhalten."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Nur Retail hinzufügen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.retail_only"
                             help="Wenn aktiviert, werden nur Retail-Releases hinzugefügt."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Listeneintrag bei Retail streichen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.cutoff"
                             help="Wenn aktiviert, werden Filme aus der Filme-Liste gestrichen, sobald ein Retail-Release gefunden wurde."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>1080p-HEVC bevorzugen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.hevc_retail"
                             help="Wenn aktiviert, werden Retail-Releases von Filmen in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen. Entspricht außerdem ein beliebiges Filmrelease den Retail-Kriterien, wir ad hoc nach einem Retail-Release in 1080p mit den Tags HEVC, h265 oder x265 gesucht. Wird ein solches gefunden, wird nur dieses hinzugefügt (das andere ignoriert). Für alle anderen Releases greifen die Einstellungen der Auflösung und Filterliste."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Hoster-Fallback</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.hoster_fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <div v-if="store.state.hostnames.s === 'Nicht gesetzt!'">
                    <h5>Staffeln suchen</h5> <!-- Checkbox labels are not placed above -->
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.enabled"
                               help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                               help-class="text-muted"
                               messages-class="text-danger"
                               outer-class="mb-4"
                               input-class="form-check-input"
                               type="checkbox"/>
                    </label>
                    <FormKit v-model="store.state.settings.mbsj.quality"
                             label="Auflösung der Staffeln"
                             help="Die Release-Auflösung der Staffeln, nach der gesucht wird."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-control bg-light mb-2"
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
                               messages-class="text-danger"
                               outer-class="mb-4"
                               input-class="form-check-input"
                               type="checkbox"/>
                    </label>
                    <FormKit v-model="store.state.settings.mbsj.source"
                             label="Quellart der Staffeln"
                             help="Die Quellart der Staffeln, nach der gesucht wird."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-control bg-light mb-2"
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
                           label="Auflösung"
                           help="Die Release-Auflösung, nach der gesucht wird."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           type="select">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.sj.ignore"
                           label="Filterliste"
                           help="Releases mit diesen Begriffen werden nicht hinzugefügt (kommagetrennt)."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. XviD,Subbed,HDTV"
                           type="text"/>
                  <h5>Auch per RegEx suchen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.regex"
                             help="Wenn aktiviert, werden Serien aus der Serien (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Nur Retail hinzufügen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.retail_only"
                             help="Wenn aktiviert, werden nur Retail-Releases hinzugefügt."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>1080p-HEVC bevorzugen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.hevc_retail"
                             help="Wenn aktiviert, werden Retail-Releases von Serien in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Hoster-Fallback</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.hoster_fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <div v-if="store.state.hostnames.bl === 'Nicht gesetzt!'">
                    <h5>Staffeln suchen</h5> <!-- Checkbox labels are not placed above -->
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.enabled"
                               help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                               help-class="text-muted"
                               messages-class="text-danger"
                               outer-class="mb-4"
                               input-class="form-check-input"
                               type="checkbox"/>
                    </label>
                    <FormKit v-model="store.state.settings.mbsj.quality"
                             label="Auflösung der Staffeln"
                             help="Die Release-Auflösung der Staffeln, nach der gesucht wird."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-control bg-light mb-2"
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
                               messages-class="text-danger"
                               outer-class="mb-4"
                               input-class="form-check-input"
                               type="checkbox"/>
                    </label>
                    <FormKit v-model="store.state.settings.mbsj.source"
                             label="Quellart der Staffeln"
                             help="Die Quellart der Staffeln, nach der gesucht wird."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-control bg-light mb-2"
                             type="select">
                      <option v-for="option in sources" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
                    <div
                        v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f === store.state.hostnames.s">
                      <FormKit v-model="store.state.settings.f.search"
                               label="Suchtiefe"
                               help="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren."
                               help-class="text-muted"
                               messages-class="text-danger"
                               outer-class="mb-4"
                               input-class=" form-control bg-light mb-2"
                               placeholder="Bspw. 3"
                               validation="required|between:1,7"
                               validation-visibility="live"
                               type="number"/>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div
                v-if="store.state.hostnames.sjbl !== 'Nicht gesetzt!' && store.state.settings.mbsj.enabled && store.state.misc.sjbl_enabled"
                class="accordion-item">
              <h2 id="headingSettingsSjBl" class="accordion-header">
                <button aria-controls="collapseSettingsSjBl" aria-expanded="false" class="accordion-button collapsed"
                        data-bs-target="#collapseSettingsSjBl"
                        data-bs-toggle="collapse" type="button">
                  {{ store.state.hostnames.sjbl }}
                </button>
              </h2>
              <div id="collapseSettingsSjBl" aria-labelledby="headingSettingsSjBl" class="accordion-collapse collapse"
                   data-bs-parent="#accordionSettings">
                <div class="accordion-body">
                  <h5>Staffeln suchen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mbsj.enabled"
                             help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <FormKit v-model="store.state.settings.mbsj.quality"
                           label="Auflösung der Staffeln"
                           help="Die Release-Auflösung der Staffeln, nach der gesucht wird."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
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
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <FormKit v-model="store.state.settings.mbsj.source"
                           label="Quellart der Staffeln"
                           help="Die Quellart der Staffeln, nach der gesucht wird."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           type="select">
                    <option v-for="option in sources" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <div
                      v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f === store.state.hostnames.sjbl">
                    <FormKit v-model="store.state.settings.f.search"
                             label="Suchtiefe"
                             help="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class=" form-control bg-light mb-2"
                             placeholder="Bspw. 3"
                             validation="required|between:1,7"
                             validation-visibility="live"
                             type="number"/>
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
                           label="Auflösung"
                           help="Die Release-Auflösung, nach der gesucht wird."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           type="select">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.dj.ignore"
                           label="Filterliste"
                           help="Releases mit diesen Begriffen werden nicht hinzugefügt (kommagetrennt)."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class="form-control bg-light mb-2"
                           placeholder="Bspw. XviD,Subbed,HDTV"
                           type="text"/>
                  <h5>Auch per RegEx suchen</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.dj.regex"
                             help="Wenn aktiviert, werden Serien aus der Dokus (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
                             type="checkbox"/>
                  </label>
                  <h5>Hoster-Fallback</h5> <!-- Checkbox labels are not placed above -->
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.dj.hoster_fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             help-class="text-muted"
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
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
                             messages-class="text-danger"
                             outer-class="mb-4"
                             input-class="form-check-input"
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
                           label="Suchtiefe"
                           help="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class=" form-control bg-light mb-2"
                           placeholder="Bspw. 3"
                           validation="required|between:1,7"
                           validation-visibility="live"
                           type="number"/>
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
                           label="Erlaubte Fehlversuche"
                           help="Um keine CAPTCHA-Credits zu verschwenden, löscht der FeedCrawler Sponsor Helper ein Paket, nachdem dieser Schwellwert erreicht wurde."
                           help-class="text-muted"
                           messages-class="text-danger"
                           outer-class="mb-4"
                           input-class=" form-control bg-light mb-2"
                           placeholder="Bspw. 3"
                           validation="required|between:1,10"
                           validation-visibility="live"
                           type="number"/>
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
