<script setup>
import axios from 'axios'
import {onMounted, ref} from 'vue'
import {Collapse} from 'bootstrap'

const props = defineProps({
  prefix: String,
  hostnames: Object,
  crawltimes: Object,
  now: Number
})

onMounted(() => {
  getBlockedSites()
})

// ToDo update this from App.vue
const settings = {
  general: {
    flaresolverr: false
  }
}

const blocked_sites = ref({
  normal: {},
  flaresolverr: {},
  flaresolverr_proxy: {}
})

function getBlockedSites() {
  axios.get(props.prefix + 'api/blocked_sites/')
      .then(function (res) {
        blocked_sites.value = res.data.blocked_sites
        console.log('Blockierte Seiten abgerufen!')
      }, function () {
        console.log('Konnte blockierte Seiten nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte blockierte Seiten nicht abrufen!')
      })
}

function showCaptchasHelp() {
  new Collapse(document.getElementById('collapseOneOne'), {
    toggle: true
  })
  sessionStorage.setItem('fromNav', '')
  window.location.href = "#collapseOneZero";
}
</script>


<template>
  <div id="offcanvasBottomHelp" aria-labelledby="offcanvasBottomHelpLabel" class="offcanvas offcanvas-bottom"
       tabindex="-1">
    <div class="offcanvas-header">
      <h3 id="offcanvasBottomHelpLabel" class="offcanvas-title"><i class="bi bi-question-diamond"></i> Hilfe</h3>
      <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas" type="button"></button>
    </div>
    <div class="offcanvas-body">
      <div id="accordionHelp" class="accordion">
        <div class="accordion-item">
          <h2 id="headingOneZero" class="accordion-header">
            <button aria-controls="collapseOneZero" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseOneZero"
                    data-bs-toggle="collapse" type="button">
              FeedCrawler Sponsors Helper
            </button>
          </h2>
          <div id="collapseOneZero" aria-labelledby="headingOneZero" class="accordion-collapse collapse"
               data-bs-parent="#accordionHelp">
            <div class="accordion-body">
              <p>Der FeedCrawler Sponsors Helper ist ein Docker-Image, das alle derzeit bekannten CAPTCHAs
                vollautomatisch löst, und dem FeedCrawler entschlüsselt übergibt.</p>
              <p>Das Image steht ausschließlich aktiven <a href="https://github.com/users/rix1337/sponsorship"
                                                           target="_blank">Sponsoren</a> zur Verfügung (daher
                der
                Name).<br>
                Die Freischaltung erfolgt automatisch für aktive Sponsoren im dafür eingerichteten
                Github-Repo.
              </p>
              <p>Benötigt wird ein Docker-Host mit mindestens 2 GB verfügbarem Arbeitsspeicher und ein Account
                beim
                unter <a href="#" @click="showCaptchasHelp()">CAPTCHAs</a> beworbenen Captcha-Solver.</p>
              <span>
                    <a v-if="!helper_active" class="btn btn-outline-danger" data-toggle="tooltip"
                       href="https://github.com/users/rix1337/sponsorship"
                       target="_blank"
                       title="Bitte unterstütze die Weiterentwicklung über eine aktive Github Sponsorship!"><i
                        id="no-heart" class="bi bi-emoji-frown"></i> Kein aktiver Sponsor</a>
                    <a v-if="helper_active" class="btn btn-outline-success" data-toggle="tooltip"
                       href="https://github.com/users/rix1337/sponsorship"
                       target="_blank" title="Vielen Dank für die aktive Github Sponsorship!"><i id="heart"
                                                                                                 class="bi bi-heart"></i> Aktiver
                        Sponsor</a>
                    <br>
                    <a class="btn btn-outline-success"
                       href="https://github.com/rix1337/FeedCrawler/wiki"
                       target="_blank">Weitere Hinweise gibt es im Wiki.</a>
                </span>
            </div>
          </div>
        </div>
        <div class="accordion-item">
          <h2 id="headingOneOne" class="accordion-header">
            <button aria-controls="collapseOneOne" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseOneOne"
                    data-bs-toggle="collapse" type="button">
              CAPTCHAs
            </button>
          </h2>
          <div id="collapseOneOne" aria-labelledby="headingOneOne" class="accordion-collapse collapse"
               data-bs-parent="#accordionHelp">
            <div class="accordion-body">
              <a class="btn btn-outline-success" href="./redirect_user/captcha" target="_blank">
                Anti-Captcha.com (schnelles Lösen von ReCaptcha, etc. - auch im Browser)
              </a>
            </div>
          </div>
        </div>
        <div class="accordion-item">
          <h2 id="headingOneTwo" class="accordion-header">
            <button aria-controls="collapseOneTwo" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseOneTwo"
                    data-bs-toggle="collapse" type="button">
              Multihoster
            </button>
          </h2>
          <div id="collapseOneTwo" aria-labelledby="headingOneTwo" class="accordion-collapse collapse"
               data-bs-parent="#accordionHelp">
            <div class="accordion-body">
              <a class="btn btn-outline-success" href="./redirect_user/multihoster" target="_blank">
                Linksnappy.com (50 GB kostenfreies Startguthaben für DDownload, Rapidgator, 1Fichier, etc.)
              </a>
            </div>
          </div>
        </div>
        <div v-if="(hostnames.bl !== 'Nicht gesetzt!') || (hostnames.s !== 'Nicht gesetzt!')"
             class="accordion-item">
          <h2 id="headingOneThree" class="accordion-header">
            <button aria-controls="collapseOneThree" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseOneThree"
                    data-bs-toggle="collapse" type="button">
              RegEx
            </button>
          </h2>
          <div id="collapseOneThree" aria-labelledby="headingOneThree" class="accordion-collapse collapse"
               data-bs-parent="#accordionHelp">
            <div id="helpText" class="accordion-body">
              <h5>Beispiele</h5>
              <div v-if="hostnames.bl !== 'Nicht gesetzt!'">
                <div class="row">
                  <div class="col text-left card bg-light">
                    <i>Film.*.Titel.*</i>
                  </div>
                  <div class="col text-left card">Sucht nach allen Filmen die mit Film beginnen und
                    Titel
                    enthalten.
                  </div>
                </div>
                <div class="row">
                  <div class="col text-left card bg-light">
                    <i>.*-GROUP</i> oder
                    <i>-GROUP</i>
                  </div>
                  <div class="col text-left card">sucht nach allen Releases der GROUP.</div>
                </div>
                <div class="row">
                  <div class="col text-left card bg-light">
                    <i>.*1080p.*-GROUP</i>
                  </div>
                  <div class="col text-left card">sucht nach allen Full-HD Releases der GROUP.</div>
                </div>
                <div class="row">
                  <div class="col text-left card bg-light">
                    <i>Film.Titel.*.DL.*.720p.*.BluRay.*-Group</i>
                  </div>
                  <div class="col text-left card">sucht nach HD-BluRay Releases von Film Titel,
                    zweisprachig
                    und in
                    720p
                    der GROUP.
                  </div>
                </div>
              </div>
              <div v-if="hostnames.s !== 'Nicht gesetzt!'">
                <div class="row">
                  <div class="col text-left card bg-light">
                    <i>Serien.Titel.*.S01.*.German.*.720p.*-GROUP</i>
                  </div>
                  <div class="col text-left card">sucht nach Releases der GROUP von Staffel 1 der
                    Serien
                    Titel
                    in 720p
                    auf
                    Deutsch.
                  </div>
                </div>
                <div class="row">
                  <div class="col text-left card bg-light">
                    <i>Serien.Titel.*</i>
                  </div>
                  <div class="col text-left card">sucht nach allen Releases von Serien Titel
                    (nützlich,
                    wenn
                    man sonst
                    HDTV
                    aussortiert).
                  </div>
                </div>
                <div class="row">
                  <div class="col text-left card bg-light">
                    <i>Serien.Titel.*.DL.*.720p.*</i>
                  </div>
                  <div class="col text-left card">sucht nach zweisprachigen Releases in 720p von
                    Serien
                    Titel.
                  </div>
                </div>
                <div class="row">
                  <div class="col text-left card bg-light">
                    <i>(?!(Diese|Andere)).*Serie.*.DL.*.720p.*-(GROUP|ANDEREGROUP)</i>
                  </div>
                  <div class="col text-left card">sucht nach Serie (aber nicht Diese Serie oder Andere
                    Serie),
                    zweisprachig
                    und in 720p und ausschließlich
                    nach Releases von GROUP oder ANDEREGROUP.
                  </div>
                </div>
              </div>
              <p>All diese Regeln lassen sich beliebig kombinieren.<br/>
                Falsche Regex-Einträge können allerdings die Feed-Suche verhindern!</p>
              <p>Daher vorher beispielsweise auf
                <a href="https://regexr.com/" target="_blank">RegExr.com</a> testen, ob ein Eintrag
                matcht
                (Beispielrelease unter Text eintragen - Expression sollte
                etwas finden).</p>
            </div>
          </div>
        </div>
        <div class="accordion-item">
          <h2 id="headingOneFour" class="accordion-header">
            <button aria-controls="collapseOneFour" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseOneFour"
                    data-bs-toggle="collapse" type="button">
              Seitenliste
            </button>
          </h2>
          <div id="collapseOneFour" aria-labelledby="headingOneFour" class="accordion-collapse collapse"
               data-bs-parent="#accordionHelp">
            <div class="accordion-body">
              <div class="row">
                <div
                    v-if="hostnames.fx !== 'Nicht gesetzt!' || hostnames.hw !== 'Nicht gesetzt!' || hostnames.ww !== 'Nicht gesetzt!' || hostnames.ff !== 'Nicht gesetzt!' || hostnames.nk !== 'Nicht gesetzt!' || hostnames.by !== 'Nicht gesetzt!'"
                    class="col">
                  <ul class="list-group">
                    <li v-if="hostnames.fx !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.fx
                      }}
                      (FX)
                      <i v-if="blocked_sites.normal.FX"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="!blocked_sites.normal.FX" class="bi bi-check-square-fill text-success"
                         title="Seite mit aktueller IP verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr.FX && blocked_sites.normal.FX"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.FX && blocked_sites.normal.FX"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.FX && ( blocked_sites.normal.FX && blocked_sites.flaresolverr.FX )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.FX && ( blocked_sites.normal.FX && blocked_sites.flaresolverr.FX )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                    </li>
                    <li v-if="hostnames.hw !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.hw
                      }}
                      (HW)
                      <i v-if="blocked_sites.normal.HW"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="!blocked_sites.normal.HW" class="bi bi-check-square-fill text-success"
                         title="Seite mit aktueller IP verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr.HW && blocked_sites.normal.HW"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.HW && blocked_sites.normal.HW"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.HW && ( blocked_sites.normal.HW && blocked_sites.flaresolverr.HW )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.HW && ( blocked_sites.normal.HW && blocked_sites.flaresolverr.HW )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                    </li>
                    <li v-if="hostnames.ww !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.ww
                      }}
                      (WW)
                      <i v-if="blocked_sites.normal.WW && !settings.general.flaresolverr"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="!blocked_sites.normal.WW && !settings.general.flaresolverr"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit aktueller IP verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr.WW && blocked_sites.normal.WW"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.WW && blocked_sites.normal.WW"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.WW && ( blocked_sites.normal.WW && blocked_sites.flaresolverr.WW )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.WW && ( blocked_sites.normal.WW && blocked_sites.flaresolverr.WW )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                    </li>
                    <li v-if="hostnames.ff !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.ff
                      }}
                      (FF)
                      <span v-if="crawltimes.next_f_run < now">
                                            <i v-if="!blocked_sites.normal.SF"
                                               class="bi bi-check-square-fill text-success"
                                               title="Seite mit aktueller IP verfügbar"></i>
                                        </span>
                      <i v-if="blocked_sites.normal.FF"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="blocked_sites.flaresolverr.FF && blocked_sites.normal.FF"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.FF && blocked_sites.normal.FF"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.FF && ( blocked_sites.normal.FF && blocked_sites.flaresolverr.FF )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.FF && ( blocked_sites.normal.FF && blocked_sites.flaresolverr.FF )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                      <span v-if="crawltimes.next_f_run > now">
                      <!-- ToDo refactor removed AngularJS filters to vue -->
                      <i class="bi bi-clock-fill text-warning"
                         :title="'Keine FF-Suchläufe bis: ' + crawltimes.next_f_run"></i></span>
                    </li>
                    <li v-if="hostnames.nk !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.nk
                      }}
                      (NK)
                      <i v-if="blocked_sites.normal.NK"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="!blocked_sites.normal.NK" class="bi bi-check-square-fill text-success"
                         title="Seite mit aktueller IP verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr.NK && blocked_sites.normal.NK"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.NK && blocked_sites.normal.NK"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.NK && ( blocked_sites.normal.NK && blocked_sites.flaresolverr.NK )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.NK && ( blocked_sites.normal.NK && blocked_sites.flaresolverr.NK )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                    </li>
                    <li v-if="hostnames.by !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.by
                      }}
                      (BY)
                      <i v-if="blocked_sites.normal.BY"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="!blocked_sites.normal.BY" class="bi bi-check-square-fill text-success"
                         title="Seite mit aktueller IP verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr.BY && blocked_sites.normal.BY"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.BY && blocked_sites.normal.BY"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.BY && ( blocked_sites.normal.BY && blocked_sites.flaresolverr.BY )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.BY && ( blocked_sites.normal.BY && blocked_sites.flaresolverr.BY )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                    </li>
                  </ul>
                </div>
                <div
                    v-if="hostnames.sj !== 'Nicht gesetzt!' || hostnames.dj !== 'Nicht gesetzt!' || hostnames.sf !== 'Nicht gesetzt!'"
                    class="col">
                  <ul class="list-group">
                    <li v-if="hostnames.sj !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.sj
                      }}
                      (SJ)
                      <i v-if="blocked_sites.normal.SJ"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="!blocked_sites.normal.SJ" class="bi bi-check-square-fill text-success"
                         title="Seite mit aktueller IP verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr.SJ && blocked_sites.normal.SJ"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.SJ && blocked_sites.normal.SJ"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.SJ && ( blocked_sites.normal.SJ && blocked_sites.flaresolverr.SJ )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.SJ && ( blocked_sites.normal.SJ && blocked_sites.flaresolverr.SJ )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                    </li>
                    <li v-if="hostnames.dj !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.dj
                      }}
                      (DJ)
                      <i v-if="blocked_sites.normal.DJ"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="!blocked_sites.normal.DJ" class="bi bi-check-square-fill text-success"
                         title="Seite mit aktueller IP verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr.DJ && blocked_sites.normal.DJ"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.DJ && blocked_sites.normal.DJ"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.DJ && ( blocked_sites.normal.DJ && blocked_sites.flaresolverr.DJ )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.DJ && ( blocked_sites.normal.DJ && blocked_sites.flaresolverr.DJ )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                    </li>
                    <li v-if="hostnames.sf !== 'Nicht gesetzt!'" class="list-group-item">{{
                        hostnames.sf
                      }}
                      (SF)
                      <span v-if="crawltimes.next_f_run < now">
                                            <i v-if="!blocked_sites.normal.SF"
                                               class="bi bi-check-square-fill text-success"
                                               title="Seite mit aktueller IP verfügbar"></i>
                                        </span>
                      <i v-if="blocked_sites.normal.SF"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit aktueller IP gesperrt"></i>
                      <i v-if="blocked_sites.flaresolverr.SF && blocked_sites.normal.SF"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (aktuelle IP) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr.SF && blocked_sites.normal.SF"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (aktuelle IP) verfügbar"></i>
                      <i v-if="blocked_sites.flaresolverr_proxy.SF && ( blocked_sites.normal.SF && blocked_sites.flaresolverr.SF )"
                         class="bi bi-exclamation-square-fill text-danger"
                         title="Seite mit FlareSolverr (Proxy) gesperrt"></i>
                      <i v-if="!blocked_sites.flaresolverr_proxy.SF && ( blocked_sites.normal.SF && blocked_sites.flaresolverr.SF )"
                         class="bi bi-check-square-fill text-success"
                         title="Seite mit FlareSolverr (Proxy) verfügbar"></i>
                      <span v-if="crawltimes.next_f_run > now">
                        <!-- ToDo refactor removed AngularJS filters to vue -->
                        <i class="bi bi-clock-fill text-warning"
                           :title="'Keine FF-Suchläufe bis: ' + crawltimes.next_f_run"></i></span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="accordion-item">
          <h2 id="headingOneFive" class="accordion-header">
            <button aria-controls="collapseOneFive" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseOneFive"
                    data-bs-toggle="collapse" type="button">
              Wiki
            </button>
          </h2>
          <div id="collapseOneFive" aria-labelledby="headingOneFive" class="accordion-collapse collapse"
               data-bs-parent="#accordionHelp">
            <div class="accordion-body">
              <a class="btn btn-outline-success" href="https://github.com/rix1337/FeedCrawler/wiki"
                 target="_blank">Weitere
                Hinweise gibt es im Wiki.</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
