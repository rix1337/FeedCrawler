<script setup>
import {useStore} from 'vuex'
import {ref} from 'vue'
import {useToast} from 'vue-toastification'
import {Collapse, Offcanvas} from 'bootstrap'
import {submitForm} from "@formkit/vue"
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
    new Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false}).show()
    new Collapse(document.getElementById('collapseRegEx'), {
        toggle: true
    })
}

function submitLists() {
    submitForm('lists')
}
</script>


<template>
    <div class="text-center">
        <div id="offcanvasBottomLists" aria-labelledby="offcanvasBottomListsLabel" class="offcanvas offcanvas-bottom"
             tabindex="-1">
            <div class="offcanvas-header">
                <h3 id="offcanvasBottomListsLabel" class="offcanvas-title"><i class="bi bi-text-left"></i> Listen für
                    die Feed-Suche
                </h3>
                <button aria-label="Close" class="btn-close text-reset" data-bs-dismiss="offcanvas"
                        type="button"></button>
            </div>
            <div class="offcanvas-body">
                <FormKit id="lists" #default="{ value }"
                         :actions="false"
                         incomplete-message="Es müssen alle Felder korrekt ausgefüllt werden! Fehler sind rot markiert."
                         messages-class="text-danger"
                         type="form"
                         @submit="saveLists()"
                >
                    <h4 v-if="!store.state.misc.loaded_lists">Listen werden geladen...</h4>
                    <div v-if="store.state.misc.loaded_lists" id="accordionLists" class="accordion">
                        <div v-if="store.state.hostnames.bl !== 'Nicht gesetzt!'" class="accordion-item">
                            <h2 id="headingHostnamesBl" class="accordion-header">
                                <button aria-controls="collapseHostnamesBl" aria-expanded="false"
                                        class="accordion-button collapsed"
                                        data-bs-target="#collapseHostnamesBl"
                                        data-bs-toggle="collapse" type="button">
                                    Filme ({{ store.state.hostnames.bl }})
                                </button>
                            </h2>
                            <div id="collapseHostnamesBl" aria-labelledby="headingHostnamesBl"
                                 class="accordion-collapse collapse"
                                 data-bs-parent="#accordionLists">
                                <div class="accordion-body">
                                    <div v-tippy="'Pro Zeile ein Film-Titel'">
                                        <FormKit v-model="store.state.lists.mb.filme"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-+&\s]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: - + &'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 label="Reguläre Suche"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Film-Titel"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                    <div v-if="store.state.settings.mb.regex"
                                         v-tippy="'Pro Zeile ein Film-/Serien-Titel im RegEx-Format (Filterliste wird hier ignoriert)'">
                                        <h5><span v-tippy="'Hilfe zu RegEx öffnen'"
                                                  class="link-primary"
                                                  @click="showRegExHelp">RegEx-Suche</span>
                                        </h5><!-- Setting variables in label is unsupported -->
                                        <FormKit v-model="store.state.lists.mb.regex"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-\s.*+()|\[\]?!]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: . * + ( ) | [ ] ? !'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Film.*.Titel.*"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                    <div
                                        v-if="store.state.settings.mbsj.enabled && store.state.hostnames.s === 'Nicht gesetzt!'"
                                        v-tippy="'Pro Zeile ein Serien-Titel (gesucht werden vollständige Staffeln)'">
                                        <FormKit v-model="store.state.lists.mbsj.staffeln"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-+&\s]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: - + &'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 label="Reguläre Suche"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Serien-Titel"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-if="store.state.hostnames.s !== 'Nicht gesetzt!'" class="accordion-item">
                            <h2 id="headingHostnamesS" class="accordion-header">
                                <button aria-controls="collapseHostnamesS" aria-expanded="false"
                                        class="accordion-button collapsed"
                                        data-bs-target="#collapseHostnamesS" data-bs-toggle="collapse" type="button">
                                    Folgen ({{ store.state.hostnames.s }})
                                </button>
                            </h2>
                            <div id="collapseHostnamesS" aria-labelledby="headingHostnamesS"
                                 class="accordion-collapse collapse"
                                 data-bs-parent="#accordionLists">
                                <div class="accordion-body">
                                    <div v-tippy="'Pro Zeile ein Serien-Titel (gesucht werden Folgen)'">
                                        <FormKit v-model="store.state.lists.sj.serien"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-+&\s]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: - + &'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 label="Reguläre Suche"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Serien-Titel"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                    <div v-if="store.state.settings.sj.regex"
                                         v-tippy="'Pro Zeile ein Serien-Titel im RegEx-Format (Filterliste wird hier ignoriert)'">
                                        <h5><span v-tippy="'Hilfe zu RegEx öffnen'"
                                                  class="link-primary"
                                                  @click="showRegExHelp">RegEx-Suche</span>
                                        </h5><!-- Setting variables in label is unsupported -->
                                        <FormKit v-model="store.state.lists.sj.regex"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-\s.*+()|\[\]?!]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: . * + ( ) | [ ] ? !'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Serien.*.Titel.*"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                    <div v-if="store.state.lists.sj.staffeln_regex"
                                         v-tippy="'Pro Zeile ein Serien-Titel im RegEx-Format für Staffeln (Filterliste wird hier ignoriert)'">
                                        <h5><span v-tippy="'Hilfe zu RegEx öffnen'"
                                                  class="link-primary"
                                                  @click="showRegExHelp">RegEx-Suche</span>
                                        </h5><!-- Setting variables in label is unsupported -->
                                        <FormKit v-if="store.state.lists.sj.staffeln_regex"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-\s.*+()|\[\]?!]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: . * + ( ) | [ ] ? !'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Serien.*.Titel.*"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                    <div
                                        v-if="store.state.settings.mbsj.enabled && store.state.hostnames.bl === 'Nicht gesetzt!'"
                                        v-tippy="'Pro Zeile ein Serien-Titel (gesucht werden vollständige Staffeln)'">
                                        <FormKit v-model="store.state.lists.mbsj.staffeln"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-+&\s]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: - + &'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 label="Reguläre Suche"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Serien-Titel"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div
                            v-if="store.state.hostnames.sjbl !== 'Nicht gesetzt!' && store.state.settings.mbsj.enabled && store.state.misc.sjbl_enabled"
                            class="accordion-item">
                            <h2 id="headingHostnamesSjBl" class="accordion-header">
                                <button aria-controls="collapseHostnamesSjBl" aria-expanded="false"
                                        class="accordion-button collapsed"
                                        data-bs-target="#collapseHostnamesSjBl" data-bs-toggle="collapse"
                                        type="button">
                                    Staffeln ({{ store.state.hostnames.sjbl }})
                                </button>
                            </h2>
                            <div id="collapseHostnamesSjBl" aria-labelledby="headingHostnamesSjBl"
                                 class="accordion-collapse collapse"
                                 data-bs-parent="#accordionLists">
                                <div class="accordion-body">
                                    <div v-tippy="'Pro Zeile ein Serien-Titel (gesucht werden vollständige Staffeln)'">
                                        <FormKit v-model="store.state.lists.mbsj.staffeln"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-+&\s]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: - + &'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 label="Reguläre Suche"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Serien-Titel"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-if="store.state.hostnames.dj !== 'Nicht gesetzt!'" class="accordion-item">
                            <h2 id="headingHostnamesDj" class="accordion-header">
                                <button aria-controls="collapseHostnamesDj" aria-expanded="false"
                                        class="accordion-button collapsed"
                                        data-bs-target="#collapseHostnamesDj" data-bs-toggle="collapse"
                                        type="button">
                                    Dokus ({{ store.state.hostnames.dj }})
                                </button>
                            </h2>
                            <div id="collapseHostnamesDj" aria-labelledby="headingHostnamesDj"
                                 class="accordion-collapse collapse"
                                 data-bs-parent="#accordionLists">
                                <div class="accordion-body">
                                    <div v-tippy="'Pro Zeile ein Doku-Titel'">
                                        <FormKit v-model="store.state.lists.dj.dokus"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-+&\s]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: - + &'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 label="Reguläre Suche"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Doku-Titel"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                    <div v-if="store.state.settings.dj.regex"
                                         v-tippy="'Pro Zeile ein Doku-Titel im RegEx-Format (Filterliste wird hier ignoriert)'">
                                        <h5><span v-tippy="'Hilfe zu RegEx öffnen'"
                                                  class="link-primary"
                                                  @click="showRegExHelp">RegEx-Suche</span>
                                        </h5><!-- Setting variables in label is unsupported -->
                                        <FormKit v-model="store.state.lists.dj.regex"
                                                 :validation="[['?matches', /^[a-zA-Z0-9ÄäÖöÜüß\-\s.*+()|\[\]?!]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Buchstaben, Zahlen, Leerzeichen oder folgende Sonderzeichen eingeben: . * + ( ) | [ ] ? !'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. Doku.*.Titel.*"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-if="store.state.hostnames.dd !== 'Nicht gesetzt!'" class="accordion-item">
                            <h2 id="headingHostnamesDd" class="accordion-header">
                                <button aria-controls="collapseHostnamesDd" aria-expanded="false"
                                        class="accordion-button collapsed"
                                        data-bs-target="#collapseHostnamesDd" data-bs-toggle="collapse"
                                        type="button">
                                    Folgen ({{ store.state.hostnames.dd }})
                                </button>
                            </h2>
                            <div id="collapseHostnamesDd" aria-labelledby="headingHostnamesDd"
                                 class="accordion-collapse collapse"
                                 data-bs-parent="#accordionLists">
                                <div class="accordion-body">
                                    <div v-tippy="'Pro Zeile eine numerische RSS-Feed-ID'">
                                        <FormKit v-model="store.state.lists.dd.feeds"
                                                 :validation="[['?matches', /^[0-9\n]+$/]]"
                                                 :validation-messages="{
                                matches: 'Bitte nur Zahlen eingeben.'
                             }"
                                                 class="liste form-control bg-light mb-4"
                                                 help-class="text-muted"
                                                 input-class="liste form-control bg-light mb-4"
                                                 label="Reguläre Suche"
                                                 messages-class="text-danger"
                                                 placeholder="Bspw. 12345"
                                                 rows="10"
                                                 type="textarea"
                                                 validation-visibility="live"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </FormKit>
                <div>
                    <button v-if="store.state.misc.loaded_lists" class="btn btn-primary mt-4" type="submit"
                            @click="submitLists()">
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

<style>
/* Custom Textarea for lists */
.liste {
    resize: none;
}
</style>
