import {createRouter, createWebHistory} from 'vue-router'
import Main from './components/_Main.vue'
import Helper from './components/_Helper.vue'

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
