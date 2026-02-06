from sqlalchemy import Column, String, Integer, Text, Float, Boolean
from .database import Base
import time

class TerminalSessionDB(Base):
    __tablename__ = "terminal_sessions"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, index=True)
    name = Column(String)
    buffer = Column(Text, default="")
    last_activity = Column(Float, default=time.time)
    created_at = Column(Float, default=time.time)
    is_active = Column(Boolean, default=True)
    pid = Column(Integer, nullable=True)
    cwd = Column(String, nullable=True)
