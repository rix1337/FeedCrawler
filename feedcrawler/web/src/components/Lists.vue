<script setup>
import {useStore} from 'vuex'
import {ref} from 'vue'
import {useToast} from 'vue-toastification'
import {Collapse, Offcanvas} from 'bootstrap'
import axios from 'axios'

const store = useStore()
const toast = useToast()

function getLists() {
  axios.get('api/lists/')
      .then(function (res) {
        store.commit('getLists', res.data.lists)
      }, function () {
        console.log('Konnte Listen nicht abrufen!')
        toast.error('Konnte Listen nicht abrufen!')
      })
}

function saveLists() {
  spinLists()
  axios.post('api/lists/', store.state.lists)
      .then(function () {
        console.log('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.')
        toast.success('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.')
        getLists()
      }, function () {
        console.log('Konnte Listen nicht speichern!')
        toast.error('Konnte Listen nicht speichern!')
      })
}

const spin_lists = ref(false)

function spinLists() {
  spin_lists.value = true
  setTimeout(function () {
    spin_lists.value = false
  }, 1000)
}

function showRegExHelp() {
  let offcanvas = new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false})
  offcanvas.show()
  new Collapse(document.getElementById('collapseRegEx'), {
    toggle: true
  })
  sessionStorage.setItem('fromNav', '')
  window.location.href = "#collapseRegEx"
}
</script>


