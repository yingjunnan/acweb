# 持久化后台会话功能

## 功能概述

终端会话现在可以像后台任务一样在服务端持续运行，即使所有客户端都断开连接。这使得系统能够支持长时间运行的任务（几十小时甚至更长），并且所有客户端都可以实时同步会话状态。

## 核心特性

### 1. 后台持续运行
- ✅ 终端会话在服务端独立运行
- ✅ 即使所有客户端断开，会话继续执行
- ✅ 支持长时间运行的任务（默认超时7天）
- ✅ 后台线程持续读取终端输出

### 2. 多客户端同步
- ✅ 多个客户端可以同时连接到同一个会话
- ✅ 所有客户端看到相同的终端输出
- ✅ 任何客户端的输入都会同步到所有其他客户端
- ✅ 实时显示连接的客户端数量

### 3. 状态可见性
- ✅ 显示会话是否在后台运行
- ✅ 显示当前连接的客户端数量
- ✅ 显示会话的运行状态（运行中/已停止）
- ✅ 每5秒自动更新状态信息

### 4. 跨设备访问
- ✅ 在任何设备上都可以连接到运行中的会话
- ✅ 会话状态完全同步
- ✅ 支持从任何地方恢复会话

## 技术实现

### 后端架构

#### 1. 会话管理 (TerminalSession)
```python
class TerminalSession:
    def __init__(self, ...):
        self.connected_clients = set()  # 跟踪连接的客户端
        self.output_queue = []          # 输出队列，用于广播
```

**关键方法:**
- `add_client(client_id)` - 添加客户端连接
- `remove_client(client_id)` - 移除客户端连接
- `has_clients()` - 检查是否有客户端连接
- `get_queued_output()` - 获取待广播的输出

#### 2. 后台读取线程
```python
def _start_background_reader(self, session_id: str):
    """启动后台任务持续读取终端输出"""
    def read_loop():
        while session_id in self.sessions:
            session.read(timeout=0.1)  # 持续读取
            time.sleep(0.01)
    
    thread = threading.Thread(target=read_loop, daemon=True)
    thread.start()
```

**特点:**
- 独立线程运行，不依赖客户端连接
- 持续读取终端输出并缓存
- 即使没有客户端也继续运行

#### 3. 多客户端 WebSocket 处理
```python
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(...):
    # 为每个客户端分配唯一 ID
    client_id = f"{username}_{id(websocket)}"
    
    # 添加到会话的客户端列表
    session.add_client(client_id)
    
    # 从输出队列读取并广播
    output = session.get_queued_output()
    
    # 断开时移除客户端
    session.remove_client(client_id)
    
    # 只有在没有客户端时才关闭会话
    if not session.has_clients():
        # 会话继续在后台运行
```

### 前端实现

#### 1. 状态显示
```vue
<a-tag v-if="info.connected_clients > 1" color="orange">
  <TeamOutlined /> {{ info.connected_clients }} 个客户端
</a-tag>

<a-tag v-if="info.running_in_background" color="gold">
  <ThunderboltOutlined /> 后台运行中
</a-tag>
```

#### 2. 定期状态更新
```javascript
// 每5秒更新一次所有会话的状态
statusUpdateInterval = setInterval(() => {
  for (const session of terminalStore.sessions) {
    updateSessionStatus(session.id)
  }
}, 5000)
```

#### 3. 会话状态 API
```javascript
const updateSessionStatus = async (sessionId) => {
  const response = await terminalApi.getSessionStatus(sessionId)
  // 更新 connected_clients, running_in_background, alive 等
}
```

## 使用场景

### 场景 1: 长时间编译任务
```bash
# 在终端中启动编译
./build.sh  # 需要运行3小时

# 关闭浏览器或切换设备
# 任务继续在后台运行

# 几小时后从任何设备重新连接
# 看到完整的编译输出和当前状态
```

### 场景 2: 多人协作
```bash
# 用户 A 在设备 1 上启动会话
ssh production-server

# 用户 B 在设备 2 上连接到同一会话
# 两个用户看到相同的输出
# 任何一方的输入都会同步

# 信息栏显示: "2 个客户端"
```

### 场景 3: 后台监控
```bash
# 启动监控任务
tail -f /var/log/app.log

# 关闭浏览器
# 任务继续运行，日志继续被读取

# 信息栏显示: "后台运行中"

# 随时重新连接查看最新日志
```

### 场景 4: 跨设备工作
```bash
# 在办公室电脑上启动任务
npm run dev

# 回家后在家里电脑上连接
# 看到完整的运行历史
# 继续工作，无缝切换
```

## 配置选项

### 会话超时时间
在 `backend/terminal_config.json` 中配置：

```json
{
  "session_timeout": 604800,  // 7天（秒）
  "buffer_size": 5000         // 缓冲区大小（行）
}
```

**推荐设置:**
- 短期任务: 3600 (1小时)
- 中期任务: 86400 (1天)
- 长期任务: 604800 (7天)
- 永久任务: 2592000 (30天)

