import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 10000
})

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Terminal API
export const terminalApi = {
  // 获取活跃会话列表
  getSessions: () => {
    const token = localStorage.getItem('token')
    return api.get(`/api/v1/terminal/sessions?token=${token}`)
  },
  
  // 检查会话状态
  checkSessionStatus: (sessionId) => {
    return api.get(`/api/v1/terminal/session/${sessionId}/status`)
  },
  
  // 获取会话详细状态
  getSessionStatus: (sessionId) => {
    const token = localStorage.getItem('token')
    return api.get(`/api/v1/terminal/session/${sessionId}/status?token=${token}`)
  }
}

export default api
