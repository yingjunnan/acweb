<template>
  <div class="terminal-page">
    <div class="terminal-header">
      <h1 class="page-title">终端管理</h1>
      <a-button @click="showNewSessionModal" type="primary">
        <template #icon><PlusOutlined /></template>
        新建会话
      </a-button>
    </div>

    <!-- 空状态：没有终端时显示 -->
    <div v-if="terminalStore.sessions.length === 0" class="empty-state">
      <div class="empty-content">
        <div class="empty-icon">
          <svg viewBox="0 0 64 64" width="120" height="120">
            <rect x="8" y="12" width="48" height="40" rx="2" fill="#667eea" opacity="0.1"/>
            <rect x="8" y="12" width="48" height="8" rx="2" fill="#667eea" opacity="0.2"/>
            <line x1="16" y1="28" x2="40" y2="28" stroke="#667eea" stroke-width="2" stroke-linecap="round"/>
            <line x1="16" y1="36" x2="32" y2="36" stroke="#764ba2" stroke-width="2" stroke-linecap="round"/>
            <circle cx="20" cy="44" r="1.5" fill="#667eea"/>
          </svg>
        </div>
        <h2 class="empty-title">暂无终端会话</h2>
        <p class="empty-description">创建一个新的终端会话开始工作</p>
        <a-button @click="showNewSessionModal" type="primary" size="large" class="empty-button">
          <template #icon><PlusOutlined /></template>
          新建终端会话
        </a-button>
      </div>
    </div>

    <!-- 终端标签页 -->
    <a-tabs
      v-else
      v-model:activeKey="terminalStore.activeSession"
      type="editable-card"
      @edit="onEdit"
      class="terminal-tabs"
    >
      <a-tab-pane
        v-for="session in terminalStore.sessions"
        :key="session.id"
        :tab="session.name"
        :closable="true"
        :force-render="true"
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
import { ref, onMounted, onUnmounted, nextTick, watch, defineOptions } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useConfigStore } from '../stores/config'
import { useTerminalStore } from '../stores/terminal'
import { terminalApi } from '../api'
import { Terminal } from 'xterm'

// 定义组件名称，用于 keep-alive
defineOptions({
  name: 'Terminal'
})
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import { WebglAddon } from 'xterm-addon-webgl'
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
    cursorStyle: 'block',
    fontSize: config.font_size || 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    fontWeight: 'normal',
    fontWeightBold: 'bold',
    lineHeight: 1.2,
    letterSpacing: 0,
    theme: config.theme === 'light' ? {
      background: '#ffffff',
      foreground: '#000000',
      cursor: '#000000',
      cursorAccent: '#ffffff',
      selection: 'rgba(0, 0, 0, 0.3)'
    } : {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#d4d4d4',
      cursorAccent: '#1e1e1e',
      selection: 'rgba(255, 255, 255, 0.3)',
      black: '#000000',
      red: '#cd3131',
      green: '#0dbc79',
      yellow: '#e5e510',
      blue: '#2472c8',
      magenta: '#bc3fbc',
      cyan: '#11a8cd',
      white: '#e5e5e5',
      brightBlack: '#666666',
      brightRed: '#f14c4c',
      brightGreen: '#23d18b',
      brightYellow: '#f5f543',
      brightBlue: '#3b8eea',
      brightMagenta: '#d670d6',
      brightCyan: '#29b8db',
      brightWhite: '#e5e5e5'
    },
    rows: 24,
    cols: 80,
    scrollback: 10000,
    allowProposedApi: true,
    allowTransparency: false,
    convertEol: false,
    disableStdin: false,
    windowsMode: false,
    macOptionIsMeta: true,
    rightClickSelectsWord: true,
    fastScrollModifier: 'shift',
    fastScrollSensitivity: 5,
    scrollSensitivity: 1
  })

  const fitAddon = new FitAddon()
  const webLinksAddon = new WebLinksAddon()
  
  term.loadAddon(fitAddon)
  term.loadAddon(webLinksAddon)
  
  // 尝试加载 WebGL 渲染器以提高性能
  let webglAddon = null
  try {
    webglAddon = new WebglAddon()
    webglAddon.onContextLoss(() => {
      webglAddon.dispose()
    })
    term.loadAddon(webglAddon)
  } catch (e) {
    console.warn('WebGL addon could not be loaded, falling back to canvas renderer', e)
  }

  // 保存所有 addon 引用以便后续清理
  terminalStore.terminals[sessionId] = { 
    term, 
    fitAddon, 
    webLinksAddon,
    webglAddon 
  }
  return { term, fitAddon }
}

