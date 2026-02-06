from fastapi import APIRouter, Depends
import psutil
import platform
import socket
from datetime import datetime, timedelta

router = APIRouter()

def get_ip_address():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@router.get("/info")
async def get_system_info():
    """获取系统信息"""
    # CPU 信息
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # 内存信息
    memory = psutil.virtual_memory()
    
    # 磁盘信息
    disk = psutil.disk_usage('/')
    
    # 网络信息
    net_io = psutil.net_io_counters()
    
    # 系统信息
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    
    return {
        "hostname": platform.node(),
        "ip_address": get_ip_address(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "boot_time": boot_time.isoformat(),
        "uptime_seconds": int(uptime.total_seconds()),
        "cpu": {
            "percent": cpu_percent,
            "count": cpu_count
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        },
        "network": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    }
