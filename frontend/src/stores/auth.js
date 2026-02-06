import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  
  const isAuthenticated = computed(() => !!token.value)
  
  async function login(username, password) {
    const response = await api.post('/api/v1/auth/login', {
      username,
      password
    })
    token.value = response.data.access_token
    localStorage.setItem('token', token.value)
  }
  
  function logout() {
    token.value = ''
    localStorage.removeItem('token')
  }
  
  return {
    token,
    isAuthenticated,
    login,
    logout
  }
})
