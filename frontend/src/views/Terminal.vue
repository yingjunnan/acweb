<template>
  <div class="terminal-page">
    <div class="terminal-header">
      <h1 class="page-title">终端管理</h1>
      <a-button @click="addSession" type="primary">
        <template #icon><PlusOutlined /></template>
        新建会话
      </a-button>
    </div>

    <a-tabs
      v-model:activeKey="activeSession"
      type="editable-card"
      @edit="onEdit"
      class="terminal-tabs"
    >
      <a-tab-pane
        v-for="session in sessions"
        :key="session.id"
        :tab="session.name"
        :closable="sessions.length > 1"
      >
        <div :ref="el => setTerminalRef(session.id, el)" class="terminal-container"></div>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useConfigStore } from '../stores/config'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'

const authStore = useAuthStore()
const configStore = useConfigStore()

const sessions = ref([])
const activeSession = ref('')
const terminalRefs = ref({})
const terminals = ref({})
const websockets = ref({})

let sessionCounter = 0

const setTerminalRef = (id, el) => {
  if (el) {
    terminalRefs.value[id] = el
  }
}

const createTerminal = (sessionId) => {
  const config = configStore.config
  const term = new Terminal({
    cursorBlink: true,
    fontSize: config.font_size || 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: config.theme === 'light' ? {
      background: '#ffffff',
      foreground: '#000000'
    } : {
      background: '#1e1e1e',
      foreground: '#d4d4d4'
    },
    rows: 24,
    cols: 80
  })

  const fitAddon = new FitAddon()
  term.loadAddon(fitAddon)

  terminals.value[sessionId] = { term, fitAddon }
  return { term, fitAddon }
}

const connectWebSocket = (sessionId) => {
  const config = configStore.config
  const cwd = config.default_path || '~'
  const wsUrl = `ws://localhost:8000/api/v1/terminal/ws/${sessionId}?token=${authStore.token}&cwd=${encodeURIComponent(cwd)}`
  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    message.success('终端连接成功')
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'output') {
      terminals.value[sessionId]?.term.write(data.data)
    }
  }

  ws.onerror = () => {
    message.error('终端连接错误')
  }

  ws.onclose = () => {
    message.info('终端连接已关闭')
  }

  websockets.value[sessionId] = ws
  return ws
}

const addSession = async () => {
  sessionCounter++
  const sessionId = `session-${Date.now()}-${sessionCounter}`
  const session = {
    id: sessionId,
    name: `终端 ${sessionCounter}`
  }

  sessions.value.push(session)
  activeSession.value = sessionId

  await nextTick()

  const container = terminalRefs.value[sessionId]
  if (container) {
    const { term, fitAddon } = createTerminal(sessionId)
    term.open(container)
    fitAddon.fit()

    const ws = connectWebSocket(sessionId)

    term.onData(data => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'input', data }))
      }
    })

    term.onResize(({ cols, rows }) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols, rows }))
      }
    })

    const resizeObserver = new ResizeObserver(() => {
      fitAddon.fit()
    })
    resizeObserver.observe(container)
  }
}

const removeSession = (sessionId) => {
  const ws = websockets.value[sessionId]
  if (ws) {
    ws.send(JSON.stringify({ type: 'close' }))
    ws.close()
    delete websockets.value[sessionId]
  }

  const terminal = terminals.value[sessionId]
  if (terminal) {
    terminal.term.dispose()
    delete terminals.value[sessionId]
  }

  sessions.value = sessions.value.filter(s => s.id !== sessionId)

  if (sessions.value.length > 0 && activeSession.value === sessionId) {
    activeSession.value = sessions.value[0].id
  }
}

const onEdit = (targetKey, action) => {
  if (action === 'remove') {
    removeSession(targetKey)
  }
}

onMounted(async () => {
  await configStore.loadConfig()
  addSession()
})

onUnmounted(() => {
  Object.keys(websockets.value).forEach(removeSession)
})
</script>

<style scoped>
.terminal-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.terminal-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.terminal-tabs :deep(.ant-tabs-content) {
  flex: 1;
  height: 0;
}

.terminal-tabs :deep(.ant-tabs-tabpane) {
  height: 100%;
}

.terminal-container {
  height: 100%;
  background: #1e1e1e;
  padding: 8px;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 18px;
  }
  
  .terminal-header {
    margin-bottom: 12px;
  }
}
</style>
