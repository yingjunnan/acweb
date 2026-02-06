# 终端历史内容持久化修复

## 问题描述
刷新浏览器页面后，虽然终端会话列表恢复了，但终端中的历史内容（命令输出）看不到了，终端是空白的。

## 根本原因

### 会话生命周期问题
1. **WebSocket 断开时会话被删除**
   - 用户刷新页面 → WebSocket 断开
   - 后端在 `finally` 块中调用 `close_session()`
   - 会话从内存中删除（`del self.sessions[session_id]`）
   - 内存中的缓冲区丢失

2. **数据库缓冲区不是最新的**
   - 虽然有 `_save_buffer_to_db()` 方法
   - 但它只在 `read()` 时调用
   - WebSocket 断开时没有保存最终的缓冲区
   - 数据库中的 buffer 可能不完整

3. **重连时无法恢复内容**
   - 用户刷新页面，尝试重连
   - `reconnect_session()` 先检查内存（已删除）
   - 然后从数据库恢复（buffer 不完整或为空）
   - 终端显示空白

## 解决方案

### 1. WebSocket 断开时不删除会话
**修改前**：
```python
finally:
    read_task.cancel()
    terminal_manager.close_session(session_id)  # 立即删除会话
    await websocket.close()
```

**修改后**：
```python
finally:
    read_task.cancel()
    # WebSocket 断开时不关闭会话，保持会话活跃以便重连
    # 只有在收到 close 消息时才真正关闭会话
    
    # 保存最终的缓冲区到数据库
    if session and session_id in terminal_manager.sessions:
        session._save_buffer_to_db()
    
    await websocket.close()
```

**关键改进**：
- WebSocket 断开时，会话保留在内存中
- 用户刷新页面后可以重连到同一个会话
- 内存中的缓冲区完整保留

### 2. 用户明确关闭时才删除会话
**修改消息处理逻辑**：
```python
if data["type"] == "close":
    # 用户明确关闭会话，真正关闭它
    terminal_manager.close_session(session_id)
    break
```

**区分两种情况**：
- **WebSocket 断开**（刷新页面）：保留会话，允许重连
- **用户关闭终端**（点击关闭按钮）：删除会话，释放资源

### 3. 关闭会话前保存缓冲区
**修改 close_session 方法**：
```python
def close_session(self, session_id: str):
    """关闭终端会话"""
    if session_id in self.sessions:
        session = self.sessions[session_id]
        # 在关闭前保存最终的缓冲区
        session._save_buffer_to_db()
        session.close()
        del self.sessions[session_id]
```

**确保数据完整性**：
- 无论何时关闭会话，都先保存缓冲区
- 数据库中的 buffer 始终是最新的

## 工作流程

### 场景 1：刷新页面（会话保留）
```
1. 用户刷新页面
   ↓
2. WebSocket 断开
   ↓
3. 后端保存缓冲区到数据库
   ↓
4. 会话保留在内存中 ✅
   ↓
5. 用户重新连接
   ↓
6. reconnect_session() 从内存获取会话 ✅
   ↓
7. 返回完整的缓冲区内容
   ↓
8. 前端显示历史内容 ✅
```

### 场景 2：用户关闭终端（会话删除）
```
1. 用户点击关闭按钮
   ↓
2. 前端发送 type: 'close' 消息
   ↓
3. 后端收到 close 消息
   ↓
4. 调用 close_session()
   ↓
5. 保存最终缓冲区到数据库
   ↓
6. 关闭 pty 进程
   ↓
7. 从内存中删除会话 ✅
   ↓
8. 释放资源
```

### 场景 3：会话超时（自动清理）
```
1. 会话长时间无活动
   ↓
2. cleanup_inactive_sessions() 定期检查
   ↓
3. 发现超时会话
   ↓
4. 调用 close_session()
   ↓
5. 保存缓冲区并删除会话
   ↓
6. 数据库标记为 is_active = False
```

## 技术要点

