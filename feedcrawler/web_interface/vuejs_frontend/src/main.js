import {createApp} from 'vue'
import {createPinia, defineStore} from 'pinia'
import axios from 'axios'
import {createToaster, Toaster} from "@meforma/vue-toaster"
import VueTippy from 'vue-tippy'
import 'tippy.js/dist/tippy.css'
import {defaultConfig, plugin} from '@formkit/vue'
import {de} from '@formkit/i18n'
import App from './App.vue'

const toast = createToaster({
    duration: 3000,
    max: 1,
    pauseOnHover: false,
    position: 'top',
})

export const useStore = defineStore({
    id: 'main',
    state: () => ({
        crawltimes: {},
        blocked_sites: {
            normal: {}, advanced: {}
        }, hostnames: {
            fx: 'Nicht gesetzt!',
            sf: 'Nicht gesetzt!',
            dw: 'Nicht gesetzt!',
            hw: 'Nicht gesetzt!',
            ff: 'Nicht gesetzt!',
            by: 'Nicht gesetzt!',
            nk: 'Nicht gesetzt!',
            nx: 'Nicht gesetzt!',
            ww: 'Nicht gesetzt!',
            sj: 'Nicht gesetzt!',
            dj: 'Nicht gesetzt!',
            dd: 'Nicht gesetzt!',
            bl: 'Nicht gesetzt!',
            s: 'Nicht gesetzt!',
            sjbl: 'Nicht gesetzt!',
            cloudflare: 'Nicht gesetzt!',
            cloudflare_shorthands: 'Nicht gesetzt!',
            search: 'Nicht gesetzt!'
        }, lists: {
            mb: [], sj: [], dj: [], dd: [], mbsj: []
        }, settings: {
            general: {
                auth_hash: '',
                myjd_user: '',
                myjd_pass: '',
                myjd_device: '',
                packages_per_myjd_page: 3,
                port: 9090,
                myjd_auto_update: false,
            }, mb: {
                quality: '1080p',
                search: 3,
                regex: false,
                imdb_score: 5,
                imdb_year: 2020,
                force_dl: false,
                retail_only: false,
                cutoff: false,
                hevc_retail: false,
                hoster_fallback: false
            }, f: {
                search: 3
            }, cloudflare: {
                wait_time: 6
            }, sj: {
                quality: '1080p', regex: false, retail_only: false, hevc_retail: false, hoster_fallback: false
            }, mbsj: {
                enabled: false, quality: '1080p', packs: false, source: ''
            }, dj: {
                quality: '1080p', regex: false, hoster_fallback: false
            }, dd: {
                hoster_fallback: false
            }, hosters: {
                ddl: true,
                rapidgator: true,
                onefichier: true,
                filer: true,
                turbobit: true,
                filefactory: true,
                uptobox: true,
                nitroflare: true,
                k2s: true,
                katfile: true,
                ironfiles: true,
            }, alerts: {
                telegram: "", discord: "", pushbullet: "", pushover: "", homeassistant: ""
            }, plex: {
                url: "", api: ""
            }, ombi: {
                url: "", api: ""
            }, overseerr: {
                url: "", api: ""
            }, crawljobs: {
                autostart: false, subdir: false, subdir_by_type: false
            }, sponsors_helper: {
                max_attempts: 3
            }

        }, misc: {
            docker: false,
            helper_active: false,
            helper_available: false,
            loaded_log: false,
            loaded_lists: false,
            loaded_settings: false,
            myjd_connection_error: false,
            no_site_blocked: 0,
            now: Date.now(),
            sjbl_enabled: true,
            starting: false,
        }
    }), actions: {
        getBlockedSites() {
            axios.get('api/blocked_sites/')
                .then((res) => {
                    this.blocked_sites = res.data.blocked_sites

                    if (this.hostnames) {
                        let current_hostnames = []
                        for (let hn in this.hostnames) {
                            if (this.hostnames[hn] !== "Nicht gesetzt!") {
                                if (!["s", "bl", "sjbl"].includes(hn)) {
                                    current_hostnames.push(hn)
                                }
                            }
                        }
                        if (current_hostnames.length > 0) {
                            const blocked_sites = this.blocked_sites
                            for (let site in blocked_sites.normal) {
                                if (current_hostnames.includes(site.toLowerCase())) {
                                    if (blocked_sites.normal[site] && blocked_sites.advanced[site]) {
                                        this.misc.no_site_blocked = 2
                                    } else if (blocked_sites.normal[site]) {
                                        this.misc.no_site_blocked = 1
                                    }
                                }
                            }
                        }
                    }

                }, () => {
                    console.log('Konnte blockierte Seiten nicht abrufen!')
                    toast.error('Konnte blockierte Seiten nicht abrufen!')
                })
        }, getCrawlTimes() {
            axios.get('api/crawltimes/')
                .then((res) => {
                    this.misc.starting = false
                    this.crawltimes = res.data.crawltimes
                }, () => {
                    console.log('Konnte Laufzeiten nicht abrufen!')
                    toast.error('Konnte Laufzeiten nicht abrufen!')
                })
        }, getHostNames() {
            axios.get('api/hostnames/')
                .then((res) => {
                    this.hostnames = res.data.hostnames
                    let not_set = 'Nicht gesetzt!'
                    this.misc.sjbl_enabled = !((this.hostnames.bl === not_set && this.hostnames.s !== not_set) || (this.hostnames.bl !== not_set && this.hostnames.s === not_set))
                }, () => {
                    console.log('Konnte Hostnamen nicht abrufen!')
                    toast.error('Konnte Hostnamen nicht abrufen!')
                })
        }, getLists() {
            axios.get('api/lists/')
                .then((res) => {
                    this.lists = res.data.lists
                    this.misc.loaded_lists = true
                }, () => {
                    console.log('Konnte Listen nicht abrufen!')
                    toast.error('Konnte Listen nicht abrufen!')
                })
        }, getSettings() {
            axios.get('api/settings/')
                .then((res) => {
                    this.settings = res.data.settings
                    this.misc.loaded_settings = true
                    this.misc.myjd_connection_error = !(this.settings.general.myjd_user && this.settings.general.myjd_device && this.settings.general.myjd_device)
                }, () => {
                    console.log('Konnte Einstellungen nicht abrufen!')
                    toast.error('Konnte Einstellungen nicht abrufen!')
                })
        }, setDocker(docker) {
            this.misc.docker = docker
        }, setHelperActive(helper_active) {
            this.misc.helper_active = helper_active
        }, setHelperAvailable(helper_available) {
            this.misc.helper_available = helper_available
        }, setMyJDConnectionError(myjd_connection_error) {
            this.misc.myjd_connection_error = myjd_connection_error
        }, setNow(now) {
            this.misc.now = now
        }, setStarting(starting) {
            this.misc.starting = starting
        }
    }
})

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(VueTippy)

app.use(plugin, defaultConfig({
    locales: {de},
    locale: 'de'
}))

app.use(Toaster).provide('toast', toast)
app.mount('#app')
