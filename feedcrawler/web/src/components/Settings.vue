<script setup>
import {ref} from 'vue'
import {useStore} from 'vuex'
import axios from "axios"

const store = useStore()

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
        console.log('Einstellungen gespeichert! Neustart wird dringend empfohlen!')
        showSuccess('Einstellungen gespeichert! Neustart wird dringend empfohlen!')
        getSettings()
      }, function () {
        getSettings()
        console.log('Konnte Einstellungen nicht speichern! Eventuelle Hinweise in der Konsole beachten.')
        showDanger('Konnte Einstellungen nicht speichern! Eventuelle Hinweise in der Konsole beachten.')
      })
}

function spinSettings() {
  // ToDo migrate to vue from jQuery
  //$("#spinner-settings").fadeIn().delay(1000).fadeOut()
}

const year = ref((new Date).getFullYear())

// todo move to shared store mutations
const myjd_connection_error = ref(false)
const pageSizeMyJD = ref(3)

function getSettings() {
  axios.get(store.state.prefix + 'api/settings/')
      .then(function (res) {
        store.commit("setSettings", res.data.settings)
        console.log('Einstellungen abgerufen!')
        myjd_connection_error.value = !(store.state.settings.general.myjd_user && store.state.settings.general.myjd_device && store.state.settings.general.myjd_device)
        pageSizeMyJD.value = store.state.settings.general.packages_per_myjd_page
      }, function () {
        console.log('Konnte Einstellungen nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Einstellungen nicht abrufen!')
      })
}
</script>


