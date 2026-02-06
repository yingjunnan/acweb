# 终端显示优化说明

## 问题描述

在 Web 终端中使用 Claude Code、vim、htop 等 CLI 工具时，可能会出现显示格式错误、混乱的情况。这通常是由于：

1. ANSI 转义序列处理不完整
2. 终端类型不匹配
3. 颜色支持不足
4. 字符编码问题
5. 渲染性能问题

## 优化措施

### 1. 增强的终端配置

#### xterm.js 配置优化
```javascript
{
  cursorBlink: true,              // 光标闪烁
  cursorStyle: 'block',           // 块状光标
  fontWeight: 'normal',           // 正常字重
  fontWeightBold: 'bold',         // 粗体字重
  lineHeight: 1.2,                // 行高
  letterSpacing: 0,               // 字符间距
  scrollback: 10000,              // 滚动缓冲区（10000行）
  allowProposedApi: true,         // 允许实验性 API
  convertEol: false,              // 不自动转换行尾
  macOptionIsMeta: true,          // Mac Option 键作为 Meta
  rightClickSelectsWord: true,    // 右键选择单词
  fastScrollModifier: 'shift',    // Shift 快速滚动
  fastScrollSensitivity: 5,       // 快速滚动灵敏度
  scrollSensitivity: 1            // 滚动灵敏度
}
```

#### 完整的颜色主题
支持 16 色 ANSI 颜色：
- 基础 8 色：black, red, green, yellow, blue, magenta, cyan, white
- 高亮 8 色：brightBlack, brightRed, brightGreen, 等

### 2. 附加组件

#### WebLinksAddon
- 自动识别并高亮 URL
- 点击 URL 可以在新标签页打开
- 支持 http、https、ftp 等协议

#### WebglAddon
- 使用 WebGL 渲染，性能更好
- 减少 CPU 占用
- 更流畅的滚动和刷新
- 自动降级到 Canvas 渲染（如果 WebGL 不可用）

### 3. 环境变量设置

后端设置正确的终端环境变量：

```python
os.environ['TERM'] = 'xterm-256color'      # 256 色支持
os.environ['COLORTERM'] = 'truecolor'      # 真彩色支持
os.environ['LANG'] = 'en_US.UTF-8'         # UTF-8 编码
os.environ['LC_ALL'] = 'en_US.UTF-8'       # 全局 UTF-8
```

## 支持的功能

### ✅ 完全支持
- 基本文本输入输出
- ANSI 颜色（16 色 + 256 色）
- 光标移动和定位
- 清屏和滚动
- 粗体、斜体、下划线
- 反色显示
- UTF-8 字符（包括中文、emoji）
- URL 自动识别和点击

### ⚠️ 部分支持
- 复杂的 TUI 应用（如 vim、nano）
- 鼠标事件（部分支持）
- 窗口大小调整（支持）
- 剪贴板操作（浏览器限制）

### ❌ 不支持
- 图形界面（GUI）
- 音频输出
- 文件拖放（可能在未来支持）

## 常见问题和解决方案

### 问题 1: 颜色显示不正确
**原因**: 终端类型不匹配或颜色主题配置错误

**解决方案**:
1. 确保后端设置了 `TERM=xterm-256color`
2. 检查前端颜色主题配置是否完整
3. 某些应用可能需要手动设置颜色：
   ```bash
   export TERM=xterm-256color
   ```

### 问题 2: vim/nano 显示混乱
**原因**: 复杂的 TUI 应用需要完整的终端模拟

**解决方案**:
1. 使用简化的编辑器：`nano -m` 或 `vi`
2. 或者使用命令行编辑：`sed`, `awk`, `cat > file`
3. 对于复杂编辑，建议使用本地编辑器

### 问题 3: 中文或 emoji 显示异常
**原因**: 字符编码或字体问题

**解决方案**:
1. 确保后端设置了 UTF-8 编码
2. 使用支持 Unicode 的字体
3. 检查浏览器字体设置

### 问题 4: Claude Code 等 AI 工具显示问题
**原因**: 这些工具使用复杂的 ANSI 转义序列和动态更新

**解决方案**:
1. 确保使用最新版本的 xterm.js
2. 启用 WebGL 渲染以提高性能
3. 增加滚动缓冲区大小（已设置为 10000 行）
4. 如果仍有问题，可以尝试：
   ```bash
   # 禁用某些特效
   export TERM=xterm
   # 或使用简化模式
   claude --no-color
   ```

### 问题 5: 性能问题（卡顿、延迟）
**原因**: 大量输出或复杂渲染

**解决方案**:
1. WebGL 渲染已启用，性能应该较好
2. 减少不必要的输出：
   ```bash
   command | head -n 100  # 只显示前100行
   command > file.log     # 输出到文件
   ```
3. 使用分页工具：
   ```bash
   command | less
   command | more
   ```

## 最佳实践

### 1. 使用 Claude Code
```bash
# 设置正确的终端类型
export TERM=xterm-256color

# 如果显示有问题，尝试禁用颜色
claude --no-color

# 或使用简化输出
claude --simple
```

### 2. 编辑文件
```bash
# 推荐使用简单编辑器
nano -m filename

# 或使用命令行工具
cat > filename << EOF
content here
EOF

# 或使用 sed 进行编辑
sed -i 's/old/new/g' filename
```

### 3. 查看日志
```bash
# 使用分页工具
tail -f log.txt | less

# 或限制输出行数
tail -n 100 log.txt

# 使用 grep 过滤
tail -f log.txt | grep ERROR
```

### 4. 运行交互式程序
```bash
# 对于简单的交互式程序，直接运行即可
python script.py

# 对于复杂的 TUI 程序，考虑使用 tmux
tmux new -s mysession
# 然后在 tmux 中运行程序
```

## 技术细节

### xterm.js 版本
- 使用 xterm.js 5.3.0
- 支持最新的 ANSI 标准
- 完整的 UTF-8 支持

### 渲染引擎
1. **WebGL 渲染器**（优先）
   - 使用 GPU 加速
   - 性能最佳
   - 自动降级

2. **Canvas 渲染器**（降级）
   - 使用 Canvas 2D API
   - 兼容性好
   - 性能略低

### 字符编码
- 前端：UTF-8
- 后端：UTF-8
- 终端：UTF-8
- 确保全链路 UTF-8 编码

## 未来改进

1. **鼠标支持增强**: 更好的鼠标事件处理
2. **剪贴板集成**: 更好的复制粘贴体验
3. **文件传输**: 支持拖放上传文件
4. **图像显示**: 支持 Sixel 或 iTerm2 图像协议
5. **性能优化**: 进一步优化大量输出的性能

## 参考资源

- [xterm.js 官方文档](https://xtermjs.org/)
- [ANSI 转义序列](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [终端颜色标准](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors)
