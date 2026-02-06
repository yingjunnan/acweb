# Web 终端系统

一个功能强大的 Web 终端管理系统，支持多用户、多会话、跨设备访问和后台持续运行。

## ✨ 核心特性

### 🔐 认证与安全
- **JWT 认证** - 安全的 Token 认证机制
- **用户隔离** - 每个用户只能访问自己的会话
- **密码加密** - 使用 bcrypt 加密存储密码

### 📱 会话管理
- **多会话支持** - 创建、命名、切换多个终端会话
- **会话持久化** - 所有会话数据保存到 SQLite 数据库
- **会话超时控制** - 可配置超时时间（默认 7 天）
- **唯一命名验证** - 实时检查会话名称是否重复

### ⚡ 后台运行
- **独立后台线程** - 会话在服务端独立运行，不依赖客户端连接
- **长时间任务支持** - 支持几十小时的后台任务执行
- **自动保存** - 每 5 秒自动保存输出到数据库
- **完整输出缓存** - 重连时恢复所有历史输出

### 🌐 多客户端协作
- **实时同步** - 多个客户端同时连接同一会话，实时同步输出
- **独立追踪** - 每个客户端独立追踪读取位置
- **客户端计数** - 实时显示连接的客户端数量
- **跨设备访问** - 在任何设备上访问相同的会话

### 🔄 网络可靠性
- **自动重连** - 网络断开后自动重连（最多 5 次）
- **心跳机制** - 每 30 秒发送心跳保持连接
- **断线恢复** - 重连后自动恢复完整历史输出
- **WebSocket 优化** - 高效的双向通信

### 🎨 终端体验
- **全屏模式** - 一键全屏，ESC 退出
- **交互式 CLI 完美支持** - vim, nano, htop, less, tmux, Claude Code 等
- **Unicode 11 支持** - 正确渲染 box-drawing 字符和特殊符号
- **WebGL 加速** - 使用 WebGL 渲染提升性能
- **主题切换** - 支持深色/浅色主题
- **字体大小调整** - 10-24px 可调

### 📊 系统监控
- **实时系统信息** - CPU、内存、磁盘、网络使用情况
- **自动刷新** - 可配置刷新间隔（1-30 秒）
- **运行时间统计** - 显示系统运行时间
- **资源使用可视化** - 进度条和图表展示

### ⚙️ 配置管理
- **终端配置** - 字体大小、主题、默认路径、Shell 类型
- **会话配置** - 超时时间、缓存行数
- **系统配置** - 刷新间隔
- **实时生效** - 配置更改立即生效

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 启动服务

```bash
# 使用启动脚本（推荐）
chmod +x start.sh
./start.sh

# 或分别启动
# 后端
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm run dev
```

### 访问系统

- **前端界面：** http://localhost:5173
- **后端 API：** http://localhost:8000
- **API 文档：** http://localhost:8000/docs

### 默认账号

- **用户名：** `admin`
- **密码：** `admin123`

> ⚠️ **安全提示：** 生产环境请立即修改默认密码！

## 📚 技术栈

**后端:**
- FastAPI (Python 3.11+)
- SQLAlchemy + SQLite
- WebSocket + PTY

**前端:**
- Vue 3 + Vite
- Ant Design Vue
- xterm.js + Pinia

## 📖 文档

详细文档请查看 [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)

包含内容：
- 完整功能说明
- API 接口文档
- 架构设计
- 配置说明
- 故障排查
- 部署指南

## 🎯 使用场景

### 长时间任务
```bash
# 启动编译任务（需要几小时）
./build.sh

# 关闭浏览器，任务继续运行
# 随时重新连接查看进度
```

### 多人协作
```bash
# 用户 A: 启动调试会话
tail -f /var/log/app.log

# 用户 B: 连接同一会话
# 两人同时看到相同的日志
```

### 跨设备工作
```bash
# 办公室: 启动开发服务器
npm run dev

# 回家后: 在家里电脑上继续工作
# 无缝切换，完整历史
```

## 🔧 配置

编辑 `backend/terminal_config.json`:

