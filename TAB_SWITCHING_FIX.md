# 终端标签页切换内容丢失问题修复（第二版）

## 问题描述
在多个终端标签页之间来回切换时，终端显示的内容会逐渐减少，好像每次切换都会删除几行输出。

## 根本原因分析

### 核心问题：fitAddon.fit() 在不可见容器上调用
当调用 `fitAddon.fit()` 时，它会根据容器的实际尺寸重新计算终端的行列数（cols/rows）。

**问题场景**：
1. 用户切换到标签页 B
2. 标签页 A 的容器变为不可见或尺寸为 0
3. 如果此时对标签页 A 调用 `fit()`，容器尺寸为 0 或很小
4. 终端被调整为极小的尺寸（如 1 行 × 10 列）
5. 超出新尺寸的内容被截断丢失
6. 即使切换回标签页 A，内容已经永久丢失

### 为什么会触发 fit()？
- **标签页切换时的 watch**: 切换标签页时主动调用 fit()
- **ResizeObserver**: 容器尺寸变化时自动调用 fit()
- **问题**: 这些调用没有检查容器是否真正可见

## 修复方案

### 1. 在 watch 中检查容器可见性和尺寸
```javascript
watch(() => terminalStore.activeSession, async (newSessionId) => {
  if (newSessionId && terminalStore.terminals[newSessionId]) {
    await nextTick()
    setTimeout(() => {
      try {
        const terminal = terminalStore.terminals[newSessionId]
        const container = terminalStore.terminalRefs[newSessionId]
        
        // 关键：只有当容器可见且有实际尺寸时才调整
        if (terminal && terminal.fitAddon && container) {
          const rect = container.getBoundingClientRect()
          if (rect.width > 0 && rect.height > 0) {
            terminal.fitAddon.fit()
          }
        }
      } catch (e) {
        console.warn('Failed to fit terminal on tab switch:', e)
      }
    }, 200)
  }
})
```

**改进点**：
- 使用 `getBoundingClientRect()` 检查容器实际尺寸
- 只有当 `width > 0 && height > 0` 时才调用 fit()
- 延迟增加到 200ms，确保标签页切换动画完成

### 2. 在 ResizeObserver 中检查尺寸
```javascript
const resizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    // 检查容器是否可见且有实际尺寸
    if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
      try {
        fitAddon.fit()
      } catch (e) {
        console.warn('Failed to fit terminal on resize:', e)
      }
    }
  }
})
```

**改进点**：
- 使用 `entry.contentRect` 检查实际内容尺寸
- 只有当尺寸大于 0 时才调用 fit()
- 避免在容器隐藏时调整终端尺寸

### 3. 在初始化时检查容器尺寸
在 `addSession` 和 `onMounted` 中：
```javascript
setTimeout(() => {
  try {
    const rect = container.getBoundingClientRect()
    if (rect.width > 0 && rect.height > 0) {
      fitAddon.fit()
    }
  } catch (e) {
    console.warn('Failed to fit terminal:', e)
  }
}, 100)
```

### 4. 清理 ResizeObserver
在 `removeSession` 中添加清理逻辑：
```javascript
if (terminal.resizeObserver) {
  terminal.resizeObserver.disconnect()
}
```

## 技术要点

### getBoundingClientRect() vs contentRect
- **getBoundingClientRect()**: 返回元素相对于视口的位置和尺寸
- **contentRect**: ResizeObserver 提供的内容区域尺寸
- 两者都可以用来判断容器是否可见

### 为什么需要延迟？
- 标签页切换有动画效果（通常 150-200ms）
- DOM 更新需要时间
- 延迟确保容器已经完全渲染且可见

### :force-render="true" 的作用
- 保持所有标签页的 DOM 始终渲染
- 避免标签页切换时重新创建终端实例
- 但不能阻止 fit() 在隐藏容器上调用

## 测试建议

### 基础测试
1. 创建 3 个终端会话
2. 在每个终端执行：`seq 1 100`（输出 100 行）
3. 快速切换标签页 20 次
4. 检查每个终端是否仍有 100 行输出

### 压力测试
1. 创建 5 个终端会话
2. 在每个终端执行：`cat /var/log/system.log`（大量输出）
3. 疯狂快速切换标签页
4. 检查内容是否完整

### 调试方法
在浏览器控制台执行：
```javascript
// 查看当前活动终端的尺寸
const activeId = terminalStore.activeSession
const terminal = terminalStore.terminals[activeId]
console.log('Cols:', terminal.term.cols, 'Rows:', terminal.term.rows)

// 查看容器尺寸
const container = terminalStore.terminalRefs[activeId]
const rect = container.getBoundingClientRect()
console.log('Container:', rect.width, 'x', rect.height)
```

## 相关文件
- `frontend/src/views/Terminal.vue`: 主要修复文件
- `frontend/src/stores/terminal.js`: 终端状态管理

## 修复版本
- 第一版：添加错误处理和延迟（未解决根本问题）
- 第二版：检查容器可见性和尺寸（彻底解决问题）
