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
          label="刷新间隔"
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
        
        <a-divider>会话管理</a-divider>
        
        <a-form-item
          label="会话超时"
          name="session_timeout"
          help="终端会话在无活动后保持的时间，超时后会话会被自动清理"
        >
          <a-slider
            v-model:value="formState.session_timeout"
            :min="300"
            :max="7200"
            :step="300"
            :marks="{ 
              300: '5分钟', 
              1800: '30分钟', 
              3600: '1小时', 
              7200: '2小时' 
            }"
          />
          <div style="margin-top: 8px; color: rgba(0, 0, 0, 0.45); font-size: 12px;">
            当前设置: {{ formatTimeout(formState.session_timeout) }}
          </div>
        </a-form-item>
        
        <a-form-item
          label="缓存行数"
          name="buffer_size"
        >
          <template #help>
            <div>终端输出缓存的最大行数，用于重连时恢复输出</div>
            <div style="color: #faad14; margin-top: 4px;">
              💡 内存占用估算: {{ calculateMemoryUsage(formState.buffer_size) }}
            </div>
          </template>
          <a-slider
            v-model:value="formState.buffer_size"
            :min="100"
            :max="5000"
            :step="100"
            :marks="{ 
              100: '100', 
              1000: '1000', 
              2500: '2500', 
              5000: '5000' 
            }"
          />
          <div style="margin-top: 8px; color: rgba(0, 0, 0, 0.45); font-size: 12px;">
            当前设置: {{ formState.buffer_size }} 行
          </div>
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
          <li><strong>会话超时：</strong>设置终端会话在无活动后保持的时间，范围 5分钟-2小时。超时后会话会被自动清理。建议根据实际使用场景设置</li>
          <li><strong>缓存行数：</strong>设置终端输出缓存的最大行数，范围 100-5000 行。重连时会恢复缓存的输出。每个会话独立占用内存，建议根据服务器资源合理设置</li>
        </ul>
      </a-typography-paragraph>
      
      <a-alert
        message="提示"
        description="系统设置立即生效。终端设置需要创建新的终端会话才能生效，已有的终端会话将继续使用旧配置。会话超时和缓存行数的更改会在下次创建会话时生效。"
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
  refresh_interval: 3,
  session_timeout: 3600,
  buffer_size: 1000
})

const formatTimeout = (seconds) => {
  if (seconds < 60) {
    return `${seconds} 秒`
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)} 分钟`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return minutes > 0 ? `${hours} 小时 ${minutes} 分钟` : `${hours} 小时`
  }
}

const calculateMemoryUsage = (lines) => {
  // 估算每行平均80个字符，每个字符约2字节（UTF-8）
  // 加上额外的数据结构开销，每行约200字节
  const bytesPerLine = 200
  const totalBytes = lines * bytesPerLine
  
  if (totalBytes < 1024) {
    return `约 ${totalBytes} B`
  } else if (totalBytes < 1024 * 1024) {
    return `约 ${(totalBytes / 1024).toFixed(1)} KB`
  } else {
    return `约 ${(totalBytes / 1024 / 1024).toFixed(2)} MB`
  }
}

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
  max-width: 900px;
}

.page-title {
  margin-bottom: 24px;
  font-size: 28px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

:deep(.ant-card) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

:deep(.ant-card:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.ant-card-head) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom: none;
  border-radius: 12px 12px 0 0;
}

:deep(.ant-card-head-title) {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

:deep(.ant-card-body) {
  padding: 24px;
}

:deep(.ant-form-item-label > label) {
  font-weight: 500;
  color: #262626;
}

:deep(.ant-slider) {
  margin: 8px 0 16px;
}

:deep(.ant-slider-mark-text) {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

:deep(.ant-slider-track) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

:deep(.ant-slider-handle) {
  border-color: #667eea;
}

:deep(.ant-slider-handle:hover),
:deep(.ant-slider-handle:focus) {
  border-color: #764ba2;
  box-shadow: 0 0 0 5px rgba(102, 126, 234, 0.12);
}

:deep(.ant-input),
:deep(.ant-select-selector) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.ant-input:hover),
:deep(.ant-select-selector:hover) {
  border-color: #667eea;
}

:deep(.ant-input:focus),
:deep(.ant-select-focused .ant-select-selector) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  height: 40px;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

:deep(.ant-btn-default) {
  border-radius: 8px;
  height: 40px;
  padding: 0 24px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.ant-btn-default:hover) {
  border-color: #667eea;
  color: #667eea;
}

:deep(.ant-radio-button-wrapper-checked) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
}

:deep(.ant-typography-title) {
  color: #262626;
  font-weight: 600;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
}

:deep(.ant-alert) {
  border-radius: 8px;
  border: none;
  background: #e6f7ff;
}

code {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  color: #667eea;
  font-weight: 500;
}

ul {
  padding-left: 20px;
}

li {
  margin-bottom: 8px;
  line-height: 1.8;
}
</style>
