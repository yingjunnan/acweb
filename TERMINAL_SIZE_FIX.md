# 终端显示格式修复

## 问题描述
终端内容显示有概率出现格式错误，特别是在跨设备登录或刷新页面后。

## 根本原因

### 终端尺寸不匹配
1. **终端尺寸的重要性**
   - 终端有固定的行数（rows）和列数（cols）
   - 例如：24 行 × 80 列
   - 所有输出都基于这个尺寸进行格式化

2. **重连时尺寸丢失**
   - 之前的实现没有保存终端尺寸
   - 重连时使用默认尺寸（24×80）
   - 如果原始尺寸不同，会导致显示错乱

3. **跨设备尺寸不一致**
   ```
   设备 A（桌面）:
   - 终端尺寸: 40 行 × 120 列
   - 执行命令，输出按 120 列格式化
   
   设备 B（手机）:
   - 重连时使用默认: 24 行 × 80 列
   - 显示之前的输出（按 120 列格式化）
   - 结果：格式错乱，内容错位
   ```

## 解决方案

### 1. 数据库添加尺寸字段

**修改 TerminalSessionDB 模型**：
```python
class TerminalSessionDB(Base):
    __tablename__ = "terminal_sessions"
    
    # ... 其他字段
    rows = Column(Integer, default=24)  # 终端行数
    cols = Column(Integer, default=80)  # 终端列数
```

**数据库迁移**：
```sql
ALTER TABLE terminal_sessions ADD COLUMN rows INTEGER DEFAULT 24;
ALTER TABLE terminal_sessions ADD COLUMN cols INTEGER DEFAULT 80;
```

### 2. 保存终端尺寸

**在 TerminalSession 类中**：
```python
class TerminalSession:
    def __init__(self, ...):
        # ...
        self.rows = 24  # 默认行数
        self.cols = 80  # 默认列数
    
    def set_winsize(self, rows: int, cols: int):
        """设置终端窗口大小"""
        if self.fd:
            self.rows = rows
            self.cols = cols
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
            # 更新数据库中的尺寸
            self._update_winsize_in_db()
```

**保存到数据库**：
```python
def _save_to_db(self):
    """保存会话到数据库"""
    # ...
    session_db.rows = self.rows
    session_db.cols = self.cols
    # ...

def _update_winsize_in_db(self):
    """更新数据库中的终端尺寸"""
    if not self.db:
        return
    
    try:
        session_db = self.db.query(TerminalSessionDB).filter(
            TerminalSessionDB.id == self.session_id
        ).first()
        
        if session_db:
            session_db.rows = self.rows
            session_db.cols = self.cols
            self.db.commit()
    except Exception as e:
        print(f"Error updating winsize in DB: {e}")
        self.db.rollback()
```

### 3. 返回尺寸信息

**在 list_sessions 中返回尺寸**：
```python
def list_sessions(self, username: str = None) -> list:
    """列出所有活跃的会话"""
    # ...
    result.append({
        "id": session_db.id,
        "name": session_db.name,
        # ...
        "rows": session_db.rows or 24,
        "cols": session_db.cols or 80
    })
```

### 4. 前端恢复尺寸

**在重连时使用保存的尺寸**：
```javascript
// 创建终端实例
const { term, fitAddon } = createTerminal(session.id)
term.open(container)

// 使用数据库中保存的尺寸
const savedRows = session.rows || 24
const savedCols = session.cols || 80
term.resize(savedCols, savedRows)

// 然后调整到容器大小
setTimeout(() => {
  fitAddon.fit()
}, 100)
```

## 工作流程

### 场景 1：首次创建终端
```
1. 用户创建终端
   ↓
2. 前端创建 xterm.js 实例（默认 24×80）
   ↓
3. fitAddon.fit() 调整到容器大小（例如 40×120）
   ↓
4. 触发 resize 事件
   ↓
5. 发送 resize 消息到后端
   ↓
6. 后端调用 set_winsize(40, 120)
   ↓
7. 保存到数据库: rows=40, cols=120 ✅
```

### 场景 2：刷新页面（同一设备）
```
1. 用户刷新页面
   ↓
2. 从后端获取会话列表
   ↓
3. 包含尺寸信息: rows=40, cols=120
   ↓
4. 创建终端实例
   ↓
5. term.resize(120, 40) 恢复尺寸 ✅
   ↓
6. 重连 WebSocket，恢复内容
   ↓
7. 内容按正确的尺寸显示 ✅
```

### 场景 3：跨设备登录
```
设备 A（桌面）:
1. 创建终端，尺寸 40×120
2. 执行命令，输出按 120 列格式化
3. 保存到数据库: rows=40, cols=120

设备 B（手机）:
1. 登录并打开终端页面
2. 从数据库获取会话: rows=40, cols=120
3. 创建终端实例
4. term.resize(120, 40) 恢复尺寸 ✅
5. 重连并显示内容
6. 内容按正确的尺寸显示 ✅
7. fitAddon.fit() 调整到手机屏幕
8. 触发 resize，更新数据库尺寸
```

## 技术要点