```json
{
  "session_timeout": 604800,  // 会话超时（秒），默认 7 天
  "buffer_size": 5000,         // 缓存行数，默认 5000 行
  "font_size": 14,             // 字体大小
  "theme": "dark",             // 主题：dark/light
  "default_path": "~",         // 默认工作目录
  "refresh_interval": 3        // 仪表盘刷新间隔（秒）
}
```

**配置说明：**
- `session_timeout`: 会话在无活动后保持的时间，超时后自动清理
- `buffer_size`: 每个会话缓存的最大输出行数，影响内存占用
- `font_size`: 终端字体大小，范围 10-24
- `theme`: 终端主题，支持 dark（深色）和 light（浅色）
- `default_path`: 新建终端时的默认工作目录，支持 `~` 表示用户主目录
- `refresh_interval`: 系统仪表盘数据刷新间隔，范围 1-30 秒

## 🚀 生产环境部署

### 方式 1：传统部署（推荐）

#### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx
```

#### 2. 部署后端

```bash
# 创建应用目录
sudo mkdir -p /opt/web-terminal
sudo chown $USER:$USER /opt/web-terminal
cd /opt/web-terminal

# 克隆代码
git clone <your-repo-url> .

# 安装后端依赖
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 修改 SECRET_KEY 等配置

# 使用 Gunicorn 运行（生产环境）
pip install gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --daemon \
  --access-logfile /var/log/web-terminal-access.log \
  --error-logfile /var/log/web-terminal-error.log
```

#### 3. 部署前端

```bash
# 构建前端
cd /opt/web-terminal/frontend
npm install
npm run build

# 前端文件将生成在 dist/ 目录
```

#### 4. 配置 Nginx

创建 Nginx 配置文件 `/etc/nginx/sites-available/web-terminal`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名
    
    # 前端静态文件
    location / {
        root /opt/web-terminal/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 超时设置
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
    
    # 日志
    access_log /var/log/nginx/web-terminal-access.log;
    error_log /var/log/nginx/web-terminal-error.log;
}
```

启用配置：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/web-terminal /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

#### 5. 配置 HTTPS（可选但推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书并自动配置 Nginx
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

#### 6. 配置 Systemd 服务

创建服务文件 `/etc/systemd/system/web-terminal.service`:

```ini
[Unit]
Description=Web Terminal Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/web-terminal/backend
Environment="PATH=/opt/web-terminal/backend/venv/bin"
ExecStart=/opt/web-terminal/backend/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/web-terminal-access.log \
  --error-logfile /var/log/web-terminal-error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start web-terminal

# 开机自启
sudo systemctl enable web-terminal

# 查看状态
sudo systemctl status web-terminal
```

### 方式 2：Docker 部署

#### 1. 创建 Dockerfile

**后端 Dockerfile** (`backend/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile** (`frontend/Dockerfile`):

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Nginx 配置** (`frontend/nginx.conf`):

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 2. 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: web-terminal-backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/terminal_sessions.db:/app/terminal_sessions.db
      - ./backend/terminal_config.json:/app/terminal_config.json
    environment:
      - SECRET_KEY=${SECRET_KEY:-your-secret-key-change-in-production}
    restart: unless-stopped
    networks:
      - web-terminal-network
  
  frontend:
    build: ./frontend
    container_name: web-terminal-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - web-terminal-network

networks:
  web-terminal-network:
    driver: bridge
```

#### 3. 启动容器

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

### 方式 3：云平台部署

#### AWS 部署

1. **使用 EC2 + RDS**
   - 在 EC2 上部署应用（参考传统部署）
   - 使用 RDS PostgreSQL 替代 SQLite
   - 配置 Security Group 开放 80/443 端口
   - 使用 Elastic IP 固定 IP 地址

2. **使用 ECS + Fargate**
   - 构建 Docker 镜像推送到 ECR
   - 创建 ECS 任务定义
   - 配置 Application Load Balancer
   - 使用 EFS 持久化数据

#### 阿里云部署

1. **使用 ECS + RDS**
   - 购买 ECS 实例
   - 配置安全组规则
   - 部署应用（参考传统部署）
   - 使用 RDS MySQL 存储数据

2. **使用容器服务 ACK**
   - 创建 Kubernetes 集群
   - 部署应用到 K8s
   - 配置 Ingress 和负载均衡
   - 使用 NAS 持久化数据

### 安全加固

#### 1. 修改默认密码

编辑 `backend/app/models/user.py`，使用以下脚本生成新密码哈希：

```python
import bcrypt

password = "your-new-password"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hashed)
```

#### 2. 配置环境变量

创建 `backend/.env` 文件：

```bash
SECRET_KEY=your-very-long-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./terminal_sessions.db
```

#### 3. 配置防火墙

```bash
# 只开放必要端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

#### 4. 配置 CORS

编辑 `backend/app/main.py`，限制允许的域名：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 修改为你的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 性能优化

#### 1. 数据库优化

```bash
# 定期清理过期会话
sqlite3 backend/terminal_sessions.db "DELETE FROM terminal_sessions WHERE is_active = 0 AND last_activity < strftime('%s', 'now') - 604800;"

# 优化数据库
sqlite3 backend/terminal_sessions.db "VACUUM;"
```

#### 2. 日志轮转

创建 `/etc/logrotate.d/web-terminal`:

```
/var/log/web-terminal-*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload web-terminal
    endscript
}
```

#### 3. 监控告警

使用 Prometheus + Grafana 监控系统资源：

```bash
# 安装 node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz
sudo mv node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter

