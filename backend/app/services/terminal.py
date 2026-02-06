import os
import pty
import select
import subprocess
import struct
import fcntl
import termios
import signal
from typing import Dict, Optional
import asyncio
import time
from sqlalchemy.orm import Session
from ..db.database import SessionLocal
from ..db.models import TerminalSessionDB

class TerminalSession:
    def __init__(self, session_id: str, username: str, name: str, buffer_size: int = 1000):
        self.session_id = session_id
        self.username = username
        self.name = name
        self.fd = None
        self.child_pid = None
        self.running = False
        self.last_activity = time.time()
        self.buffer = []  # 内存缓存
        self.max_buffer_size = buffer_size
        self.cwd = None
        self.rows = 24  # 默认行数
        self.cols = 80  # 默认列数
        self.connected_clients = {}  # 跟踪连接的客户端 {client_id: last_output_index}
        self.output_history = []  # 完整的输出历史，用于新客户端连接
        self.output_index = 0  # 当前输出索引
        import threading
        self.lock = threading.Lock()  # 线程锁，保护共享数据
        
    def start(self, cols: int = 80, rows: int = 24, cwd: str = None):
        """启动终端会话"""
        self.cwd = cwd
        self.child_pid, self.fd = pty.fork()
        
        if self.child_pid == 0:
            # 子进程
            if cwd:
                try:
                    os.chdir(os.path.expanduser(cwd))
                except:
                    pass
            
            # 设置终端环境变量 - 增强对交互式 CLI 工具的支持
            os.environ['TERM'] = 'xterm-256color'
            os.environ['COLORTERM'] = 'truecolor'
            os.environ['LANG'] = 'en_US.UTF-8'
            os.environ['LC_ALL'] = 'en_US.UTF-8'
            # 确保支持完整的终端功能
            os.environ['TERM_PROGRAM'] = 'xterm'
            os.environ['TERM_PROGRAM_VERSION'] = '1.0'
            
            subprocess.run([os.environ.get('SHELL', '/bin/bash')])
        else:
            # 父进程
            # 先设置窗口大小
            self.set_winsize(rows, cols)
            
            # 配置终端属性以支持交互式应用
            try:
                # 获取当前终端属性
                attrs = termios.tcgetattr(self.fd)
                
                # 设置输入模式 (iflag)
                # ICRNL: 将输入的 CR 转换为 NL
                # IXON: 启用 XON/XOFF 流控制
                attrs[0] = termios.ICRNL | termios.IXON
                
                # 设置输出模式 (oflag)
                # OPOST: 启用输出处理
                # ONLCR: 将输出的 NL 转换为 CR-NL
                attrs[1] = termios.OPOST | termios.ONLCR
                
                # 设置控制模式 (cflag)
                # CS8: 8位字符
                # CREAD: 启用接收
                attrs[2] = termios.CS8 | termios.CREAD
                
                # 设置本地模式 (lflag)
                # ISIG: 启用信号
                # ICANON: 启用规范模式
                # ECHO: 回显输入字符
                # ECHOE: 回显擦除字符
                # ECHOK: 回显 KILL 字符
                # ECHOCTL: 回显控制字符
                # ECHOKE: 回显 KILL 字符并擦除行
                # IEXTEN: 启用扩展处理
                attrs[3] = (termios.ISIG | termios.ICANON | termios.ECHO | 
                           termios.ECHOE | termios.ECHOK | termios.ECHOCTL | 
                           termios.ECHOKE | termios.IEXTEN)
                
                # 应用终端属性
                termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
            except Exception as e:
                print(f"Warning: Could not set terminal attributes: {e}")
            
            self.running = True
            self.last_activity = time.time()
            
            # 设置非阻塞
            flag = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
            
            # 保存到数据库
            self._save_to_db()
    
    def set_winsize(self, rows: int, cols: int):
        """设置终端窗口大小"""
        if self.fd:
            self.rows = rows
            self.cols = cols
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
            
            # 发送 SIGWINCH 信号通知子进程窗口大小改变
            # 这对于交互式 CLI 工具（如 vim, less, 菜单界面等）非常重要
            if self.child_pid:
                try:
                    import signal
                    os.kill(self.child_pid, signal.SIGWINCH)
                except Exception as e:
                    print(f"Warning: Could not send SIGWINCH: {e}")
            
            # 更新数据库中的尺寸
            self._update_winsize_in_db()
    
    def write(self, data: str):
        """写入数据到终端"""
        if self.fd and self.running:
            self.last_activity = time.time()
            os.write(self.fd, data.encode())
            self._update_activity()
    
    def read(self, timeout: float = 0.01) -> str:
        """从终端读取数据"""
        if not self.fd or not self.running:
            return ""
        
        try:
            ready, _, _ = select.select([self.fd], [], [], timeout)
            if ready:
                data = os.read(self.fd, 1024 * 10)
                output = data.decode('utf-8', errors='ignore')
                self.last_activity = time.time()
                
                with self.lock:
                    # 缓存输出到 buffer（用于 get_buffer）
                    self.buffer.append(output)
                    if len(self.buffer) > self.max_buffer_size:
                        self.buffer.pop(0)
                    
                    # 添加到输出历史（用于多客户端同步）
                    self.output_history.append({
                        'index': self.output_index,
                        'data': output,
                        'timestamp': time.time()
                    })
                    self.output_index += 1
                    
                    # 限制历史记录大小
                    if len(self.output_history) > self.max_buffer_size:
                        self.output_history.pop(0)
                
                # 异步保存到数据库
                self._save_buffer_to_db()
                
                return output
        except OSError:
            pass
        return ""
    
    def get_new_output_for_client(self, client_id: str) -> str:
        """获取客户端未读取的输出"""
        with self.lock:
            if client_id not in self.connected_clients:
                return ""
            
            last_index = self.connected_clients[client_id]
            new_outputs = []
            
            for item in self.output_history:
                if item['index'] > last_index:
                    new_outputs.append(item['data'])
                    last_index = item['index']
            
            # 更新客户端的最后读取索引
            if new_outputs:
                self.connected_clients[client_id] = last_index
            
            return ''.join(new_outputs)
    
    def add_client(self, client_id: str) -> str:
        """添加连接的客户端，返回历史缓冲区"""
        with self.lock:
            # 设置客户端的起始索引为当前索引
            self.connected_clients[client_id] = self.output_index - 1
            print(f"Client {client_id} connected to session {self.session_id}. Total clients: {len(self.connected_clients)}")
            
            # 返回完整的历史缓冲区
            return self.get_buffer()
    
    def remove_client(self, client_id: str):
        """移除断开的客户端"""
        with self.lock:
            self.connected_clients.pop(client_id, None)
            print(f"Client {client_id} disconnected from session {self.session_id}. Remaining clients: {len(self.connected_clients)}")
        print(f"Client {client_id} disconnected from session {self.session_id}. Remaining clients: {len(self.connected_clients)}")
    
    def has_clients(self) -> bool:
        """检查是否有客户端连接"""
        return len(self.connected_clients) > 0
    
    def get_buffer(self) -> str:
        """获取缓存的输出"""
        return ''.join(self.buffer)
    
    def is_alive(self) -> bool:
        """检查会话是否存活"""
        if not self.running or not self.child_pid:
            return False
        try:
            os.kill(self.child_pid, 0)
            return True
        except OSError:
            return False
    
    def _save_to_db(self):
        """保存会话到数据库 - 线程安全版本"""
        try:
            from ..db.database import SessionLocal
            db = SessionLocal()
            
            try:
                session_db = db.query(TerminalSessionDB).filter(
                    TerminalSessionDB.id == self.session_id
                ).first()
                
                if session_db:
                    session_db.last_activity = self.last_activity
                    session_db.is_active = True
                    session_db.pid = self.child_pid
                    session_db.cwd = self.cwd
                    session_db.rows = self.rows
                    session_db.cols = self.cols
                else:
                    session_db = TerminalSessionDB(
                        id=self.session_id,
                        username=self.username,
                        name=self.name,
                        last_activity=self.last_activity,
                        created_at=time.time(),
                        is_active=True,
                        pid=self.child_pid,
                        cwd=self.cwd,
                        rows=self.rows,
                        cols=self.cols
                    )
                    db.add(session_db)
                
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Error saving session to DB: {e}")
    
    def _update_winsize_in_db(self):
        """更新数据库中的终端尺寸 - 线程安全版本"""
        try:
            from ..db.database import SessionLocal
            db = SessionLocal()
            
            try:
                session_db = db.query(TerminalSessionDB).filter(
                    TerminalSessionDB.id == self.session_id
                ).first()
                
                if session_db:
                    session_db.rows = self.rows
                    session_db.cols = self.cols
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Error updating winsize in DB: {e}")
    
    def _save_buffer_to_db(self):
        """保存缓冲区到数据库 - 线程安全版本"""
        try:
            # 使用新的数据库会话，避免线程冲突
            from ..db.database import SessionLocal
            db = SessionLocal()
            
            try:
                session_db = db.query(TerminalSessionDB).filter(
                    TerminalSessionDB.id == self.session_id
                ).first()
                
                if session_db:
                    # 保存完整的缓冲区
                    buffer_content = self.get_buffer()
                    session_db.buffer = buffer_content
                    session_db.last_activity = self.last_activity
                    
                    # 立即提交
                    db.commit()
                else:
                    # 如果会话不存在，创建它
                    session_db = TerminalSessionDB(
                        id=self.session_id,
                        username=self.username,
                        name=self.name,
                        last_activity=self.last_activity,
                        created_at=time.time(),
                        is_active=True,
                        pid=self.child_pid,
                        cwd=self.cwd,
                        rows=self.rows,
                        cols=self.cols,
                        buffer=self.get_buffer()
                    )
                    db.add(session_db)
                    db.commit()
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error saving buffer to DB: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_activity(self):
        """更新最后活动时间 - 线程安全版本"""
        try:
            from ..db.database import SessionLocal
            db = SessionLocal()
            
            try:
                session_db = db.query(TerminalSessionDB).filter(
                    TerminalSessionDB.id == self.session_id
                ).first()
                
                if session_db:
                    session_db.last_activity = self.last_activity
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Error updating activity: {e}")
    
    def close(self):
        """关闭终端会话"""
        self.running = False
        
        # 只有在没有客户端连接时才真正关闭
        if self.has_clients():
            print(f"Session {self.session_id} has active clients, keeping alive")
            return
        
        print(f"Closing session {self.session_id}")
        
        # 标记为不活跃 - 使用独立的数据库会话
        try:
            from ..db.database import SessionLocal
            db = SessionLocal()
            
            try:
                session_db = db.query(TerminalSessionDB).filter(
                    TerminalSessionDB.id == self.session_id
                ).first()
                
                if session_db:
                    session_db.is_active = False
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Error marking session inactive: {e}")
        
        if self.fd:
            try:
                os.close(self.fd)
            except:
                pass
        if self.child_pid:
            try:
                os.kill(self.child_pid, 9)
            except:
                pass

