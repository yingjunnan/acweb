<template>
  <div class="terminal-page" :class="{ fullscreen: isFullscreen }">
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
        <!-- 终端信息栏 -->
        <div class="terminal-info-bar" v-if="getSessionInfo(session.id)">
          <div class="info-left">
            <a-tag color="blue">
              <template #icon><ClockCircleOutlined /></template>
              {{ formatDate(getSessionInfo(session.id).created_at) }}
            </a-tag>
            <a-tag color="purple">
              <template #icon><DatabaseOutlined /></template>
              {{ formatBufferSize(getSessionInfo(session.id).buffer_size) }}
            </a-tag>
            <a-tag 
              v-if="getSessionInfo(session.id).connected_clients !== undefined"
              :color="getSessionInfo(session.id).connected_clients > 1 ? 'orange' : 'cyan'"
            >
              <template #icon><TeamOutlined /></template>
              {{ getSessionInfo(session.id).connected_clients }} 个客户端
            </a-tag>
            <a-tag 
              v-if="getSessionInfo(session.id).running_in_background"
              color="gold"
            >
              <template #icon><ThunderboltOutlined /></template>
              后台运行中
            </a-tag>
          </div>
          <div class="info-right">
            <a-button 
              size="small" 
              @click="toggleFullscreen"
              :type="isFullscreen ? 'default' : 'default'"
              :class="{ 'fullscreen-active': isFullscreen }"
            >
              <template #icon>
                <FullscreenExitOutlined v-if="isFullscreen" />
                <FullscreenOutlined v-else />
              </template>
              {{ isFullscreen ? '退出全屏' : '全屏' }}
            </a-button>
            <a-button 
              size="small" 
              @click="showSessionDetails(session.id)"
            >
              <template #icon><InfoCircleOutlined /></template>
              详情
            </a-button>
          </div>
        </div>
        
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
    
    <!-- 会话详情对话框 -->
    <a-modal
      v-model:open="detailsModalVisible"
      title="会话详情"
      :footer="null"
      width="600px"
    >
      <div v-if="selectedSessionDetails" class="session-details">
        <a-descriptions bordered :column="1">
          <a-descriptions-item label="会话名称">
            {{ selectedSessionDetails.name }}
          </a-descriptions-item>
          <a-descriptions-item label="会话 ID">
            <a-typography-text copyable>{{ selectedSessionDetails.id }}</a-typography-text>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ formatDateTime(selectedSessionDetails.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="最后活动">
            {{ formatDateTime(selectedSessionDetails.last_activity) }}
          </a-descriptions-item>
          <a-descriptions-item label="缓存大小">
            {{ formatBufferSize(selectedSessionDetails.buffer_size) }}
          </a-descriptions-item>
          <a-descriptions-item label="工作目录">
            {{ selectedSessionDetails.cwd || '~' }}
          </a-descriptions-item>
          <a-descriptions-item label="进程 ID">
            {{ selectedSessionDetails.pid || 'N/A' }}
          </a-descriptions-item>
          <a-descriptions-item label="运行状态">
            <a-badge :status="selectedSessionDetails.running ? 'processing' : 'default'" 
                     :text="selectedSessionDetails.running ? '运行中' : '已停止'" />
          </a-descriptions-item>
          <a-descriptions-item label="连接客户端">
            <a-tag :color="selectedSessionDetails.connected_clients > 1 ? 'orange' : 'cyan'">
              {{ selectedSessionDetails.connected_clients || 0 }} 个
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="后台运行">
            <a-tag :color="selectedSessionDetails.running_in_background ? 'gold' : 'default'">
              {{ selectedSessionDetails.running_in_background ? '是' : '否' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, defineOptions } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { 
  PlusOutlined, 
  ClockCircleOutlined, 
  DatabaseOutlined,
  InfoCircleOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined
} from '@ant-design/icons-vue'
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
import { Unicode11Addon } from '@xterm/addon-unicode11'
import 'xterm/css/xterm.css'

const authStore = useAuthStore()
const configStore = useConfigStore()
const terminalStore = useTerminalStore()

const modalVisible = ref(false)
const newSessionName = ref('')
const validateStatus = ref('')
const validateMessage = ref('')
const detailsModalVisible = ref(false)
const selectedSessionDetails = ref(null)
const sessionInfoMap = ref({}) // 存储会话详细信息
const isFullscreen = ref(false) // 全屏状态
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
    lineHeight: 1.0,
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
    scrollSensitivity: 1,
    windowOptions: {
      setWinLines: true,
      setWinSizePixels: false,
      getWinSizePixels: false,
      getCellSizePixels: false,
      getIconTitle: false,
      getWinTitle: false,
      pushTitle: false,
      popTitle: false,
      setWinPosition: false,
      getWinPosition: false,
      getWinState: false,
      raiseWin: false,
      lowerWin: false,
      refreshWin: false,
      restoreWin: false,
      maximizeWin: false,
      minimizeWin: false,
      fullscreenWin: false
    },
    altClickMovesCursor: true,
    cursorInactiveStyle: 'outline',
    smoothScrollDuration: 0,
    cursorWidth: 1,
    screenReaderMode: false,
    tabStopWidth: 8,
    // 关键修复：启用 Unicode 11 支持以正确渲染 box-drawing 字符
    allowProposedApi: true,
    // 日志级别设置为 off 以避免控制台警告
    logLevel: 'off'
  })

  const fitAddon = new FitAddon()
  const webLinksAddon = new WebLinksAddon()
  const unicode11Addon = new Unicode11Addon()
  
  term.loadAddon(fitAddon)
  term.loadAddon(webLinksAddon)
  term.loadAddon(unicode11Addon)
  
  // 激活 Unicode 11 支持以正确渲染 box-drawing 和其他 Unicode 字符
  term.unicode.activeVersion = '11'
  
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
    unicode11Addon,
    webglAddon 
  }
  return { term, fitAddon }
}