# 创建 systemd 服务
sudo nano /etc/systemd/system/node_exporter.service
```

### 备份策略

#### 1. 数据库备份

```bash
# 创建备份脚本
cat > /opt/backup-terminal.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/web-terminal"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/web-terminal/backend/terminal_sessions.db $BACKUP_DIR/terminal_sessions_$DATE.db

# 备份配置
cp /opt/web-terminal/backend/terminal_config.json $BACKUP_DIR/terminal_config_$DATE.json

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.json" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/backup-terminal.sh

# 添加到 crontab（每天凌晨 2 点备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup-terminal.sh") | crontab -
```

#### 2. 恢复数据

```bash
# 停止服务
sudo systemctl stop web-terminal

# 恢复数据库
cp /opt/backups/web-terminal/terminal_sessions_YYYYMMDD_HHMMSS.db /opt/web-terminal/backend/terminal_sessions.db

# 恢复配置
cp /opt/backups/web-terminal/terminal_config_YYYYMMDD_HHMMSS.json /opt/web-terminal/backend/terminal_config.json

# 启动服务
sudo systemctl start web-terminal
```

### 故障排查

#### 查看日志

```bash
# 后端日志
tail -f /var/log/web-terminal-error.log

# Nginx 日志
tail -f /var/log/nginx/web-terminal-error.log

# Systemd 日志
sudo journalctl -u web-terminal -f

# Docker 日志
docker-compose logs -f backend
```

#### 常见问题

1. **WebSocket 连接失败**
   - 检查 Nginx 配置是否支持 WebSocket
   - 确认防火墙规则
   - 查看后端日志

2. **会话无法保存**
   - 检查数据库文件权限
   - 确认磁盘空间充足
   - 查看后端错误日志

3. **性能问题**
   - 增加 Gunicorn workers 数量
   - 优化数据库（VACUUM）
   - 检查系统资源使用情况

## 🐛 故障排查

### 开发环境

#### 输入无响应
- 检查 WebSocket 连接状态（浏览器开发者工具 → Network → WS）
- 查看浏览器控制台是否有错误
- 检查后端日志输出

#### 输出不同步
- 刷新页面重新连接
- 检查网络连接是否稳定
- 查看客户端数量是否正常

#### 会话丢失
- 检查会话超时设置（默认 7 天）
- 查看数据库: `sqlite3 backend/terminal_sessions.db`
- 检查后端是否正常运行

### 生产环境

详细的故障排查步骤请参考上方"生产环境部署"章节中的"故障排查"部分。

## 📝 更新日志

### v1.0.0 (2026-02-06)

- ✅ 完整的多用户终端系统
- ✅ 后台持续运行支持
- ✅ 多客户端实时同步
- ✅ 完整的数据持久化
- ✅ 自动重连机制
- ✅ 全屏模式
- ✅ 交互式 CLI 完美支持

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**文档:** [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)  
**版本:** 1.0.0  
**更新:** 2026-02-06
