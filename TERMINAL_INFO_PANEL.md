# 终端信息面板功能

## 功能概述
为每个终端会话添加信息栏，显示会话的详细信息，并提供一键适配尺寸的功能，解决跨设备显示不一致的问题。

## 主要功能

### 1. 终端信息栏
在每个终端标签页的顶部显示关键信息：

**显示内容**：
- 📅 **创建时间**: 显示会话创建时间（智能格式化）
- 📏 **终端尺寸**: 显示保存的行列数（cols × rows）
- 💾 **缓存大小**: 显示缓冲区占用的内存

**操作按钮**：
- 🔄 **适配尺寸**: 当前尺寸与保存的尺寸不同时显示
- ℹ️ **详情**: 查看完整的会话信息

### 2. 会话详情对话框
点击"详情"按钮显示完整的会话信息：

**详细信息**：
- 会话名称
- 会话 ID（可复制）
- 创建时间（完整日期时间）
- 最后活动时间
- 终端尺寸（保存的尺寸）
- 当前尺寸（实际显示的尺寸）
- 缓存大小
- 工作目录
- 进程 ID
- 运行状态

### 3. 一键适配尺寸
当检测到当前终端尺寸与数据库中保存的尺寸不同时：

**自动检测**：
- 比较当前终端的 cols/rows 与数据库中的值
- 如果不同，显示"适配尺寸"按钮

**一键适配**：
- 点击按钮，终端自动调整到保存的尺寸
- 发送 resize 消息到后端
- 重新调整容器大小以适应

## 使用场景

### 场景 1：跨设备查看
```
设备 A（桌面，大屏幕）:
- 创建终端，尺寸自动调整为 120×40
- 执行命令，输出按 120 列格式化

设备 B（手机，小屏幕）:
- 登录并打开终端
- 信息栏显示: 120 × 40
- 当前尺寸: 80 × 24（手机屏幕）
- 显示"适配尺寸"按钮 ✅
- 点击按钮，终端调整为 120×40
- 内容显示正确 ✅
```

### 场景 2：检查会话信息
```
用户想知道会话的详细信息:
1. 点击"详情"按钮
2. 查看完整信息：
   - 创建时间: 2024-02-06 20:15:30
   - 终端尺寸: 120 列 × 40 行
   - 当前尺寸: 80 列 × 24 行
   - 缓存大小: 256.5 KB
   - 工作目录: /home/user/project
3. 点击"适配到保存的尺寸"
4. 终端调整完成 ✅
```

### 场景 3：调试显示问题
```
用户发现终端显示格式错误:
1. 查看信息栏
2. 发现: 保存尺寸 120×40，当前尺寸 80×24
3. 点击"适配尺寸"
4. 问题解决 ✅
```

## 技术实现

### 前端数据结构
```javascript
const sessionInfoMap = ref({
  'session-id-1': {
    id: 'session-id-1',
    name: '开发环境',
    rows: 40,
    cols: 120,
    created_at: 1707223530,
    last_activity: 1707223600,
    running: true,
    cwd: '/home/user',
    pid: 12345,
    buffer_size: 262144
  }
})
```

### 尺寸检测逻辑
```javascript
const needsResize = (sessionId) => {
  const info = sessionInfoMap.value[sessionId]
  const terminal = terminalStore.terminals[sessionId]
  
  if (!info || !terminal || !terminal.term) return false
  
  // 比较当前尺寸与保存的尺寸
  return terminal.term.cols !== info.cols || 
         terminal.term.rows !== info.rows
}
```

### 适配尺寸逻辑
```javascript
const adaptTerminalSize = (sessionId) => {
  const info = sessionInfoMap.value[sessionId]
  const terminal = terminalStore.terminals[sessionId]
  
  // 1. 调整终端尺寸
  terminal.term.resize(info.cols, info.rows)
  
  // 2. 通知后端
  ws.send(JSON.stringify({ 
    type: 'resize', 
    cols: info.cols, 
    rows: info.rows 
  }))
  
  // 3. 调整容器
  terminal.fitAddon.fit()
}
```

## UI 设计

### 信息栏样式
```css
.terminal-info-bar {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.05) 0%, 
    rgba(118, 75, 162, 0.05) 100%);
  border-bottom: 1px solid #e8e8e8;
}
```

