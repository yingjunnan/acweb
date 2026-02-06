from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..services.terminal import terminal_manager
from ..core.security import decode_access_token
import asyncio
import json

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, token: str = Query(...), cwd: str = Query(None)):
    """WebSocket 终端连接"""
    # 验证 token
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    
    # 创建终端会话
    session = terminal_manager.create_session(session_id, cwd=cwd)
    
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
async def list_sessions():
    """列出所有会话"""
    return {
        "sessions": [
            {"id": sid, "running": session.running}
            for sid, session in terminal_manager.sessions.items()
        ]
    }