### 缓冲区大小
控制保存的历史输出行数：

```json
{
  "buffer_size": 5000  // 保存最近5000行
}
```

**推荐设置:**
- 轻量任务: 1000 行
- 普通任务: 5000 行
- 大量输出: 10000 行

## API 接口

### 1. 获取会话状态
```
GET /api/v1/terminal/session/{session_id}/status?token={token}
```

**响应:**
```json
{
  "exists": true,
  "alive": true,
  "last_activity": 1707234567.89,
  "connected_clients": 2,
  "running_in_background": false,
  "rows": 24,
  "cols": 80,
  "pid": 12345
}
```

### 2. 列出所有会话
```
GET /api/v1/terminal/sessions?token={token}
```

**响应:**
```json
{
  "sessions": [
    {
      "id": "session-123",
      "name": "编译任务",
      "running": true,
      "last_activity": 1707234567.89,
      "rows": 24,
      "cols": 80
    }
  ]
}
```

### 3. WebSocket 连接
```
ws://localhost:8000/api/v1/terminal/ws/{session_id}?token={token}&reconnect=true
```

**消息类型:**
- `reconnect` - 重连成功，包含历史缓冲区
- `output` - 终端输出
- `input` - 用户输入
- `resize` - 调整终端尺寸
- `close` - 关闭会话

## 状态指示器

### 信息栏标签

#### 客户端数量
- **1 个客户端** (青色) - 只有你连接
- **2+ 个客户端** (橙色) - 多人同时连接

#### 后台运行
- **后台运行中** (金色) - 会话在后台执行，没有客户端连接

#### 运行状态
- **运行中** (绿色脉冲) - 进程正在运行
- **已停止** (灰色) - 进程已结束

## 最佳实践

### 1. 长时间任务
```bash
# 使用 nohup 确保任务不受 SIGHUP 影响
nohup ./long-running-task.sh &

# 或使用 screen/tmux 风格的命令
./task.sh
# 然后可以安全地断开连接
```

### 2. 监控后台任务
```bash
# 定期检查任务状态
ps aux | grep your-process

# 查看日志
tail -f /var/log/your-app.log
```

### 3. 多人协作
- 使用有意义的会话名称（如"生产部署"、"调试会话"）
- 在会话详情中查看当前连接的客户端数量
- 协调输入，避免冲突

### 4. 资源管理
- 定期清理不需要的会话
- 监控服务器资源使用
- 设置合理的超时时间

## 安全考虑

### 1. 用户隔离
- 每个用户只能访问自己的会话
- Token 验证确保身份安全

### 2. 会话保护
- 会话 ID 使用时间戳和计数器生成，难以猜测
- 数据库中的会话与用户名关联

### 3. 资源限制
- 设置会话超时防止资源泄漏
- 限制缓冲区大小防止内存溢出
- 后台线程使用 daemon 模式，进程退出时自动清理

## 故障排查

### 问题 1: 会话没有在后台运行
**检查:**
1. 后端日志中是否有 "Started background reader" 消息
2. 会话是否已超时
3. 进程是否仍在运行 (`ps aux | grep {pid}`)

### 问题 2: 客户端数量不准确
**解决:**
1. 刷新页面重新连接
2. 检查网络连接是否稳定
3. 查看后端日志中的客户端连接/断开消息

### 问题 3: 输出不同步
**解决:**
1. 检查所有客户端的网络连接
2. 确认 WebSocket 连接正常
3. 查看后端输出队列是否正常工作

### 问题 4: 会话意外关闭
**检查:**
1. 会话超时设置
2. 服务器是否重启
3. 进程是否被 kill

## 性能优化

### 1. 缓冲区管理
- 使用循环缓冲区，自动丢弃旧数据
- 定期保存到数据库，避免内存溢出

### 2. 后台线程
- 使用 daemon 线程，不阻塞主进程
- 适当的 sleep 时间，平衡响应速度和 CPU 使用

### 3. 数据库写入
- 批量写入减少 I/O
- 异步保存避免阻塞

### 4. WebSocket 优化
- 使用输出队列避免重复发送
- 适当的读取间隔（10ms）

## 未来改进

### 计划中的功能
1. **会话分享** - 生成分享链接，允许其他用户只读访问
2. **会话录制** - 记录完整的会话历史，支持回放
3. **资源监控** - 显示会话的 CPU、内存使用情况
4. **会话分组** - 按项目或用途组织会话
5. **通知系统** - 任务完成时发送通知
6. **会话快照** - 保存会话状态，支持恢复到特定时间点

## 总结

持久化后台会话功能使得 Web 终端系统能够支持真正的长时间运行任务，提供了类似 tmux/screen 的体验，同时增加了多客户端同步和跨设备访问的能力。这使得系统适用于更广泛的场景，从简单的命令执行到复杂的多人协作开发。
