import {createRouter, createWebHistory} from 'vue-router'
import Main from './components/__Main.vue'
import Helper from './components/__Helper.vue'

export default createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            component: Main,
        },
        {
            path: '/sponsors_helper',
            component: Helper,
        }
    ]
})
