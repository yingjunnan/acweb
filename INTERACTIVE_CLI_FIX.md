# 交互式 CLI 工具支持修复

## 问题描述
在使用交互式 CLI 工具（如 Claude Code）时，即使适配了终端尺寸，使用方向键导航菜单界面时仍然会出现格式错误。同时，浏览器控制台显示 xterm.js 解析错误，特别是在渲染 box-drawing 字符（如 `─`, `│`, `┌`, `┐` 等）时。

## 根本原因
1. **终端属性配置不完整**：pty 没有正确配置终端属性（termios），导致交互式应用无法正确处理输入/输出
2. **缺少窗口大小变化信号**：调整终端尺寸时没有发送 SIGWINCH 信号，交互式应用无法感知窗口大小变化
3. **前端终端配置不够精确**：xterm.js 的行高和其他参数设置不够精确，导致光标定位偏差
4. **缺少 Unicode 支持**：xterm.js 默认不支持 Unicode 11，导致 box-drawing 字符和其他特殊字符无法正确渲染

## 解决方案

### 后端修改 (backend/app/services/terminal.py)

#### 1. 增强终端属性配置
在 `start()` 方法中添加了完整的 termios 配置：

```python
# 配置终端属性以支持交互式应用
attrs = termios.tcgetattr(self.fd)

# 输入模式：启用 CR->NL 转换和流控制
attrs[0] = termios.ICRNL | termios.IXON

# 输出模式：启用输出处理和 NL->CR-NL 转换
attrs[1] = termios.OPOST | termios.ONLCR

# 控制模式：8位字符，启用接收
attrs[2] = termios.CS8 | termios.CREAD

# 本地模式：启用信号、规范模式、回显等
attrs[3] = (termios.ISIG | termios.ICANON | termios.ECHO | 
           termios.ECHOE | termios.ECHOK | termios.ECHOCTL | 
           termios.ECHOKE | termios.IEXTEN)

termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
```

这些设置确保：
- 正确处理回车和换行
- 启用信号处理（Ctrl+C, Ctrl+Z 等）
- 正确回显用户输入
- 支持扩展的终端功能

#### 2. 添加 SIGWINCH 信号支持
在 `set_winsize()` 方法中添加了 SIGWINCH 信号发送：

```python
# 发送 SIGWINCH 信号通知子进程窗口大小改变
if self.child_pid:
    os.kill(self.child_pid, signal.SIGWINCH)
```

这确保当终端尺寸改变时，运行中的交互式应用（如 vim, less, 菜单界面）能够立即感知并重新绘制界面。

#### 3. 增强环境变量
添加了额外的环境变量以提高兼容性：

```python
os.environ['TERM_PROGRAM'] = 'xterm'
os.environ['TERM_PROGRAM_VERSION'] = '1.0'
```

### 前端修改 (frontend/src/views/Terminal.vue)

#### 1. 安装 Unicode 11 Addon
```bash
npm install @xterm/addon-unicode11
```

#### 2. 导入 Unicode Addon
```javascript
import { Unicode11Addon } from '@xterm/addon-unicode11'
```

#### 3. 加载并激活 Unicode 11 支持
```javascript
const unicode11Addon = new Unicode11Addon()
term.loadAddon(unicode11Addon)
term.unicode.activeVersion = '11'
```

这确保终端能够正确渲染：
- Box-drawing 字符（`─`, `│`, `┌`, `┐`, `└`, `┘`, `├`, `┤`, `┬`, `┴`, `┼` 等）
- 其他 Unicode 字符（emoji, 特殊符号等）
- 双宽字符（中文、日文、韩文等）

#### 4. 优化行高设置
将 `lineHeight` 从 1.2 改为 1.0，确保行高精确匹配字符高度，避免光标定位偏差。

#### 5. 添加精确的终端配置
```javascript
lineHeight: 1.0,           // 精确的行高
cursorWidth: 1,            // 标准光标宽度
screenReaderMode: false,   // 禁用屏幕阅读器模式以提高性能
tabStopWidth: 8,           // 标准制表符宽度
logLevel: 'off'            // 关闭日志以避免控制台警告
```

## 技术细节

