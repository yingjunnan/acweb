# 交互式 CLI 工具支持 - 修改摘要

## 修改时间
2026-02-06

## 问题
即使适配了终端尺寸，在使用交互式 CLI 工具（如 Claude Code）时，使用方向键导航菜单界面仍然会出现格式错误。

## 修改文件

### 1. backend/app/services/terminal.py

#### 修改 1: 添加 signal 模块导入
```python
import signal
```

#### 修改 2: 增强 start() 方法中的终端属性配置
在 pty.fork() 的父进程部分添加了完整的 termios 配置：
- 配置输入模式 (ICRNL, IXON)
- 配置输出模式 (OPOST, ONLCR)
- 配置控制模式 (CS8, CREAD)
- 配置本地模式 (ISIG, ICANON, ECHO, ECHOE, ECHOK, ECHOCTL, ECHOKE, IEXTEN)

这些配置确保终端能够正确处理交互式应用的输入输出。

#### 修改 3: 在 set_winsize() 方法中添加 SIGWINCH 信号
```python
if self.child_pid:
    os.kill(self.child_pid, signal.SIGWINCH)
```

当终端尺寸改变时，发送 SIGWINCH 信号通知子进程，使交互式应用能够重新绘制界面。

#### 修改 4: 增强环境变量
添加了 TERM_PROGRAM 和 TERM_PROGRAM_VERSION 环境变量以提高兼容性。

### 2. frontend/src/views/Terminal.vue

#### 修改: 优化 createTerminal() 函数中的 xterm.js 配置
- `lineHeight: 1.0` - 从 1.2 改为 1.0，确保行高精确匹配
- `cursorWidth: 1` - 添加标准光标宽度
- `screenReaderMode: false` - 禁用屏幕阅读器模式以提高性能
- `tabStopWidth: 8` - 添加标准制表符宽度

这些配置确保前端终端模拟器能够精确渲染交互式应用的界面。

## 技术原理

### termios 配置
termios 是 POSIX 标准的终端 I/O 接口，用于控制终端的行为。正确配置 termios 对于交互式应用至关重要：

- **输入模式**: 控制如何处理输入字符（如回车转换）
- **输出模式**: 控制如何处理输出字符（如换行转换）
- **控制模式**: 控制硬件特性（如字符大小）
- **本地模式**: 控制终端的本地行为（如回显、信号处理）

### SIGWINCH 信号
SIGWINCH (Window Change) 是当终端窗口大小改变时发送的信号。交互式应用（如 vim, less, 菜单界面）会监听这个信号并重新绘制界面以适应新的窗口大小。

### xterm.js 精确配置
行高和字符间距的精确配置对于光标定位至关重要。如果行高不精确，会导致光标位置与实际字符位置不匹配，特别是在使用方向键导航时。

## 测试建议

1. **基本测试**: 运行 `./test_interactive_cli.sh` 测试基本终端功能
2. **vim 测试**: 打开 vim，使用方向键移动光标，检查光标位置是否准确
3. **less 测试**: 使用 less 查看长文件，使用方向键和 Page Up/Down 导航
4. **Claude Code 测试**: 运行 claude 命令，使用方向键在菜单中导航
5. **尺寸适配测试**: 在不同设备上打开同一会话，点击"适配尺寸"，测试交互式工具

## 预期效果

修复后，所有交互式 CLI 工具应该能够：
- ✅ 正确响应方向键、Home、End、Page Up/Down 等按键
- ✅ 正确显示菜单和 TUI 界面
- ✅ 光标定位准确无偏差
- ✅ 窗口大小变化时自动重绘
- ✅ 支持所有标准的 ANSI 转义序列
- ✅ 正确处理 Ctrl+C、Ctrl+Z 等控制信号

## 兼容性

这些修改遵循 POSIX 和 ANSI 标准，与以下工具兼容：
- 文本编辑器: vim, nano, emacs
- 分页器: less, more
- 系统监控: top, htop, iotop
- 终端复用器: tmux, screen
- 现代 CLI 工具: claude, gh, kubectl (交互模式)
- 所有使用 ncurses 或类似库的 TUI 应用

## 回滚方案

如果修改导致问题，可以通过以下方式回滚：

### 后端回滚
删除 termios 配置代码块和 SIGWINCH 信号发送代码，恢复到简单的 set_winsize 调用。

### 前端回滚
将 lineHeight 改回 1.2，删除新添加的配置项。

## 相关文档

- `INTERACTIVE_CLI_FIX.md` - 详细的修复说明
- `TERMINAL_OPTIMIZATION.md` - 之前的终端优化
- `TERMINAL_SIZE_FIX.md` - 终端尺寸修复
- `test_interactive_cli.sh` - 测试脚本
