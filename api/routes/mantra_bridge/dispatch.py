from fastapi import APIRouter, Depends
from pydantic import BaseModel
from loguru import logger
import uuid

from api.services.auth.depends import get_user
from api.db.models import UserModel
from api.routes.telephony import initiate_call, InitiateCallRequest

router = APIRouter(prefix="/dispatch", tags=["mantra-bridge-dispatch"])

from typing import Any, Dict

class DispatchRequest(BaseModel):
    # Support for legacy/UI fields
    workflow_id: int | None = 1
    destination_number: str | None = None
    
    # Support for native Mantra Assist CALL_TRIGGER webhook fields
    call_id: int | None = None
    client_phone: str | None = None
    prompt: str | None = None
    org_id: int | None = None
    ai_payload: Dict[str, Any] | None = None

class DispatchResponse(BaseModel):
    status: str
    call_id: str | None = None

@router.post("/", response_model=DispatchResponse)
async def dispatch_call(request: DispatchRequest, user: UserModel = Depends(get_user)):
    target_phone = request.destination_number or request.client_phone
    logger.info(f"[Mantra Bridge] Dispatch call requested for {target_phone}, workflow: {request.workflow_id}")
    
    if not target_phone:
        logger.error("[Mantra Bridge] Missing phone number in payload")
        return DispatchResponse(status="error")

    # We inject mantra_assist_call so our webhook notifier picks it up at the end of the call
    extra_context = {
        "mantra_assist_call": True,
        "ma_call_id": request.call_id
    }
    
    if request.prompt:
        extra_context["prompt"] = request.prompt
        
    initiate_request = InitiateCallRequest(
        workflow_id=request.workflow_id or 1,
        phone_number=target_phone,
        extra_context=extra_context
    )
    
    try:
        # We reuse the core Dograh initiate_call logic which correctly acquires concurrency slots,
        # checks quotas, and safely dispatches to the correct telephony provider.
        await initiate_call(request=initiate_request, user=user)
        
        return DispatchResponse(
            status="success",
            # initiate_call generates a run ID internally and redirects or returns 200.
            # For simplicity, we assume success means it's enqueued.
            call_id=None
        )
    except Exception as e:
        logger.error(f"[Mantra Bridge] Failed to dispatch call: {e}")
        return DispatchResponse(status="error")
