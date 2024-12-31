<script setup>
import {useStore} from '@/main.js'
import {computed} from 'vue'
import {Collapse} from "bootstrap"

const store = useStore()

function showCaptchasHelp() {
  new Collapse(document.getElementById('collapseCaptchas'), {
    toggle: true
  })
}

function openSponsorsLink() {
  window.open('/redirect_sponsors/', '_blank')
}

function openCaptchaLink() {
  window.open('/redirect_captcha/', '_blank')
}

function openHosterLink() {
  window.open('/redirect_hoster/', '_blank')
}

function getTimestamp(ms) {
  const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s)
  const d = new Date(ms)

  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const waitTimeActive = computed(() => {
      if (store.crawltimes.next_cloudflare_run !== "undefined" && !isNaN(store.crawltimes.next_cloudflare_run) && !isNaN(store.misc.now)) {
        return store.crawltimes.next_cloudflare_run > store.misc.now
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
                      v-if="store.hostnames.fx !== 'Nicht gesetzt!' || store.hostnames.dw !== 'Nicht gesetzt!' || store.hostnames.hw !== 'Nicht gesetzt!' || store.hostnames.ff !== 'Nicht gesetzt!' || store.hostnames.by !== 'Nicht gesetzt!' || store.hostnames.nk !== 'Nicht gesetzt!'  || store.hostnames.nx !== 'Nicht gesetzt!'  || store.hostnames.ww !== 'Nicht gesetzt!' "
                      class="col">
                    <ul class="list-group">
                      <li v-if="store.hostnames.fx !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.fx
                        }}
                        (FX)
                        <i v-if="store.blocked_sites.normal.FX"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.normal.FX" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.blocked_sites.advanced.FX && store.blocked_sites.normal.FX"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.FX && store.blocked_sites.normal.FX"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.hostnames.dw !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.dw
                        }}
                        (DW)
                        <i v-if="store.blocked_sites.normal.DW"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.normal.DW" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.blocked_sites.advanced.DW && store.blocked_sites.normal.DW"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.DW && store.blocked_sites.normal.DW"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.hostnames.hw !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.hw
                        }}
                        (HW)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.blocked_sites.normal.HW"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.blocked_sites.normal.HW"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.blocked_sites.advanced.HW && store.blocked_sites.normal.HW"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.HW && store.blocked_sites.normal.HW"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine HW-Suchläufe bis: ' + getTimestamp(store.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.hostnames.ff !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.ff
                        }}
                        (FF)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.blocked_sites.normal.FF"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.blocked_sites.normal.FF"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.blocked_sites.advanced.FF && store.blocked_sites.normal.FF"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.FF && store.blocked_sites.normal.FF"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine FF-Suchläufe bis: ' + getTimestamp(store.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.hostnames.by !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.by
                        }}
                        (BY)
                        <i v-if="store.blocked_sites.normal.BY"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.normal.BY" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.blocked_sites.advanced.BY && store.blocked_sites.normal.BY"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.BY && store.blocked_sites.normal.BY"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.hostnames.nk !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.nk
                        }}
                        (NK)
                        <i v-if="store.blocked_sites.normal.NK"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.normal.NK" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.blocked_sites.advanced.NK && store.blocked_sites.normal.NK"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.NK && store.blocked_sites.normal.NK"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.hostnames.nx !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.nx
                        }}
                        (NX)
                        <i v-if="store.blocked_sites.normal.NX && !store.settings.general.flaresolverr"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.normal.NX && !store.settings.general.flaresolverr"
                           v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.blocked_sites.advanced.NX && store.blocked_sites.normal.NX"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.NX && store.blocked_sites.normal.NX"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                      </li>
                      <li v-if="store.hostnames.ww !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.ww
                        }}
                        (WW)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.blocked_sites.normal.WW"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.blocked_sites.normal.WW"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.blocked_sites.advanced.WW && store.blocked_sites.normal.WW"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.WW && store.blocked_sites.normal.WW"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine WW-Suchläufe bis: ' + getTimestamp(store.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                    </ul>
                  </div>
                  <div
                      v-if="store.hostnames.sj !== 'Nicht gesetzt!' || store.hostnames.dj !== 'Nicht gesetzt!' || store.hostnames.dd !== 'Nicht gesetzt!' || store.hostnames.sf !== 'Nicht gesetzt!'"
                      class="col">
                    <ul class="list-group">
                      <li v-if="store.hostnames.sj !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.sj
                        }}
                        (SJ)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.blocked_sites.normal.SJ"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.blocked_sites.normal.SJ"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.blocked_sites.advanced.SJ && store.blocked_sites.normal.SJ"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.SJ && store.blocked_sites.normal.SJ"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine SJ-Suchläufe bis: ' + getTimestamp(store.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.hostnames.dj !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.dj
                        }}
                        (DJ)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.blocked_sites.normal.DJ"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.blocked_sites.normal.DJ"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.blocked_sites.advanced.DJ && store.blocked_sites.normal.DJ"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.DJ && store.blocked_sites.normal.DJ"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine DJ-Suchläufe bis: ' + getTimestamp(store.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.hostnames.sf !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.sf
                        }}
                        (SF)
                        <span v-if="!waitTimeActive">
                          <i v-if="!store.blocked_sites.normal.SF"
                             v-tippy="'Seite verfügbar'"
                             class="bi bi-check-square-fill text-success"></i>
                        </span>
                        <i v-if="store.blocked_sites.normal.SF"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="store.blocked_sites.advanced.SF && store.blocked_sites.normal.SF"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.SF && store.blocked_sites.normal.SF"
                           v-tippy="'Cloudflare-Blockade erfolgreich umgangen'"
                           class="bi bi-check-square-fill text-success"></i>
                        <span v-if="waitTimeActive">
                        <i v-tippy="'Keine SF-Suchläufe bis: ' + getTimestamp(store.crawltimes.next_cloudflare_run)"
                           class="bi bi-clock-fill text-warning"></i>
                      </span>
                      </li>
                      <li v-if="store.hostnames.dd !== 'Nicht gesetzt!'" class="list-group-item">{{
                          store.hostnames.dd
                        }}
                        (DD)
                        <i v-if="store.blocked_sites.normal.DD"
                           v-tippy="'Seite gesperrt'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.normal.DD" v-tippy="'Seite verfügbar'"
                           class="bi bi-check-square-fill text-success"></i>
                        <i v-if="store.blocked_sites.advanced.DD && store.blocked_sites.normal.DD"
                           v-tippy="'Cloudflare-Blockade nicht umgangen'"
                           class="bi bi-exclamation-square-fill text-danger"></i>
                        <i v-if="!store.blocked_sites.advanced.DD && store.blocked_sites.normal.DD"
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
                SponsorsHelper
              </button>
            </h2>
            <div id="collapseSponsorsHelper" aria-labelledby="headingSponsorsHelper" class="accordion-collapse collapse"
                 data-bs-parent="#accordionHelp">
              <div class="accordion-body">
                <p>Der SponsorsHelper ist ein Docker-Image, das alle derzeit bekannten CAPTCHAs
                  vollautomatisch löst, und dem FeedCrawler entschlüsselt übergibt.</p>
                <p>Das Image steht ausschließlich aktiven <a href="#" target="_blank"
                                                             @click="openSponsorsLink()">Sponsoren</a> zur Verfügung
                  (daher
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
                 href="https://github.com/rix1337/FeedCrawler/wiki/SponsorsHelper"
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
                  DeathByCaptcha.com (schnelles Lösen von reCAPTCHA, cutcaptcha, etc. - auch im Browser)
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
          <div v-if="(store.hostnames.bl !== 'Nicht gesetzt!') || (store.hostnames.s !== 'Nicht gesetzt!')"
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
                    <tbody v-if="store.hostnames.bl !== 'Nicht gesetzt!'">
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
                    <tbody v-if="store.hostnames.s !== 'Nicht gesetzt!'">
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
