<template>
  <div class="terminal-page">
    <div class="terminal-header">
      <h1 class="page-title">终端管理</h1>
      <a-button @click="showNewSessionModal" type="primary">
        <template #icon><PlusOutlined /></template>
        新建会话
      </a-button>
    </div>

    <a-tabs
      v-model:activeKey="terminalStore.activeSession"
      type="editable-card"
      @edit="onEdit"
      class="terminal-tabs"
    >
      <a-tab-pane
        v-for="session in terminalStore.sessions"
        :key="session.id"
        :tab="session.name"
        :closable="terminalStore.sessions.length > 1"
      >
        <div :ref="el => setTerminalRef(session.id, el)" class="terminal-container"></div>
      </a-tab-pane>
    </a-tabs>
    
    <!-- 新建会话对话框 -->
    <a-modal
      v-model:open="modalVisible"
      title="新建终端会话"
      @ok="handleCreateSession"
      @cancel="handleCancelModal"
      okText="创建"
      cancelText="取消"
      :okButtonProps="{ disabled: !newSessionName.trim() }"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item 
          label="会话名称"
          :validate-status="validateStatus"
          :help="validateMessage"
        >
          <a-input
            v-model:value="newSessionName"
            placeholder="例如: 开发环境、生产服务器"
            @pressEnter="handleCreateSession"
            @input="checkDuplicateName"
          />
        </a-form-item>
      </a-form>
      <a-alert
        message="提示"
        description="会话名称不能重复，建议使用有意义的名称方便识别"
        type="info"
        show-icon
        style="margin-top: 16px"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useConfigStore } from '../stores/config'
import { useTerminalStore } from '../stores/terminal'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'

const authStore = useAuthStore()
const configStore = useConfigStore()
const terminalStore = useTerminalStore()

const modalVisible = ref(false)
const newSessionName = ref('')
const validateStatus = ref('')
const validateMessage = ref('')
let sessionCounter = 0

const setTerminalRef = (id, el) => {
  if (el) {
    terminalStore.terminalRefs[id] = el
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

  terminalStore.terminals[sessionId] = { term, fitAddon }
  return { term, fitAddon }
}

const connectWebSocket = (sessionId) => {
  const config = configStore.config
  const cwd = config.default_path || '~'
  const wsUrl = `ws://localhost:8000/api/v1/terminal/ws/${sessionId}?token=${authStore.token}&cwd=${encodeURIComponent(cwd)}`
  const ws = new WebSocket(wsUrl)
  
  // 找到会话名称
  const session = terminalStore.sessions.find(s => s.id === sessionId)
  const sessionName = session ? session.name : '终端'

  ws.onopen = () => {
    message.success(`${sessionName} 连接成功`)
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'output') {
      terminalStore.terminals[sessionId]?.term.write(data.data)
    }
  }

  ws.onerror = () => {
    message.error(`${sessionName} 连接错误`)
  }

  ws.onclose = () => {
    message.info(`${sessionName} 连接已关闭`)
  }

  terminalStore.websockets[sessionId] = ws
  return ws
}

const showNewSessionModal = () => {
  newSessionName.value = `终端 ${sessionCounter + 1}`
  validateStatus.value = ''
  validateMessage.value = ''
  modalVisible.value = true
}

const handleCancelModal = () => {
  modalVisible.value = false
  newSessionName.value = ''
  validateStatus.value = ''
  validateMessage.value = ''
}

const checkDuplicateName = () => {
  const name = newSessionName.value.trim()
  
  if (!name) {
    validateStatus.value = 'error'
    validateMessage.value = '会话名称不能为空'
    return false
  }
  
  const isDuplicate = terminalStore.sessions.some(s => s.name === name)
  if (isDuplicate) {
    validateStatus.value = 'error'
    validateMessage.value = '该名称已存在，请使用其他名称'
    return false
  }
  
  validateStatus.value = 'success'
  validateMessage.value = ''
  return true
}

