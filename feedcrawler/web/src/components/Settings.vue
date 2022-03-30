<script setup>
import {useStore} from 'vuex'
import {ref} from 'vue'
import {useToast} from "vue-toastification"
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
  spinSettings()
  axios.post(store.state.prefix + 'api/settings/', store.state.settings)
      .then(function () {
        console.log('Einstellungen gespeichert! Neustart des FeedCrawlers wird dringend empfohlen!')
        toast.success('Einstellungen gespeichert!\nNeustart des FeedCrawlers wird dringend empfohlen!')
        store.commit("getSettings")
      }, function () {
        store.commit("getSettings")
        console.log('Konnte Einstellungen nicht speichern! Bitte die angegebenen Werte auf Richtigkeit prüfen.')
        toast.error('Konnte Einstellungen nicht speichern!\nBitte die angegebenen Werte auf Richtigkeit prüfen.')
      })
}

const spin_settings = ref(false)

function spinSettings() {
  spin_settings.value = true
  setTimeout(function () {
    spin_settings.value = false
  }, 1000)
}

const year = ref((new Date).getFullYear())
</script>


<template>
  <div id="offcanvasBottomSettings" aria-labelledby="offcanvasBottomSettingsLabel" class="offcanvas offcanvas-bottom"
       tabindex="-1">
    <div class="offcanvas-header">
      <h3 id="offcanvasBottomSettingsLabel" class="offcanvas-title"><i class="bi bi-gear"></i> Einstellungen</h3>
      <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas" type="button"></button>
    </div>
    <div class="offcanvas-body">
      <div id="accordionSettings" class="accordion">
        <div class="accordion-item">
          <h2 id="headingTwoZero" class="accordion-header">
            <button aria-controls="collapseTwoZero" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoZero"
                    data-bs-toggle="collapse" type="button">
              My JDownloader
            </button>
          </h2>
          <div id="collapseTwoZero" aria-labelledby="headingTwoZero" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <h5>Nutzername</h5>
              <input v-model="store.state.settings.general.myjd_user"
                     v-tooltip="'Hier den Nutzernamen von My JDownloader angeben.'"
                     class="form-control"/>
              <h5>Passwort</h5>
              <input v-model="store.state.settings.general.myjd_pass"
                     v-tooltip="'Hier das Passwort von My JDownloader angeben.'"
                     class="form-control"
                     type="password"/>
              <h5>Gerätename</h5>
              <input v-model="store.state.settings.general.myjd_device" class="form-control"

                     v-tooltip="'Hier den Gerätenamen des mit dem obigen My JDownloader-Konto verbundenen JDownloaders angeben.'"/>
              <h5>Autostart</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.crawljobs.autostart" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden Downloads automatisch gestartet, sobald diese entschlüsselt vorliegen.'"
                       type="checkbox">
              </label>
              <h5>Unterordner bei Download</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.crawljobs.subdir" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden Downloads in passende Unterordner sortiert - Empfohlen für die Weiterverarbeitung per Script!'"
                       type="checkbox">
              </label>
              <h5>Bereich zuklappen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.general.closed_myjd_tab" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, bleibt der MyJDownloader-Tab beim Aufruf des FeedCrawlers zunächst geschlossen, egal ob Pakete vorhanden sind, oder nicht.'"
                       type="checkbox">
              </label>
              <h5>Pakete pro Seite</h5>
              <input v-model="store.state.settings.general.packages_per_myjd_page" class="number form-control"
                     v-tooltip="'Pakete ab dieser Anzahl werden auf Folgeseiten umgebrochen, was unnötiges Scrollen verhindert.'"
                     min="3"
                     required
                     max="30"
                     type="number"/>
            </div>
          </div>
        </div>
        <div class="accordion-item">
          <h2 id="headingTwoOne" class="accordion-header">
            <button aria-controls="collapseTwoOne" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoOne"
                    data-bs-toggle="collapse" type="button">
              Allgemein
            </button>
          </h2>
          <div id="collapseTwoOne" aria-labelledby="headingTwoOne" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <div v-if="!store.state.misc.docker">
                <h5>Port</h5>
                <input v-model="store.state.settings.general.port" v-tooltip="'Hier den Port des Webservers wählen.'"
                       class="number form-control docker"
                       max="65535"
                       min="1024" required
                       type="number"/>
              </div>
              <h5>Prefix</h5>
              <input v-model="store.state.settings.general.prefix"
                     v-tooltip="'Hier den Prefix des Webservers wählen (nützlich für Reverse-Proxies).'"
                     class="form-control"/>
              <h5>Nutzername</h5>
              <input v-model="store.state.settings.general.auth_user"
                     v-tooltip="'Hier den Nutzernamen für FeedCrawler eingeben (erfordert gesetztes Passwort!).'"
                     class="form-control"/>
              <h5>Passwort</h5>
              <input v-model="store.state.settings.general.auth_hash"
                     v-tooltip="'Hier das Passwort für FeedCrawler angeben (erfordert gesetzten Nutzernamen!).'"
                     class="form-control"
                     type="password"/>
              <h5>Suchintervall</h5>
              <input v-model="store.state.settings.general.interval"
                     v-tooltip="'Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren - Minimum sind 5 Minuten. Aus Sicherheitsgründen wird das Intervall zufällig um bis zu 25% erhöht.'"
                     max="1440"
                     min="5"
                     required
                     class="number form-control"
                     type="number"/>
              <h5>FlareSolverr-URL</h5>
              <input v-model="store.state.settings.general.flaresolverr"
                     v-tooltip="'Hier die URL eines durch FeedCrawler erreichbaren FlareSolverrs angeben, bspw. http://192.168.0.1:8191 - FlareSolverr ist ein Proxy-Server zur Umgehung des Cloudflare-Schutzes von Seiten wie SF oder WW. FlareSolverr wird nur dann genutzt, wenn eine Blockade durch Cloudflare erkannt wurde.'"
                     class="form-control"/>
              <h5>FlareSolverr-Proxy-URL</h5>
              <input v-model="store.state.settings.general.flaresolverr_proxy" class="form-control"

                     v-tooltip="'Hier optional die URL eines durch FlareSolverr erreichbaren ungeschützten HTTP-Proxies (ohne Nutzername/Passwort) angeben, bspw. http://192.168.0.1:8080 - FlareSolverr nutzt den hinterlegten Proxy-Server zum Seitenaufruf, wenn eine Blockade der normalen IP durch Cloudflare erkannt wurde.'"/>
              <h5>Ein Mirror genügt</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.general.one_mirror_policy" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, und sofern mindestens ein entschlüsselter Link im Paket vorhanden ist, werden vor dem Download alle Links aus einem Paket entfernt die offline oder verschlüsselt sind. Das ermöglicht den sofortigen Start ohne Click\'n\'Load-Automatik - betrifft aber alle Pakete im JDownloader!'"
                       type="checkbox">
              </label>
              <h5>Englische Releases hinzufügen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.general.english" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden auch englischsprachige Titel gesucht.'"
                       type="checkbox">
              </label>
              <h5>Mehrkanalton erzwingen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.general.surround" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden ausschließlich Titel mit Mehrkanalton-Tags hinzugefügt.'"
                       type="checkbox">
              </label>
            </div>
          </div>
        </div>
        <div class="accordion-item">
          <h2 id="headingTwoThree" class="accordion-header">
            <button aria-controls="collapseTwoThree" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoThree"
                    data-bs-toggle="collapse" type="button">
              Hoster
            </button>
          </h2>
          <div id="collapseTwoThree" aria-labelledby="headingTwoThree" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body"

                 v-tooltip="'Für jeden gewählten Hoster werden Links hinzugefügt, sofern verfügbar. Der damit einhergehende Captchabedarf sollte beachtet werden! Ist kein gewählter Hoster am Release verfürbar, wird dieses übersprungen!'">
              <div class="row">
                <div class="col-sm">
                  <h5>Rapidgator</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.rapidgator" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>Turbobit</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.turbobit" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>Uploaded</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.uploaded" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>Zippyshare</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.zippyshare" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>OBOOM</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.oboom" class="form-check-input"
                           type="checkbox">

                  </label>
                </div>
                <div class="col-sm">
                  <h5>DDownload</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.ddl" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>FileFactory</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.filefactory" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>Uptobox</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.uptobox" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>1Fichier</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.onefichier" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>Filer</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.filer" class="form-check-input"
                           type="checkbox">

                  </label>
                </div>
                <div class="col-sm">
                  <h5>Nitroflare</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.nitroflare" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>IronFiles</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.ironfiles" class="form-check-input"
                           type="checkbox">

                  </label>
                  <h5>Keep2Share</h5>
                  <label class="form-check form-switch">
                    <input v-model="store.state.settings.hosters.k2s" class="form-check-input"
                           type="checkbox">

                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="accordion-item">
          <h2 id="headingTwoFour" class="accordion-header">
            <button aria-controls="collapseTwoFour" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoFour"
                    data-bs-toggle="collapse" type="button">
              Benachrichtigungen
            </button>
          </h2>
          <div id="collapseTwoFour" aria-labelledby="headingTwoFour" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <h5>Pushbullet</h5>
              <input v-model="store.state.settings.alerts.pushbullet"
                     v-tooltip="'Access-Token auf Pushbullet.com anlegen und hier angeben.'"
                     class="form-control"/>
              <h5>Pushover</h5>
              <input v-model="store.state.settings.alerts.pushover"
                     v-tooltip="'Hier durch ein Komma getrennt (Keine Leerzeichen!) den User-Key und danach einen API-Token angeben - Für letzteren zunächst eine auf Pushover.net anlegen.'"
                     class="form-control"/>
              <h5>Home Assistant</h5>
              <input v-model="store.state.settings.alerts.homeassistant" class="form-control"

                     v-tooltip="'Hier durch ein Komma getrennt (Keine Leerzeichen!) die URL zur API und danach das Passwort angeben.'"/>
              <h5>Telegram</h5>
              <input v-model="store.state.settings.alerts.telegram"
                     v-tooltip="'Hier durch ein Komma getrennt (Keine Leerzeichen!) den Token des eigenen Bots und danach die Chat Id des Ziel Chats angeben - Beide werden über Chat mit BotFather angelegt.'"
                     class="form-control"/>
            </div>
          </div>
        </div>
        <div class="accordion-item">
          <h2 id="headingTwoFive" class="accordion-header">
            <button aria-controls="collapseTwoFive" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoFive"
                    data-bs-toggle="collapse" type="button">
              Ombi
            </button>
          </h2>
          <div id="collapseTwoFive" aria-labelledby="headingTwoFive" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <h5>Ombi URL</h5>
              <input v-model="store.state.settings.ombi.url"
                     v-tooltip="'Pflichtangabe: Hier die URL von Ombi angeben, bspw. http://192.168.0.1:5000/ombi.'"
                     class="form-control"/>
              <h5>Ombi API-Key</h5>
              <input v-model="store.state.settings.ombi.api"
                     v-tooltip="'Pflichtangabe: Hier den API-Key von Ombi angeben.'"
                     class="form-control"/>
            </div>
          </div>
        </div>
        <div v-if="store.state.hostnames.bl !== 'Nicht gesetzt!'" class="accordion-item">
          <h2 id="headingTwoSix" class="accordion-header">
            <button aria-controls="collapseTwoSix" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoSix"
                    data-bs-toggle="collapse" type="button">
              {{ store.state.hostnames.bl }}
            </button>
          </h2>
          <div id="collapseTwoSix" aria-labelledby="headingTwoSix" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <h5>Auflösung</h5>
              <select v-model="store.state.settings.mb.quality"
                      class="form-control"

                      v-tooltip="'Die Release-Auflösung, nach der gesucht wird.'">
                <option v-for="option in resolutions" v-bind:value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <h5>Suchtiefe</h5>
              <select v-model="store.state.settings.mb.search" class="form-control"

                      v-tooltip="'Hier wählen, wie weit die Suche in die Vergangenheit gehen soll (Je weiter, desto länger dauert der Suchlauf)!'">
                <option v-for="option in mb_search" v-bind:value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <h5>Filterliste</h5>
              <input v-model="store.state.settings.mb.ignore"
                     v-tooltip="'Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt).'"
                     class="form-control"/>
              <h5>Auch per RegEx suchen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.mb.regex" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden Filme aus der Filme (RegEx)-Liste nach den entsprechenden Regeln gesucht.'"
                       type="checkbox">
              </label>
              <h5>Ab IMDb-Wertung hinzufügen</h5>
              <input v-model="store.state.settings.mb.imdb_score"
                     v-tooltip="'Alle Filme die im Feed über der genannten Wertung auftauchen, werden hinzugefügt - Wert unter 6.5 nicht empfehlenswert, 0.0 zum Deaktivieren.'"
                     max="10.0"
                     min="0.0"
                     required
                     step="0.1"
                     class="number form-control"
                     type="number"/>
              <h5>IMDb hinzufügen ab Erscheinungsjahr</h5>
              <input v-model="store.state.settings.mb.imdb_year" :max="year" class="number form-control"

                     min="1900"
                     v-tooltip="'Berücksichtige Filme bei IMDb-Suche erst ab diesem Erscheinungsjahr.'"
                     type="number"/>
              <h5>Zweisprachige Releases erzwingen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.mb.force_dl" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, sucht das Script zu jedem nicht zweisprachigen Release (kein DL-Tag im Titel), das nicht O-Ton Deutsch ist, ein passendes Release in 1080p mit DL Tag. Findet das Script kein Release wird dies im DEBUG-Log vermerkt. Bei der nächsten Ausführung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nützlich um (durch späteres Remuxen) eine zweisprachige Bibliothek in 720p zu erhalten.'"
                       type="checkbox">
              </label>
              <h5>Nur Retail hinzufügen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.mb.retail_only" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden nur Retail-Releases hinzugefügt.'"
                       type="checkbox">
              </label>
              <h5>Listeneintrag bei Retail streichen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.mb.cutoff" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden Filme aus der Filme-Liste gestrichen, sobald ein Retail-Release gefunden wurde.'"
                       type="checkbox">
              </label>
              <h5>1080p-HEVC bevorzugen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.mb.hevc_retail" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden Retail-Releases von Filmen in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen. Entspricht außerdem ein beliebiges Filmrelease den Retail-Kriterien, wir ad hoc nach einem Retail-Release in 1080p mit den Tags HEVC, h265 oder x265 gesucht. Wird ein solches gefunden, wird nur dieses hinzugefügt (das andere ignoriert). Für alle anderen Releases greifen die Einstellungen der Auflösung und Filterliste.'"
                       type="checkbox">
              </label>
              <h5>Hoster-Fallback</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.mb.hoster_fallback" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!'"
                       type="checkbox">
              </label>
              <div v-if="store.state.hostnames.s === 'Nicht gesetzt!'">
                <h5>Staffeln suchen</h5>
                <label class="form-check form-switch">
                  <input v-model="store.state.settings.mbsj.enabled" class="form-check-input"

                         v-tooltip="'Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht.'"
                         type="checkbox">
                </label>
                <h5>Auflösung der Staffeln</h5>
                <select v-model="store.state.settings.mbsj.quality"
                        class="form-control"

                        v-tooltip="'Die Release-Auflösung der Staffeln, nach der gesucht wird.'">
                  <option v-for="option in resolutions" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <h5>Staffelpakete erlauben</h5>
                <label class="form-check form-switch">
                  <input v-model="store.state.settings.mbsj.packs" class="form-check-input"

                         v-tooltip="'Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind.'"
                         type="checkbox">
                </label>
                <h5>Quellart der Staffeln</h5>
                <select v-model="store.state.settings.mbsj.source" class="form-control"

                        v-tooltip="'Die Quellart der Staffeln, nach der gesucht wird.'">
                  <option v-for="option in sources" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
              <div
                  v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f === store.state.hostnames.bl">
                <h5>Suchintervall</h5>
                <input v-model="store.state.settings.f.interval"
                       v-tooltip="'Das Suchintervall in Stunden sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren - Minimum sind 6 Stunden, Maximum sind 24 Stunden.'"
                       max="24"
                       min="6"
                       required
                       class="number form-control"
                       type="number"/>
                <h5>Suchtiefe</h5>
                <input v-model="store.state.settings.f.search"
                       v-tooltip="'Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren - Minimum ist 1 Tag, Maximum sind 7 Tage.'"
                       max="7"
                       min="1"
                       required
                       class="number form-control"
                       type="number"/>
              </div>
            </div>
          </div>
        </div>
        <div v-if="store.state.hostnames.s !== 'Nicht gesetzt!'" class="accordion-item">
          <h2 id="headingTwoSeven" class="accordion-header">
            <button aria-controls="collapseTwoSeven" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoSeven"
                    data-bs-toggle="collapse" type="button">
              {{ store.state.hostnames.s }}
            </button>
          </h2>
          <div id="collapseTwoSeven" aria-labelledby="headingTwoSeven" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <h5>Auflösung</h5>
              <select v-model="store.state.settings.sj.quality"
                      class="form-control"

                      v-tooltip="'Die Release-Auflösung, nach der gesucht wird.'">
                <option v-for="option in resolutions" v-bind:value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <h5>Filterliste</h5>
              <input v-model="store.state.settings.sj.ignore"
                     v-tooltip="'Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt).'"
                     class="form-control"/>
              <h5>Auch per RegEx suchen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.sj.regex" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden Serien aus der Serien (RegEx)-Liste nach den entsprechenden Regeln gesucht.'"
                       type="checkbox">
              </label>
              <h5>Nur Retail hinzufügen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.sj.retail_only" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden nur Retail-Releases hinzugefügt.'"
                       type="checkbox">
              </label>
              <h5>1080p-HEVC bevorzugen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.sj.hevc_retail" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden Retail-Releases von Serien in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen.'"
                       type="checkbox">
              </label>
              <h5>Hoster-Fallback</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.sj.hoster_fallback" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!'"
                       type="checkbox">
              </label>
              <div v-if="store.state.hostnames.bl === 'Nicht gesetzt!'">
                <h5>Staffeln suchen</h5>
                <label class="form-check form-switch">
                  <input v-model="store.state.settings.mbsj.enabled" class="form-check-input"

                         v-tooltip="'Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht.'"
                         type="checkbox">
                </label>
                <h5>Auflösung der Staffeln</h5>
                <select v-model="store.state.settings.mbsj.quality"
                        class="form-control"

                        v-tooltip="'Die Release-Auflösung der Staffeln, nach der gesucht wird.'">
                  <option v-for="option in resolutions" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <h5>Staffelpakete erlauben</h5>
                <label class="form-check form-switch">
                  <input v-model="store.state.settings.mbsj.packs" class="form-check-input"

                         v-tooltip="'Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind.'"
                         type="checkbox">
                </label>
                <h5>Quellart der Staffeln</h5>
                <select v-model="store.state.settings.mbsj.source" class="form-control"

                        v-tooltip="'Die Quellart der Staffeln, nach der gesucht wird.'">
                  <option v-for="option in sources" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>
        <div
            v-if="store.state.hostnames.sjbl !== 'Nicht gesetzt!' && store.state.settings.mbsj.enabled && store.state.misc.sjbl_enabled"
            class="accordion-item">
          <h2 id="headingTwoEight" class="accordion-header">
            <button aria-controls="collapseTwoEight" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoEight"
                    data-bs-toggle="collapse" type="button">
              {{ store.state.hostnames.sjbl }}
            </button>
          </h2>
          <div id="collapseTwoEight" aria-labelledby="headingTwoEight" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <h5>Staffeln suchen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.mbsj.enabled" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht.'"
                       type="checkbox">
              </label>
              <h5>Auflösung der Staffeln</h5>
              <select v-model="store.state.settings.mbsj.quality"
                      class="form-control"

                      v-tooltip="'Die Release-Auflösung der Staffeln, nach der gesucht wird.'">
                <option v-for="option in resolutions" v-bind:value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <h5>Staffelpakete erlauben</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.mbsj.packs" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind.'"
                       type="checkbox">
              </label>
              <h5>Quellart der Staffeln</h5>
              <select v-model="store.state.settings.mbsj.source" class="form-control"

                      v-tooltip="'Die Quellart der Staffeln, nach der gesucht wird.'">
                <option v-for="option in sources" v-bind:value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <div v-if="store.state.hostnames.dj !== 'Nicht gesetzt!'" class="accordion-item">
          <h2 id="headingTwoNine" class="accordion-header">
            <button aria-controls="collapseTwoNine" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoNine"
                    data-bs-toggle="collapse" type="button">
              {{ store.state.hostnames.dj }}
            </button>
          </h2>
          <div id="collapseTwoNine" aria-labelledby="headingTwoNine" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <h5>Auflösung</h5>
              <select v-model="store.state.settings.dj.quality"
                      class="form-control"

                      v-tooltip="'Die Release-Auflösung, nach der gesucht wird.'">
                <option v-for="option in resolutions" v-bind:value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <h5>Filterliste</h5>
              <input v-model="store.state.settings.dj.ignore"
                     v-tooltip="'Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt).'"
                     class="form-control"/>
              <h5>Auch per RegEx suchen</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.dj.regex" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, werden Serien aus der Dokus (RegEx)-Liste nach den entsprechenden Regeln gesucht.'"
                       type="checkbox">
              </label>
              <h5>Hoster-Fallback</h5>
              <label class="form-check form-switch">
                <input v-model="store.state.settings.dj.hoster_fallback" class="form-check-input"

                       v-tooltip="'Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!'"
                       type="checkbox">
              </label>
            </div>
          </div>
        </div>
        <div
            v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f !== store.state.hostnames.bl"
            class="accordion-item">
          <h2 id="headingTwoTen" class="accordion-header">
            <button aria-controls="collapseTwoTen" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseTwoTen"
                    data-bs-toggle="collapse" type="button">
              {{ store.state.hostnames.f }}
            </button>
          </h2>
          <div id="collapseTwoTen" aria-labelledby="headingTwoTen" class="accordion-collapse collapse"
               data-bs-parent="#accordionSettings">
            <div class="accordion-body">
              <h5>Suchintervall</h5>
              <input v-model="store.state.settings.f.interval"
                     v-tooltip="'Das Suchintervall in Stunden sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren - Minimum sind 6 Stunden, Maximum sind 24 Stunden.'"
                     max="24"
                     min="6"
                     required
                     class="number form-control"
                     type="number"/>
              <h5>Suchtiefe</h5>
              <input v-model="store.state.settings.f.search"
                     v-tooltip="'Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren - Minimum ist 1 Tag, Maximum sind 7 Tage.'"
                     class="number form-control"
                     min="1"
                     required
                     max="7"
                     type="number"/>
            </div>
          </div>
        </div>
      </div>
      <button class="btn btn-dark" type="submit" @click="saveSettings()">
        <span v-if="spin_settings" class="spinner-border spinner-border-sm" role="status"></span>
        <i v-if="!spin_settings" class="bi bi-save"></i> Speichern
      </button>
    </div>
  </div>
</template>
