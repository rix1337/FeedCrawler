import {createApp} from 'vue'
import {createStore} from 'vuex'
import axios from 'axios'
import router from './router'
import Toast, {TYPE, useToast} from "vue-toastification"
import "vue-toastification/dist/index.css"
import VueTippy from 'vue-tippy'
import 'tippy.js/dist/tippy.css'
import App from './App.vue'

const toast = useToast()

// The store is created here, and then passed to the Vue instance
// It contains the state of the application and is updated through calls to the FeedCrawler API
const store = createStore({
    state() {
        return {
            crawltimes: {},
            blocked_sites: {
                normal: {},
                flaresolverr: {},
                flaresolverr_proxy: {}
            },
            hostnames: {
                sj: 'Nicht gesetzt!',
                dj: 'Nicht gesetzt!',
                sf: 'Nicht gesetzt!',
                by: 'Nicht gesetzt!',
                dd: 'Nicht gesetzt!',
                fx: 'Nicht gesetzt!',
                nk: 'Nicht gesetzt!',
                ww: 'Nicht gesetzt!',
                bl: 'Nicht gesetzt!',
                s: 'Nicht gesetzt!',
                sjbl: 'Nicht gesetzt!'
            },
            lists: {
                mb: [],
                sj: [],
                dj: [],
                dd: [],
                mbsj: [],
            },
            settings: {
                general: {
                    myjd_user: '',
                    myjd_pass: '',
                    myjd_device: '',
                    packages_per_myjd_page: 3,
                    port: 9090,
                },
                mb: {
                    quality: '1080p',
                    search: 3,
                    regex: false,
                    imdb_score: 5,
                    imdb_year: 2020,
                    force_dl: false,
                    retail_only: false,
                    cutoff: false,
                    hevc_retail: false,
                    hoster_fallback: false,
                },
                f: {
                    interval: 6,
                    search: 3,
                },
                sj: {
                    quality: '1080p',
                    regex: false,
                    retail_only: false,
                    hevc_retail: false,
                    hoster_fallback: false,
                },
                mbsj: {
                    enabled: false,
                    quality: '1080p',
                    packs: false,
                    source: '',
                },
                dj: {
                    quality: '1080p',
                    regex: false,
                    hoster_fallback: false,
                },
                dd: {
                    hoster_fallback: false,
                },
                hosters: {
                    rapidgator: true,
                    turbobit: true,
                    uploaded: true,
                    zippyshare: true,
                    oboom: true,
                    ddl: true,
                    filefactory: true,
                    uptobox: true,
                    onefichier: true,
                    filer: true,
                    nitroflare: true,
                    ironfiles: true,
                    k2s: true,
                },
                alerts: {
                    pushbullet: "",
                    pushover: "",
                    telegram: "",
                },
                ombi: {
                    url: "",
                    api: ""
                },
                overseerr: {
                    url: "",
                    api: ""
                },
                crawljobs: {
                    autostart: false,
                    subdir: false,
                }
            },
            misc: {
                docker: false,
                helper_active: false,
                helper_available: false,
                loaded_lists: false,
                loaded_settings: false,
                myjd_connection_error: false,
                no_site_blocked: true,
                now: Date.now(),
                pageSizeMyJD: 3,
                sjbl_enabled: true,
                starting: false,
            },
        }
    }, mutations: {
        getBlockedSites(state) {
            axios.get('api/blocked_sites/')
                .then(function (res) {
                    state.blocked_sites = res.data.blocked_sites

                    if (state.hostnames) {
                        let current_hostnames = []
                        for (let hn in state.hostnames) {
                            if (state.hostnames[hn] !== "Nicht gesetzt!") {
                                if (!["s", "bl", "sjbl"].includes(hn)) {
                                    current_hostnames.push(hn)
                                }
                            }
                        }
                        if (current_hostnames.length > 0) {
                            const blocked_sites = state.blocked_sites
                            for (let site in blocked_sites.normal) {
                                if (current_hostnames.includes(site.toLowerCase())) {
                                    if (blocked_sites.normal[site] && blocked_sites.flaresolverr[site] && blocked_sites.flaresolverr_proxy[site]) {
                                        state.misc.no_site_blocked = false
                                    }
                                }
                            }
                        }
                    }

                }, function () {
                    console.log('Konnte blockierte Seiten nicht abrufen!')
                    toast.error('Konnte blockierte Seiten nicht abrufen!')
                })
        },
        getCrawlTimes(state) {
            axios.get('api/crawltimes/')
                .then(function (res) {
                    state.misc.starting = false
                    state.crawltimes = res.data.crawltimes
                }, function () {
                    console.log('Konnte Laufzeiten nicht abrufen!')
                    toast.error('Konnte Laufzeiten nicht abrufen!')
                })
        },
        getHostNames(state) {
            axios.get('api/hostnames/')
                .then(function (res) {
                    state.hostnames = res.data.hostnames
                    let not_set = 'Nicht gesetzt!'
                    state.misc.sjbl_enabled = !((state.hostnames.bl === not_set && state.hostnames.s !== not_set) || (state.hostnames.bl !== not_set && state.hostnames.s === not_set))
                }, function () {
                    console.log('Konnte Hostnamen nicht abrufen!')
                    toast.error('Konnte Hostnamen nicht abrufen!')
                })
        },
        getLists(state) {
            axios.get('api/lists/')
                .then(function (res) {
                    state.lists = res.data.lists
                    state.misc.loaded_lists = true
                }, function () {
                    console.log('Konnte Listen nicht abrufen!')
                    toast.error('Konnte Listen nicht abrufen!')
                })
        },
        getSettings(state) {
            axios.get('api/settings/')
                .then(function (res) {
                    state.settings = res.data.settings
                    state.misc.loaded_settings = true
                    state.misc.myjd_connection_error = !(state.settings.general.myjd_user && state.settings.general.myjd_device && state.settings.general.myjd_device)
                    state.misc.pageSizeMyJD = state.settings.general.packages_per_myjd_page
                }, function () {
                    console.log('Konnte Einstellungen nicht abrufen!')
                    toast.error('Konnte Einstellungen nicht abrufen!')
                })
        },
        setDocker(state, docker) {
            state.misc.docker = docker
        },
        setHelperActive(state, helper_active) {
            state.misc.helper_active = helper_active
        },
        setHelperAvailable(state, helper_available) {
            state.misc.helper_available = helper_available
        },
        setMyJDConnectionError(state, myjd_connection_error) {
            state.misc.myjd_connection_error = myjd_connection_error
        },
        setNow(state, now) {
            state.misc.now = now
        },
        setSjBlEnabled(state, enabled) {
            state.misc.sjbl_enabled = enabled
        },
        setStarting(state, starting) {
            state.misc.starting = starting
        }
    }
})

const app = createApp(App)
app.use(store)
app.use(router)
app.use(Toast, {
    position: "top-center",
    draggable: false,
    maxToasts: 3,
    bodyClassName: ["toast-body"],
    toastDefaults: {
        [TYPE.ERROR]: {
            icon: 'bi bi-exclamation-triangle',
        },
        [TYPE.WARNING]: {
            icon: 'bi bi-exclamation-circle',
        },
        [TYPE.INFO]: {
            icon: 'bi bi-info-circle',
        },
        [TYPE.SUCCESS]: {
            icon: 'bi bi-check-circle-fill',
            timeout: 3000,
        }
    }
})
app.use(VueTippy)
app.mount('#app')
