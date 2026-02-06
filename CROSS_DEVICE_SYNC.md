# 跨设备会话同步

## 问题描述
在同一个浏览器中终端会话工作正常，但切换设备登录时，无法恢复之前的终端会话。

## 根本原因

### localStorage 的局限性
1. **设备本地存储**
   - localStorage 数据存储在浏览器本地
   - 不同设备、不同浏览器之间无法共享
   - 用户在设备 A 创建的会话，在设备 B 看不到

2. **之前的恢复策略**
   - 优先从 localStorage 恢复会话
   - 只有在 localStorage 为空时才从后端获取
   - 导致跨设备时数据不一致

3. **数据不一致问题**
   ```
   设备 A:
   - localStorage: [session-1, session-2]
   - 后端数据库: [session-1, session-2, session-3]
   
   设备 B:
   - localStorage: []
   - 后端数据库: [session-1, session-2, session-3]
   
   问题：设备 A 看不到 session-3（被 localStorage 覆盖）
   ```

## 解决方案

### 数据库作为唯一真实来源（Single Source of Truth）

**核心原则**：
- 后端数据库是会话数据的唯一权威来源
- localStorage 仅作为缓存，不作为真实数据源
- 所有设备始终从后端获取最新的会话列表

### 修改前的逻辑
```javascript
onMounted(async () => {
  // 1. 检查 keep-alive 缓存
  if (hasExistingTerminals) return
  
  // 2. 从 localStorage 恢复（问题所在）
  terminalStore.loadSessions()
  if (localSessions.length > 0) {
    // 使用本地会话，不查询后端
    restoreLocalSessions()
  } else {
    // 3. 从后端获取（仅在本地为空时）
    const sessions = await api.getSessions()
    restoreSessions(sessions)
  }
})
```

**问题**：
- 设备 A 的 localStorage 有数据，不会查询后端
- 设备 B 的 localStorage 为空，会查询后端
- 两个设备看到的会话列表不一致

### 修改后的逻辑
```javascript
onMounted(async () => {
  // 1. 检查 keep-alive 缓存
  if (hasExistingTerminals) return
  
  // 2. 始终从后端获取会话列表（唯一真实来源）
  const sessions = await api.getSessions()
  
  if (sessions.length > 0) {
    // 恢复后端的会话
    restoreSessions(sessions)
    // 更新 localStorage（仅作为缓存）
    terminalStore.saveSessions()
  } else {
    // 后端没有会话，创建默认终端
    createDefaultTerminal()
  }
})
```

**优势**：
- 所有设备都从后端获取相同的会话列表
- localStorage 仅用于缓存，不影响数据一致性
- 跨设备、跨浏览器完全同步

## 数据流

### 场景 1：设备 A 创建会话
```
设备 A:
1. 用户创建终端 "开发环境"
   ↓
2. 前端调用 WebSocket 连接
   ↓
3. 后端创建会话并保存到数据库
   ↓
4. 数据库: [session-1: "开发环境"]
   ↓
5. 前端更新 localStorage（缓存）
```

### 场景 2：设备 B 登录
```
设备 B:
1. 用户登录并打开终端页面
   ↓
2. 前端调用 api.getSessions()
   ↓
3. 后端从数据库查询用户的会话
   ↓
4. 返回: [session-1: "开发环境"]
   ↓
5. 前端恢复会话并显示
   ↓
6. 用户可以看到设备 A 创建的终端 ✅
```

### 场景 3：设备 A 刷新页面
```
设备 A:
1. 用户刷新页面
   ↓
2. 前端调用 api.getSessions()（不使用 localStorage）
   ↓
3. 后端返回最新的会话列表
   ↓
4. 包括设备 B 可能创建的新会话
   ↓
5. 所有设备保持同步 ✅
```

## 技术实现

### 后端 API
```python
@router.get("/sessions")
async def list_sessions(token: str = Query(...)):
    """列出所有活跃会话"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="未授权")
    
    username = payload.get("sub")
    return {
        "sessions": terminal_manager.list_sessions(username)
    }
```

**关键点**：
- 按用户过滤会话（`username`）
- 只返回活跃的会话（`is_active = True`）
- 检查会话是否超时

### 前端实现
```javascript
// 始终从后端获取会话列表
const response = await terminalApi.getSessions()
const activeSessions = response.data.sessions || []

// 更新前端状态
terminalStore.sessions = activeSessions.map(s => ({
  id: s.id,
  name: s.name
}))

// 保存到 localStorage（仅作为缓存）
terminalStore.saveSessions()
```

**关键点**：
- 不检查 localStorage
- 直接调用后端 API
- localStorage 仅用于缓存，不影响逻辑

## 数据库设计

### TerminalSessionDB 表
```python
class TerminalSessionDB(Base):
    __tablename__ = "terminal_sessions"
    
    id = Column(String, primary_key=True)          # 会话 ID
    username = Column(String, nullable=False)      # 用户名（用于隔离）
    name = Column(String, nullable=False)          # 会话名称
    buffer = Column(Text)                          # 缓存的输出
    last_activity = Column(Float, nullable=False)  # 最后活动时间
    created_at = Column(Float, nullable=False)     # 创建时间
    is_active = Column(Boolean, default=True)      # 是否活跃
    pid = Column(Integer)                          # 进程 ID
    cwd = Column(String)                           # 工作目录
```

