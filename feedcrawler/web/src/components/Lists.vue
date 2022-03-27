<script setup>
import {useStore} from 'vuex'
import axios from 'axios'

const store = useStore()

function getLists() {
  axios.get(store.state.prefix + 'api/lists/')
      .then(function (res) {
        store.commit('getLists', res.data.lists)
        console.log('Listen abgerufen!')
      }, function () {
        console.log('Konnte Listen nicht abrufen!')
        // ToDo migrate to vue
        //showDanger('Konnte Listen nicht abrufen!')
      })
}

function saveLists() {
  spinLists()
  axios.post(store.state.prefix + 'api/lists/', store.state.lists)
      .then(function () {
        console.log('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.')
        // ToDo migrate to vue
        //showSuccess('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.')
        getLists()
      }, function () {
        console.log('Konnte Listen nicht speichern!')
        // ToDo migrate to vue
        //showDanger('Konnte Listen nicht speichern!')
      })
}

function spinLists() {
  // ToDo migrate to vue from jQuery
  //$("#spinner-lists").fadeIn().delay(1000).fadeOut()
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
      <div id="accordionLists" class="accordion">
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
              <textarea v-model="store.state.lists.mb.filme" class="liste form-control" data-toggle="tooltip"
                        title="Pro Zeile ein Filmtitel (wahlweise mit Erscheinungsjahr in Klammern)."></textarea>
              <h5 v-if="store.state.settings.mb.regex">Filme/Serien (RegEx)</h5>
              <textarea v-if="store.state.settings.mb.regex" v-model="store.state.lists.mb.regex"
                        class="liste form-control"
                        data-toggle="tooltip"
                        title="Pro Zeile ein Film-/Serientitel im RegEx-Format - Die Filterliste wird hierbei ignoriert."></textarea>
              <div v-if="store.state.settings.mbsj.enabled && store.state.hostnames.s === 'Nicht gesetzt!'">
                <h5>Staffeln</h5>
                <textarea v-model="store.state.lists.mbsj.staffeln" class="liste form-control"
                          data-toggle="tooltip"
                          title="Pro Zeile ein Serientitel für ganze Staffeln."></textarea>
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
              <textarea v-model="store.state.lists.sj.serien" class="liste form-control" data-toggle="tooltip"
                        title="Pro Zeile ein Serientitel für Episoden."></textarea>
              <h5 v-if="store.state.settings.sj.regex">Serien (RegEx)</h5>
              <textarea v-if="store.state.settings.sj.regex" v-model="store.state.lists.sj.regex"
                        class="liste form-control"
                        data-toggle="tooltip"
                        title="Pro Zeile ein Serientitel im RegEx-Format für Episoden - Die Filterliste wird hierbei ignoriert."></textarea>
              <h5 v-if="store.state.lists.sj.staffeln_regex">Staffeln (RegEx)</h5>
              <textarea v-if="store.state.lists.sj.staffeln_regex" v-model="store.state.lists.sj.staffeln_regex"
                        class="liste form-control" data-toggle="tooltip"
                        title="Pro Zeile ein Serientitel im RegEx-Format für Staffeln - Die Filterliste wird hierbei ignoriert."></textarea>
              <div v-if="store.state.settings.mbsj.enabled && store.state.hostnames.bl === 'Nicht gesetzt!'">
                <h5>Staffeln</h5>
                <textarea v-model="store.state.lists.mbsj.staffeln" class="liste form-control"
                          data-toggle="tooltip"
                          title="Pro Zeile ein Serientitel für ganze Staffeln."></textarea>
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
                        data-toggle="tooltip"
                        title="Pro Zeile ein Serientitel für ganze Staffeln."></textarea>
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
              <textarea v-model="store.state.lists.dj.dokus" class="liste form-control" data-toggle="tooltip"
                        title="Pro Zeile ein Dokutitel."></textarea>
              <h5 v-if="store.state.settings.dj.regex">Dokus (RegEx)</h5>
              <textarea v-if="store.state.settings.dj.regex" v-model="store.state.lists.dj.regex"
                        class="liste form-control"
                        data-toggle="tooltip"
                        title="Pro Zeile ein Dokutitel im RegEx-Format - Die Filterliste wird hierbei ignoriert."></textarea>
            </div>
          </div>
        </div>
      </div>
      <div>
        <a class="btn btn-dark" href="" type="submit" @click="saveLists()">
          <div id="spinner-lists"
               class="spinner-border spinner-border-sm"
               role="status" style="display: none"></div>
          <i class="bi bi-save"></i> Speichern</a></div>
    </div>
  </div>
</template>