class TerminalManager:
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
        self.session_timeout = 3600 * 24 * 7  # 默认7天，支持长时间运行的任务
        self.buffer_size = 1000  # 默认1000行，可通过配置更新
        self.background_tasks = {}  # 存储后台读取任务
        
    def update_config(self, session_timeout: int = None, buffer_size: int = None):
        """更新配置"""
        if session_timeout is not None:
            self.session_timeout = session_timeout
        if buffer_size is not None:
            self.buffer_size = buffer_size
        
    def create_session(self, session_id: str, username: str, name: str, cols: int = 80, rows: int = 24, cwd: str = None) -> TerminalSession:
        """创建新的终端会话"""
        if session_id in self.sessions:
            # 如果会话已存在且还活着，直接返回
            if self.sessions[session_id].is_alive():
                return self.sessions[session_id]
            # 否则清理旧会话
            self.sessions[session_id].close()
        
        session = TerminalSession(session_id, username, name, self.buffer_size)
        session.start(cols, rows, cwd)
        self.sessions[session_id] = session
        
        # 启动后台读取任务，持续读取终端输出
        self._start_background_reader(session_id)
        
        return session
    
    def _start_background_reader(self, session_id: str):
        """启动后台任务持续读取终端输出"""
        import threading
        
        def read_loop():
            """后台循环读取终端输出"""
            last_save_time = time.time()
            save_interval = 5  # 每5秒强制保存一次
            
            while session_id in self.sessions:
                session = self.sessions.get(session_id)
                if not session or not session.is_alive():
                    break
                
                # 读取输出（即使没有客户端连接也继续读取）
                session.read(timeout=0.1)
                
                # 定期强制保存到数据库
                current_time = time.time()
                if current_time - last_save_time >= save_interval:
                    session._save_buffer_to_db()
                    last_save_time = current_time
                
                time.sleep(0.01)
            
            # 退出前最后保存一次
            if session_id in self.sessions:
                session = self.sessions.get(session_id)
                if session:
                    session._save_buffer_to_db()
            
            print(f"Background reader for session {session_id} stopped")
        
        # 创建并启动后台线程
        thread = threading.Thread(target=read_loop, daemon=True)
        thread.start()
        self.background_tasks[session_id] = thread
        print(f"Started background reader for session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """获取终端会话"""
        session = self.sessions.get(session_id)
        if session and session.is_alive():
            return session
        return None
    
    def reconnect_session(self, session_id: str, username: str) -> tuple[bool, str]:
        """重连到已存在的会话"""
        # 先检查内存中的会话
        session = self.sessions.get(session_id)
        if session and session.is_alive():
            buffer = session.get_buffer()
            return True, buffer
        
        # 从数据库恢复
        db = SessionLocal()
        try:
            session_db = db.query(TerminalSessionDB).filter(
                TerminalSessionDB.id == session_id,
                TerminalSessionDB.username == username,
                TerminalSessionDB.is_active == True
            ).first()
            
            if session_db:
                # 检查会话是否超时
                if time.time() - session_db.last_activity > self.session_timeout:
                    session_db.is_active = False
                    db.commit()
                    return False, "会话已超时"
                
                # 返回缓存的输出
                return True, session_db.buffer or ""
            
            return False, "会话不存在"
        except Exception as e:
            print(f"Error reconnecting session: {e}")
            return False, f"重连失败: {str(e)}"
        finally:
            db.close()
    
    def list_sessions(self, username: str = None) -> list:
        """列出所有活跃的会话"""
        db = SessionLocal()
        try:
            query = db.query(TerminalSessionDB).filter(
                TerminalSessionDB.is_active == True
            )
            
            if username:
                query = query.filter(TerminalSessionDB.username == username)
            
            sessions = query.all()
            
            result = []
            for session_db in sessions:
                # 检查是否超时
                if time.time() - session_db.last_activity > self.session_timeout:
                    session_db.is_active = False
                    continue
                
                result.append({
                    "id": session_db.id,
                    "name": session_db.name,
                    "username": session_db.username,
                    "last_activity": session_db.last_activity,
                    "created_at": session_db.created_at,
                    "running": session_db.id in self.sessions and self.sessions[session_db.id].is_alive(),
                    "rows": session_db.rows or 24,
                    "cols": session_db.cols or 80
                })
            
            db.commit()
            return result
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
        finally:
            db.close()
    
    def close_session(self, session_id: str):
        """关闭终端会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # 在关闭前保存最终的缓冲区
            session._save_buffer_to_db()
            
            # 清除所有客户端连接
            session.connected_clients.clear()
            
            # 关闭会话
            session.close()
            
            # 从管理器中移除
            del self.sessions[session_id]
            
            # 清理后台任务
            if session_id in self.background_tasks:
                del self.background_tasks[session_id]
    
    def cleanup_inactive_sessions(self):
        """清理不活跃的会话"""
        current_time = time.time()
        to_remove = []
        
        # 清理内存中的会话
        for session_id, session in self.sessions.items():
            if not session.is_alive() or (current_time - session.last_activity) > self.session_timeout:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            self.close_session(session_id)
        
        # 清理数据库中的会话
        db = SessionLocal()
        try:
            sessions = db.query(TerminalSessionDB).filter(
                TerminalSessionDB.is_active == True
            ).all()
            
            for session_db in sessions:
                if current_time - session_db.last_activity > self.session_timeout:
                    session_db.is_active = False
            
            db.commit()
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            db.rollback()
        finally:
            db.close()
    
    def close_all(self):
        """关闭所有会话"""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()

terminal_manager = TerminalManager()
