import {createApp} from 'vue'
import {createStore} from 'vuex'
import axios from "axios"

import App from './App.vue'

// The store is created here, and then passed to the Vue instance
// It contains the state of the application and is updated through calls to the FeedCrawler API
const store = createStore({
    state() {
        return {
            prefix: '',
            crawltimes: {},
            hostnames: {
                sj: 'Nicht gesetzt!',
                dj: 'Nicht gesetzt!',
                sf: 'Nicht gesetzt!',
                by: 'Nicht gesetzt!',
                fx: 'Nicht gesetzt!',
                nk: 'Nicht gesetzt!',
                ww: 'Nicht gesetzt!',
                bl: 'Nicht gesetzt!',
                s: 'Nicht gesetzt!',
                sjbl: 'Nicht gesetzt!'
            },
            lists: {
                sj: [],
                dj: [],
                sf: [],
                by: [],
                fx: [],
                nk: [],
                ww: [],
                bl: [],
                s: [],
                sjbl: []
            },
            settings: {
                general: {
                    myjd_user: '',
                    myjd_pass: '',
                    myjd_device: '',
                    closed_myjd_tab: false,
                    packages_per_myjd_page: 10,
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
                crawljobs: {
                    autostart: false,
                    subdir: false,
                }
            },
            misc: {
                myjd_connection_error: false,
                now: Date.now(),
                pageSizeMyJD: 3,
                sjbl_enabled: true,
                starting: false,
            },
        }
    }, mutations: {
        getCrawlTimes(state) {
            axios.get(state.prefix + 'api/crawltimes/')
                .then(function (res) {
                    state.starting = false
                    state.crawltimes = res.data.crawltimes
                    console.log('Laufzeiten abgerufen!')
                }, function () {
                    console.log('Konnte Laufzeiten nicht abrufen!')
                    // ToDo migrate to vue
                    //showDanger('Konnte Laufzeiten nicht abrufen!')
                })
        },
        getHostNames(state) {
            axios.get(state.prefix + 'api/hostnames/')
                .then(function (res) {
                    state.hostnames = res.data.hostnames
                    let not_set = 'Nicht gesetzt!'
                    state.misc.sjbl_enabled = !((store.state.hostnames.bl === not_set && store.state.hostnames.s !== not_set) || (store.state.hostnames.bl !== not_set && store.state.hostnames.s === not_set))
                    console.log('Hostnamen abgerufen!')
                }, function () {
                    console.log('Konnte Hostnamen nicht abrufen!')
                    // ToDo migrate to vue
                    //showDanger('Konnte Hostnamen nicht abrufen!')
                })
        },
        getLists(state) {
            axios.get(state.prefix + 'api/lists/')
                .then(function (res) {
                    state.lists = res.data.lists
                    console.log('Listen abgerufen!')
                }, function () {
                    console.log('Konnte Listen nicht abrufen!')
                    // ToDo migrate to vue
                    //showDanger('Konnte Listen nicht abrufen!')
                })
        },
        getSettings(state) {
            axios.get(store.state.prefix + 'api/settings/')
                .then(function (res) {
                    state.settings = res.data.settings
                    console.log('Einstellungen abgerufen!')
                    state.misc.myjd_connection_error.value = !(store.state.settings.general.myjd_user && store.state.settings.general.myjd_device && store.state.settings.general.myjd_device)
                    state.misc.pageSizeMyJD.value = store.state.settings.general.packages_per_myjd_page
                }, function () {
                    console.log('Konnte Einstellungen nicht abrufen!')
                    // ToDo migrate to vue
                    //showDanger('Konnte Einstellungen nicht abrufen!')
                })
        },
        setMyJDConnectionError(state, myjd_connection_error) {
            state.misc.myjd_connection_error = myjd_connection_error
        },
        setNow(state, now) {
            state.misc.now = now
        },
        setPrefix(state, prefix) {
            console.log('Running in dev mode! Expecting FeedCrawler at ' + prefix)
            state.prefix = prefix
        },
        setSjBlEnabled(state, enabled) {
            state.misc.sjbl_enabled = enabled
        },
        setStarting(state, starting) {
            state.misc.starting = starting
        }
    }
})

createApp(App).use(store).mount('#app')