const handleCreateSession = () => {
  const name = newSessionName.value.trim()
  
  if (!name) {
    message.warning('请输入会话名称')
    return
  }
  
  // 检查名称是否重复
  if (!checkDuplicateName()) {
    return
  }
  
  addSession(name)
  modalVisible.value = false
  newSessionName.value = ''
  validateStatus.value = ''
  validateMessage.value = ''
}

const addSession = async (name) => {
  sessionCounter++
  const sessionId = `session-${Date.now()}-${sessionCounter}`
  const session = {
    id: sessionId,
    name: name || `终端 ${sessionCounter}`
  }

  terminalStore.sessions.push(session)
  terminalStore.activeSession = sessionId

  await nextTick()

  const container = terminalStore.terminalRefs[sessionId]
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
    
    // 显示创建成功消息
    message.success(`终端 "${session.name}" 创建成功`)
  }
}

const removeSession = (sessionId) => {
  // 找到要删除的会话
  const session = terminalStore.sessions.find(s => s.id === sessionId)
  const sessionName = session ? session.name : '未知终端'
  
  const ws = terminalStore.websockets[sessionId]
  if (ws) {
    ws.send(JSON.stringify({ type: 'close' }))
    ws.close()
    delete terminalStore.websockets[sessionId]
  }

  const terminal = terminalStore.terminals[sessionId]
  if (terminal) {
    terminal.term.dispose()
    delete terminalStore.terminals[sessionId]
  }

  terminalStore.sessions = terminalStore.sessions.filter(s => s.id !== sessionId)

  if (terminalStore.sessions.length > 0 && terminalStore.activeSession === sessionId) {
    terminalStore.activeSession = terminalStore.sessions[0].id
  }
  
  // 显示关闭成功消息
  message.info(`终端 "${sessionName}" 已关闭`)
}

const onEdit = (targetKey, action) => {
  if (action === 'remove') {
    removeSession(targetKey)
  }
}

// 监听路由变化，重新渲染终端
watch(() => terminalStore.activeSession, async (newSessionId) => {
  if (newSessionId) {
    await nextTick()
    const terminal = terminalStore.terminals[newSessionId]
    if (terminal) {
      terminal.fitAddon.fit()
    }
  }
})

onMounted(async () => {
  await configStore.loadConfig()
  
  // 如果没有会话，创建默认终端
  if (terminalStore.sessions.length === 0) {
    addSession('默认终端')
  } else {
    // 恢复已有会话的终端显示
    await nextTick()
    for (const session of terminalStore.sessions) {
      const container = terminalStore.terminalRefs[session.id]
      const terminal = terminalStore.terminals[session.id]
      if (container && terminal) {
        terminal.term.open(container)
        terminal.fitAddon.fit()
      }
    }
  }
})

onUnmounted(() => {
  // 不关闭会话，保持连接
})
</script>

<style scoped>
.terminal-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
  flex-shrink: 0;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  height: 36px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.terminal-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  min-height: 0;
}

:deep(.ant-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.ant-tabs-nav) {
  margin-bottom: 16px;
  flex-shrink: 0;
}

:deep(.ant-tabs-tab) {
  border-radius: 8px 8px 0 0;
  transition: all 0.3s ease;
}

:deep(.ant-tabs-tab-active) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

:deep(.ant-tabs-tab:hover) {
  color: #667eea;
}

:deep(.ant-tabs-content-holder) {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

:deep(.ant-tabs-content) {
  height: 100%;
}

:deep(.ant-tabs-tabpane) {
  height: 100%;
}

.terminal-container {
  height: 100%;
  width: 100%;
  background: #1e1e1e;
  padding: 12px;
  border-radius: 8px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

:deep(.xterm) {
  height: 100% !important;
  padding: 0;
}

:deep(.xterm-viewport) {
  overflow-y: auto !important;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 20px;
  }
  
  .terminal-header {
    margin-bottom: 12px;
    padding-bottom: 12px;
  }
  
  .terminal-tabs {
    padding: 12px;
  }
  
  .terminal-container {
    padding: 8px;
  }
}
</style>
