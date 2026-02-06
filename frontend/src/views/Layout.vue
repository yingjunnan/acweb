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

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const collapsed = ref(false)
const selectedKeys = ref([route.path])
const windowWidth = ref(window.innerWidth)

const isMobile = computed(() => windowWidth.value < 768)

const handleMenuClick = ({ key }) => {
  router.push(key)
  selectedKeys.value = [key]
}

const handleLogout = () => {
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
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.1);
}

.sider-footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.header {
  background: white;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.trigger {
  font-size: 18px;
  cursor: pointer;
  transition: color 0.3s;
}

.trigger:hover {
  color: #1890ff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  color: rgba(0, 0, 0, 0.65);
}

.content {
  margin: 16px;
  padding: 24px;
  background: white;
  min-height: calc(100vh - 112px);
  overflow: auto;
}

@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .content {
    margin: 8px;
    padding: 16px;
    min-height: calc(100vh - 96px);
  }
}
</style>
