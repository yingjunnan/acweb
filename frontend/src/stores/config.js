import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useConfigStore = defineStore('config', () => {
  const config = ref({
    default_path: '~',
    shell: '/bin/bash',
    font_size: 14,
    theme: 'dark',
    refresh_interval: 3,
    session_timeout: 3600,  // 会话超时（秒）
    buffer_size: 1000  // 缓存行数
  })
  
  async function loadConfig() {
    try {
      const response = await api.get('/api/v1/config/')
      config.value = response.data
    } catch (error) {
      console.error('Failed to load config:', error)
    }
  }
  
  async function saveConfig(newConfig) {
    try {
      const response = await api.post('/api/v1/config/', newConfig)
      config.value = response.data
      return true
    } catch (error) {
      console.error('Failed to save config:', error)
      return false
    }
  }
  
  return {
    config,
    loadConfig,
    saveConfig
  }
})