### 终端尺寸的影响
- **行数（rows）**: 决定垂直方向可以显示多少行
- **列数（cols）**: 决定水平方向可以显示多少字符
- **换行**: 当输出超过列数时，会自动换行
- **滚动**: 当输出超过行数时，会滚动

### xterm.js 的 resize 方法
```javascript
// 设置终端尺寸（不改变容器大小）
term.resize(cols, rows)

// 调整终端尺寸以适应容器（会改变 cols 和 rows）
fitAddon.fit()
```

### 尺寸同步流程
1. **前端 resize** → 触发 `term.onResize` 事件
2. **发送到后端** → WebSocket 消息 `{type: 'resize', cols, rows}`
3. **后端更新** → 调用 `set_winsize()` 和 `_update_winsize_in_db()`
4. **保存到数据库** → 持久化存储

### 为什么需要两步调整？
```javascript
// 第一步：恢复保存的尺寸
term.resize(savedCols, savedRows)

// 第二步：调整到当前容器大小
fitAddon.fit()
```

**原因**：
- 第一步确保历史内容按正确的尺寸显示
- 第二步适应当前设备的屏幕大小
- 如果直接 fit()，会丢失原始尺寸信息

## 数据库迁移

### 迁移脚本
```python
#!/usr/bin/env python3
"""
数据库迁移脚本：添加终端尺寸字段
"""

import sqlite3

def migrate():
    conn = sqlite3.connect('terminal_sessions.db')
    cursor = conn.cursor()
    
    # 添加 rows 字段
    cursor.execute("ALTER TABLE terminal_sessions ADD COLUMN rows INTEGER DEFAULT 24")
    
    # 添加 cols 字段
    cursor.execute("ALTER TABLE terminal_sessions ADD COLUMN cols INTEGER DEFAULT 80")
    
    conn.commit()
    conn.close()
```

### 运行迁移
```bash
cd backend
python3 migrate_add_terminal_size.py
```

## 测试场景

### 场景 1：基本尺寸保存
1. 创建终端，调整浏览器窗口大小
2. 刷新页面
3. **验证**：终端尺寸正确恢复 ✅

### 场景 2：跨设备尺寸
1. 在桌面（大屏幕）创建终端，执行 `ls -la`
2. 在手机（小屏幕）登录
3. **验证**：内容显示正确，无格式错乱 ✅

### 场景 3：动态调整
1. 创建终端，执行命令
2. 调整浏览器窗口大小
3. 刷新页面
4. **验证**：使用最新的尺寸 ✅

### 场景 4：多设备并发
1. 在设备 A 和设备 B 同时打开同一个终端
2. 在设备 A 调整窗口大小
3. 在设备 B 刷新页面
4. **验证**：设备 B 使用设备 A 的最新尺寸 ✅

## 注意事项

### 1. 尺寸冲突
- 多个设备可能有不同的屏幕尺寸
- 当前实现：使用最后一次调整的尺寸
- 可能导致在小屏幕设备上显示为大屏幕格式

### 2. 性能影响
- 每次调整窗口大小都会更新数据库
- 频繁调整可能导致大量数据库写入
- **优化建议**：添加节流（throttle），例如 500ms 更新一次

### 3. 默认值
- 新会话默认使用 24×80
- 这是传统终端的标准尺寸
- 会在首次 fit() 后更新为实际尺寸

### 4. 兼容性
- 旧的会话数据没有 rows 和 cols 字段
- 迁移脚本会添加默认值（24×80）
- 首次重连后会更新为实际尺寸

## 未来改进

### 1. 智能尺寸适配
根据设备类型自动调整：
```javascript
if (isMobile) {
  // 手机使用较小的尺寸
  term.resize(40, 20)
} else {
  // 桌面使用保存的尺寸
  term.resize(savedCols, savedRows)
}
```

### 2. 尺寸历史
保存每个设备的尺寸偏好：
```python
class TerminalSizePreference(Base):
    __tablename__ = "terminal_size_preferences"
    
    user_id = Column(String, primary_key=True)
    device_type = Column(String, primary_key=True)  # desktop, mobile, tablet
    rows = Column(Integer)
    cols = Column(Integer)
```

### 3. 响应式布局
根据内容类型自动调整：
```javascript
// 查看日志时使用更多行
if (isViewingLogs) {
  term.resize(cols, 50)
}

// 编辑文件时使用更多列
if (isEditing) {
  term.resize(120, rows)
}
```

## 相关文件
- `backend/app/db/models.py`: 数据库模型（添加 rows 和 cols 字段）
- `backend/app/services/terminal.py`: 终端服务（保存和恢复尺寸）
- `frontend/src/views/Terminal.vue`: 前端组件（恢复尺寸）
- `backend/migrate_add_terminal_size.py`: 数据库迁移脚本

## 总结

通过保存和恢复终端尺寸，我们解决了：
- ✅ 跨设备显示格式一致
- ✅ 刷新页面后格式正确
- ✅ 历史内容按正确的尺寸显示
- ✅ 动态调整尺寸并持久化

用户现在可以在任何设备上看到格式正确的终端内容，无论原始尺寸是多少。
