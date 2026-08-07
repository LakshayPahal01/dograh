from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
import uuid

from api.db import db_client

router = APIRouter(prefix="/sip", tags=["mantra-bridge-sip"])

class SetupInboundRequest(BaseModel):
    number: str
    org_id: int
    provider: str

class SetupInboundResponse(BaseModel):
    status: str
    sip_trunk_id: str
    sip_dispatch_rule_id: str
    sip_uri: str
    message: Optional[str] = None

@router.post("/inbound/setup", response_model=SetupInboundResponse)
async def setup_inbound(request: SetupInboundRequest):
    logger.info(f"[Mantra Bridge] Inbound setup requested for {request.number}")
    
    # 1. Find the telephony config for this provider in this org
    configs = await db_client.list_telephony_configurations_by_provider(
        organization_id=request.org_id, provider=request.provider.lower()
    )
    if not configs:
        # Fallback to the first available config for the org
        configs = await db_client.list_telephony_configurations(request.org_id)
        if not configs:
            raise HTTPException(status_code=400, detail="No telephony configuration found for this organization.")
    
    config = configs[0]
    
    # 2. Check if phone number already exists
    phone_numbers = await db_client.list_phone_numbers_for_config(config.id)
    exists = False
    for pn in phone_numbers:
        if pn.address == request.number:
            exists = True
            break
            
    if not exists:
        # 3. Add phone number
        await db_client.create_phone_number(
            organization_id=request.org_id,
            telephony_configuration_id=config.id,
            address=request.number,
            label=f"{request.provider.capitalize()} Bridge Number"
        )
        
    return SetupInboundResponse(
        status="success",
        sip_trunk_id=str(config.id),
        sip_dispatch_rule_id="default_dispatch",
        sip_uri=f"sip:{request.number}@{request.provider}.sip.dograh.com"
    )

class CreateSipTrunkPayload(BaseModel):
    name: str
    address: str
    numbers: str
    authUsername: Optional[str] = ""
    authPassword: Optional[str] = ""

class CreateSipTrunkResponse(BaseModel):
    status: str
    sip_trunk_id: str
    message: Optional[str] = None

@router.post("/trunks/outbound/{providerSlug}", response_model=CreateSipTrunkResponse)
async def create_outbound_trunk(providerSlug: str, request: CreateSipTrunkPayload):
    logger.info(f"[Mantra Bridge] Outbound setup requested for {request.numbers}")
    
    return CreateSipTrunkResponse(
        status="success",
        sip_trunk_id=f"outbound_{providerSlug}_{uuid.uuid4().hex[:8]}"
    )

@router.delete("/trunks/outbound/{sip_trunk_id}")
async def delete_outbound_trunk(sip_trunk_id: str):
    return {"status": "success"}

@router.delete("/trunks/inbound/{sip_trunk_id}")
async def delete_inbound_trunk(sip_trunk_id: str):
    return {"status": "success"}
