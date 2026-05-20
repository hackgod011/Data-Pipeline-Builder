import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.routes.executions import subscribe, unsubscribe
from app.core.database import AsyncSessionLocal
from app.models.execution import Execution

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/execution/{execution_id}")
async def execution_ws(websocket: WebSocket, execution_id: str):
    await websocket.accept()

    # Send buffered logs for clients that reconnect after execution already finished
    async with AsyncSessionLocal() as db:
        exe = await db.get(Execution, execution_id)
        if exe and exe.log_buffer:
            for line in exe.log_buffer.splitlines():
                await websocket.send_text(json.dumps({
                    "type": "log",
                    "timestamp": "",
                    "message": line,
                }))
        if exe and exe.status in {"success", "failed"}:
            await websocket.send_text(json.dumps({
                "type": "status",
                "timestamp": "",
                "status": exe.status,
                "message": exe.error_message or "Execution complete",
            }))
            await websocket.close()
            return

    queue = subscribe(execution_id)
    try:
        while True:
            msg = await queue.get()
            await websocket.send_text(json.dumps(msg))
            if msg.get("type") == "status" and msg.get("status") in {"success", "failed"}:
                break
    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe(execution_id, queue)
        try:
            await websocket.close()
        except Exception:
            pass
