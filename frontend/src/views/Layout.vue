<template>
  <a-layout class="main-layout">
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      :breakpoint="isMobile ? 'lg' : null"
      :collapsed-width="isMobile ? 0 : 80"
      class="sider"
    >
      <div class="logo">
        <template v-if="!collapsed">Web Terminal</template>
        <template v-else>WT</template>
      </div>
      
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="/dashboard">
          <template #icon><DashboardOutlined /></template>
          <span>仪表盘</span>
        </a-menu-item>
        
        <a-menu-item key="/terminal">
          <template #icon><CodeOutlined /></template>
          <span>终端</span>
        </a-menu-item>
        
        <a-menu-item key="/settings">
          <template #icon><SettingOutlined /></template>
          <span>配置</span>
        </a-menu-item>
      </a-menu>
      
      <div class="sider-footer">
        <a-button
          type="text"
          danger
          block
          @click="handleLogout"
        >
          <template #icon><LogoutOutlined /></template>
          <span v-if="!collapsed">退出登录</span>
        </a-button>
      </div>
    </a-layout-sider>
    
    <a-layout>
      <a-layout-header class="header">
        <MenuUnfoldOutlined
          v-if="collapsed"
          class="trigger"
          @click="collapsed = !collapsed"
        />
        <MenuFoldOutlined
          v-else
          class="trigger"
          @click="collapsed = !collapsed"
        />
        
        <div class="header-right">
          <span class="username">{{ authStore.token ? 'admin' : '' }}</span>
        </div>
      </a-layout-header>
      
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  DashboardOutlined,
  CodeOutlined,
  SettingOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useTerminalStore } from '../stores/terminal'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const terminalStore = useTerminalStore()

const collapsed = ref(false)
const selectedKeys = ref([route.path])
const windowWidth = ref(window.innerWidth)

const isMobile = computed(() => windowWidth.value < 768)

const handleMenuClick = ({ key }) => {
  router.push(key)
  selectedKeys.value = [key]
}

const handleLogout = () => {
  // 关闭所有终端会话
  Object.keys(terminalStore.websockets).forEach(sessionId => {
    const ws = terminalStore.websockets[sessionId]
    if (ws) {
      ws.send(JSON.stringify({ type: 'close' }))
      ws.close()
    }
    const terminal = terminalStore.terminals[sessionId]
    if (terminal) {
      terminal.term.dispose()
    }
  })
  
  // 清空终端状态
  terminalStore.sessions = []
  terminalStore.activeSession = ''
  terminalStore.terminalRefs = {}
  terminalStore.terminals = {}
  terminalStore.websockets = {}
  
  authStore.logout()
  router.push('/login')
}

const handleResize = () => {
  windowWidth.value = window.innerWidth
  if (windowWidth.value < 768) {
    collapsed.value = true
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
  selectedKeys.value = [route.path]
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
}

.sider {
  position: relative;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

:deep(.ant-menu-dark) {
  background: #001529;
}

:deep(.ant-menu-item) {
  margin: 8px 8px;
  width: calc(100% - 16px);
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.ant-menu-item-selected) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

:deep(.ant-menu-item:hover) {
  background: rgba(102, 126, 234, 0.2) !important;
}

:deep(.ant-menu-item-icon) {
  font-size: 18px;
}

.sider-footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
}

:deep(.sider-footer .ant-btn) {
  color: rgba(255, 255, 255, 0.85);
  transition: all 0.3s ease;
}

:deep(.sider-footer .ant-btn:hover) {
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

.header {
  background: white;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  z-index: 10;
}

.trigger {
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 8px;
  border-radius: 8px;
}

.trigger:hover {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  color: #262626;
  font-weight: 500;
  padding: 6px 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-radius: 20px;
  font-size: 14px;
}

.content {
  margin: 20px;
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 128px);
  height: calc(100vh - 128px);
  overflow: auto;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .content {
    margin: 12px;
    padding: 16px;
    min-height: calc(100vh - 112px);
    height: calc(100vh - 112px);
  }
  
  .username {
    padding: 4px 12px;
    font-size: 13px;
  }
}
</style>
