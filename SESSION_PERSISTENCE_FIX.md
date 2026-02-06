# 终端会话持久化修复

## 问题描述
当用户在终端页面创建会话后，切换到其他菜单（如 Dashboard 或 Settings），再切换回终端页面时：
- 显示"正在恢复会话..."提示
- 但实际上会话恢复失败
- 终端内容丢失，需要重新创建

## 根本原因

### 1. 组件生命周期问题
- Vue Router 默认会销毁不活跃的路由组件
- 当切换菜单时，Terminal 组件被卸载（unmounted）
- 组件卸载时，xterm.js 终端实例被销毁
- WebSocket 连接也被关闭
- 只有会话 ID 和名称保存在 localStorage 中

### 2. 重连失败
- 组件重新挂载时，尝试从 localStorage 恢复会话
- 但后端的会话可能已经超时或不存在
- 前端没有调用后端 API 验证会话是否还活跃
- 导致重连失败，但用户看到"正在恢复会话..."的误导信息

## 解决方案

### 1. 使用 keep-alive 缓存组件
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

### 2. 添加后端会话列表 API
前端调用后端 API 获取活跃会话列表，而不是只依赖 localStorage。

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

### 3. 优化 onMounted 逻辑
组件挂载时，先检查是否有缓存的终端实例，如果有则直接使用，无需重新创建。

```javascript
onMounted(async () => {
  await configStore.loadConfig()
  
  // 检查是否有已存在的终端实例（keep-alive 缓存）
  const hasExistingTerminals = Object.keys(terminalStore.terminals).length > 0
  
  if (hasExistingTerminals) {
    // 有已存在的终端实例，无需重新创建
    console.log('Terminal component activated from cache')
    return
  }
  
  // 首次加载，从后端获取活跃会话列表
  try {
    const response = await terminalApi.getSessions()
    const activeSessions = response.data.sessions || []
    
    if (activeSessions.length > 0) {
      // 恢复活跃会话
      // ...
    } else {
      // 创建默认终端
      addSession('默认终端')
    }
  } catch (error) {
    // 错误处理
  }
})
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
调用 terminalApi.getSessions()
  ↓
后端返回活跃会话列表
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

### 场景 1：正常切换
1. 打开终端页面，创建 2 个会话
2. 在终端中执行一些命令
3. 切换到 Dashboard
4. 切换回终端页面
5. **预期**: 终端立即显示，内容完整，无需重连

### 场景 2：页面刷新
1. 打开终端页面，创建会话
2. 刷新浏览器页面
3. **预期**: 从后端恢复会话，显示"正在恢复会话..."，然后成功恢复

### 场景 3：会话超时
1. 打开终端页面，创建会话
2. 等待超过超时时间（默认 1 小时）
3. 刷新页面
4. **预期**: 后端返回空会话列表，创建新的默认终端

### 场景 4：多标签页
1. 在标签页 A 打开终端
2. 在标签页 B 打开同一个应用
3. 在标签页 A 创建会话
4. 在标签页 B 刷新
5. **预期**: 标签页 B 可以看到标签页 A 创建的会话

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
