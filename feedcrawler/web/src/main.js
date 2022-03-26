import {createApp} from 'vue'
import {createStore} from 'vuex'
import App from './App.vue'

const store = createStore({
    state() {
        return {
            prefix: '',
            crawltimes: {},
            starting: false,
            now: Date.now(),
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
            lists: {sj: [], dj: [], sf: [], by: [], fx: [], nk: [], ww: [], bl: [], s: [], sjbl: []},
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
            sjbl_enabled: true,
        }
    }, mutations: {
        setPrefix(state, prefix) {
            state.prefix = prefix
        },
        setCrawlTimes(state, crawltimes) {
            state.crawltimes = crawltimes
        },
        setStarting(state, starting) {
            state.starting = starting
        },
        setNow(state) {
            state.now = Date.now()
        },
        setHostNames(state, hostnames) {
            state.hostnames = hostnames
        },
        setLists(state, lists) {
            state.lists = lists
        },
        setSettings(state, settings) {
            state.settings = settings
        },
        setSjBlEnabled(state, enabled) {
            state.sjbl_enabled = enabled
        }
    }
})

createApp(App).use(store).mount('#app')