### 会话状态管理
- **内存中的会话**：快速访问，包含完整的缓冲区和 pty 进程
- **数据库中的会话**：持久化存储，用于恢复和跨进程共享
- **双层缓存**：内存优先，数据库备份

### 缓冲区同步策略
1. **实时同步**：每次 `read()` 时保存到数据库
2. **断开同步**：WebSocket 断开时保存最终状态
3. **关闭同步**：会话关闭前保存最终状态

### 重连优先级
1. **内存中的会话**（最快，最完整）
2. **数据库中的会话**（备用，可能不是最新）
3. **创建新会话**（最后选择）

## 数据库字段

### TerminalSessionDB 表
```python
class TerminalSessionDB(Base):
    __tablename__ = "terminal_sessions"
    
    id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    name = Column(String, nullable=False)
    buffer = Column(Text)  # 缓存的输出内容
    last_activity = Column(Float, nullable=False)
    created_at = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    pid = Column(Integer)
    cwd = Column(String)
```

### buffer 字段
- **类型**：Text（可以存储大量文本）
- **内容**：终端的所有输出内容（join 后的字符串）
- **更新时机**：每次 read()、WebSocket 断开、会话关闭
- **用途**：重连时恢复历史内容

## 性能考虑

### 数据库写入频率
- 每次 `read()` 都会调用 `_save_buffer_to_db()`
- 如果输出频繁，可能导致大量数据库写入
- **优化建议**：添加写入节流（throttle），例如每秒最多写入一次

### 缓冲区大小
- 默认 `max_buffer_size = 1000` 行
- 每行约 200 字节（80 字符 × 2 字节 + 开销）
- 总计约 200 KB
- **优化建议**：可配置缓冲区大小，平衡内存和功能

### 会话清理
- 定期清理超时会话（默认 1 小时）
- 避免内存泄漏
- **优化建议**：添加定时任务，自动清理过期会话

## 测试场景

### 场景 1：基本刷新
1. 创建终端，执行 `ls -la`
2. 刷新页面
3. **验证**：终端显示 `ls -la` 的输出 ✅

### 场景 2：大量输出
1. 创建终端，执行 `cat /var/log/system.log`（大量输出）
2. 等待输出完成
3. 刷新页面
4. **验证**：终端显示完整的日志内容 ✅

### 场景 3：多次刷新
1. 创建终端，执行命令
2. 刷新页面 3 次
3. **验证**：每次刷新后内容都完整 ✅

### 场景 4：关闭后刷新
1. 创建终端，执行命令
2. 关闭终端
3. 刷新页面
4. **验证**：终端不再出现（已被删除）✅

### 场景 5：超时后刷新
1. 创建终端，执行命令
2. 等待超过超时时间（1 小时）
3. 刷新页面
4. **验证**：显示"会话已超时"，创建新会话

## 注意事项

### 1. 内存管理
- 会话保留在内存中会占用资源
- 需要合理设置超时时间
- 建议：1 小时超时，平衡用户体验和资源占用

### 2. 并发问题
- 多个 WebSocket 可能同时连接到同一个会话
- 需要处理并发读写
- 当前实现：最后一个连接生效

### 3. 数据一致性
- 内存和数据库可能不同步
- 优先使用内存中的数据
- 数据库作为备份和恢复手段

### 4. 安全性
- 确保用户只能访问自己的会话
- token 验证和 username 过滤
- 防止会话劫持

## 相关文件
- `backend/app/api/terminal.py`: WebSocket 端点（修改 finally 块）
- `backend/app/services/terminal.py`: 会话管理（修改 close_session）
- `backend/app/db/models.py`: 数据库模型（buffer 字段）
- `frontend/src/views/Terminal.vue`: 前端终端组件（处理 reconnect 消息）

## 未来改进
1. 添加缓冲区写入节流，减少数据库压力
2. 支持会话共享，多个客户端同时查看同一个终端
3. 添加会话快照功能，保存特定时刻的状态
4. 实现会话录制和回放功能
5. 优化大缓冲区的存储和传输（压缩）