const connectWebSocket = (sessionId, sessionName, isReconnect = false) => {
  const terminalConfig = configStore.config
  const cwd = terminalConfig.default_path || '~'
  const wsUrl = `ws://localhost:8000/api/v1/terminal/ws/${sessionId}?token=${authStore.token}&cwd=${encodeURIComponent(cwd)}&reconnect=${isReconnect}&name=${encodeURIComponent(sessionName)}`
  const ws = new WebSocket(wsUrl)
  
  let reconnectAttempts = 0
  const maxReconnectAttempts = 5
  const reconnectDelay = 2000
  let heartbeatInterval = null

  ws.onopen = () => {
    reconnectAttempts = 0
    if (isReconnect) {
      message.success(`${sessionName} 重连成功`)
    } else {
      message.success(`${sessionName} 连接成功`)
    }
    
    // 启动心跳
    heartbeatInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify({ type: 'ping' }))
        } catch (error) {
          console.error('Failed to send heartbeat:', error)
        }
      }
    }, 30000) // 每30秒发送一次心跳
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.type === 'reconnect') {
        // 重连成功，恢复缓存的输出
        if (terminalStore.terminals[sessionId]?.term) {
          terminalStore.terminals[sessionId].term.write(data.data)
        }
        if (data.message) {
          message.info(data.message)
        }
      } else if (data.type === 'reconnect_failed') {
        // 重连失败，会话已失效
        message.warning(`${sessionName} 会话已失效，已创建新会话`)
      } else if (data.type === 'output') {
        // 正常输出
        if (terminalStore.terminals[sessionId]?.term) {
          terminalStore.terminals[sessionId].term.write(data.data)
        }
      } else if (data.type === 'error') {
        // 错误消息
        message.error(data.message || '终端错误')
      } else if (data.type === 'pong') {
        // 心跳响应，忽略
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  ws.onerror = (error) => {
    console.error(`${sessionName} WebSocket 错误:`, error)
  }

  ws.onclose = (event) => {
    console.log(`${sessionName} WebSocket 连接已关闭`, event.code, event.reason)
    
    // 清除心跳
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
    
    // 如果不是正常关闭，尝试重连
    if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++
      console.log(`尝试重连 ${sessionName} (${reconnectAttempts}/${maxReconnectAttempts})`)
      
      setTimeout(() => {
        // 检查会话是否还存在
        if (terminalStore.sessions.find(s => s.id === sessionId)) {
          const newWs = connectWebSocket(sessionId, sessionName, true)
          terminalStore.websockets[sessionId] = newWs
          
          // 重新绑定事件
          const terminal = terminalStore.terminals[sessionId]
          if (terminal && terminal.term) {
            terminal.term.onData(data => {
              if (newWs.readyState === WebSocket.OPEN) {
                newWs.send(JSON.stringify({ type: 'input', data }))
              }
            })
            
            terminal.term.onResize(({ cols, rows }) => {
              if (newWs.readyState === WebSocket.OPEN) {
                newWs.send(JSON.stringify({ type: 'resize', cols, rows }))
              }
            })
          }
        }
      }, reconnectDelay)
    } else if (reconnectAttempts >= maxReconnectAttempts) {
      message.error(`${sessionName} 重连失败，请刷新页面`)
    }
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
      if (terminal.unicode11Addon) {
        try {
          terminal.unicode11Addon.dispose()
        } catch (e) {
          // 忽略错误
        }
        delete terminal.unicode11Addon
      }
      
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
    // 找到要删除的会话名称
    const session = terminalStore.sessions.find(s => s.id === targetKey)
    const sessionName = session ? session.name : '未知终端'
    
    // 弹出确认对话框
    Modal.confirm({
      title: '确认关闭终端',
      content: `确定要关闭终端 "${sessionName}" 吗？关闭后会话将被终止，所有未保存的数据将丢失。`,
      okText: '确认关闭',
      okType: 'danger',
      cancelText: '取消',
      onOk() {
        removeSession(targetKey)
      }
    })
  }
}

