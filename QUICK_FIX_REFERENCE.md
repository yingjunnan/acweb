# 快速修复参考

## 问题
Claude Code 等交互式 CLI 工具使用方向键时格式错误，浏览器控制台显示 xterm.js 解析错误。

## 快速解决方案

### 1. 安装依赖（前端）
```bash
cd frontend
npm install @xterm/addon-unicode11
```

### 2. 重启服务
```bash
# 停止当前服务（Ctrl+C）
# 重新启动
./start.sh
```

## 验证修复

### 测试 1: 检查控制台
打开浏览器开发者工具，应该**没有** xterm.js 解析错误。

### 测试 2: 测试 Box-Drawing
在终端中运行：
```bash
echo "┌─────┐"
echo "│ OK! │"
echo "└─────┘"
```
应该显示完整的方框。

### 测试 3: 测试 Claude Code
```bash
claude
```
使用方向键导航菜单，应该没有格式错误。

## 修改的文件

### 后端
- `backend/app/services/terminal.py`
  - 添加 termios 配置
  - 添加 SIGWINCH 信号

### 前端
- `frontend/package.json`
  - 添加 @xterm/addon-unicode11
- `frontend/src/views/Terminal.vue`
  - 导入并激活 Unicode11Addon
  - 优化终端配置

## 关键代码片段

### 后端 - termios 配置
```python
attrs = termios.tcgetattr(self.fd)
attrs[0] = termios.ICRNL | termios.IXON
attrs[1] = termios.OPOST | termios.ONLCR
attrs[2] = termios.CS8 | termios.CREAD
attrs[3] = (termios.ISIG | termios.ICANON | termios.ECHO | 
           termios.ECHOE | termios.ECHOK | termios.ECHOCTL | 
           termios.ECHOKE | termios.IEXTEN)
termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
```

### 后端 - SIGWINCH 信号
```python
if self.child_pid:
    os.kill(self.child_pid, signal.SIGWINCH)
```

### 前端 - Unicode 支持
```javascript
import { Unicode11Addon } from '@xterm/addon-unicode11'

const unicode11Addon = new Unicode11Addon()
term.loadAddon(unicode11Addon)
term.unicode.activeVersion = '11'
```

### 前端 - 优化配置
```javascript
lineHeight: 1.0,
cursorWidth: 1,
screenReaderMode: false,
tabStopWidth: 8,
logLevel: 'off'
```

## 常见问题

### Q: 还是有解析错误？
A: 确保：
1. npm install 成功
2. 服务已重启
3. 浏览器已刷新（Ctrl+Shift+R 强制刷新）

### Q: 方向键还是不工作？
A: 检查：
1. 后端服务是否重启
2. termios 配置是否生效（查看后端日志）
3. 终端尺寸是否适配

### Q: 跨设备还是有问题？
A: 点击"适配尺寸"按钮，将终端调整到保存的尺寸。

## 详细文档

- `FINAL_FIX_SUMMARY.md` - 完整修复总结
- `INTERACTIVE_CLI_FIX.md` - 交互式 CLI 修复详解
- `UNICODE_FIX.md` - Unicode 支持详解
- `TESTING_GUIDE.md` - 完整测试指南

## 成功标志

- ✅ 无控制台错误
- ✅ Box-drawing 字符正常
- ✅ 方向键导航正常
- ✅ 窗口调整自动适应
- ✅ 跨设备会话正常

## 需要帮助？

查看详细文档或检查：
1. 浏览器控制台错误
2. 后端日志输出
3. 网络请求状态
