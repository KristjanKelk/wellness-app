// src/store/index.js
import { createStore } from 'vuex'
import auth from './modules/auth.module'

export default createStore({
    state: {
        // your state here
    },
    getters: {
        // your getters here
    },
    mutations: {
        // your mutations here
    },
    actions: {
        // your actions here
    },
    modules: {
        auth
    }
})