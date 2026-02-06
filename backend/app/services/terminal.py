import os
import pty
import select
import subprocess
import struct
import fcntl
import termios
from typing import Dict
import asyncio
import time

class TerminalSession:
    def __init__(self, session_id: str, buffer_size: int = 1000):
        self.session_id = session_id
        self.fd = None
        self.child_pid = None
        self.running = False
        self.last_activity = time.time()
        self.buffer = []  # 缓存最近的输出
        self.max_buffer_size = buffer_size  # 可配置的缓存大小
        
    def start(self, cols: int = 80, rows: int = 24, cwd: str = None):
        """启动终端会话"""
        self.child_pid, self.fd = pty.fork()
        
        if self.child_pid == 0:
            # 子进程
            if cwd:
                try:
                    os.chdir(os.path.expanduser(cwd))
                except:
                    pass
            subprocess.run([os.environ.get('SHELL', '/bin/bash')])
        else:
            # 父进程
            self.set_winsize(rows, cols)
            self.running = True
            self.last_activity = time.time()
            # 设置非阻塞
            flag = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
    
    def set_winsize(self, rows: int, cols: int):
        """设置终端窗口大小"""
        if self.fd:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
    
    def write(self, data: str):
        """写入数据到终端"""
        if self.fd and self.running:
            self.last_activity = time.time()
            os.write(self.fd, data.encode())
    
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
                
                # 缓存输出
                self.buffer.append(output)
                if len(self.buffer) > self.max_buffer_size:
                    self.buffer.pop(0)
                
                return output
        except OSError:
            pass
        return ""
    
    def get_buffer(self) -> str:
        """获取缓存的输出"""
        return ''.join(self.buffer)
    
    def is_alive(self) -> bool:
        """检查会话是否存活"""
        if not self.running or not self.child_pid:
            return False
        try:
            # 检查进程是否存在
            os.kill(self.child_pid, 0)
            return True
        except OSError:
            return False
    
    def close(self):
        """关闭终端会话"""
        self.running = False
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
        self.session_timeout = 3600  # 默认1小时，可通过配置更新
        self.buffer_size = 1000  # 默认1000行，可通过配置更新
        
    def update_config(self, session_timeout: int = None, buffer_size: int = None):
        """更新配置"""
        if session_timeout is not None:
            self.session_timeout = session_timeout
        if buffer_size is not None:
            self.buffer_size = buffer_size
        
    def create_session(self, session_id: str, cols: int = 80, rows: int = 24, cwd: str = None) -> TerminalSession:
        """创建新的终端会话"""
        if session_id in self.sessions:
            # 如果会话已存在且还活着，直接返回
            if self.sessions[session_id].is_alive():
                return self.sessions[session_id]
            # 否则清理旧会话
            self.sessions[session_id].close()
        
        session = TerminalSession(session_id, self.buffer_size)
        session.start(cols, rows, cwd)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> TerminalSession:
        """获取终端会话"""
        session = self.sessions.get(session_id)
        if session and session.is_alive():
            return session
        return None
    
    def reconnect_session(self, session_id: str) -> tuple[bool, str]:
        """重连到已存在的会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False, "会话不存在"
        
        if not session.is_alive():
            return False, "会话已失效"
        
        # 返回缓存的输出
        buffer = session.get_buffer()
        return True, buffer
    
    def list_sessions(self) -> list:
        """列出所有活跃的会话"""
        active_sessions = []
        for session_id, session in self.sessions.items():
            if session.is_alive():
                active_sessions.append({
                    "id": session_id,
                    "running": session.running,
                    "last_activity": session.last_activity
                })
        return active_sessions
    
    def close_session(self, session_id: str):
        """关闭终端会话"""
        if session_id in self.sessions:
            self.sessions[session_id].close()
            del self.sessions[session_id]
    
    def cleanup_inactive_sessions(self):
        """清理不活跃的会话"""
        current_time = time.time()
        to_remove = []
        
        for session_id, session in self.sessions.items():
            # 检查会话是否超时或已死亡
            if not session.is_alive() or (current_time - session.last_activity) > self.session_timeout:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            self.close_session(session_id)
    
    def close_all(self):
        """关闭所有会话"""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()

terminal_manager = TerminalManager()
