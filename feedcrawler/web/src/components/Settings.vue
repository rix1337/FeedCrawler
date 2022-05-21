<script setup>
import {useStore} from 'vuex'
import {ref} from 'vue'
import {useToast} from "vue-toastification"
import {submitForm} from '@formkit/vue'
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

const year = ref((new Date).getFullYear())

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
          <FormKit
              type="form"
              id="settings"
              :actions="false"
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
                           label="Nutzername"
                           help="Hier den Nutzernamen von My JDownloader angeben."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.general.myjd_pass"
                           label="Passwort"
                           help="Hier das Passwort von My JDownloader angeben."
                           input-class="form-control bg-light mb-2"
                           type="password"/>
                  <FormKit v-model="store.state.settings.general.myjd_device" input-class="form-control bg-light mb-2"
                           label="Gerätename"
                           help="Hier den Gerätenamen des mit dem obigen My JDownloader-Konto verbundenen JDownloaders angeben."/>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.crawljobs.autostart" class="form-check-FormKit"
                             label="Autostart"
                             help="Wenn aktiviert, werden Downloads automatisch gestartet, sobald diese entschlüsselt vorliegen."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.crawljobs.subdir" class="form-check-FormKit"
                             label="Unterordner bei Download"
                             help="Wenn aktiviert, werden Downloads in passende Unterordner sortiert - Empfohlen für die Weiterverarbeitung per Script!"
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <FormKit v-model="store.state.settings.general.packages_per_myjd_page"
                           label="Pakete pro Seite"
                           input-class="number form-control bg-light mb-2"
                           help="Pakete ab dieser Anzahl werden auf Folgeseiten umgebrochen, was unnötiges Scrollen verhindert."
                           min="3"
                           required
                           max="30"
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
                             input-class="form-control bg-light mb-2"
                             max="65535"
                             min="1024" required
                             type="number"/>
                  </div>
                  <FormKit v-model="store.state.settings.general.prefix"
                           label="Prefix"
                           help="Hier den Prefix des Webservers wählen (nützlich für Reverse-Proxies)."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.general.auth_user"
                           label="Nutzername"
                           help="Hier den Nutzernamen für FeedCrawler eingeben (erfordert gesetztes Passwort!)."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.general.auth_hash"
                           label="Passwort"
                           help="Hier das Passwort für FeedCrawler angeben (erfordert gesetzten Nutzernamen!)."
                           input-class="form-control bg-light mb-2"
                           type="password"/>
                  <FormKit v-model="store.state.settings.general.interval"
                           label="Suchintervall (Allgemein)"
                           help="Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren - Minimum sind 5 Minuten. Aus Sicherheitsgründen wird das Intervall zufällig um bis zu 25% erhöht."
                           max="1440"
                           min="5"
                           required
                           input-class="number form-control bg-light mb-2"
                           type="number"/>
                  <FormKit v-model="store.state.settings.jf.wait_time"
                           label="Wartezeit ({{ store.state.hostnames.jf }})"
                           help="Die Wartezeit in Stunden sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren - Minimum sind 6 Stunden, Maximum sind 24 Stunden."
                           max="24"
                           min="6"
                           required
                           input-class="number form-control bg-light mb-2"
                           type="number"/>
                  <FormKit v-model="store.state.settings.general.flaresolverr"
                           label="FlareSolverr-URL"
                           help="Hier die URL eines durch FeedCrawler erreichbaren FlareSolverrs angeben, bspw. http://192.168.0.1:8191 - FlareSolverr ist ein Proxy-Server zur Umgehung des Cloudflare-Schutzes von Seiten wie SF oder WW. FlareSolverr wird nur dann genutzt, wenn eine Blockade durch Cloudflare erkannt wurde."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.general.flaresolverr_proxy"
                           label="FlareSolverr-Proxy-URL"
                           input-class="form-control bg-light mb-2"
                           help="Hier optional die URL eines durch FlareSolverr erreichbaren ungeschützten HTTP-Proxies (ohne Nutzername/Passwort) angeben, bspw. http://192.168.0.1:8080 - FlareSolverr nutzt den hinterlegten Proxy-Server zum Seitenaufruf, wenn eine Blockade der normalen IP durch Cloudflare erkannt wurde."/>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.one_mirror_policy" class="form-check-FormKit"
                             label="Ein Mirror genügt"
                             help="Wenn aktiviert, und sofern mindestens ein entschlüsselter Link im Paket vorhanden ist, werden vor dem Download alle Links aus einem Paket entfernt die offline oder verschlüsselt sind. Das ermöglicht den sofortigen Start ohne Click\'n\'Load-Automatik - betrifft aber alle Pakete im JDownloader!"
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.english" class="form-check-FormKit"
                             label="Englische Releases hinzufügen"
                             help="Wenn aktiviert, werden auch englischsprachige Titel gesucht."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.general.surround" class="form-check-FormKit"
                             label="Mehrkanalton erzwingen"
                             help="Wenn aktiviert, werden ausschließlich Titel mit Mehrkanalton-Tags hinzugefügt."
                             type="checkbox" input-class="form-check-input"/>
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
                     help="Für jeden gewählten Hoster werden Links hinzugefügt, sofern verfügbar. Der damit einhergehende CAPTCHA-Bedarf sollte beachtet werden! Ist kein gewählter Hoster am Release verfügbar, wird dieses übersprungen!">
                  <div class="row">
                    <div class="col-sm">
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.rapidgator" class="form-check-FormKit"
                                 label="Rapidgator"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.turbobit" class="form-check-FormKit"
                                 label="Turbobit"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.uploaded" class="form-check-FormKit"
                                 label="Uploaded"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.zippyshare" class="form-check-FormKit"
                                 label="Zippyshare"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.oboom" class="form-check-FormKit"
                                 label="OBOOM"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                    </div>
                    <div class="col-sm">
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.ddl" class="form-check-FormKit"
                                 label="DDownload"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.filefactory" class="form-check-FormKit"
                                 label="FileFactory"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.uptobox" class="form-check-FormKit"
                                 label="Uptobox"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.onefichier" class="form-check-FormKit"
                                 label="1Fichier"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.filer" class="form-check-FormKit"
                                 label="Filer"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                    </div>
                    <div class="col-sm">
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.nitroflare" class="form-check-FormKit"
                                 label="Nitroflare"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.ironfiles" class="form-check-FormKit"
                                 label="IronFiles"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
                      <label class="form-check form-switch">
                        <FormKit v-model="store.state.settings.hosters.k2s" class="form-check-FormKit"
                                 label="Keep2Share"
                                 type="checkbox" input-class="form-check-input"/>
                      </label>
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
                  <FormKit v-model="store.state.settings.alerts.pushbullet"
                           label="Pushbullet"
                           help="Access-Token auf Pushbullet.com anlegen und hier angeben."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.alerts.pushover"
                           label="Pushover"
                           help="Hier durch ein Komma getrennt (Keine Leerzeichen!) den User-Key und danach einen API-Token angeben - Für letzteren zunächst eine auf Pushover.net anlegen."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.alerts.homeassistant" input-class="form-control bg-light mb-2"
                           label="Home Assistant"
                           help="Hier durch ein Komma getrennt (Keine Leerzeichen!) die URL zur API und danach das Passwort angeben."/>
                  <FormKit v-model="store.state.settings.alerts.telegram"
                           label="Telegram"
                           help="Hier durch ein Komma getrennt (Keine Leerzeichen!) den Token des eigenen Bots und danach die Chat Id des Ziel Chats angeben - Beide werden über Chat mit BotFather angelegt."
                           input-class="form-control bg-light mb-2"/>
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
                           help="Pflichtangabe: Hier die URL von Overseerr angeben, bspw. http://192.168.0.1:5055."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.overseerr.api"
                           label="Overseerr API-Key"
                           help="Pflichtangabe: Hier den API-Key von Overseerr angeben."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.ombi.url"
                           label="Ombi URL"
                           help="Pflichtangabe: Hier die URL von Ombi angeben, bspw. http://192.168.0.1:5000/ombi."
                           input-class="form-control bg-light mb-2"/>
                  <FormKit v-model="store.state.settings.ombi.api"
                           label="Ombi API-Key"
                           help="Pflichtangabe: Hier den API-Key von Ombi angeben."
                           input-class="form-control bg-light mb-2"/>
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
                  <FormKit type="select" v-model="store.state.settings.mb.quality"
                           label="Auflösung"
                           input-class="form-control bg-light mb-2"
                           help="Die Release-Auflösung, nach der gesucht wird.">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit type="select" v-model="store.state.settings.mb.search"
                           label="Suchtiefe"
                           input-class="form-control bg-light mb-2"
                           help="Hier wählen, wie weit die Suche in die Vergangenheit gehen soll (Je weiter, desto länger dauert der Suchlauf)!">
                    <option v-for="option in mb_search" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.mb.ignore"
                           label="Filterliste"
                           help="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."
                           input-class="form-control bg-light mb-2"/>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.regex" class="form-check-FormKit"
                             label="Auch per RegEx suchen"
                             help="Wenn aktiviert, werden Filme aus der Filme (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <FormKit v-model="store.state.settings.mb.imdb_score"
                           label="Ab IMDb-Wertung hinzufügen"
                           help="Alle Filme die im Feed über der genannten Wertung auftauchen, werden hinzugefügt - Wert unter 6.5 nicht empfehlenswert, 0.0 zum Deaktivieren."
                           max="10.0"
                           min="0.0"
                           required
                           step="0.1"
                           input-class="number form-control bg-light mb-2"
                           type="number"/>
                  <FormKit v-model="store.state.settings.mb.imdb_year" :max="year"
                           label="IMDb hinzufügen ab Erscheinungsjahr"
                           input-class="number form-control bg-light mb-2"
                           min="1900"
                           help="Berücksichtige Filme bei IMDb-Suche erst ab diesem Erscheinungsjahr."
                           type="number"/>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.force_dl" class="form-check-FormKit"
                             label="Zweisprachige Releases erzwingen"
                             help="Wenn aktiviert, sucht das Script zu jedem nicht zweisprachigen Release (kein DL-Tag im Titel), das nicht O-Ton Deutsch ist, ein passendes Release in 1080p mit DL Tag. Findet das Script kein Release wird dies im DEBUG-Log vermerkt. Bei der nächsten Ausführung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nützlich um (durch späteres Remuxen) eine zweisprachige Bibliothek in 720p zu erhalten."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.retail_only" class="form-check-FormKit"
                             label="Nur Retail hinzufügen"
                             help="Wenn aktiviert, werden nur Retail-Releases hinzugefügt."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.cutoff" class="form-check-FormKit"
                             label="Listeneintrag bei Retail streichen"
                             help="Wenn aktiviert, werden Filme aus der Filme-Liste gestrichen, sobald ein Retail-Release gefunden wurde."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.hevc_retail" class="form-check-FormKit"
                             label="1080p-HEVC bevorzugen"
                             help="Wenn aktiviert, werden Retail-Releases von Filmen in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen. Entspricht außerdem ein beliebiges Filmrelease den Retail-Kriterien, wir ad hoc nach einem Retail-Release in 1080p mit den Tags HEVC, h265 oder x265 gesucht. Wird ein solches gefunden, wird nur dieses hinzugefügt (das andere ignoriert). Für alle anderen Releases greifen die Einstellungen der Auflösung und Filterliste."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mb.hoster_fallback" class="form-check-FormKit"
                             label="Hoster-Fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <div v-if="store.state.hostnames.s === 'Nicht gesetzt!'">
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.enabled" class="form-check-FormKit"
                               label="Staffeln suchen"
                               help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                               type="checkbox" input-class="form-check-input"/>
                    </label>
                    <FormKit type="select" v-model="store.state.settings.mbsj.quality"
                             label="Auflösung der Staffeln"
                             input-class="form-control bg-light mb-2"
                             help="Die Release-Auflösung der Staffeln, nach der gesucht wird.">
                      <option v-for="option in resolutions" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.packs" class="form-check-FormKit"
                               label="Staffelpakete erlauben"
                               help="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                               type="checkbox" input-class="form-check-input"/>
                    </label>
                    <FormKit type="select" v-model="store.state.settings.mbsj.source"
                             label="Quellart der Staffeln"
                             input-class="form-control bg-light mb-2"
                             help="Die Quellart der Staffeln, nach der gesucht wird.">
                      <option v-for="option in sources" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
                  </div>
                  <div
                      v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f === store.state.hostnames.bl">
                    <FormKit v-model="store.state.settings.f.search"
                             label="Suchtiefe"
                             help="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren - Minimum ist 1 Tag, Maximum sind 7 Tage."
                             max="7"
                             min="1"
                             required
                             input-class="number form-control bg-light mb-2"
                             type="number"/>
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
                  <FormKit type="select" v-model="store.state.settings.sj.quality"
                           label="Auflösung"
                           input-class="form-control bg-light mb-2"
                           help="Die Release-Auflösung, nach der gesucht wird.">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  <FormKit v-model="store.state.settings.sj.ignore"
                           label="Filterliste"
                           help="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."
                           input-class="form-control bg-light mb-2"/>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.regex" class="form-check-FormKit"
                             label="Auch per RegEx suchen"
                             help="Wenn aktiviert, werden Serien aus der Serien (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.retail_only" class="form-check-FormKit"
                             label="Nur Retail hinzufügen"
                             help="Wenn aktiviert, werden nur Retail-Releases hinzugefügt."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.hevc_retail" class="form-check-FormKit"
                             label="1080p-HEVC bevorzugen"
                             help="Wenn aktiviert, werden Retail-Releases von Serien in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.sj.hoster_fallback" class="form-check-FormKit"
                             label="Hoster-Fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  <div v-if="store.state.hostnames.bl === 'Nicht gesetzt!'">
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.enabled" class="form-check-FormKit"
                               label="Staffeln suchen"
                               help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                               type="checkbox" input-class="form-check-input"/>
                    </label>
                    <FormKit type="select" v-model="store.state.settings.mbsj.quality"
                             label="Auflösung der Staffeln"
                             input-class="form-control bg-light mb-2"
                             help="Die Release-Auflösung der Staffeln, nach der gesucht wird.">
                      <option v-for="option in resolutions" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
                    <label class="form-check form-switch">
                      <FormKit v-model="store.state.settings.mbsj.packs" class="form-check-FormKit"
                               label="Staffelpakete erlauben"
                               help="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                               type="checkbox" input-class="form-check-input"/>
                    </label>
                    <FormKit type="select" v-model="store.state.settings.mbsj.source"
                             label="Quellart der Staffeln"
                             input-class="form-control bg-light mb-2"
                             help="Die Quellart der Staffeln, nach der gesucht wird.">
                      <option v-for="option in sources" v-bind:value="option.value">
                        {{ option.label }}
                      </option>
                    </FormKit>
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
                  label="Staffeln suchen"
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mbsj.enabled" class="form-check-FormKit"
                             help="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  label="Auflösung der Staffeln"
                  <FormKit type="select" v-model="store.state.settings.mbsj.quality"
                           input-class="form-control bg-light mb-2"
                           help="Die Release-Auflösung der Staffeln, nach der gesucht wird.">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  label="Staffelpakete erlauben"
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.mbsj.packs" class="form-check-FormKit"

                             help="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  label="Quellart der Staffeln"
                  <FormKit type="select" v-model="store.state.settings.mbsj.source"
                           input-class="form-control bg-light mb-2"
                           help="Die Quellart der Staffeln, nach der gesucht wird.">
                    <option v-for="option in sources" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
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
                  label="Auflösung"
                  <FormKit type="select" v-model="store.state.settings.dj.quality"
                           input-class="form-control bg-light mb-2"
                           help="Die Release-Auflösung, nach der gesucht wird.">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </FormKit>
                  label="Filterliste"
                  <FormKit v-model="store.state.settings.dj.ignore"
                           help="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."
                           input-class="form-control bg-light mb-2"/>
                  label="Auch per RegEx suchen"
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.dj.regex" class="form-check-FormKit"
                             help="Wenn aktiviert, werden Serien aus der Dokus (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                  label="Hoster-Fallback"
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.dj.hoster_fallback" class="form-check-FormKit"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             type="checkbox" input-class="form-check-input"/>
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
                  label="Hoster-Fallback"
                  <label class="form-check form-switch">
                    <FormKit v-model="store.state.settings.dd.hoster_fallback"
                             help="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                             class="form-check-FormKit"
                             type="checkbox" input-class="form-check-input"/>
                  </label>
                </div>
              </div>
            </div>
            <div
                v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f !== store.state.hostnames.bl"
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
                           help="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren - Minimum ist 1 Tag, Maximum sind 7 Tage."
                           input-class="number form-control bg-light mb-2"
                           min="1"
                           required
                           max="7"
                           type="number"/>
                </div>
              </div>
            </div>
          </FormKit>
        </div>
        <div>
          <button v-if="store.state.misc.loaded_settings" class="btn btn-primary mt-2" type="submit"
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
  max-width: 260px;
  margin-left: auto;
  margin-right: auto;
  text-align-last: center;
}

/* Center Toggle Switches */
.form-check {
  display: inline-block;
}
</style>