<template>
  <div id="offcanvasBottomSettings" aria-labelledby="offcanvasBottomSettingsLabel" class="offcanvas offcanvas-bottom"
       tabindex="-1">
    <div class="offcanvas-header">
      <h3 id="offcanvasBottomSettingsLabel" class="offcanvas-title"><i class="bi bi-gear"></i> Einstellungen</h3>
      <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas" type="button"></button>
    </div>
    <div class="offcanvas-body">
      <form name="settingsForm">
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
                <input v-model="store.state.settings.general.myjd_user" class="form-control" data-toggle="tooltip"
                       title="Hier den Nutzernamen von My JDownloader angeben."/>
                <h5>Passwort</h5>
                <input v-model="store.state.settings.general.myjd_pass" class="form-control" data-toggle="tooltip"
                       title="Hier das Passwort von My JDownloader angeben."
                       type="password"/>
                <h5>Gerätename</h5>
                <input class="form-control" data-toggle="tooltip"
                       v-model="store.state.settings.general.myjd_device"
                       title="Hier den Gerätenamen des mit dem obigen My JDownloader-Konto verbundenen JDownloaders angeben."/>
                <h5>Autostart</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.crawljobs.autostart"
                         title="Wenn aktiviert, werden Downloads automatisch gestartet, sobald diese entschlüsselt vorliegen."
                         type="checkbox">
                </label>
                <h5>Unterordner bei Download</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.crawljobs.subdir"
                         title="Wenn aktiviert, werden Downloads in passende Unterordner sortiert - Empfohlen für die Weiterverarbeitung per Script!"
                         type="checkbox">
                </label>
                <h5>Bereich zuklappen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.general.closed_myjd_tab"
                         title="Wenn aktiviert, bleibt der MyJDownloader-Tab beim Aufruf des FeedCrawlers zunächst geschlossen, egal ob Pakete vorhanden sind, oder nicht."
                         type="checkbox">
                </label>
                <h5>Pakete pro Seite</h5>
                <input class="number form-control" data-toggle="tooltip" max="30" min="3"
                       v-model="store.state.settings.general.packages_per_myjd_page"
                       required
                       title="Pakete ab dieser Anzahl werden auf Folgeseiten umgebrochen, was unnötiges Scrollen verhindert."
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
                <h5>Port</h5>
                <!-- ToDo disable if we are dockerized this is detected within head.getVersion() -->
                <input class="number form-control docker" data-toggle="tooltip" max="65535" min="1024"
                       v-model="store.state.settings.general.port"
                       required title="Hier den Port des Webservers wählen."
                       type="number"/>
                <h5>Prefix</h5>
                <input v-model="store.state.settings.general.prefix" class="form-control" data-toggle="tooltip"
                       title="Hier den Prefix des Webservers wählen (nützlich für Reverse-Proxies)."/>
                <h5>Nutzername</h5>
                <input v-model="store.state.settings.general.auth_user" class="form-control" data-toggle="tooltip"
                       title="Hier den Nutzernamen für FeedCrawler eingeben (erfordert gesetztes Passwort!)."/>
                <h5>Passwort</h5>
                <input v-model="store.state.settings.general.auth_hash" class="form-control" data-toggle="tooltip"
                       title="Hier das Passwort für FeedCrawler angeben (erfordert gesetzten Nutzernamen!)."
                       type="password"/>
                <h5>Suchintervall</h5>
                <input class="number form-control" data-toggle="tooltip" max="1440" min="5"
                       v-model="store.state.settings.general.interval"
                       required
                       title="Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren - Minimum sind 5 Minuten. Aus Sicherheitsgründen wird das Intervall zufällig um bis zu 25% erhöht."
                       type="number"/>
                <h5>FlareSolverr-URL</h5>
                <input v-model="store.state.settings.general.flaresolverr" class="form-control" data-toggle="tooltip"
                       title="Hier die URL eines durch FeedCrawler erreichbaren FlareSolverrs angeben, bspw. http://192.168.0.1:8191 - FlareSolverr ist ein Proxy-Server zur Umgehung des Cloudflare-Schutzes von Seiten wie SF oder WW. FlareSolverr wird nur dann genutzt, wenn eine Blockade durch Cloudflare erkannt wurde."/>
                <h5>FlareSolverr-Proxy-URL</h5>
                <input class="form-control" data-toggle="tooltip"
                       v-model="store.state.settings.general.flaresolverr_proxy"
                       title="Hier optional die URL eines durch FlareSolverr erreichbaren ungeschützten HTTP-Proxies (ohne Nutzername/Passwort) angeben, bspw. http://192.168.0.1:8080 - FlareSolverr nutzt den hinterlegten Proxy-Server zum Seitenaufruf, wenn eine Blockade der normalen IP durch Cloudflare erkannt wurde."/>
                <h5>Ein Mirror genügt</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.general.one_mirror_policy"
                         title="Wenn aktiviert, und sofern mindestens ein entschlüsselter Link im Paket vorhanden ist, werden vor dem Download alle Links aus einem Paket entfernt die offline oder verschlüsselt sind. Das ermöglicht den sofortigen Start ohne Click'n'Load-Automatik - betrifft aber alle Pakete im JDownloader!"
                         type="checkbox">
                </label>
                <h5>Englische Releases hinzufügen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.general.english"
                         title="Wenn aktiviert, werden auch englischsprachige Titel gesucht."
                         type="checkbox">
                </label>
                <h5>Mehrkanalton erzwingen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.general.surround"
                         title="Wenn aktiviert, werden ausschließlich Titel mit Mehrkanalton-Tags hinzugefügt."
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
                   data-toggle="tooltip"
                   title="Für jeden gewählten Hoster werden Links hinzugefügt, sofern verfügbar. Der damit
                    einhergehende Captchabedarf sollte beachtet werden! Ist kein gewählter Hoster am Release verfürbar,
                    wird dieses übersprungen!">
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
                <input v-model="store.state.settings.alerts.pushbullet" class="form-control" data-toggle="tooltip"
                       title="Access-Token auf Pushbullet.com anlegen und hier angeben."/>
                <h5>Pushover</h5>
                <input v-model="store.state.settings.alerts.pushover" class="form-control" data-toggle="tooltip"
                       title="Hier durch ein Komma getrennt (Keine Leerzeichen!) den User-Key und danach einen API-Token angeben - Für letzteren zunächst eine auf Pushover.net anlegen."/>
                <h5>Home Assistant</h5>
                <input class="form-control" data-toggle="tooltip"
                       v-model="store.state.settings.alerts.homeassistant"
                       title="Hier durch ein Komma getrennt (Keine Leerzeichen!) die URL zur API und danach das Passwort angeben."/>
                <h5>Telegram</h5>
                <input v-model="store.state.settings.alerts.telegram" class="form-control" data-toggle="tooltip"
                       title="Hier durch ein Komma getrennt (Keine Leerzeichen!) den Token des eigenen Bots und danach die Chat Id des Ziel Chats angeben - Beide werden über Chat mit BotFather angelegt."/>
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
                <input v-model="store.state.settings.ombi.url" class="form-control" data-toggle="tooltip"
                       title="Pflichtangabe: Hier die URL von Ombi angeben, bspw. http://192.168.0.1:5000/ombi."/>
                <h5>Ombi API-Key</h5>
                <input v-model="store.state.settings.ombi.api" class="form-control" data-toggle="tooltip"
                       title="Pflichtangabe: Hier den API-Key von Ombi angeben."/>
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
                <select class="form-control"
                        data-toggle="tooltip"
                        v-model="store.state.settings.mb.quality"
                        title="Die Release-Auflösung, nach der gesucht wird.">
                  <option v-for="option in resolutions" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <h5>Suchtiefe</h5>
                <select class="form-control" data-toggle="tooltip"
                        v-model="store.state.settings.mb.search"
                        title="Hier wählen, wie weit die Suche in die Vergangenheit gehen soll (Je weiter, desto länger dauert der Suchlauf)!">
                  <option v-for="option in mb_search" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <h5>Filterliste</h5>
                <input v-model="store.state.settings.mb.ignore" class="form-control" data-toggle="tooltip"
                       title="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."/>
                <h5>Auch per RegEx suchen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.mb.regex"
                         title="Wenn aktiviert, werden Filme aus der Filme (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                         type="checkbox">
                </label>
                <h5>Ab IMDb-Wertung hinzufügen</h5>
                <input class="number form-control" data-toggle="tooltip" max="10.0" min="0.0"
                       v-model="store.state.settings.mb.imdb_score"
                       required
                       step="0.1"
                       title="Alle Filme die im Feed über der genannten Wertung auftauchen, werden hinzugefügt - Wert unter 6.5 nicht empfehlenswert, 0.0 zum Deaktivieren."
                       type="number"/>
                <h5>IMDb hinzufügen ab Erscheinungsjahr</h5>
                <input :max="year" class="number form-control" data-toggle="tooltip" min="1900"
                       v-model="store.state.settings.mb.imdb_year"
                       title="Berücksichtige Filme bei IMDb-Suche erst ab diesem Erscheinungsjahr."
                       type="number"/>
                <h5>Zweisprachige Releases erzwingen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.mb.force_dl"
                         title="Wenn aktiviert, sucht das Script zu jedem nicht zweisprachigen Release (kein DL-Tag im Titel), das nicht O-Ton Deutsch ist, ein passendes Release in 1080p mit DL Tag. Findet das Script kein Release wird dies im DEBUG-Log vermerkt. Bei der nächsten Ausführung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nützlich um (durch späteres Remuxen) eine zweisprachige Bibliothek in 720p zu erhalten."
                         type="checkbox">
                </label>
                <h5>Nur Retail hinzufügen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.mb.retail_only"
                         title="Wenn aktiviert, werden nur Retail-Releases hinzugefügt."
                         type="checkbox">
                </label>
                <h5>Listeneintrag bei Retail streichen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.mb.cutoff"
                         title="Wenn aktiviert, werden Filme aus der Filme-Liste gestrichen, sobald ein Retail-Release gefunden wurde."
                         type="checkbox">
                </label>
                <h5>1080p-HEVC bevorzugen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.mb.hevc_retail"
                         title="Wenn aktiviert, werden Retail-Releases von Filmen in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen. Entspricht außerdem ein beliebiges Filmrelease den Retail-Kriterien, wir ad hoc nach einem Retail-Release in 1080p mit den Tags HEVC, h265 oder x265 gesucht. Wird ein solches gefunden, wird nur dieses hinzugefügt (das andere ignoriert). Für alle anderen Releases greifen die Einstellungen der Auflösung und Filterliste."
                         type="checkbox">
                </label>
                <h5>Hoster-Fallback</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.mb.hoster_fallback"
                         title="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                         type="checkbox">
                </label>
                <div v-if="store.state.hostnames.s === 'Nicht gesetzt!'">
                  <h5>Staffeln suchen</h5>
                  <label class="form-check form-switch">
                    <input class="form-check-input" data-toggle="tooltip"
                           v-model="store.state.settings.mbsj.enabled"
                           title="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                           type="checkbox">
                  </label>
                  <h5>Auflösung der Staffeln</h5>
                  <select class="form-control"
                          data-toggle="tooltip"
                          v-model="store.state.settings.mbsj.quality"
                          title="Die Release-Auflösung der Staffeln, nach der gesucht wird.">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                  <h5>Staffelpakete erlauben</h5>
                  <label class="form-check form-switch">
                    <input class="form-check-input" data-toggle="tooltip"
                           v-model="store.state.settings.mbsj.packs"
                           title="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                           type="checkbox">
                  </label>
                  <h5>Quellart der Staffeln</h5>
                  <select class="form-control" data-toggle="tooltip"
                          v-model="store.state.settings.mbsj.source"
                          title="Die Quellart der Staffeln, nach der gesucht wird.">
                    <option v-for="option in sources" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </div>
                <div
                    v-if="store.state.hostnames.f !== 'Nicht gesetzt!' && store.state.hostnames.f === store.state.hostnames.bl">
                  <h5>Suchintervall</h5>
                  <input class="number form-control" data-toggle="tooltip" max="24" min="6"
                         v-model="store.state.settings.f.interval"
                         required
                         title="Das Suchintervall in Stunden sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren - Minimum sind 6 Stunden, Maximum sind 24 Stunden."
                         type="number"/>
                  <h5>Suchtiefe</h5>
                  <input v-model="store.state.settings.f.search" class="number form-control" data-toggle="tooltip"
                         max="7"
                         min="1"
                         required
                         title="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren - Minimum ist 1 Tag, Maximum sind 7 Tage."
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
                <select class="form-control"
                        data-toggle="tooltip"
                        v-model="store.state.settings.sj.quality"
                        title="Die Release-Auflösung, nach der gesucht wird.">
                  <option v-for="option in resolutions" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <h5>Filterliste</h5>
                <input v-model="store.state.settings.sj.ignore" class="form-control" data-toggle="tooltip"
                       title="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."/>
                <h5>Auch per RegEx suchen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.sj.regex"
                         title="Wenn aktiviert, werden Serien aus der Serien (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                         type="checkbox">
                </label>
                <h5>Nur Retail hinzufügen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.sj.retail_only"
                         title="Wenn aktiviert, werden nur Retail-Releases hinzugefügt."
                         type="checkbox">
                </label>
                <h5>1080p-HEVC bevorzugen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.sj.hevc_retail"
                         title="Wenn aktiviert, werden Retail-Releases von Serien in 1080p und dem HEVC-Codec bevorzugt (ein Download erfolgt, auch wenn in anderen Codecs bereits ein Release gefunden wurde). Dadurch werden Qualitäts- und Ignore-Einstellungen bei Retail-Releases im Feed ignoriert, solange diese in 1080p und im HEVC Codec vorliegen."
                         type="checkbox">
                </label>
                <h5>Hoster-Fallback</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.sj.hoster_fallback"
                         title="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
                         type="checkbox">
                </label>
                <div v-if="store.state.hostnames.bl === 'Nicht gesetzt!'">
                  <h5>Staffeln suchen</h5>
                  <label class="form-check form-switch">
                    <input class="form-check-input" data-toggle="tooltip"
                           v-model="store.state.settings.mbsj.enabled"
                           title="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                           type="checkbox">
                  </label>
                  <h5>Auflösung der Staffeln</h5>
                  <select class="form-control"
                          data-toggle="tooltip"
                          v-model="store.state.settings.mbsj.quality"
                          title="Die Release-Auflösung der Staffeln, nach der gesucht wird.">
                    <option v-for="option in resolutions" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                  <h5>Staffelpakete erlauben</h5>
                  <label class="form-check form-switch">
                    <input class="form-check-input" data-toggle="tooltip"
                           v-model="store.state.settings.mbsj.packs"
                           title="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                           type="checkbox">
                  </label>
                  <h5>Quellart der Staffeln</h5>
                  <select class="form-control" data-toggle="tooltip"
                          v-model="store.state.settings.mbsj.source"
                          title="Die Quellart der Staffeln, nach der gesucht wird.">
                    <option v-for="option in sources" v-bind:value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          <div
              v-if="store.state.hostnames.sjbl !== 'Nicht gesetzt!' && store.state.settings.mbsj.enabled && store.state.sjbl_enabled"
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
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.mbsj.enabled"
                         title="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste gesucht."
                         type="checkbox">
                </label>
                <h5>Auflösung der Staffeln</h5>
                <select class="form-control"
                        data-toggle="tooltip"
                        v-model="store.state.settings.mbsj.quality"
                        title="Die Release-Auflösung der Staffeln, nach der gesucht wird.">
                  <option v-for="option in resolutions" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <h5>Staffelpakete erlauben</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.mbsj.packs"
                         title="Wenn aktiviert, werden auch Staffelpakete hinzugefügt, die häufig mehrere hundert Gigabyte groß sind."
                         type="checkbox">
                </label>
                <h5>Quellart der Staffeln</h5>
                <select class="form-control" data-toggle="tooltip"
                        v-model="store.state.settings.mbsj.source"
                        title="Die Quellart der Staffeln, nach der gesucht wird.">
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
                <select class="form-control"
                        data-toggle="tooltip"
                        v-model="store.state.settings.dj.quality"
                        title="Die Release-Auflösung, nach der gesucht wird.">
                  <option v-for="option in resolutions" v-bind:value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <h5>Filterliste</h5>
                <input v-model="store.state.settings.dj.ignore" class="form-control" data-toggle="tooltip"
                       title="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."/>
                <h5>Auch per RegEx suchen</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.dj.regex"
                         title="Wenn aktiviert, werden Serien aus der Dokus (RegEx)-Liste nach den entsprechenden Regeln gesucht."
                         type="checkbox">
                </label>
                <h5>Hoster-Fallback</h5>
                <label class="form-check form-switch">
                  <input class="form-check-input" data-toggle="tooltip"
                         v-model="store.state.settings.dj.hoster_fallback"
                         title="Wenn aktiviert, und sofern kein anderer Link gefunden werden konnte, werden alle gefundenen Hoster akzeptiert!"
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
                <input v-model="store.state.settings.f.interval" class="number form-control" data-toggle="tooltip"
                       max="24"
                       min="6"
                       required
                       title="Das Suchintervall in Stunden sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren - Minimum sind 6 Stunden, Maximum sind 24 Stunden."
                       type="number"/>
                <h5>Suchtiefe</h5>
                <input v-model="store.state.settings.f.search" class="number form-control" data-toggle="tooltip" max="7"
                       min="1"
                       required
                       title="Die Suchtiefe in Tagen sollte nicht zu hoch angesetzt werden, um keinen Ban zu riskieren - Minimum ist 1 Tag, Maximum sind 7 Tage."
                       type="number"/>
              </div>
            </div>
          </div>
        </div>
        <div>
          <a class="btn btn-dark" href="" type="submit"
             @click="saveSettings()">
            <div id="spinner-settings"
                 class="spinner-border spinner-border-sm"
                 role="status" style="display: none"></div>
            <i class="bi bi-save"></i> Speichern</a>
        </div>
        <!-- ToDo validity check with v-if not working -->
        <div class="btn btn-danger" data-toggle="tooltip"
             title="Mindestens ein Feld wurde falsch befüllt und muss korrigiert werden (erkennbar am roten Rahmen darum).">
          <i class="bi bi-x"></i> Speichern nicht möglich
        </div>
      </form>
    </div>
  </div>
</template>
