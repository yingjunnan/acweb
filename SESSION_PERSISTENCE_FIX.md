# 终端会话持久化修复（最终版）

## 问题历史

### 问题 1：切换菜单时会话丢失
**现象**：切换到其他菜单再返回时，显示"正在恢复会话..."但恢复失败。
**原因**：组件被销毁，终端实例和 WebSocket 连接丢失。
**解决**：使用 keep-alive 缓存组件。

### 问题 2：刷新页面时重置所有终端
**现象**：刷新浏览器页面后，所有终端会话被重置为默认终端。
**原因**：优先从后端获取会话，但后端可能没有返回会话（超时或清理），导致创建新的默认终端。
**解决**：优先使用 localStorage 中的会话信息，只有在本地没有会话时才从后端获取。

## 解决方案

### 1. 使用 keep-alive 缓存组件（解决切换菜单问题）
Vue 的 `<keep-alive>` 可以缓存组件实例，避免组件被销毁。

**修改 Layout.vue**：
```vue
<a-layout-content class="content">
  <router-view v-slot="{ Component }">
    <keep-alive include="Terminal">
      <component :is="Component" />
    </keep-alive>
  </router-view>
</a-layout-content>
```

**修改 Terminal.vue**：
```javascript
import { defineOptions } from 'vue'

defineOptions({
  name: 'Terminal'  // 组件名称，用于 keep-alive 识别
})
```

### 2. 优先使用 localStorage（解决刷新重置问题）
刷新页面时，优先从 localStorage 恢复会话，而不是从后端获取。

**恢复优先级**：
1. **keep-alive 缓存**（切换菜单时）- 最高优先级
2. **localStorage**（刷新页面时）- 次优先级
3. **后端 API**（首次访问或 localStorage 为空时）- 最低优先级

**修改 onMounted 逻辑**：
```javascript
onMounted(async () => {
  // 1. 检查 keep-alive 缓存
  const hasExistingTerminals = Object.keys(terminalStore.terminals).length > 0
  if (hasExistingTerminals) {
    return  // 直接使用缓存
  }
  
  // 2. 尝试从 localStorage 恢复
  terminalStore.loadSessions()
  const localSessions = terminalStore.sessions
  
  if (localSessions.length > 0) {
    // 有本地会话，尝试重连
    for (const session of localSessions) {
      // 创建终端实例并重连
    }
  } else {
    // 3. 从后端获取会话
    const response = await terminalApi.getSessions()
    // ...
  }
})
```

### 3. 添加后端会话列表 API（备用方案）
前端可以调用后端 API 获取活跃会话列表，作为备用方案。

**添加 API 方法（frontend/src/api/index.js）**：
```javascript
export const terminalApi = {
  // 获取活跃会话列表
  getSessions: () => {
    const token = localStorage.getItem('token')
    return api.get(`/api/v1/terminal/sessions?token=${token}`)
  },
  
  // 检查会话状态
  checkSessionStatus: (sessionId) => {
    return api.get(`/api/v1/terminal/session/${sessionId}/status`)
  }
}
```

## 技术要点

### keep-alive 的工作原理
1. **缓存组件实例**: 组件不会被销毁，而是被缓存
2. **保持状态**: 组件的所有状态（data、computed、refs）都被保留
3. **生命周期钩子**: 
   - `onMounted` 只在首次挂载时调用
   - `onActivated` 在组件被激活时调用（从缓存恢复）
   - `onDeactivated` 在组件被停用时调用（进入缓存）

### include 属性
- `include="Terminal"` 指定只缓存名为 "Terminal" 的组件
- 其他组件（Dashboard、Settings）不会被缓存
- 可以使用数组或正则表达式匹配多个组件

### 为什么不缓存所有组件？
1. **内存占用**: 缓存所有组件会占用更多内存
2. **数据新鲜度**: Dashboard 需要实时数据，不应该缓存
3. **针对性优化**: 只有 Terminal 需要保持连接状态

## 数据流

### 首次访问终端页面
```
用户访问 /terminal
  ↓
onMounted 触发
  ↓
检查 terminalStore.terminals（空）
  ↓
检查 localStorage（空）
  ↓
调用 terminalApi.getSessions()
  ↓
后端返回活跃会话列表（或空）
  ↓
创建终端实例并连接 WebSocket
  ↓
显示终端界面
```

### 切换到其他页面
```
用户点击 Dashboard
  ↓
Terminal 组件被 keep-alive 缓存
  ↓
终端实例和 WebSocket 保持活跃
  ↓
显示 Dashboard 页面
```