// 获取会话信息
const getSessionInfo = (sessionId) => {
  return sessionInfoMap.value[sessionId]
}

// 定期更新会话状态
const updateSessionStatus = async (sessionId) => {
  try {
    const response = await terminalApi.getSessionStatus(sessionId)
    if (response.data) {
      const info = sessionInfoMap.value[sessionId]
      if (info) {
        info.connected_clients = response.data.connected_clients || 0
        info.running_in_background = response.data.running_in_background || false
        info.alive = response.data.alive || false
      }
    }
  } catch (error) {
    console.error('Failed to update session status:', error)
  }
}

// 格式化日期
const formatDate = (timestamp) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  
  return date.toLocaleDateString('zh-CN')
}

// 格式化完整日期时间
const formatDateTime = (timestamp) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化缓存大小
const formatBufferSize = (size) => {
  if (!size) return '0 KB'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

// 全屏切换
const showSessionDetails = (sessionId) => {
  const info = sessionInfoMap.value[sessionId]
  if (info) {
    selectedSessionDetails.value = { ...info }
    detailsModalVisible.value = true
  }
}

// 全屏切换
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  
  // 延迟调整终端尺寸以适应新的容器大小
  nextTick(() => {
    setTimeout(() => {
      const activeSessionId = terminalStore.activeSession
      if (activeSessionId && terminalStore.terminals[activeSessionId]) {
        try {
          const terminal = terminalStore.terminals[activeSessionId]
          const container = terminalStore.terminalRefs[activeSessionId]
          
          if (terminal && terminal.fitAddon && container) {
            const rect = container.getBoundingClientRect()
            if (rect.width > 0 && rect.height > 0) {
              terminal.fitAddon.fit()
            }
          }
        } catch (e) {
          console.warn('Failed to fit terminal after fullscreen toggle:', e)
        }
      }
    }, 100)
  })
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

// ESC 键处理函数
const handleEscape = (event) => {
  if (event.key === 'Escape' && isFullscreen.value) {
    toggleFullscreen()
  }
}

onMounted(async () => {
  await configStore.loadConfig()
  
  // 添加 ESC 键监听，退出全屏
  window.addEventListener('keydown', handleEscape)
  
  // 检查是否有已存在的终端实例（keep-alive 缓存）
  const hasExistingTerminals = Object.keys(terminalStore.terminals).length > 0
  
  if (hasExistingTerminals) {
    // 有已存在的终端实例，无需重新创建
    console.log('Terminal component activated from cache')
    
    // 但需要更新会话状态
    for (const session of terminalStore.sessions) {
      updateSessionStatus(session.id)
    }
    
    // 启动定期状态更新
    startStatusUpdater()
    return
  }
  
  // 从后端获取活跃会话列表（唯一的真实来源）
  try {
    const response = await terminalApi.getSessions()
    const activeSessions = response.data.sessions || []
    
    if (activeSessions.length > 0) {
      // 有活跃会话，显示加载提示并恢复它们
      message.info('正在加载会话...')
      console.log(`Found ${activeSessions.length} active sessions from server`)
      
      // 更新 store 中的会话列表
      terminalStore.sessions = activeSessions.map(s => ({
        id: s.id,
        name: s.name
      }))
      
      // 保存会话详细信息
      activeSessions.forEach(s => {
        sessionInfoMap.value[s.id] = {
          id: s.id,
          name: s.name,
          rows: s.rows || 24,
          cols: s.cols || 80,
          created_at: s.created_at,
          last_activity: s.last_activity,
          running: s.running,
          cwd: s.cwd,
          pid: s.pid,
          buffer_size: 0,
          connected_clients: 0,
          running_in_background: false
        }
      })
      
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
            
            // 更新会话状态
            updateSessionStatus(session.id)
            
            successCount++
          } catch (error) {
            console.error(`Failed to restore session ${session.id}:`, error)
          }
        }
      }
      
      if (successCount > 0) {
        message.success(`成功恢复 ${successCount} 个会话`)
      } else {
        message.warning('会话恢复失败，请手动创建新会话')
        terminalStore.clearSessions()
      }
    } else {
      // 后端没有会话，显示空状态
      console.log('No active sessions found')
      terminalStore.clearSessions()
    }
    
    // 启动定期状态更新
    startStatusUpdater()
  } catch (error) {
    console.error('Failed to load sessions from server:', error)
    message.error('加载会话失败，请手动创建新会话')
    
    // 从服务器加载失败，清空会话列表
    terminalStore.clearSessions()
  }
})

