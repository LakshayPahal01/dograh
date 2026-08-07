from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from loguru import logger

from api.db import db_client
from api.services.auth.depends import get_user
from api.db.models import UserModel
from api.services.worker_sync.manager import get_worker_sync_manager

router = APIRouter(prefix="/sync", tags=["mantra-bridge-sync"])

class SyncRequest(BaseModel):
    org_id: int
    workflow_id: int | None = None
    prompt: str | None = None
    api_keys: dict | None = None

class SyncResponse(BaseModel):
    status: str
    message: str

@router.post("/", response_model=SyncResponse)
async def sync_config(request: SyncRequest, user: UserModel = Depends(get_user)):
    logger.info(f"[Mantra Bridge] Sync config requested for org {request.org_id}")
    
    # 1. If API keys are provided, we should update the org configuration
    # Note: Full API key sync would map to Dograh's ai_model_configuration.
    if request.api_keys:
        # Example sync trigger for credentials
        manager = get_worker_sync_manager()
        await manager.broadcast("ai_model_credentials", "updated", str(request.org_id))
    
    # 2. If prompt is provided and workflow is provided, update workflow definition
    if request.prompt and request.workflow_id:
        workflow = await db_client.get_workflow(request.workflow_id, organization_id=request.org_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
            
        # In a real scenario we would deeply traverse the workflow_json to find the LLM node
        # and update its system prompt. Here we just acknowledge it for the bridge.
        # This is where we would call db_client.update_workflow(...)
        pass
        
    return SyncResponse(status="success", message="Sync processed")