**特点**：
- 渐变背景，与整体设计风格一致
- 左右布局，信息和操作分离
- 使用 Ant Design 的 Tag 和 Button 组件

### 标签颜色
- 🔵 **蓝色**: 时间信息
- 🟢 **绿色**: 尺寸信息
- 🟣 **紫色**: 缓存信息

### 响应式设计
```css
@media (max-width: 768px) {
  .terminal-info-bar {
    flex-direction: column;
    gap: 8px;
  }
  
  .info-left, .info-right {
    width: 100%;
    justify-content: space-between;
  }
}
```

## 时间格式化

### 智能时间显示
```javascript
const formatDate = (timestamp) => {
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return '5 分钟前'
  if (diff < 86400000) return '2 小时前'
  
  return '2024-02-06'
}
```

**优势**：
- 最近的时间显示相对时间（更直观）
- 较早的时间显示绝对日期（更准确）

### 完整时间显示
```javascript
const formatDateTime = (timestamp) => {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
```

**输出**: `2024-02-06 20:15:30`

## 缓存大小计算

### 格式化逻辑
```javascript
const formatBufferSize = (size) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}
```

**示例**：
- 512 → `512 B`
- 2048 → `2.0 KB`
- 262144 → `256.0 KB`
- 1048576 → `1.0 MB`

## 用户体验

### 视觉反馈
1. **适配尺寸按钮**
   - 只在需要时显示（智能检测）
   - 主色调按钮，醒目易见
   - 带图标，操作明确

2. **信息标签**
   - 不同颜色区分不同类型
   - 带图标，信息清晰
   - 紧凑布局，不占用过多空间

3. **详情对话框**
   - 使用 Descriptions 组件，信息结构化
   - 可复制会话 ID，方便调试
   - 实时显示当前尺寸，便于对比

### 交互流程
```
用户打开终端
  ↓
查看信息栏
  ↓
发现尺寸不匹配（显示"适配尺寸"按钮）
  ↓
点击"适配尺寸"
  ↓
终端自动调整
  ↓
显示成功提示
  ↓
按钮消失（尺寸已匹配）
```

## 性能考虑

### 数据缓存
- 会话信息存储在 `sessionInfoMap` 中
- 避免重复请求后端
- 只在首次加载时获取

### 按需渲染
- 信息栏只在有数据时渲染
- 适配按钮只在需要时显示
- 详情对话框按需打开

### 内存管理
- 关闭会话时清理 `sessionInfoMap`
- 避免内存泄漏

## 未来改进

### 1. 实时更新
使用 WebSocket 推送会话信息变更：
```javascript
ws.onmessage = (event) => {
  if (event.type === 'session_info_update') {
    sessionInfoMap.value[event.sessionId] = event.data
  }
}
```

### 2. 自动适配选项
添加设置选项，自动适配尺寸：
```javascript
if (configStore.config.auto_adapt_size) {
  adaptTerminalSize(sessionId)
}
```

### 3. 尺寸历史
记录尺寸变更历史：
```javascript
const sizeHistory = [
  { timestamp: 1707223530, cols: 80, rows: 24 },
  { timestamp: 1707223600, cols: 120, rows: 40 }
]
```

### 4. 性能监控
显示终端性能指标：
- CPU 使用率
- 内存使用量
- 网络延迟

### 5. 快捷操作
添加更多快捷操作：
- 清空缓冲区
- 重启会话
- 导出历史
- 分享会话

## 相关文件
- `frontend/src/views/Terminal.vue`: 终端组件（添加信息栏和详情对话框）
- `backend/app/services/terminal.py`: 终端服务（返回完整的会话信息）
- `backend/app/db/models.py`: 数据库模型（包含 rows 和 cols 字段）

## 总结

通过添加终端信息面板，我们实现了：
- ✅ 可视化会话信息
- ✅ 一键适配尺寸
- ✅ 跨设备显示一致性
- ✅ 更好的用户体验
- ✅ 便于调试和问题排查

用户现在可以清楚地看到每个会话的详细信息，并在需要时快速适配尺寸，解决了跨设备显示不一致的问题。
