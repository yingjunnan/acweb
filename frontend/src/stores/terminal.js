import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTerminalStore = defineStore('terminal', () => {
  const sessions = ref([])
  const activeSession = ref('')
  const terminalRefs = ref({})
  const terminals = ref({})
  const websockets = ref({})
  
  return {
    sessions,
    activeSession,
    terminalRefs,
    terminals,
    websockets
  }
})
