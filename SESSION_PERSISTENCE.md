# 终端会话持久化和重连机制

## 功能概述

系统实现了完整的终端会话持久化和重连机制，即使关闭浏览器页面，后台终端会话也会保持运行，重新打开页面时可以自动重连。

## 核心特性

### 1. 会话持久化
- **后台保持**: 关闭浏览器页面后，服务器端的终端会话继续运行
- **保留时长**: 默认保留 1 小时（3600 秒）
- **输出缓存**: 最多缓存最近 1000 行输出，重连时可以恢复
- **自动清理**: 超过 1 小时未活动的会话会被自动清理

### 2. 自动重连
- **会话信息保存**: 会话 ID 和名称保存在浏览器 localStorage
- **智能重连**: 重新打开页面时自动尝试重连到之前的会话
- **状态恢复**: 重连成功后恢复缓存的终端输出
- **失败处理**: 如果会话已失效，自动创建新会话

### 3. 会话管理
- **活跃检测**: 实时检测会话是否存活
- **最后活动时间**: 记录每个会话的最后活动时间
- **进程监控**: 检查终端进程是否还在运行

## 使用场景

### 场景 1: 意外关闭浏览器
```
1. 在终端中运行长时间任务（如编译、下载等）
2. 不小心关闭了浏览器标签页
3. 重新打开页面
4. 系统自动重连，恢复之前的会话
5. 可以看到任务继续运行的输出
```

### 场景 2: 切换设备
```
1. 在办公室电脑上启动终端会话
2. 下班回家
3. 在家里电脑上登录（1小时内）
4. 可以重连到办公室启动的会话
5. 继续之前的工作
```

### 场景 3: 网络中断
```
1. 终端会话正在运行
2. 网络临时中断
3. 网络恢复后刷新页面
4. 自动重连到之前的会话
5. 不会丢失任何数据
```

## 技术实现

### 后端实现

#### 会话缓存
```python
class TerminalSession:
    def __init__(self):
        self.buffer = []  # 缓存最近的输出
        self.max_buffer_size = 1000  # 最多缓存1000行
        self.last_activity = time.time()  # 最后活动时间
```

#### 会话管理
```python
class TerminalManager:
    def __init__(self):
        self.session_timeout = 3600  # 1小时超时
    
    def reconnect_session(self, session_id):
        # 检查会话是否存在且存活
        # 返回缓存的输出
    
    def cleanup_inactive_sessions(self):
        # 清理超时的会话
```

### 前端实现

#### 会话持久化
```javascript
// 保存到 localStorage
const saveSessions = () => {
  localStorage.setItem('terminal_sessions', JSON.stringify(sessions))
}

// 从 localStorage 恢复
const loadSessions = () => {
  const saved = localStorage.getItem('terminal_sessions')
  sessions.value = JSON.parse(saved)
}
```

#### 自动重连
```javascript
// 页面加载时尝试重连
onMounted(async () => {
  terminalStore.loadSessions()
  
  for (const session of terminalStore.sessions) {
    // 尝试重连，reconnect=true
    connectWebSocket(session.id, true)
  }
})
```

## API 接口

### 1. WebSocket 连接
```
ws://localhost:8000/api/v1/terminal/ws/{session_id}?token={token}&reconnect={bool}
```
- `reconnect=true`: 尝试重连到已存在的会话
- `reconnect=false`: 创建新会话

### 2. 检查会话状态
```
GET /api/v1/terminal/session/{session_id}/status
```
返回:
```json
{
  "exists": true,
  "alive": true,
  "last_activity": 1234567890.123
}
```

### 3. 列出活跃会话
```
GET /api/v1/terminal/sessions
```
返回所有活跃会话的列表

### 4. 清理不活跃会话
```
POST /api/v1/terminal/cleanup
```
手动触发清理超时会话

## 配置选项

### 后端配置
在 `backend/app/services/terminal.py` 中修改：

```python
class TerminalManager:
    def __init__(self):
        self.session_timeout = 3600  # 会话超时时间（秒）

class TerminalSession:
    def __init__(self):
        self.max_buffer_size = 1000  # 输出缓存行数
```

### 前端配置
会话信息保存在浏览器 localStorage 中：
- `terminal_sessions`: 会话列表
- `terminal_active_session`: 当前激活的会话

## 注意事项

1. **会话超时**: 默认 1 小时后会话会被清理，长时间任务需要注意
2. **缓存限制**: 只缓存最近 1000 行输出，更早的输出会丢失
3. **服务器重启**: 服务器重启后所有会话都会丢失
4. **浏览器数据**: 清除浏览器数据会导致无法重连
5. **同一账号**: 只能重连到同一账号创建的会话

## 最佳实践

1. **重要任务**: 使用 `screen` 或 `tmux` 等工具额外保护
2. **定期保存**: 重要工作定期保存到文件
3. **监控会话**: 定期检查会话状态
4. **及时清理**: 不用的会话及时关闭，释放资源

## 故障排查

### 问题: 重连失败
- 检查会话是否超过 1 小时
- 检查服务器是否重启
- 检查浏览器 localStorage 是否被清除

### 问题: 输出丢失
- 检查是否超过 1000 行缓存限制
- 检查网络是否稳定
- 考虑使用日志文件记录输出

### 问题: 会话被意外清理
- 增加 `session_timeout` 配置
- 使用 `screen` 或 `tmux` 额外保护
- 定期发送命令保持会话活跃
