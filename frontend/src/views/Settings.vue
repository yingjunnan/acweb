<template>
  <div class="settings">
    <h1 class="page-title">系统配置</h1>
    
    <!-- 系统设置 -->
    <a-card title="系统设置" :bordered="false" style="margin-bottom: 16px">
      <a-form
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item
          label="Dashboard刷新间隔"
          name="refresh_interval"
          help="仪表盘数据自动刷新的时间间隔（秒）"
        >
          <a-slider
            v-model:value="formState.refresh_interval"
            :min="1"
            :max="30"
            :marks="{ 1: '1s', 3: '3s', 5: '5s', 10: '10s', 30: '30s' }"
          />
        </a-form-item>
      </a-form>
    </a-card>
    
    <!-- 终端设置 -->
    <a-card title="终端设置" :bordered="false">
      <a-form
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item
          label="默认路径"
          name="default_path"
          help="终端启动时的默认工作目录，支持 ~ 表示用户主目录"
        >
          <a-input
            v-model:value="formState.default_path"
            placeholder="例如: ~ 或 /home/user/projects"
          />
        </a-form-item>
        
        <a-form-item
          label="Shell"
          name="shell"
          help="使用的 Shell 程序路径"
        >
          <a-select v-model:value="formState.shell">
            <a-select-option value="/bin/bash">Bash</a-select-option>
            <a-select-option value="/bin/zsh">Zsh</a-select-option>
            <a-select-option value="/bin/sh">Sh</a-select-option>
            <a-select-option value="/bin/fish">Fish</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item
          label="字体大小"
          name="font_size"
        >
          <a-slider
            v-model:value="formState.font_size"
            :min="10"
            :max="24"
            :marks="{ 10: '10', 14: '14', 18: '18', 24: '24' }"
          />
        </a-form-item>
        
        <a-form-item
          label="主题"
          name="theme"
        >
          <a-radio-group v-model:value="formState.theme">
            <a-radio value="dark">深色</a-radio>
            <a-radio value="light">浅色</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-card>
    
    <!-- 保存按钮 -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-space>
        <a-button type="primary" @click="handleSave" :loading="saving">
          保存所有配置
        </a-button>
        <a-button @click="handleReset">
          重置
        </a-button>
      </a-space>
    </a-card>
    
    <a-card title="使用说明" :bordered="false" style="margin-top: 16px">
      <a-typography-paragraph>
        <a-typography-title :level="5">系统设置</a-typography-title>
        <ul>
          <li><strong>刷新间隔：</strong>设置仪表盘数据自动刷新的时间间隔，范围 1-30 秒。较短的间隔可以更实时地监控系统状态，但会增加服务器负载</li>
        </ul>
        
        <a-typography-title :level="5">终端设置</a-typography-title>
        <ul>
          <li><strong>默认路径：</strong>设置终端启动时的工作目录。使用 <code>~</code> 表示用户主目录，例如 <code>~/projects</code></li>
          <li><strong>Shell：</strong>选择要使用的 Shell 程序。确保所选 Shell 已安装在服务器上</li>
          <li><strong>字体大小：</strong>调整终端显示的字体大小，范围 10-24</li>
          <li><strong>主题：</strong>选择终端的颜色主题</li>
        </ul>
      </a-typography-paragraph>
      
      <a-alert
        message="提示"
        description="系统设置立即生效。终端设置需要创建新的终端会话才能生效，已有的终端会话将继续使用旧配置。"
        type="info"
        show-icon
      />
    </a-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useConfigStore } from '../stores/config'

const configStore = useConfigStore()
const saving = ref(false)

const formState = reactive({
  default_path: '~',
  shell: '/bin/bash',
  font_size: 14,
  theme: 'dark',
  refresh_interval: 3
})

const loadConfig = async () => {
  await configStore.loadConfig()
  Object.assign(formState, configStore.config)
}

const handleSave = async () => {
  saving.value = true
  try {
    const success = await configStore.saveConfig(formState)
    if (success) {
      message.success('配置保存成功')
    } else {
      message.error('配置保存失败')
    }
  } finally {
    saving.value = false
  }
}

const handleReset = () => {
  Object.assign(formState, configStore.config)
  message.info('已重置为当前保存的配置')
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.settings {
  max-width: 800px;
}

.page-title {
  margin-bottom: 24px;
  font-size: 24px;
  font-weight: 600;
}

code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 20px;
    margin-bottom: 16px;
  }
  
  :deep(.ant-form-item-label) {
    text-align: left;
  }
}
</style>