// 定期更新会话状态
let statusUpdateInterval = null
const startStatusUpdater = () => {
  // 清除旧的定时器
  if (statusUpdateInterval) {
    clearInterval(statusUpdateInterval)
  }
  
  // 每5秒更新一次所有会话的状态
  statusUpdateInterval = setInterval(() => {
    for (const session of terminalStore.sessions) {
      updateSessionStatus(session.id)
    }
  }, 5000)
}

onUnmounted(() => {
  // 不关闭 WebSocket 连接，保持会话活跃
  // 当用户切换菜单时，终端会话继续在后台运行
  // 只清理 DOM 相关的资源，不清理网络连接
  console.log('Terminal component unmounted, keeping sessions alive')
  
  // 清除状态更新定时器
  if (statusUpdateInterval) {
    clearInterval(statusUpdateInterval)
    statusUpdateInterval = null
  }
  
  // 移除 ESC 键监听
  window.removeEventListener('keydown', handleEscape)
  
  // 退出全屏
  if (isFullscreen.value) {
    isFullscreen.value = false
  }
})
</script>

<style scoped>
.terminal-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 全屏模式 */
.terminal-page.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: #fff;
  padding: 0;
  margin: 0;
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

/* 全屏模式下隐藏标题 */
.fullscreen .terminal-header {
  display: none;
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

/* 全屏模式下的终端标签页 */
.fullscreen .terminal-tabs {
  border-radius: 0;
  padding: 8px;
  height: 100vh;
}

/* 全屏模式下的终端容器 */
.fullscreen .terminal-container {
  border-radius: 0;
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
  display: flex;
  flex-direction: column;
}

.terminal-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.info-left {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.info-right {
  display: flex;
  gap: 8px;
}

:deep(.terminal-info-bar .ant-tag) {
  margin: 0;
  border-radius: 6px;
  font-size: 12px;
}

:deep(.terminal-info-bar .ant-btn) {
  border-radius: 6px;
  font-size: 12px;
}

.fullscreen-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  border-color: transparent !important;
}

.fullscreen-active:hover {
  background: linear-gradient(135deg, #5568d3 0%, #653a8b 100%) !important;
  color: white !important;
}

.session-details {
  padding: 8px 0;
}

:deep(.session-details .ant-descriptions-item-label) {
  font-weight: 500;
  background: #fafafa;
}

.terminal-container {
  flex: 1;
  width: 100%;
  background: #1e1e1e;
  padding: 12px;
  border-radius: 0 0 8px 8px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  min-height: 0;
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
</style>
