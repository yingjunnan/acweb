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

@media (max-width: 768px) {
  .page-title {
    font-size: 22px;
    margin-bottom: 16px;
  }
  
  :deep(.ant-form-item-label) {
    text-align: left;
  }
  
  :deep(.ant-card-body) {
    padding: 16px;
  }
}
</style>