<template>
  <div class="text-center">
    <div id="offcanvasBottomLists" aria-labelledby="offcanvasBottomListsLabel" class="offcanvas offcanvas-bottom"
         tabindex="-1">
      <div class="offcanvas-header">
        <h3 id="offcanvasBottomListsLabel" class="offcanvas-title"><i class="bi bi-text-left"></i> Suchlisten</h3>
        <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas" type="button"></button>
      </div>
      <div class="offcanvas-body">
        <h4 v-if="!store.state.misc.loaded_lists">Suchlisten werden geladen...</h4>
        <div v-if="store.state.misc.loaded_lists" id="accordionLists" class="accordion">
          <div v-if="store.state.hostnames.bl !== 'Nicht gesetzt!'" class="accordion-item">
            <h2 id="headingHostnamesBl" class="accordion-header">
              <button aria-controls="collapseHostnamesBl" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseHostnamesBl"
                      data-bs-toggle="collapse" type="button">
                {{ store.state.hostnames.bl }}
              </button>
            </h2>
            <div id="collapseHostnamesBl" aria-labelledby="headingHostnamesBl" class="accordion-collapse collapse"
                 data-bs-parent="#accordionLists">
              <div class="accordion-body">
                <h5>Filme</h5>
                <textarea v-model="store.state.lists.mb.filme"
                          v-tippy="'Pro Zeile ein Filmtitel (wahlweise mit Erscheinungsjahr in Klammern).'"
                          class="liste form-control bg-light mb-4"></textarea>
                <h5 v-if="store.state.settings.mb.regex">Filme/Serien <span v-tippy="'Hilfe zu RegEx öffnen'"
                                                                            class="link-primary"
                                                                            @click="showRegExHelp">(RegEx)</span>
                </h5>
                <textarea v-if="store.state.settings.mb.regex" v-model="store.state.lists.mb.regex"
                          class="liste form-control bg-light mb-4"
                          v-tippy="'Pro Zeile ein Film-/Serientitel im RegEx-Format - Die Filterliste wird hierbei ignoriert.'"></textarea>
                <div v-if="store.state.settings.mbsj.enabled && store.state.hostnames.s === 'Nicht gesetzt!'">
                  <h5>Staffeln</h5>
                  <textarea v-model="store.state.lists.mbsj.staffeln" class="liste form-control bg-light mb-4"
                            v-tippy="'Pro Zeile ein Serientitel für ganze Staffeln.'"></textarea>
                </div>
              </div>
            </div>
          </div>
          <div v-if="store.state.hostnames.s !== 'Nicht gesetzt!'" class="accordion-item">
            <h2 id="headingHostnamesS" class="accordion-header">
              <button aria-controls="collapseHostnamesS" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseHostnamesS" data-bs-toggle="collapse" type="button">
                {{ store.state.hostnames.s }}
              </button>
            </h2>
            <div id="collapseHostnamesS" aria-labelledby="headingHostnamesS" class="accordion-collapse collapse"
                 data-bs-parent="#accordionLists">
              <div class="accordion-body">
                <h5>Serien</h5>
                <textarea v-model="store.state.lists.sj.serien" v-tippy="'Pro Zeile ein Serientitel für Episoden.'"
                          class="liste form-control bg-light mb-4"></textarea>
                <h5 v-if="store.state.settings.sj.regex">Serien <span v-tippy="'Hilfe zu RegEx öffnen'"
                                                                      class="link-primary"
                                                                      @click="showRegExHelp">(RegEx)</span></h5>
                <textarea v-if="store.state.settings.sj.regex" v-model="store.state.lists.sj.regex"
                          class="liste form-control bg-light mb-4"
                          v-tippy="'Pro Zeile ein Serientitel im RegEx-Format für Episoden - Die Filterliste wird hierbei ignoriert.'"></textarea>
                <h5 v-if="store.state.lists.sj.staffeln_regex">Staffeln <span v-tippy="'Hilfe zu RegEx öffnen'"
                                                                              class="link-primary"
                                                                              @click="showRegExHelp">(RegEx)</span></h5>
                <textarea v-if="store.state.lists.sj.staffeln_regex" v-model="store.state.lists.sj.staffeln_regex"
                          v-tippy="'Pro Zeile ein Serientitel im RegEx-Format für Staffeln - Die Filterliste wird hierbei ignoriert.'"
                          class="liste form-control bg-light mb-4"></textarea>
                <div v-if="store.state.settings.mbsj.enabled && store.state.hostnames.bl === 'Nicht gesetzt!'">
                  <h5>Staffeln</h5>
                  <textarea v-model="store.state.lists.mbsj.staffeln" class="liste form-control bg-light mb-4"
                            v-tippy="'Pro Zeile ein Serientitel für ganze Staffeln.'"></textarea>
                </div>
              </div>
            </div>
          </div>
          <div
              v-if="store.state.hostnames.sjbl !== 'Nicht gesetzt!' && store.state.settings.mbsj.enabled && store.state.misc.sjbl_enabled"
              class="accordion-item">
            <h2 id="headingHostnamesSjBl" class="accordion-header">
              <button aria-controls="collapseHostnamesSjBl" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseHostnamesSjBl" data-bs-toggle="collapse"
                      type="button">
                {{ store.state.hostnames.sjbl }}
              </button>
            </h2>
            <div id="collapseHostnamesSjBl" aria-labelledby="headingHostnamesSjBl" class="accordion-collapse collapse"
                 data-bs-parent="#accordionLists">
              <div class="accordion-body">
                <h5>Staffeln</h5>
                <textarea v-model="store.state.lists.mbsj.staffeln" class="liste form-control bg-light mb-4"

                          v-tippy="'Pro Zeile ein Serientitel für ganze Staffeln.'"></textarea>
              </div>
            </div>
          </div>
          <div v-if="store.state.hostnames.dj !== 'Nicht gesetzt!'" class="accordion-item">
            <h2 id="headingHostnamesDj" class="accordion-header">
              <button aria-controls="collapseHostnamesDj" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseHostnamesDj" data-bs-toggle="collapse"
                      type="button">
                {{ store.state.hostnames.dj }}
              </button>
            </h2>
            <div id="collapseHostnamesDj" aria-labelledby="headingHostnamesDj" class="accordion-collapse collapse"
                 data-bs-parent="#accordionLists">
              <div class="accordion-body">
                <h5>Dokus</h5>
                <textarea v-model="store.state.lists.dj.dokus" v-tippy="'Pro Zeile ein Dokutitel.'"
                          class="liste form-control bg-light mb-4"></textarea>
                <h5 v-if="store.state.settings.dj.regex">Dokus <span v-tippy="'Hilfe zu RegEx öffnen'"
                                                                     class="link-primary"
                                                                     @click="showRegExHelp">(RegEx)</span></h5>
                <textarea v-if="store.state.settings.dj.regex" v-model="store.state.lists.dj.regex"
                          class="liste form-control bg-light mb-4"

                          v-tippy="'Pro Zeile ein Dokutitel im RegEx-Format - Die Filterliste wird hierbei ignoriert.'"></textarea>
              </div>
            </div>
          </div>
          <div v-if="store.state.hostnames.dd !== 'Nicht gesetzt!'" class="accordion-item">
            <h2 id="headingHostnamesDd" class="accordion-header">
              <button aria-controls="collapseHostnamesDd" aria-expanded="false" class="accordion-button collapsed"
                      data-bs-target="#collapseHostnamesDd" data-bs-toggle="collapse"
                      type="button">
                {{ store.state.hostnames.dd }}
              </button>
            </h2>
            <div id="collapseHostnamesDd" aria-labelledby="headingHostnamesDd" class="accordion-collapse collapse"
                 data-bs-parent="#accordionLists">
              <div class="accordion-body">
                <h5>Feed-IDs</h5>
                <textarea v-model="store.state.lists.dd.feeds"
                          v-tippy="'Pro Zeile eine numerische RSS-Feed-ID.'"
                          class="liste form-control bg-light mb-4"></textarea>
              </div>
            </div>
          </div>
        </div>
        <div>
          <button v-if="store.state.misc.loaded_lists" class="btn btn-primary mt-2" type="submit" @click="saveLists()">
            <div v-if="spin_lists" class="spinner-border spinner-border-sm" role="status"></div>
            <i v-if="!spin_lists" class="bi bi-save"></i> Speichern
          </button>
          <button v-else class="btn btn-dark disabled">
            <span class="spinner-border spinner-border-sm" role="status"></span> Lädt...
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
