# 数据库持久化说明

## 概述

系统现在使用 SQLite 数据库来持久化终端会话信息，解决了刷新页面导致重连失败的问题。

## 数据库架构

### 表结构: terminal_sessions

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String (PK) | 会话唯一标识 |
| username | String | 用户名（索引） |
| name | String | 会话名称 |
| buffer | Text | 终端输出缓存 |
| last_activity | Float | 最后活动时间（时间戳） |
| created_at | Float | 创建时间（时间戳） |
| is_active | Boolean | 是否活跃 |
| pid | Integer | 进程ID |
| cwd | String | 工作目录 |

## 工作流程

### 1. 创建会话
```
用户创建终端
    ↓
生成唯一 session_id
    ↓
启动 pty 进程
    ↓
保存到数据库（id, username, name, pid, cwd）
    ↓
保存到内存（TerminalManager）
```

### 2. 会话活动
```
用户输入/输出
    ↓
更新 last_activity
    ↓
缓存输出到内存
    ↓
定期保存 buffer 到数据库
```

### 3. 刷新页面重连
```
页面加载
    ↓
从 localStorage 读取会话列表
    ↓
尝试重连每个会话
    ↓
查询数据库（by id + username）
    ↓
检查是否超时
    ↓
返回缓存的 buffer
    ↓
恢复终端显示
```

### 4. 会话关闭
```
用户关闭会话
    ↓
标记 is_active = False
    ↓
关闭 pty 进程
    ↓
从内存中移除
```

## 优势

### 1. 可靠性
- **数据持久化**: 会话信息保存在数据库中，不会因为刷新页面丢失
- **断线重连**: 即使 WebSocket 断开，也能从数据库恢复
- **服务器重启**: 服务器重启后，数据库中的会话信息仍然存在

### 2. 性能
- **双层缓存**: 内存 + 数据库，读取快速
- **异步保存**: 不阻塞终端输出
- **SQLite**: 轻量级，无需额外配置

### 3. 多用户支持
- **用户隔离**: 每个用户只能看到自己的会话
- **会话管理**: 支持列出用户的所有会话
- **权限控制**: 基于 JWT token 验证

## 数据流

### 写入流程
```
终端输出
    ↓
内存缓存（buffer 数组）
    ↓
定期批量写入数据库
    ↓
SQLite 文件（terminal_sessions.db）
```

### 读取流程
```
重连请求
    ↓
查询数据库
    ↓
读取 buffer 字段
    ↓
返回给前端
    ↓
恢复终端显示
```

## 配置

### 数据库文件位置
```
backend/terminal_sessions.db
```

### 缓存策略
- **内存缓存**: 最近 N 行（可配置，默认 1000 行）
- **数据库缓存**: 完整的输出历史
- **更新频率**: 每次有新输出时更新

### 超时清理
- **会话超时**: 默认 1 小时（可配置）
- **自动清理**: 定期清理超时的会话
- **标记失效**: 超时会话标记为 is_active = False

## API 变更

### WebSocket 连接
```
ws://localhost:8000/api/v1/terminal/ws/{session_id}
  ?token={jwt_token}
  &cwd={working_directory}
  &reconnect={true|false}
  &name={session_name}
```

新增参数:
- `name`: 会话名称（用于数据库记录）

### 列出会话
```
GET /api/v1/terminal/sessions?token={jwt_token}
```

返回当前用户的所有活跃会话

## 使用示例

### 场景 1: 正常使用
```
1. 用户登录
2. 创建终端 "开发环境"
3. 执行命令
4. 关闭浏览器
5. 重新打开（1小时内）
6. 自动重连，看到之前的输出
```

### 场景 2: 多会话
```
1. 创建会话 "前端开发"
2. 创建会话 "后端开发"
3. 创建会话 "数据库"
4. 刷新页面
5. 所有会话自动恢复
```

### 场景 3: 超时处理
```
1. 创建会话
2. 离开 2 小时
3. 返回尝试重连
4. 提示 "会话已超时"
5. 自动创建新会话
```

## 故障排查

### 问题 1: 重连失败
**检查**:
1. 数据库文件是否存在
2. 会话是否超时
3. 用户名是否匹配
4. JWT token 是否有效

**解决**:
```bash
# 查看数据库
sqlite3 terminal_sessions.db
SELECT * FROM terminal_sessions WHERE username='admin';
```

### 问题 2: 数据库损坏
**解决**:
```bash
# 备份数据库
cp terminal_sessions.db terminal_sessions.db.bak

# 重建数据库
rm terminal_sessions.db
# 重启服务，自动创建新数据库
```

### 问题 3: 性能问题
**优化**:
1. 定期清理旧会话
2. 限制 buffer 大小
3. 使用索引（已自动创建）

## 维护

### 数据库备份
```bash
# 定期备份
cp terminal_sessions.db backups/terminal_sessions_$(date +%Y%m%d).db

# 自动备份脚本
0 2 * * * cp /path/to/terminal_sessions.db /path/to/backups/terminal_sessions_$(date +\%Y\%m\%d).db
```

### 清理旧数据
```python
# 清理 7 天前的不活跃会话
import time
from app.db.database import SessionLocal
from app.db.models import TerminalSessionDB

db = SessionLocal()
cutoff = time.time() - (7 * 24 * 3600)

db.query(TerminalSessionDB).filter(
    TerminalSessionDB.is_active == False,
    TerminalSessionDB.last_activity < cutoff
).delete()

db.commit()
```

### 数据库迁移
如果需要迁移到 PostgreSQL 或 MySQL:

1. 修改 `database.py` 中的连接字符串
2. 安装相应的驱动（psycopg2 或 pymysql）
3. 重新初始化数据库

## 安全考虑

### 1. 数据隔离
- 每个用户只能访问自己的会话
- 基于 JWT token 验证身份
- 数据库查询包含 username 过滤

### 2. 敏感信息
- 不保存用户输入的密码
- buffer 可能包含敏感信息，注意权限
- 定期清理不活跃的会话

### 3. 文件权限
```bash
# 设置数据库文件权限
chmod 600 terminal_sessions.db
chown app_user:app_group terminal_sessions.db
```

## 未来改进

1. **压缩存储**: 对 buffer 进行压缩，节省空间
2. **分页加载**: 大量输出时分页加载
3. **搜索功能**: 在历史输出中搜索
4. **导出功能**: 导出会话历史到文件
5. **会话共享**: 支持多用户共享同一会话（只读）
