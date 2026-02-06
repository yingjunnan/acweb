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
    """WebSocket 终端连接 - 支持多客户端同时连接，改进的同步机制"""
    # 验证 token
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    
    username = payload.get("sub")
    client_id = f"{username}_{id(websocket)}"
    
    await websocket.accept()
    
    # 加载配置并更新终端管理器
    config = load_config()
    terminal_manager.update_config(
        session_timeout=config.session_timeout,
        buffer_size=config.buffer_size
    )
    
    # 获取或创建会话
    session = terminal_manager.get_session(session_id)
    
    if session and session.is_alive():
        # 会话已存在，直接连接
        print(f"Attaching to existing session {session_id}")
        
        # 添加客户端并获取历史缓冲区
        buffer = session.add_client(client_id)
        
        if buffer:
            await websocket.send_json({
                "type": "reconnect",
                "data": buffer,
                "message": f"已连接到运行中的会话（{len(session.connected_clients)} 个客户端）"
            })
    elif reconnect:
        # 尝试从数据库恢复会话
        success, buffer = terminal_manager.reconnect_session(session_id, username)
        if success:
            # 重新创建会话
            session = terminal_manager.create_session(session_id, username, name, cwd=cwd)
            buffer = session.add_client(client_id)
            
            await websocket.send_json({
                "type": "reconnect",
                "data": buffer,
                "message": "会话已从数据库恢复"
            })
        else:
            # 恢复失败，创建新会话
            await websocket.send_json({
                "type": "reconnect_failed",
                "message": buffer
            })
            session = terminal_manager.create_session(session_id, username, name, cwd=cwd)
            session.add_client(client_id)
    else:
        # 创建新的终端会话
        session = terminal_manager.create_session(session_id, username, name, cwd=cwd)
        session.add_client(client_id)
    
    # 用于跟踪 WebSocket 是否仍然活跃
    websocket_active = True
    
    try:
        # 创建读取任务 - 使用改进的同步机制
        async def read_from_terminal():
            nonlocal websocket_active
            while session.running and client_id in session.connected_clients and websocket_active:
                try:
                    # 获取该客户端未读取的输出
                    output = session.get_new_output_for_client(client_id)
                    if output:
                        await websocket.send_json({
                            "type": "output",
                            "data": output
                        })
                    await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"Error sending output to client {client_id}: {e}")
                    websocket_active = False
                    break
        
        read_task = asyncio.create_task(read_from_terminal())
        
        # 处理客户端消息
        while websocket_active:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                data = json.loads(message)
                
                if data["type"] == "input":
                    # 确保会话仍然活跃
                    if session.running and session.is_alive():
                        session.write(data["data"])
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "会话已关闭"
                        })
                        break
                        
                elif data["type"] == "resize":
                    session.set_winsize(data["rows"], data["cols"])
                    
                elif data["type"] == "ping":
                    # 心跳请求，回复 pong
                    await websocket.send_json({
                        "type": "pong"
                    })
                    
                elif data["type"] == "close":
                    # 用户明确关闭会话
                    session.remove_client(client_id)
                    
                    # 如果没有其他客户端连接，才真正关闭会话
                    if not session.has_clients():
                        terminal_manager.close_session(session_id)
                    break
                    
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except WebSocketDisconnect:
                websocket_active = False
                break
            except Exception as e:
                print(f"Error processing message from client {client_id}: {e}")
                websocket_active = False
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
    finally:
        websocket_active = False
        read_task.cancel()
        
        # 移除客户端
        if session:
            session.remove_client(client_id)
            
            # 保存缓冲区到数据库
            if session_id in terminal_manager.sessions:
                session._save_buffer_to_db()
            
            # 如果没有客户端连接，会话继续在后台运行
            # 不会被关闭，除非用户明确关闭或超时
            if not session.has_clients():
                print(f"Session {session_id} has no clients, but keeping alive in background")
        
        try:
            await websocket.close()
        except:
            pass

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
async def check_session_status(session_id: str, token: str = Query(...)):
    """检查会话状态"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="未授权")
    
    session = terminal_manager.get_session(session_id)
    if session:
        return {
            "exists": True,
            "alive": session.is_alive(),
            "last_activity": session.last_activity,
            "connected_clients": len(session.connected_clients),
            "running_in_background": not session.has_clients() and session.is_alive(),
            "rows": session.rows,
            "cols": session.cols,
            "pid": session.child_pid
        }
    
    # 检查数据库中是否有记录
    from ..db.database import SessionLocal
    db = SessionLocal()
    try:
        from ..db.models import TerminalSessionDB
        session_db = db.query(TerminalSessionDB).filter(
            TerminalSessionDB.id == session_id
        ).first()
        
        if session_db:
            return {
                "exists": True,
                "alive": False,
                "in_database": True,
                "last_activity": session_db.last_activity,
                "connected_clients": 0,
                "running_in_background": False
            }
    finally:
        db.close()
    
    return {
        "exists": False,
        "alive": False
    }