### termios 标志说明

**输入模式 (iflag):**
- `ICRNL`: 将输入的回车符 (CR) 转换为换行符 (NL)
- `IXON`: 启用 XON/XOFF 流控制

**输出模式 (oflag):**
- `OPOST`: 启用输出后处理
- `ONLCR`: 将输出的换行符 (NL) 转换为回车换行 (CR-NL)

**控制模式 (cflag):**
- `CS8`: 8位字符大小
- `CREAD`: 启用接收器

**本地模式 (lflag):**
- `ISIG`: 启用信号生成（INTR, QUIT, SUSP）
- `ICANON`: 启用规范输入模式（行编辑）
- `ECHO`: 回显输入字符
- `ECHOE`: 回显擦除字符为退格-空格-退格
- `ECHOK`: 回显 KILL 字符
- `ECHOCTL`: 回显控制字符为 ^X
- `ECHOKE`: 回显 KILL 字符并擦除行
- `IEXTEN`: 启用扩展处理

### SIGWINCH 信号
SIGWINCH (Window Change) 是一个 POSIX 信号，当终端窗口大小改变时发送给前台进程组。交互式应用（如 vim, less, top, 菜单界面等）会监听这个信号并重新绘制界面以适应新的窗口大小。

## 测试方法

### 1. 测试基本交互式工具
```bash
# 测试 vim
vim test.txt

# 测试 less
less /var/log/system.log

# 测试 top
top
```

### 2. 测试 Claude Code
```bash
# 启动 Claude Code
claude

# 使用方向键导航菜单
# 检查是否有格式错误或光标错位
```

### 3. 测试终端尺寸适配
1. 在一个设备上创建终端会话
2. 在另一个设备上登录并打开同一会话
3. 点击"适配尺寸"按钮
4. 运行交互式工具，检查显示是否正常

### 4. 测试窗口大小变化
1. 打开一个交互式工具（如 vim）
2. 调整浏览器窗口大小
3. 检查工具界面是否正确重绘

## 预期效果

修复后，交互式 CLI 工具应该能够：
1. ✅ 正确响应方向键导航
2. ✅ 正确显示菜单和界面元素
3. ✅ 光标定位准确
4. ✅ 窗口大小变化时正确重绘
5. ✅ 支持所有标准的终端控制序列
6. ✅ 正确处理 Ctrl+C, Ctrl+Z 等信号
7. ✅ 正确渲染 box-drawing 字符和 Unicode 字符
8. ✅ 不再出现 xterm.js 解析错误

## 解决的具体问题

### 1. xterm.js 解析错误
**错误信息:**
```
xterm.js: Parsing error: {position: 0, code: 9472, currentState: 3, ...}
```

**原因:** code 9472 是 Unicode box-drawing 字符 `─`，xterm.js 默认不支持 Unicode 11

**解决:** 安装并激活 Unicode11Addon，设置 `term.unicode.activeVersion = '11'`

### 2. 菜单界面格式错误
**现象:** 使用方向键导航时，菜单边框和布局错乱

**原因:** 
- Box-drawing 字符无法正确渲染
- 终端尺寸不匹配
- 缺少 SIGWINCH 信号

**解决:** 
- Unicode 11 支持 + termios 配置 + SIGWINCH 信号

## 兼容性

这些修改遵循 POSIX 标准，应该与所有标准的交互式 CLI 工具兼容，包括：
- vim, nano, emacs
- less, more
- top, htop
- tmux, screen
- 各种 TUI (Text User Interface) 应用
- Claude Code 等现代 CLI 工具

## 注意事项

1. **性能影响**：termios 配置和 SIGWINCH 信号处理对性能影响极小
2. **向后兼容**：这些修改不会影响非交互式命令的执行
3. **错误处理**：所有新增的配置都有适当的错误处理，即使失败也不会影响基本功能

## 相关文件

- `backend/app/services/terminal.py` - 后端终端服务
- `frontend/src/views/Terminal.vue` - 前端终端组件
- `TERMINAL_OPTIMIZATION.md` - 之前的终端优化文档
- `TERMINAL_SIZE_FIX.md` - 终端尺寸修复文档