const connectWebSocket = (sessionId, sessionName, isReconnect = false) => {
  const terminalConfig = configStore.config
  const cwd = terminalConfig.default_path || '~'
  const wsUrl = `ws://localhost:8000/api/v1/terminal/ws/${sessionId}?token=${authStore.token}&cwd=${encodeURIComponent(cwd)}&reconnect=${isReconnect}&name=${encodeURIComponent(sessionName)}`
  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    if (isReconnect) {
      message.success(`${sessionName} 重连成功`)
    } else {
      message.success(`${sessionName} 连接成功`)
    }
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'reconnect') {
      // 重连成功，恢复缓存的输出
      terminalStore.terminals[sessionId]?.term.write(data.data)
      message.info(data.message)
    } else if (data.type === 'reconnect_failed') {
      // 重连失败，会话已失效
      message.warning(`${sessionName} 会话已失效，已创建新会话`)
    } else if (data.type === 'output') {
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

const addSession = async (name, isReconnect = false) => {
  sessionCounter++
  const sessionId = `session-${Date.now()}-${sessionCounter}`
  const session = {
    id: sessionId,
    name: name || `终端 ${sessionCounter}`
  }

  terminalStore.sessions.push(session)
  terminalStore.activeSession = sessionId
  terminalStore.saveSessions()

  await nextTick()

  const container = terminalStore.terminalRefs[sessionId]
  if (container && !terminalStore.terminals[sessionId]) {
    // 只有当终端不存在时才创建
    const { term, fitAddon } = createTerminal(sessionId)
    term.open(container)
    
    // 延迟调整大小，确保容器已经渲染且可见
    setTimeout(() => {
      try {
        const rect = container.getBoundingClientRect()
        if (rect.width > 0 && rect.height > 0) {
          fitAddon.fit()
        }
      } catch (e) {
        console.warn('Failed to fit terminal:', e)
      }
    }, 100)

    const ws = connectWebSocket(sessionId, session.name, isReconnect)

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

    // ResizeObserver 只在容器可见时调用 fit
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        // 检查容器是否可见且有实际尺寸
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          try {
            fitAddon.fit()
          } catch (e) {
            console.warn('Failed to fit terminal on resize:', e)
          }
        }
      }
    })
    resizeObserver.observe(container)
    
    // 保存 resizeObserver 以便后续清理
    if (!terminalStore.terminals[sessionId].resizeObserver) {
      terminalStore.terminals[sessionId].resizeObserver = resizeObserver
    }
    
    // 显示创建成功消息
    if (!isReconnect) {
      message.success(`终端 "${session.name}" 创建成功`)
    }
  }
}

const removeSession = (sessionId) => {
  // 找到要删除的会话
  const session = terminalStore.sessions.find(s => s.id === sessionId)
  const sessionName = session ? session.name : '未知终端'
  
  // 先关闭 WebSocket
  const ws = terminalStore.websockets[sessionId]
  if (ws) {
    try {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'close' }))
      }
      ws.close()
    } catch (e) {
      console.warn('Failed to close websocket:', e)
    }
    delete terminalStore.websockets[sessionId]
  }

  // 清理终端实例
  const terminal = terminalStore.terminals[sessionId]
  if (terminal) {
    try {
      // 1. 先断开 ResizeObserver
      if (terminal.resizeObserver) {
        terminal.resizeObserver.disconnect()
        delete terminal.resizeObserver
      }
      
      // 2. 手动清理 WebGL addon（这是导致错误的主要原因）
      if (terminal.webglAddon) {
        try {
          terminal.webglAddon.dispose()
        } catch (e) {
          // WebGL addon dispose 可能失败，忽略错误
        }
        delete terminal.webglAddon
      }
      
      // 3. 清理其他 addons
      if (terminal.webLinksAddon) {
        try {
          terminal.webLinksAddon.dispose()
        } catch (e) {
          // 忽略错误
        }
        delete terminal.webLinksAddon
      }
      
      if (terminal.fitAddon) {
        try {
          terminal.fitAddon.dispose()
        } catch (e) {
          // 忽略错误
        }
        delete terminal.fitAddon
      }
      
      // 4. 最后清理终端实例
      if (terminal.term) {
        try {
          terminal.term.dispose()
        } catch (e) {
          // 即使 dispose 失败也继续清理
          console.warn('Terminal dispose had issues, but continuing cleanup')
        }
      }
    } catch (e) {
      console.warn('Failed to dispose terminal:', e)
    }
    delete terminalStore.terminals[sessionId]
  }

  // 删除 terminalRef
  if (terminalStore.terminalRefs[sessionId]) {
    delete terminalStore.terminalRefs[sessionId]
  }

  // 更新会话列表
  terminalStore.sessions = terminalStore.sessions.filter(s => s.id !== sessionId)

  // 如果删除的是当前活动会话，切换到第一个会话
  if (terminalStore.sessions.length > 0 && terminalStore.activeSession === sessionId) {
    terminalStore.activeSession = terminalStore.sessions[0].id
  }
  
  // 保存会话状态
  terminalStore.saveSessions()
  
  // 显示关闭成功消息
  message.info(`终端 "${sessionName}" 已关闭`)
}

const onEdit = (targetKey, action) => {
  if (action === 'remove') {
    removeSession(targetKey)
  }
}

