# Web 终端系统

一个功能强大的 Web 终端管理系统，支持多用户、多会话、跨设备访问和后台持续运行。

## ✨ 核心特性

- 🔐 **多用户支持** - JWT 认证，用户隔离
- 📱 **多会话管理** - 创建、命名、切换多个终端会话
- ⚡ **后台持续运行** - 会话在服务端独立运行，支持长时间任务（默认 7 天）
- 🌐 **跨设备同步** - 在任何设备上访问相同的会话
- 👥 **多客户端协作** - 多人可以同时连接同一会话
- 💾 **完整持久化** - 所有输出自动保存到数据库
- 🔄 **自动重连** - 网络断开自动恢复，不丢失数据
- 🖥️ **全屏模式** - 专注工作，减少干扰
- 🎨 **交互式 CLI 支持** - 完美支持 vim, htop, Claude Code 等

## 🚀 快速开始

### 安装依赖

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 启动服务

```bash
# 使用启动脚本（推荐）
./start.sh

# 或分别启动
# 后端
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm run dev
```

### 访问系统

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 📚 技术栈

**后端:**
- FastAPI (Python 3.11+)
- SQLAlchemy + SQLite
- WebSocket + PTY

**前端:**
- Vue 3 + Vite
- Ant Design Vue
- xterm.js + Pinia

## 📖 文档

详细文档请查看 [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)

包含内容：
- 完整功能说明
- API 接口文档
- 架构设计
- 配置说明
- 故障排查
- 部署指南

## 🎯 使用场景

### 长时间任务
```bash
# 启动编译任务（需要几小时）
./build.sh

# 关闭浏览器，任务继续运行
# 随时重新连接查看进度
```

### 多人协作
```bash
# 用户 A: 启动调试会话
tail -f /var/log/app.log

# 用户 B: 连接同一会话
# 两人同时看到相同的日志
```

### 跨设备工作
```bash
# 办公室: 启动开发服务器
npm run dev

# 回家后: 在家里电脑上继续工作
# 无缝切换，完整历史
```

## 🔧 配置

编辑 `backend/terminal_config.json`:

```json
{
  "session_timeout": 604800,  // 7 天
  "buffer_size": 5000,         // 5000 行
  "font_size": 14,
  "theme": "dark",
  "default_path": "~"
}
```

## 🐛 故障排查

### 输入无响应
- 检查 WebSocket 连接状态
- 查看浏览器控制台
- 检查后端日志

### 输出不同步
- 刷新页面重新连接
- 检查网络连接

### 会话丢失
- 检查会话超时设置
- 查看数据库: `sqlite3 backend/terminal_sessions.db`

## 📝 更新日志

### v1.0.0 (2026-02-06)

- ✅ 完整的多用户终端系统
- ✅ 后台持续运行支持
- ✅ 多客户端实时同步
- ✅ 完整的数据持久化
- ✅ 自动重连机制
- ✅ 全屏模式
- ✅ 交互式 CLI 完美支持

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**文档:** [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)  
**版本:** 1.0.0  
**更新:** 2026-02-06
