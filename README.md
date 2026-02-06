# Web Terminal System

一个基于 FastAPI + Vue3 的 Web 终端系统，支持在浏览器中操作服务器终端执行 AI Agent 工具。

## 功能特性

- 🔐 用户登录验证（JWT）
- 📱 响应式设计，支持移动端
- 🖥️ 多会话终端管理
- ⚡ WebSocket 实时通信
- 🎨 Ant Design Vue UI
- 📊 系统监控仪表盘（CPU、内存、磁盘、网络）
- ⚙️ 终端配置管理（默认路径、Shell、字体、主题）

## 技术栈

### 后端
- FastAPI
- WebSocket
- JWT 认证
- pty (伪终端)

### 前端
- Vue 3
- Ant Design Vue
- Vite
- Pinia
- xterm.js

## 项目结构

```
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── core/     # 核心配置
│   │   ├── models/   # 数据模型
│   │   └── services/ # 业务逻辑
│   └── requirements.txt
├── frontend/         # Vue3 前端
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   └── api/
│   └── package.json
└── README.md
```

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

默认账号：admin / admin123
