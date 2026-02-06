import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTerminalStore = defineStore('terminal', () => {
  const sessions = ref([])
  const activeSession = ref('')
  const terminalRefs = ref({})
  const terminals = ref({})
  const websockets = ref({})
  
  // 持久化会话信息到 localStorage
  const saveSessions = () => {
    const sessionData = sessions.value.map(s => ({
      id: s.id,
      name: s.name
    }))
    localStorage.setItem('terminal_sessions', JSON.stringify(sessionData))
    localStorage.setItem('terminal_active_session', activeSession.value)
  }
  
  // 从 localStorage 恢复会话信息
  const loadSessions = () => {
    try {
      const savedSessions = localStorage.getItem('terminal_sessions')
      const savedActiveSession = localStorage.getItem('terminal_active_session')
      
      if (savedSessions) {
        sessions.value = JSON.parse(savedSessions)
      }
      if (savedActiveSession) {
        activeSession.value = savedActiveSession
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }
  
  // 清除持久化数据
  const clearSessions = () => {
    localStorage.removeItem('terminal_sessions')
    localStorage.removeItem('terminal_active_session')
    sessions.value = []
    activeSession.value = ''
    terminalRefs.value = {}
    terminals.value = {}
    websockets.value = {}
  }
  
  return {
    sessions,
    activeSession,
    terminalRefs,
    terminals,
    websockets,
    saveSessions,
    loadSessions,
    clearSessions
  }
})
