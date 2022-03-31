<script setup>
import {useStore} from 'vuex'
import {ref} from 'vue'
import {useToast} from 'vue-toastification'
import axios from 'axios'

const store = useStore()
const toast = useToast()

function getLists() {
  axios.get(store.state.prefix + 'api/lists/')
      .then(function (res) {
        store.commit('getLists', res.data.lists)
      }, function () {
        console.log('Konnte Listen nicht abrufen!')
        toast.error('Konnte Listen nicht abrufen!')
      })
}

function saveLists() {
  spinLists()
  axios.post(store.state.prefix + 'api/lists/', store.state.lists)
      .then(function () {
        console.log('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.')
        toast.success('Listen gespeichert!\nÄnderungen werden im nächsten Suchlauf berücksichtigt.')
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
</script>


<template>
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
          <h2 id="headingZeroOne" class="accordion-header">
            <button aria-controls="collapseZeroOne" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseZeroOne"
                    data-bs-toggle="collapse" type="button">
              {{ store.state.hostnames.bl }}
            </button>
          </h2>
          <div id="collapseZeroOne" aria-labelledby="headingZeroOne" class="accordion-collapse collapse"
               data-bs-parent="#accordionLists">
            <div class="accordion-body">
              <h5>Filme</h5>
              <textarea v-model="store.state.lists.mb.filme"
                        v-tooltip="'Pro Zeile ein Filmtitel (wahlweise mit Erscheinungsjahr in Klammern).'"
                        class="liste form-control"></textarea>
              <h5 v-if="store.state.settings.mb.regex">Filme/Serien (RegEx)</h5>
              <textarea v-if="store.state.settings.mb.regex" v-model="store.state.lists.mb.regex"
                        class="liste form-control"

                        v-tooltip="'Pro Zeile ein Film-/Serientitel im RegEx-Format - Die Filterliste wird hierbei ignoriert.'"></textarea>
              <div v-if="store.state.settings.mbsj.enabled && store.state.hostnames.s === 'Nicht gesetzt!'">
                <h5>Staffeln</h5>
                <textarea v-model="store.state.lists.mbsj.staffeln" class="liste form-control"

                          v-tooltip="'Pro Zeile ein Serientitel für ganze Staffeln.'"></textarea>
              </div>
            </div>
          </div>
        </div>
        <div v-if="store.state.hostnames.s !== 'Nicht gesetzt!'" class="accordion-item">
          <h2 id="headingZeroTwo" class="accordion-header">
            <button aria-controls="collapseZeroTwo" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseZeroTwo" data-bs-toggle="collapse" type="button">
              {{ store.state.hostnames.s }}
            </button>
          </h2>
          <div id="collapseZeroTwo" aria-labelledby="headingZeroTwo" class="accordion-collapse collapse"
               data-bs-parent="#accordionLists">
            <div class="accordion-body">
              <h5>Serien</h5>
              <textarea v-model="store.state.lists.sj.serien" v-tooltip="'Pro Zeile ein Serientitel für Episoden.'"
                        class="liste form-control"></textarea>
              <h5 v-if="store.state.settings.sj.regex">Serien (RegEx)</h5>
              <textarea v-if="store.state.settings.sj.regex" v-model="store.state.lists.sj.regex"
                        class="liste form-control"

                        v-tooltip="'Pro Zeile ein Serientitel im RegEx-Format für Episoden - Die Filterliste wird hierbei ignoriert.'"></textarea>
              <h5 v-if="store.state.lists.sj.staffeln_regex">Staffeln (RegEx)</h5>
              <textarea v-if="store.state.lists.sj.staffeln_regex" v-model="store.state.lists.sj.staffeln_regex"
                        v-tooltip="'Pro Zeile ein Serientitel im RegEx-Format für Staffeln - Die Filterliste wird hierbei ignoriert.'"
                        class="liste form-control"></textarea>
              <div v-if="store.state.settings.mbsj.enabled && store.state.hostnames.bl === 'Nicht gesetzt!'">
                <h5>Staffeln</h5>
                <textarea v-model="store.state.lists.mbsj.staffeln" class="liste form-control"

                          v-tooltip="'Pro Zeile ein Serientitel für ganze Staffeln.'"></textarea>
              </div>
            </div>
          </div>
        </div>
        <div
            v-if="store.state.hostnames.sjbl !== 'Nicht gesetzt!' && store.state.settings.mbsj.enabled && store.state.misc.sjbl_enabled"
            class="accordion-item">
          <h2 id="headingZeroThree" class="accordion-header">
            <button aria-controls="collapseZeroThree" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseZeroThree" data-bs-toggle="collapse"
                    type="button">
              {{ store.state.hostnames.sjbl }}
            </button>
          </h2>
          <div id="collapseZeroThree" aria-labelledby="headingZeroThree" class="accordion-collapse collapse"
               data-bs-parent="#accordionLists">
            <div class="accordion-body">
              <h5>Staffeln</h5>
              <textarea v-model="store.state.lists.mbsj.staffeln" class="liste form-control"

                        v-tooltip="'Pro Zeile ein Serientitel für ganze Staffeln.'"></textarea>
            </div>
          </div>
        </div>
        <div v-if="store.state.hostnames.dj !== 'Nicht gesetzt!'" class="accordion-item">
          <h2 id="headingZeroFour" class="accordion-header">
            <button aria-controls="collapseZeroFour" aria-expanded="false" class="accordion-button collapsed"
                    data-bs-target="#collapseZeroFour" data-bs-toggle="collapse"
                    type="button">
              {{ store.state.hostnames.dj }}
            </button>
          </h2>
          <div id="collapseZeroFour" aria-labelledby="headingZeroFour" class="accordion-collapse collapse"
               data-bs-parent="#accordionLists">
            <div class="accordion-body">
              <h5>Dokus</h5>
              <textarea v-model="store.state.lists.dj.dokus" v-tooltip="'Pro Zeile ein Dokutitel.'"
                        class="liste form-control"></textarea>
              <h5 v-if="store.state.settings.dj.regex">Dokus (RegEx)</h5>
              <textarea v-if="store.state.settings.dj.regex" v-model="store.state.lists.dj.regex"
                        class="liste form-control"

                        v-tooltip="'Pro Zeile ein Dokutitel im RegEx-Format - Die Filterliste wird hierbei ignoriert.'"></textarea>
            </div>
          </div>
        </div>
      </div>
      <div>
        <button class="btn btn-dark" type="submit" @click="saveLists()">
          <div v-if="spin_lists" class="spinner-border spinner-border-sm" role="status"></div>
          <i v-if="!spin_lists" class="bi bi-save"></i> Speichern
        </button>
      </div>
    </div>
  </div>
</template>
