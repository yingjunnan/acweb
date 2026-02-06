<template>
  <div class="login-container">
    <a-card class="login-card" title="Web Terminal 登录">
      <a-form
        :model="formState"
        @finish="handleLogin"
        layout="vertical"
      >
        <a-form-item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input
            v-model:value="formState.username"
            placeholder="admin"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password
            v-model:value="formState.password"
            placeholder="admin123"
            size="large"
          />
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            size="large"
            block
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formState = reactive({
  username: '',
  password: ''
})

const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    await authStore.login(formState.username, formState.password)
    message.success('登录成功')
    router.push('/')
  } catch (error) {
    message.error('登录失败：' + (error.response?.data?.detail || '网络错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.login-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: moveBackground 20s linear infinite;
}

@keyframes moveBackground {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(50px, 50px);
  }
}

.login-card {
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.ant-card-head) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom: none;
  padding: 24px;
}

:deep(.ant-card-head-title) {
  color: white;
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  letter-spacing: 0.5px;
}

:deep(.ant-card-body) {
  padding: 32px 24px;
  background: white;
}

:deep(.ant-form-item-label > label) {
  font-weight: 500;
  color: #262626;
  font-size: 14px;
}

:deep(.ant-input),
:deep(.ant-input-password) {
  border-radius: 8px;
  height: 44px;
  font-size: 15px;
  transition: all 0.3s ease;
}

:deep(.ant-input:hover),
:deep(.ant-input-password:hover .ant-input) {
  border-color: #667eea;
}

:deep(.ant-input:focus),
:deep(.ant-input-password .ant-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
}

:deep(.ant-btn-primary:active) {
  transform: translateY(0);
}

@media (max-width: 768px) {
  .login-card {
    max-width: 100%;
    border-radius: 12px;
  }
  
  :deep(.ant-card-head-title) {
    font-size: 20px;
  }
  
  :deep(.ant-card-body) {
    padding: 24px 20px;
  }
}
</style>