**索引**：
```python
# 按用户和活跃状态查询
Index('idx_username_active', 'username', 'is_active')
```

## 优势

### 1. 跨设备同步 ✅
- 用户在任何设备登录都能看到所有会话
- 在设备 A 创建的会话，在设备 B 立即可见（刷新后）
- 真正的云端同步体验

### 2. 数据一致性 ✅
- 数据库是唯一的真实来源
- 避免 localStorage 和数据库不一致
- 所有设备看到相同的数据

### 3. 多用户隔离 ✅
- 每个用户只能看到自己的会话
- 通过 `username` 字段过滤
- 安全可靠

### 4. 会话持久化 ✅
- 会话保存在数据库中
- 即使所有设备都关闭，会话仍然存在
- 下次登录时可以恢复

## 性能考虑

### API 调用频率
- 每次打开终端页面调用一次 `getSessions()`
- 使用 keep-alive 缓存组件，减少重复调用
- 切换菜单时不会重新调用

### 数据库查询优化
```python
# 使用索引加速查询
query = db.query(TerminalSessionDB).filter(
    TerminalSessionDB.username == username,
    TerminalSessionDB.is_active == True
)
```

### 缓存策略
- **内存缓存**：后端保持活跃会话在内存中
- **数据库持久化**：定期同步到数据库
- **前端缓存**：localStorage 作为 UI 缓存

## 测试场景

### 场景 1：跨设备创建和查看
1. 在设备 A（Chrome）登录，创建终端 "开发环境"
2. 在设备 B（Safari）登录
3. **验证**：设备 B 可以看到 "开发环境" 终端 ✅

### 场景 2：跨设备执行命令
1. 在设备 A 的终端执行 `ls -la`
2. 在设备 B 刷新页面
3. **验证**：设备 B 可以看到 `ls -la` 的输出 ✅

### 场景 3：跨浏览器同步
1. 在 Chrome 创建 3 个终端
2. 在 Firefox 登录
3. **验证**：Firefox 可以看到 3 个终端 ✅

### 场景 4：会话超时
1. 在设备 A 创建终端
2. 等待超过超时时间（1 小时）
3. 在设备 B 登录
4. **验证**：设备 B 看不到超时的会话 ✅

### 场景 5：多设备并发
1. 在设备 A 和设备 B 同时登录
2. 在设备 A 创建终端
3. 在设备 B 刷新页面
4. **验证**：设备 B 可以看到新创建的终端 ✅

## 注意事项

### 1. 会话共享限制
- 当前实现：多个设备可以看到相同的会话列表
- 但不支持实时同步（需要刷新页面）
- 未来可以使用 WebSocket 推送实现实时同步

### 2. 并发写入
- 多个设备可能同时连接到同一个会话
- 当前实现：最后一个连接生效
- 可能导致输入冲突

### 3. 会话所有权
- 会话属于创建它的用户
- 其他用户无法访问
- 通过 token 和 username 验证

### 4. 数据安全
- 会话数据存储在服务器
- 需要确保服务器安全
- 定期备份数据库

## 未来改进

### 1. 实时同步
使用 WebSocket 推送会话变更：
```javascript
// 当其他设备创建/删除会话时，实时通知所有设备
ws.onmessage = (event) => {
  if (event.type === 'session_created') {
    // 添加新会话到列表
  } else if (event.type === 'session_deleted') {
    // 从列表中删除会话
  }
}
```

### 2. 会话共享
允许多个用户共享同一个终端：
```python
class TerminalSessionDB(Base):
    # ...
    shared_with = Column(JSON)  # 共享给哪些用户
    owner = Column(String)      # 会话所有者
```

### 3. 会话锁定
防止多个设备同时操作同一个会话：
```python
class TerminalSessionDB(Base):
    # ...
    locked_by = Column(String)  # 当前锁定的设备
    locked_at = Column(Float)   # 锁定时间
```

### 4. 会话历史
保存会话的完整历史记录：
```python
class TerminalHistory(Base):
    __tablename__ = "terminal_history"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('terminal_sessions.id'))
    command = Column(String)
    output = Column(Text)
    timestamp = Column(Float)
```

## 相关文件
- `frontend/src/views/Terminal.vue`: 前端终端组件（修改 onMounted）
- `backend/app/api/terminal.py`: 后端 API（getSessions 端点）
- `backend/app/services/terminal.py`: 会话管理（list_sessions 方法）
- `backend/app/db/models.py`: 数据库模型（TerminalSessionDB）

## 总结

通过将数据库作为唯一的真实来源，我们实现了：
- ✅ 跨设备会话同步
- ✅ 数据一致性保证
- ✅ 多用户隔离
- ✅ 会话持久化

用户可以在任何设备登录，都能看到完整的会话列表和历史内容，提供了真正的云端终端体验。
