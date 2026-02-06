import os
import pty
import select
import subprocess
import struct
import fcntl
import termios
from typing import Dict
import asyncio

class TerminalSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.fd = None
        self.child_pid = None
        self.running = False
        
    def start(self, cols: int = 80, rows: int = 24):
        """启动终端会话"""
        self.child_pid, self.fd = pty.fork()
        
        if self.child_pid == 0:
            # 子进程
            subprocess.run([os.environ.get('SHELL', '/bin/bash')])
        else:
            # 父进程
            self.set_winsize(rows, cols)
            self.running = True
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
            os.write(self.fd, data.encode())
    
    def read(self, timeout: float = 0.01) -> str:
        """从终端读取数据"""
        if not self.fd or not self.running:
            return ""
        
        try:
            ready, _, _ = select.select([self.fd], [], [], timeout)
            if ready:
                data = os.read(self.fd, 1024 * 10)
                return data.decode('utf-8', errors='ignore')
        except OSError:
            pass
        return ""
    
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
    
    def create_session(self, session_id: str, cols: int = 80, rows: int = 24) -> TerminalSession:
        """创建新的终端会话"""
        if session_id in self.sessions:
            self.sessions[session_id].close()
        
        session = TerminalSession(session_id)
        session.start(cols, rows)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> TerminalSession:
        """获取终端会话"""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: str):
        """关闭终端会话"""
        if session_id in self.sessions:
            self.sessions[session_id].close()
            del self.sessions[session_id]
    
    def close_all(self):
        """关闭所有会话"""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()

terminal_manager = TerminalManager()
