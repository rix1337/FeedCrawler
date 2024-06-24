<script setup>
import {useStore} from 'vuex'
import {computed} from 'vue'
import {Collapse} from "bootstrap"

const store = useStore()

function showCaptchasHelp() {
  new Collapse(document.getElementById('collapseCaptchas'), {
    toggle: true
  })
}

function openCaptchaLink() {
  window.open('http://getcaptchasolution.com/zuoo67f5cq', '_blank')
}

function openHosterLink() {
  window.open('http://linksnappy.com/?ref=397097', '_blank')
}

function getTimestamp(ms) {
  const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s)
  const d = new Date(ms)

  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const waitTimeActive = computed(() => {
      if (store.state.crawltimes.next_cloudflare_run !== "undefined" && !isNaN(store.state.crawltimes.next_cloudflare_run) && !isNaN(store.state.misc.now)) {
        return store.state.crawltimes.next_cloudflare_run > store.state.misc.now
      } else {
        return false
      }
    }
)
</script>


<template>
  <div class="text-center">
    <div id="offcanvasBottomHelp" aria-labelledby="offcanvasBottomHelpLabel" class="offcanvas offcanvas-bottom"
         tabindex="-1">
      <div class="offcanvas-header">
        <h3 id="offcanvasBottomHelpLabel" class="offcanvas-title"><i class="bi bi-question-diamond"></i> Hilfe</h3>
        <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas" type="button"></button>
      </div>
      <div class="offcanvas-body">
        <div id="accordionHelp" class="accordion">
          <div class="accordion-item">
            <h2 id="headingSiteStatus" class="accordion-header">
              <button aria-controls="collapseSiteStatus" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseSiteStatus"
                      data-bs-toggle="collapse" type="button">
                Seitenstatus
              </button>
            </h2>
            <div id="collapseSiteStatus" aria-labelledby="headingSiteStatus" class="accordion-collapse collapse"
                 data-bs-parent="#accordionHelp">
              <div class="accordion-body">
                <div class="row">
                  <div
                      v-if="store.state.hostnames.fx !== 'Nicht gesetzt!' || store.state.hostnames.dw !== 'Nicht gesetzt!' || store.state.hostnames.hw !== 'Nicht gesetzt!' || store.state.hostnames.ff !== 'Nicht gesetzt!' || store.state.hostnames.by !== 'Nicht gesetzt!' || store.state.hostnames.nk !== 'Nicht gesetzt!'  || store.state.hostnames.nx !== 'Nicht gesetzt!'  || store.state.hostnames.ww !== 'Nicht gesetzt!' "
                      class="col">
                    <ul class="list-group">
                      <li v-if="store.state.hostnames.fx !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.fx
                        }}
                        (FX)
                        <i v-if="store.state.blocked_sites.normal.FX"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.normal.FX" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.state.blocked_sites.advanced.FX && store.state.blocked_sites.normal.FX"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.FX && store.state.blocked_sites.normal.FX"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.state.hostnames.dw !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.dw
                        }}
                        (DW)
                        <i v-if="store.state.blocked_sites.normal.DW"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.normal.DW" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.state.blocked_sites.advanced.DW && store.state.blocked_sites.normal.DW"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.DW && store.state.blocked_sites.normal.DW"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.state.hostnames.hw !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.hw
                        }}
                        (HW)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.state.blocked_sites.normal.HW"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.state.blocked_sites.normal.HW"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.state.blocked_sites.advanced.HW && store.state.blocked_sites.normal.HW"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.HW && store.state.blocked_sites.normal.HW"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine HW-Suchläufe bis: ' + getTimestamp(store.state.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.state.hostnames.ff !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.ff
                        }}
                        (FF)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.state.blocked_sites.normal.FF"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.state.blocked_sites.normal.FF"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.state.blocked_sites.advanced.FF && store.state.blocked_sites.normal.FF"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.FF && store.state.blocked_sites.normal.FF"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine FF-Suchläufe bis: ' + getTimestamp(store.state.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.state.hostnames.by !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.by
                        }}
                        (BY)
                        <i v-if="store.state.blocked_sites.normal.BY"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.normal.BY" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.state.blocked_sites.advanced.BY && store.state.blocked_sites.normal.BY"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.BY && store.state.blocked_sites.normal.BY"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.state.hostnames.nk !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.nk
                        }}
                        (NK)
                        <i v-if="store.state.blocked_sites.normal.NK"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.normal.NK" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.state.blocked_sites.advanced.NK && store.state.blocked_sites.normal.NK"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.NK && store.state.blocked_sites.normal.NK"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.state.hostnames.nx !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.nx
                        }}
                        (NX)
                        <i v-if="store.state.blocked_sites.normal.NX && !store.state.settings.general.flaresolverr"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.normal.NX && !store.state.settings.general.flaresolverr"
                           v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.state.blocked_sites.advanced.NX && store.state.blocked_sites.normal.NX"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.NX && store.state.blocked_sites.normal.NX"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.state.hostnames.ww !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.ww
                        }}
                        (WW)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.state.blocked_sites.normal.WW"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.state.blocked_sites.normal.WW"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.state.blocked_sites.advanced.WW && store.state.blocked_sites.normal.WW"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.WW && store.state.blocked_sites.normal.WW"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine WW-Suchläufe bis: ' + getTimestamp(store.state.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                    </ul>
                  </div>
                  <div
                      v-if="store.state.hostnames.sj !== 'Nicht gesetzt!' || store.state.hostnames.dj !== 'Nicht gesetzt!' || store.state.hostnames.dd !== 'Nicht gesetzt!' || store.state.hostnames.sf !== 'Nicht gesetzt!'"
                      class="col">
                    <ul class="list-group">
                      <li v-if="store.state.hostnames.sj !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.sj
                        }}
                        (SJ)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.state.blocked_sites.normal.SJ"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.state.blocked_sites.normal.SJ"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.state.blocked_sites.advanced.SJ && store.state.blocked_sites.normal.SJ"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.SJ && store.state.blocked_sites.normal.SJ"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine SJ-Suchläufe bis: ' + getTimestamp(store.state.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.state.hostnames.dj !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.dj
                        }}
                        (DJ)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.state.blocked_sites.normal.DJ"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.state.blocked_sites.normal.DJ"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.state.blocked_sites.advanced.DJ && store.state.blocked_sites.normal.DJ"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.DJ && store.state.blocked_sites.normal.DJ"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine DJ-Suchläufe bis: ' + getTimestamp(store.state.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.state.hostnames.sf !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.sf
                        }}
                        (SF)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.state.blocked_sites.normal.SF"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.state.blocked_sites.normal.SF"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.state.blocked_sites.advanced.SF && store.state.blocked_sites.normal.SF"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.SF && store.state.blocked_sites.normal.SF"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine SF-Suchläufe bis: ' + getTimestamp(store.state.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.state.hostnames.dd !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.state.hostnames.dd
                        }}
                        (DD)
                        <i v-if="store.state.blocked_sites.normal.DD"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.normal.DD" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.state.blocked_sites.advanced.DD && store.state.blocked_sites.normal.DD"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.state.blocked_sites.advanced.DD && store.state.blocked_sites.normal.DD"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="accordion-item">
            <h2 id="headingSponsorsHelper" class="accordion-header">
              <button aria-controls="collapseSponsorsHelper" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseSponsorsHelper"
                      data-bs-toggle="collapse" type="button">
                FeedCrawler Sponsors Helper
              </button>
            </h2>
            <div id="collapseSponsorsHelper" aria-labelledby="headingSponsorsHelper" class="accordion-collapse collapse"
                 data-bs-parent="#accordionHelp">
              <div class="accordion-body">
                <p>Der FeedCrawler Sponsors Helper ist ein Docker-Image, das alle derzeit bekannten CAPTCHAs
                  vollautomatisch löst, und dem FeedCrawler entschlüsselt übergibt.</p>
                <p>Das Image steht ausschließlich aktiven <a href="https://github.com/users/rix1337/sponsorship"
                                                             target="_blank">Sponsoren</a> zur Verfügung (daher
                  der
                  Name).<br>
                  Die Freischaltung erfolgt automatisch für aktive Sponsoren im dafür eingerichteten
                  GitHub-Repo.
                </p>
                <p>Benötigt wird ein Account beim
                  unter <a href="#" @click="showCaptchasHelp()">CAPTCHAs</a> beworbenen Captcha-Solver.</p>
                <span>
              <br>
              <a class="btn btn-outline-success"
                 href="https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper"
                 target="_blank">Weitere Hinweise gibt es im Wiki.</a>
                </span>
              </div>
            </div>
          </div>
          <div class="accordion-item">
            <h2 id="headingCaptchas" class="accordion-header">
              <button aria-controls="collapseCaptchas" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseCaptchas"
                      data-bs-toggle="collapse" type="button">
                CAPTCHAs
              </button>
            </h2>
            <div id="collapseCaptchas" aria-labelledby="headingCaptchas" class="accordion-collapse collapse"
                 data-bs-parent="#accordionHelp">
              <div class="accordion-body">
                <button class="btn btn-outline-success" @click="openCaptchaLink">
                  Anti-Captcha.com (schnelles Lösen von reCAPTCHA, cutcaptcha, etc. - auch im Browser)
                </button>
              </div>
            </div>
          </div>
          <div class="accordion-item">
            <h2 id="headingMultiHoster" class="accordion-header">
              <button aria-controls="collapseMultiHoster" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseMultiHoster"
                      data-bs-toggle="collapse" type="button">
                Multihoster
              </button>
            </h2>
            <div id="collapseMultiHoster" aria-labelledby="headingMultiHoster" class="accordion-collapse collapse"
                 data-bs-parent="#accordionHelp">
              <div class="accordion-body">
                <button class="btn btn-outline-success" @click="openHosterLink">
                  LinkSnappy.com (für DDownload, Rapidgator, 1Fichier, etc.)
                </button>
              </div>
            </div>
          </div>
          <div v-if="(store.state.hostnames.bl !== 'Nicht gesetzt!') || (store.state.hostnames.s !== 'Nicht gesetzt!')"
               class="accordion-item">
            <h2 id="headingRegEx" class="accordion-header">
              <button aria-controls="collapseRegEx" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseRegEx"
                      data-bs-toggle="collapse" type="button">
                RegEx
              </button>
            </h2>
            <div id="collapseRegEx" aria-labelledby="headingRegEx" class="accordion-collapse collapse"
                 data-bs-parent="#accordionHelp">
              <div id="helpText" class="accordion-body">
                <h5>Erklärung</h5>
                <p>Reguläre Ausdrücke (Regular Expressions, kurz RegEx) bilden in der Programmierung eine spezielle
                  Form von Zeichenketten, die als Filterkriterien in der Textsuche verwendet werden können.<br>
                  Die unten aufgeführten Beispiel-Regeln lassen sich beliebig erweitern und kombinieren.
                  Falsche RegEx-Einträge können allerdings die Feed-Suche blockieren!<br>
                  Daher jeden Ausdruck auf <a href="https://regexr.com/" target="_blank">RegExr.com</a> testen.
                  Beim Eintrag eines Beispiel-Releases unter <i>Text</i> sollte <i>Expression</i> matchen!</p>
                <h5>Beispiele</h5>
                <div class="table-responsive">
                  <table class="table table-hover">
                    <thead>
                    <tr>
                      <th scope="col">Ausdruck</th>
                      <th scope="col">Bedeutung</th>
                    </tr>
                    </thead>
                    <tbody v-if="store.state.hostnames.bl !== 'Nicht gesetzt!'">
                    <tr>
                      <td>Film.*.Titel.*</td>
                      <td>akzeptiert alle Filmen die mit <i>Film</i> beginnen und <i>Titel</i> enthalten</td>
                    </tr>
                    <tr>
                      <td>.*-GROUP oder -GROUP</td>
                      <td>akzeptiert alle Releases der <i>GROUP</i></td>
                    </tr>
                    <tr>
                      <td>.*1080p.*-GROUP</td>
                      <td>akzeptiert alle Full-HD-Releases der <i>GROUP</i></td>
                    </tr>
                    <tr>
                      <td>Film.Titel.*.DL.*.720p.*.BluRay.*-GROUP</td>
                      <td>akzeptiert alle zweisprachigen HD-BluRay-Releases von <i>Film Titel</i> der <i>GROUP</i></td>
                    </tr>
                    </tbody>
                    <tbody v-if="store.state.hostnames.s !== 'Nicht gesetzt!'">
                    <tr>
                      <td>Serien.Titel.*.S01.*.German.*.720p.*-GROUP</td>
                      <td>akzeptiert alle deutschsprachigen HD-Releases von Staffel 1 des <i>Serien Titel</i> der
                        <i>GROUP</i>
                      </td>
                    </tr>
                    <tr>
                      <td>Serien.Titel.*</td>
                      <td>akzeptiert alle Releases des <i>Serien Titel</i></td>
                    </tr>
                    <tr>
                      <td>Serien.Titel.*.DL.*.720p.*</td>
                      <td>
                        akzeptiert alle zweisprachigen Releases des <i>Serien Titel</i>
                      </td>
                    </tr>
                    <tr>
                      <td>(?!(Diese|Andere)).*Serie.*.DL.*.720p.*-(GROUP|ANDEREGROUP)</td>
                      <td>
                        akzeptiert alle zweisprachigen Releases des <i>Serien Titel</i>, aber nicht <i>Diese
                        Serie</i><br>
                        und nicht <i>Andere Serie</i> und ausschließlich von <i>GROUP</i> oder <i>ANDEREGROUP</i>
                      </td>
                    </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
