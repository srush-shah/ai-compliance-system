from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from adk.tools.tools_registry import get_adk_tools
from security import get_auth_context_for_token
from services.run_updates import run_update_manager

router = APIRouter(prefix="/ws/runs", tags=["ws"])
tools = get_adk_tools()


@router.websocket("/{run_id}")
async def run_updates(websocket: WebSocket, run_id: int) -> None:
    auth = get_auth_context_for_token()

    run = tools["get_adk_run_by_id"](
        run_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )
    if "id" not in run and "error" in run:
        await websocket.close(code=1008)
        return

    await run_update_manager.connect(run_id, websocket)
    await websocket.send_json({"status": run.get("status"), "step": None, "payload": {"run": run}})

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await run_update_manager.disconnect(run_id, websocket)