### 切换回终端页面
```
用户点击 Terminal
  ↓
Terminal 组件从缓存恢复
  ↓
onMounted 不会再次触发
  ↓
检查 terminalStore.terminals（有数据）
  ↓
直接显示缓存的终端界面
  ↓
WebSocket 连接仍然活跃
```

### 刷新浏览器页面（新增）
```
用户刷新页面
  ↓
所有组件重新创建（keep-alive 缓存清空）
  ↓
onMounted 触发
  ↓
检查 terminalStore.terminals（空）
  ↓
检查 localStorage（有数据）✅
  ↓
使用 localStorage 中的会话信息
  ↓
创建终端实例并尝试重连
  ↓
WebSocket 重连到后端会话
  ↓
恢复终端内容
```

## 后端支持

后端已经实现了完整的会话管理：

### 数据库持久化
- 会话信息存储在 SQLite 数据库
- 包括：session_id、username、name、buffer、last_activity、is_active

### API 端点
1. **GET /api/v1/terminal/sessions**: 获取用户的活跃会话列表
2. **GET /api/v1/terminal/session/{id}/status**: 检查特定会话状态
3. **WebSocket /api/v1/terminal/ws/{id}**: 终端连接（支持重连）

### 会话超时管理
- 配置的超时时间（默认 1 小时）
- 自动清理超时的会话
- 重连时检查会话是否超时

## 测试场景

### 场景 1：正常切换（keep-alive）
1. 打开终端页面，创建 2 个会话
2. 在终端中执行一些命令
3. 切换到 Dashboard
4. 切换回终端页面
5. **预期**: 终端立即显示，内容完整，无需重连 ✅

### 场景 2：页面刷新（localStorage）
1. 打开终端页面，创建 2 个会话
2. 在终端中执行命令
3. 刷新浏览器页面
4. **预期**: 显示"正在恢复会话..."，然后成功恢复 2 个会话 ✅

### 场景 3：会话超时
1. 打开终端页面，创建会话
2. 等待超过超时时间（默认 1 小时）
3. 刷新页面
4. **预期**: 尝试重连，如果失败则显示警告并创建新会话

### 场景 4：清空 localStorage
1. 打开终端页面，创建会话
2. 手动清空 localStorage
3. 刷新页面
4. **预期**: 从后端获取会话列表，如果后端有会话则恢复，否则创建默认终端

### 场景 5：多标签页
1. 在标签页 A 打开终端，创建会话
2. 在标签页 B 打开同一个应用
3. 在标签页 B 刷新
4. **预期**: 标签页 B 从 localStorage 恢复会话（可能与标签页 A 不同步）

## 优势

### 1. 用户体验
- ✅ 切换菜单时终端状态完全保留
- ✅ 无需等待重连，立即可用
- ✅ 命令历史和输出完整保留
- ✅ 正在运行的命令不会中断

### 2. 性能
- ✅ 避免重复创建终端实例
- ✅ 避免重复建立 WebSocket 连接
- ✅ 减少网络请求
- ✅ 更快的页面切换

### 3. 可靠性
- ✅ 从后端获取真实的会话状态
- ✅ 避免 localStorage 和后端状态不一致
- ✅ 更好的错误处理
- ✅ 支持多标签页同步

## 注意事项

### 1. 内存管理
- keep-alive 会占用内存
- 如果用户长时间不使用终端，考虑添加自动清理机制
- 可以监听 `onDeactivated` 钩子，在一定时间后清理资源

### 2. 会话同步
- 多个标签页可能同时操作同一个会话
- 后端需要处理并发写入
- 考虑添加会话锁机制

### 3. 安全性
- 确保 token 验证正确
- 用户只能访问自己的会话
- 防止会话劫持

## 相关文件
- `frontend/src/views/Terminal.vue`: 终端组件（添加 keep-alive 支持）
- `frontend/src/views/Layout.vue`: 布局组件（添加 keep-alive）
- `frontend/src/api/index.js`: API 方法（添加会话列表接口）
- `backend/app/api/terminal.py`: 后端 API（已有会话管理）
- `backend/app/services/terminal.py`: 终端服务（已有数据库持久化）

## 未来改进
1. 添加 `onActivated` 钩子，检查 WebSocket 连接状态
2. 如果 WebSocket 断开，自动重连
3. 添加会话同步机制，支持多标签页实时更新
4. 优化内存使用，添加自动清理机制
5. 添加会话导出/导入功能
