from typing import Any
import httpx
from loguru import logger
import os
import time
import json
import hmac
import hashlib

from api.db import db_client
from api.constants import BACKEND_API_ENDPOINT

# Configurable via environment variable for local ngrok testing
N8N_WEBHOOK_URL = os.getenv("MANTRA_WEBHOOK_URL", "http://localhost:5500/api/v1/webhooks/n8n")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "n8n-webhook-secret-local")

async def mantra_webhook_notifier(ctx: Any, workflow_run_id: int):
    """
    ARQ task to notify Mantra Assist's n8n webhook endpoint when a call completes.
    """
    logger.info(f"[Mantra Webhook Notifier] Processing run {workflow_run_id}")
    
    workflow_run, org_id = await db_client.get_workflow_run_with_context(workflow_run_id)
    if not workflow_run:
        logger.warning(f"Workflow run {workflow_run_id} not found")
        return
        
    public_token = await db_client.ensure_public_access_token(workflow_run_id)
    
    base_url = f"{BACKEND_API_ENDPOINT}/api/v1/public/download/workflow/{public_token}"
    recording_url = f"{base_url}/recording" if workflow_run.recording_url else None
    
    gathered = workflow_run.gathered_context or {}
    
    # Extract the original MA call_id passed during dispatch
    initial_context = workflow_run.initial_context or {}
    ma_call_id = initial_context.get("ma_call_id")
    if ma_call_id:
        try:
            ma_call_id = int(ma_call_id)
        except ValueError:
            pass

    payload_dict = {
        "event": "CALL_AI_INTERNAL_DATA",
        "data": {
            "call_id": ma_call_id,
            "call_transcript": gathered.get("transcript", ""),
            "recording_url": recording_url,
            "ai_call_id": str(workflow_run.id)
        }
    }
    
    # To bypass signature validation, we must sign the EXACT raw body
    raw_body = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
    timestamp = str(int(time.time()))
    sign_string = raw_body + b'.' + timestamp.encode('utf-8')
    
    signature = hmac.new(
        N8N_WEBHOOK_SECRET.encode('utf-8'),
        sign_string,
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "x-signature": signature,
        "x-timestamp": timestamp,
        "x-source": "n8n",
        "Content-Type": "application/json"
    }

    logger.info(f"[Mantra Webhook Notifier] Sending payload to {N8N_WEBHOOK_URL}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(N8N_WEBHOOK_URL, content=raw_body, headers=headers, timeout=10.0)
            response.raise_for_status()
            logger.info("[Mantra Webhook Notifier] Successfully delivered webhook")
    except Exception as e:
        logger.error(f"[Mantra Webhook Notifier] Failed to deliver webhook: {e}")
        # Re-raise to trigger ARQ retries
        raise
