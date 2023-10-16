import {createRouter, createWebHistory} from 'vue-router'
import Main from './components/_Main.vue'

export default createRouter({
    history: createWebHistory(), routes: [{
        path: '/:pathMatch(.*)*', // required for path prefixing
        component: Main
    }]
})
