import {createRouter, createWebHistory} from 'vue-router'
import Main from './components/_Main.vue'
import Helper from './components/_Helper.vue'

export default createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: ':pathMatch(.*)*', // required for path prefixing
            component: Main
        }, {
            path: '/:pathMatch(.*/sponsors_helper.*)*', // required for path prefixing
            component: Helper
        }
    ]
})
