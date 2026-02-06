import os
import pty
import select
import subprocess
import struct
import fcntl
import termios
from typing import Dict, Optional
import asyncio
import time
from sqlalchemy.orm import Session
from ..db.database import SessionLocal
from ..db.models import TerminalSessionDB

class TerminalSession:
    def __init__(self, session_id: str, username: str, name: str, buffer_size: int = 1000, db: Session = None):
        self.session_id = session_id
        self.username = username
        self.name = name
        self.fd = None
        self.child_pid = None
        self.running = False
        self.last_activity = time.time()
        self.buffer = []  # 内存缓存
        self.max_buffer_size = buffer_size
        self.db = db
        self.cwd = None
        
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
            
            # 设置终端环境变量
            os.environ['TERM'] = 'xterm-256color'
            os.environ['COLORTERM'] = 'truecolor'
            os.environ['LANG'] = 'en_US.UTF-8'
            os.environ['LC_ALL'] = 'en_US.UTF-8'
            
            subprocess.run([os.environ.get('SHELL', '/bin/bash')])
        else:
            # 父进程
            self.set_winsize(rows, cols)
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
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
    
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
                
                # 缓存输出
                self.buffer.append(output)
                if len(self.buffer) > self.max_buffer_size:
                    self.buffer.pop(0)
                
                # 异步保存到数据库
                self._save_buffer_to_db()
                
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
            os.kill(self.child_pid, 0)
            return True
        except OSError:
            return False
    
    def _save_to_db(self):
        """保存会话到数据库"""
        if not self.db:
            return
        
        try:
            session_db = self.db.query(TerminalSessionDB).filter(
                TerminalSessionDB.id == self.session_id
            ).first()
            
            if session_db:
                session_db.last_activity = self.last_activity
                session_db.is_active = True
                session_db.pid = self.child_pid
                session_db.cwd = self.cwd
            else:
                session_db = TerminalSessionDB(
                    id=self.session_id,
                    username=self.username,
                    name=self.name,
                    last_activity=self.last_activity,
                    created_at=time.time(),
                    is_active=True,
                    pid=self.child_pid,
                    cwd=self.cwd
                )
                self.db.add(session_db)
            
            self.db.commit()
        except Exception as e:
            print(f"Error saving session to DB: {e}")
            self.db.rollback()
    
    def _save_buffer_to_db(self):
        """保存缓冲区到数据库"""
        if not self.db:
            return
        
        try:
            session_db = self.db.query(TerminalSessionDB).filter(
                TerminalSessionDB.id == self.session_id
            ).first()
            
            if session_db:
                session_db.buffer = self.get_buffer()
                session_db.last_activity = self.last_activity
                self.db.commit()
        except Exception as e:
            print(f"Error saving buffer to DB: {e}")
            self.db.rollback()
    
    def _update_activity(self):
        """更新最后活动时间"""
        if not self.db:
            return
        
        try:
            session_db = self.db.query(TerminalSessionDB).filter(
                TerminalSessionDB.id == self.session_id
            ).first()
            
            if session_db:
                session_db.last_activity = self.last_activity
                self.db.commit()
        except Exception as e:
            print(f"Error updating activity: {e}")
            self.db.rollback()
    
    def close(self):
        """关闭终端会话"""
        self.running = False
        
        # 标记为不活跃
        if self.db:
            try:
                session_db = self.db.query(TerminalSessionDB).filter(
                    TerminalSessionDB.id == self.session_id
                ).first()
                
                if session_db:
                    session_db.is_active = False
                    self.db.commit()
            except Exception as e:
                print(f"Error marking session inactive: {e}")
                self.db.rollback()
        
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
        
    def create_session(self, session_id: str, username: str, name: str, cols: int = 80, rows: int = 24, cwd: str = None) -> TerminalSession:
        """创建新的终端会话"""
        db = SessionLocal()
        
        if session_id in self.sessions:
            # 如果会话已存在且还活着，直接返回
            if self.sessions[session_id].is_alive():
                return self.sessions[session_id]
            # 否则清理旧会话
            self.sessions[session_id].close()
        
        session = TerminalSession(session_id, username, name, self.buffer_size, db)
        session.start(cols, rows, cwd)
        self.sessions[session_id] = session
        return session
    
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
                    "running": session_db.id in self.sessions and self.sessions[session_db.id].is_alive()
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
            self.sessions[session_id].close()
            del self.sessions[session_id]
    
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
