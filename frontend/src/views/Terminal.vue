<template>
  <a-layout class="terminal-layout">
    <a-layout-header class="header">
      <div class="header-content">
        <h2 class="title">Web Terminal</h2>
        <a-space>
          <a-button @click="addSession" type="primary">
            <template #icon><PlusOutlined /></template>
            新建会话
          </a-button>
          <a-button @click="handleLogout" danger>
            <template #icon><LogoutOutlined /></template>
            退出
          </a-button>
        </a-space>
      </div>
    </a-layout-header>

    <a-layout-content class="content">
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
    </a-layout-content>
  </a-layout>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined, LogoutOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'

const router = useRouter()
const authStore = useAuthStore()

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
  const term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
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
  const wsUrl = `ws://localhost:8000/api/v1/terminal/ws/${sessionId}?token=${authStore.token}`
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

const handleLogout = () => {
  Object.keys(websockets.value).forEach(removeSession)
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  addSession()
})

onUnmounted(() => {
  Object.keys(websockets.value).forEach(removeSession)
})
</script>

<style scoped>
.terminal-layout {
  height: 100vh;
}

.header {
  background: #001529;
  padding: 0 24px;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  color: white;
  margin: 0;
  font-size: 20px;
}

.content {
  padding: 16px;
  background: #f0f2f5;
  overflow: hidden;
}

.terminal-tabs {
  height: 100%;
}

.terminal-tabs :deep(.ant-tabs-content) {
  height: calc(100vh - 120px);
}

.terminal-container {
  height: 100%;
  background: #1e1e1e;
  padding: 8px;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .header {
    padding: 0 12px;
  }

  .title {
    font-size: 16px;
  }

  .content {
    padding: 8px;
  }

  .terminal-tabs :deep(.ant-tabs-content) {
    height: calc(100vh - 110px);
  }
}
</style>
