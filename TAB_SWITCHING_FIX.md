# 终端标签页切换内容丢失问题修复

## 问题描述
在多个终端标签页之间来回切换时，终端显示的内容会逐渐减少，好像每次切换都会删除几行输出。

## 根本原因
1. **终端实例管理问题**: 虽然使用了 `:force-render="true"` 保持所有标签页渲染，但在某些情况下终端实例可能被重复操作
2. **fit() 调用时机**: 在标签页切换时调用 `fitAddon.fit()` 可能在 DOM 还未完全稳定时执行，导致计算错误
3. **缺少错误处理**: fit() 调用失败时没有捕获异常，可能导致后续操作中断

## 修复方案

### 1. 增强 watch 函数的安全性
```javascript
// 修复前
watch(() => terminalStore.activeSession, async (newSessionId) => {
  if (newSessionId) {
    await nextTick()
    const terminal = terminalStore.terminals[newSessionId]
    if (terminal) {
      setTimeout(() => {
        terminal.fitAddon.fit()
      }, 100)
    }
  }
})

// 修复后
watch(() => terminalStore.activeSession, async (newSessionId) => {
  if (newSessionId && terminalStore.terminals[newSessionId]) {
    await nextTick()
    // 延迟调整尺寸，确保标签页切换动画完成
    setTimeout(() => {
      try {
        const terminal = terminalStore.terminals[newSessionId]
        if (terminal && terminal.fitAddon) {
          terminal.fitAddon.fit()
        }
      } catch (e) {
        console.warn('Failed to fit terminal on tab switch:', e)
      }
    }, 150)
  }
})
```

**改进点**:
- 增加了终端实例存在性检查: `terminalStore.terminals[newSessionId]`
- 在 setTimeout 内部再次检查 terminal 和 fitAddon 是否存在
- 添加 try-catch 错误处理，防止 fit() 失败影响其他操作
- 延迟时间从 100ms 增加到 150ms，确保标签页切换动画完成

### 2. 为所有 fit() 调用添加错误处理

在 `addSession` 函数中:
```javascript
setTimeout(() => {
  try {
    fitAddon.fit()
  } catch (e) {
    console.warn('Failed to fit terminal:', e)
  }
}, 100)

const resizeObserver = new ResizeObserver(() => {
  try {
    fitAddon.fit()
  } catch (e) {
    console.warn('Failed to fit terminal on resize:', e)
  }
})
```

在 `onMounted` 函数中:
```javascript
setTimeout(() => {
  try {
    fitAddon.fit()
  } catch (e) {
    console.warn('Failed to fit terminal on mount:', e)
  }
}, 100)

const resizeObserver = new ResizeObserver(() => {
  try {
    fitAddon.fit()
  } catch (e) {
    console.warn('Failed to fit terminal on resize:', e)
  }
})
```

### 3. 保持终端实例的唯一性
代码中已经有检查 `!terminalStore.terminals[sessionId]`，确保每个会话只创建一次终端实例。配合 `:force-render="true"`，所有标签页的 DOM 都会保持渲染状态，终端实例不会被销毁和重建。

## 测试建议
1. 创建 3-5 个终端会话
2. 在每个终端中执行一些命令，产生输出
3. 快速在标签页之间来回切换 10-20 次
4. 验证每个终端的内容是否完整保留
5. 检查浏览器控制台是否有错误信息

## 技术要点
- **`:force-render="true"`**: 确保所有标签页的 DOM 始终渲染，不会被销毁
- **终端实例缓存**: 通过 `terminalStore.terminals` 缓存所有终端实例
- **延迟 fit()**: 给 DOM 足够时间完成渲染和动画
- **错误处理**: 防止单个 fit() 失败影响整体功能
- **双重检查**: 在操作前检查对象是否存在，避免空指针错误

## 相关文件
- `frontend/src/views/Terminal.vue`: 主要修复文件
- `frontend/src/stores/terminal.js`: 终端状态管理