// 监听活动会话变化，调整终端尺寸
watch(() => terminalStore.activeSession, async (newSessionId) => {
  if (newSessionId && terminalStore.terminals[newSessionId]) {
    await nextTick()
    // 延迟调整尺寸，确保标签页切换动画完成且容器可见
    setTimeout(() => {
      try {
        const terminal = terminalStore.terminals[newSessionId]
        const container = terminalStore.terminalRefs[newSessionId]
        
        // 只有当容器可见且有实际尺寸时才调整
        if (terminal && terminal.fitAddon && container) {
          const rect = container.getBoundingClientRect()
          if (rect.width > 0 && rect.height > 0) {
            terminal.fitAddon.fit()
          }
        }
      } catch (e) {
        console.warn('Failed to fit terminal on tab switch:', e)
      }
    }, 200)
  }
})

onMounted(async () => {
  await configStore.loadConfig()
  
  // 检查是否有已存在的终端实例（keep-alive 缓存）
  const hasExistingTerminals = Object.keys(terminalStore.terminals).length > 0
  
  if (hasExistingTerminals) {
    // 有已存在的终端实例，无需重新创建
    console.log('Terminal component activated from cache')
    return
  }
  
  // 从后端获取活跃会话列表（唯一的真实来源）
  try {
    message.info('正在加载会话...')
    const response = await terminalApi.getSessions()
    const activeSessions = response.data.sessions || []
    
    if (activeSessions.length > 0) {
      // 有活跃会话，恢复它们
      console.log(`Found ${activeSessions.length} active sessions from server`)
      
      // 更新 store 中的会话列表
      terminalStore.sessions = activeSessions.map(s => ({
        id: s.id,
        name: s.name
      }))
      
      // 设置活动会话
      if (!terminalStore.activeSession || !activeSessions.find(s => s.id === terminalStore.activeSession)) {
        terminalStore.activeSession = activeSessions[0].id
      }
      
      // 保存到 localStorage（仅作为缓存，不作为真实来源）
      terminalStore.saveSessions()
      
      await nextTick()
      
      // 为每个会话创建终端实例并重连
      let successCount = 0
      for (const session of activeSessions) {
        const container = terminalStore.terminalRefs[session.id]
        if (container && !terminalStore.terminals[session.id]) {
          try {
            // 创建终端实例（使用数据库中保存的尺寸）
            const { term, fitAddon } = createTerminal(session.id)
            term.open(container)
            
            // 使用数据库中保存的尺寸
            const savedRows = session.rows || 24
            const savedCols = session.cols || 80
            term.resize(savedCols, savedRows)
            
            setTimeout(() => {
              try {
                const rect = container.getBoundingClientRect()
                if (rect.width > 0 && rect.height > 0) {
                  // 调整到容器大小
                  fitAddon.fit()
                }
              } catch (e) {
                console.warn('Failed to fit terminal on mount:', e)
              }
            }, 100)

            // 重连到已存在的会话
            const ws = connectWebSocket(session.id, session.name, true)

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

            // ResizeObserver 只在容器可见时调用 fit
            const resizeObserver = new ResizeObserver((entries) => {
              for (const entry of entries) {
                if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
                  try {
                    fitAddon.fit()
                  } catch (e) {
                    console.warn('Failed to fit terminal on resize:', e)
                  }
                }
              }
            })
            resizeObserver.observe(container)
            
            // 保存 resizeObserver
            if (!terminalStore.terminals[session.id].resizeObserver) {
              terminalStore.terminals[session.id].resizeObserver = resizeObserver
            }
            
            successCount++
          } catch (error) {
            console.error(`Failed to restore session ${session.id}:`, error)
          }
        }
      }
      
      if (successCount > 0) {
        message.success(`成功恢复 ${successCount} 个会话`)
      } else {
        message.warning('会话恢复失败，已创建新会话')
        terminalStore.clearSessions()
        addSession('默认终端')
      }
    } else {
      // 后端没有会话，创建默认终端
      console.log('No active sessions found, creating default terminal')
      terminalStore.clearSessions()
      addSession('默认终端')
    }
  } catch (error) {
    console.error('Failed to load sessions from server:', error)
    message.error('加载会话失败，已创建新会话')
    
    // 从服务器加载失败，创建默认终端
    terminalStore.clearSessions()
    addSession('默认终端')
  }
})

onUnmounted(() => {
  // 不关闭 WebSocket 连接，保持会话活跃
  // 当用户切换菜单时，终端会话继续在后台运行
  // 只清理 DOM 相关的资源，不清理网络连接
  console.log('Terminal component unmounted, keeping sessions alive')
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

/* 空状态样式 */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 40px;
}

.empty-content {
  text-align: center;
  max-width: 400px;
}

.empty-icon {
  margin-bottom: 24px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.empty-description {
  font-size: 16px;
  color: #666;
  margin: 0 0 32px 0;
  line-height: 1.6;
}

.empty-button {
  height: 48px;
  font-size: 16px;
  padding: 0 32px;
  border-radius: 24px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.empty-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
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
  
  .empty-state {
    padding: 20px;
  }
  
  .empty-title {
    font-size: 20px;
  }
  
  .empty-description {
    font-size: 14px;
  }
  
  .empty-button {
    height: 40px;
    font-size: 14px;
    padding: 0 24px;
  }
}
</style>
