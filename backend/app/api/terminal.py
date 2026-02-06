from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from ..services.terminal import terminal_manager
from ..core.security import decode_access_token
from ..api.config import load_config
import asyncio
import json

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str, 
    token: str = Query(...), 
    cwd: str = Query(None), 
    reconnect: bool = Query(False),
    name: str = Query("终端")
):
    """WebSocket 终端连接"""
    # 验证 token
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    
    username = payload.get("sub")
    
    await websocket.accept()
    
    # 加载配置并更新终端管理器
    config = load_config()
    terminal_manager.update_config(
        session_timeout=config.session_timeout,
        buffer_size=config.buffer_size
    )
    
    # 如果是重连，尝试恢复会话
    if reconnect:
        success, buffer = terminal_manager.reconnect_session(session_id, username)
        if success:
            # 发送缓存的输出
            await websocket.send_json({
                "type": "reconnect",
                "data": buffer,
                "message": "会话重连成功"
            })
            session = terminal_manager.get_session(session_id)
            if not session:
                # 会话不在内存中，需要重新创建
                session = terminal_manager.create_session(session_id, username, name, cwd=cwd)
        else:
            # 重连失败，创建新会话
            await websocket.send_json({
                "type": "reconnect_failed",
                "message": buffer
            })
            session = terminal_manager.create_session(session_id, username, name, cwd=cwd)
    else:
        # 创建新的终端会话
        session = terminal_manager.create_session(session_id, username, name, cwd=cwd)
    
    try:
        # 创建读取任务
        async def read_from_terminal():
            while session.running:
                output = session.read()
                if output:
                    await websocket.send_json({
                        "type": "output",
                        "data": output
                    })
                await asyncio.sleep(0.01)
        
        read_task = asyncio.create_task(read_from_terminal())
        
        # 处理客户端消息
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data["type"] == "input":
                session.write(data["data"])
            elif data["type"] == "resize":
                session.set_winsize(data["rows"], data["cols"])
            elif data["type"] == "close":
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        read_task.cancel()
        terminal_manager.close_session(session_id)
        await websocket.close()

@router.get("/sessions")
async def list_sessions(token: str = Query(...)):
    """列出所有活跃会话"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="未授权")
    
    username = payload.get("sub")
    return {
        "sessions": terminal_manager.list_sessions(username)
    }

@router.post("/cleanup")
async def cleanup_sessions():
    """清理不活跃的会话"""
    terminal_manager.cleanup_inactive_sessions()
    return {"message": "清理完成"}

@router.get("/session/{session_id}/status")
async def check_session_status(session_id: str):
    """检查会话状态"""
    session = terminal_manager.get_session(session_id)
    if session:
        return {
            "exists": True,
            "alive": session.is_alive(),
            "last_activity": session.last_activity
        }
    return {
        "exists": False,
        "alive": False
    }
