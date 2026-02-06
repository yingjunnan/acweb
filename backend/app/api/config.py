from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import json
import os

router = APIRouter()

CONFIG_FILE = "terminal_config.json"

class TerminalConfig(BaseModel):
    default_path: str = "~"
    shell: str = "/bin/bash"
    font_size: int = 14
    theme: str = "dark"
    refresh_interval: int = 3  # 仪表盘刷新间隔（秒）
    session_timeout: int = 3600  # 会话超时时间（秒），默认1小时
    buffer_size: int = 1000  # 输出缓存行数

def load_config() -> TerminalConfig:
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return TerminalConfig(**data)
        except:
            pass
    return TerminalConfig()

def save_config(config: TerminalConfig):
    """保存配置"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config.dict(), f, indent=2)

@router.get("/", response_model=TerminalConfig)
async def get_config():
    """获取终端配置"""
    return load_config()

@router.post("/", response_model=TerminalConfig)
async def update_config(config: TerminalConfig):
    """更新终端配置"""
    save_config(config)
    return config
