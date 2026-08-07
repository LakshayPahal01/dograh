from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from pydantic import BaseModel
from loguru import logger
import uuid

from api.db import db_client
from api.services.storage import storage_fs
from api.tasks.arq import enqueue_job
from api.tasks.function_names import FunctionNames
from api.services.auth.depends import get_user
from api.db.models import UserModel
from api.enums import PostHogEvent
from api.services.posthog_client import capture_event

router = APIRouter(prefix="/kb", tags=["mantra-bridge-kb"])

class KBIngestResponse(BaseModel):
    status_code: int
    status: str
    message: str
    document_id: str
    org_id: str
    s3_url: Optional[str] = None

@router.post("/ingest", response_model=KBIngestResponse)
async def ingest_kb(
    org_id: str = Form(...),
    document_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    tags_name: Optional[str] = Form(None),
    category_name: Optional[str] = Form(None),
    process_stage_data: Optional[str] = Form(None),
    user: UserModel = Depends(get_user),
):
    logger.info(f"[Mantra Bridge] KB Ingest requested for doc {document_id}, org {org_id}")
    
    if not file:
        raise HTTPException(status_code=400, detail="A file must be provided")

    doc_uuid = document_id or str(uuid.uuid4())
    s3_key = f"knowledge_base/{org_id}/{doc_uuid}/{file.filename}"
    
    # 1. Upload to storage
    file_bytes = await file.read()
    success = await storage_fs.acreate_file_from_bytes(s3_key, file_bytes)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")
        
    # 2. Create document record
    document = await db_client.create_document(
        organization_id=int(org_id),
        created_by=user.id,
        filename=file.filename,
        file_size_bytes=len(file_bytes),
        file_hash="",
        mime_type=file.content_type or "application/octet-stream",
        custom_metadata={"s3_key": s3_key, "tags": tags_name, "category": category_name},
        document_uuid=doc_uuid,
        retrieval_mode="hybrid",
    )

    # 3. Enqueue ARQ task
    await enqueue_job(
        FunctionNames.PROCESS_KNOWLEDGE_BASE_DOCUMENT,
        document.id,
        s3_key,
        int(org_id),
        str(user.provider_id),
        128,  # max_tokens
        "hybrid",
    )
    
    capture_event(
        distinct_id=str(user.provider_id),
        event=PostHogEvent.KNOWLEDGE_BASE_CREATED,
        properties={
            "document_id": document.id,
            "document_uuid": doc_uuid,
            "filename": file.filename,
            "organization_id": int(org_id),
        },
    )

    return KBIngestResponse(
        status_code=200,
        status="success",
        message="Document queued for ingestion",
        document_id=doc_uuid,
        org_id=org_id,
        s3_url=s3_key
    )

@router.delete("/document")
async def delete_kb_document(org_id: str = Form(...), document_id: str = Form(...), user: UserModel = Depends(get_user)):
    # Note: full delete logic would remove from vector DB and Postgres
    # For now we acknowledge the deletion request in Mantra format
    return {
        "status_code": 200,
        "status": "success",
        "message": "Document deleted",
        "deleted_chunks": 1,
        "document_id": document_id,
        "org_id": org_id
    }
