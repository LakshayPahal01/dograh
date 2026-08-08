"""
Voicelink implementation of the TelephonyProvider interface.
"""

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import aiohttp
from fastapi import HTTPException, Response
from loguru import logger

from api.enums import TelephonyCallStatus, WorkflowRunMode
from api.services.telephony.base import (
    CallInitiationResult,
    NormalizedInboundData,
    ProviderSyncResult,
    TelephonyProvider,
)
from api.utils.common import get_backend_endpoints
from api.services.telephony import ws_auth

if TYPE_CHECKING:
    from fastapi import WebSocket


class VoicelinkProvider(TelephonyProvider):
    """
    Voicelink implementation of TelephonyProvider.
    """
    PROVIDER_NAME = WorkflowRunMode.VOICELINK.value
    WEBHOOK_ENDPOINT = "voicelink-webhook"

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.from_numbers = config.get("from_numbers", [])
        if isinstance(self.from_numbers, str):
            self.from_numbers = [self.from_numbers]

    async def initiate_call(
        self,
        to_number: str,
        webhook_url: str,
        workflow_run_id: Optional[int] = None,
        from_number: Optional[str] = None,
        **kwargs: Any,
    ) -> CallInitiationResult:
        # Placeholder for actual Voicelink outbound call initiation
        logger.info(f"Initiating Voicelink call to {to_number}")
        return CallInitiationResult(
            call_id="mock-voicelink-call-id",
            status="initiated",
            caller_number=from_number or self.from_numbers[0] if self.from_numbers else to_number,
            provider_metadata={},
            raw_response={},
        )

    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        return {"status": "in-progress"}

    async def get_available_phone_numbers(self) -> List[str]:
        return self.from_numbers

    def validate_config(self) -> bool:
        return bool(self.api_key and self.api_secret)

    async def verify_webhook_signature(
        self,
        url: str,
        webhook_data: Dict[str, Any],
        headers: Dict[str, str],
        body: str = "",
        **kwargs: Any
    ) -> bool:
        # Placeholder for Voicelink webhook signature verification
        return True

    async def verify_inbound_signature(
        self,
        url: str,
        webhook_data: Dict[str, Any],
        headers: Dict[str, str],
        body: str = "",
    ) -> bool:
        return True

    async def get_webhook_response(
        self, workflow_id: int, organization_id: int, workflow_run_id: int
    ) -> str:
        _, wss_backend_endpoint = await get_backend_endpoints()
        ws_url = ws_auth.build_media_ws_url(
            wss_backend_endpoint, workflow_id, organization_id, workflow_run_id
        )
        return json.dumps({"action": "connect", "websocket_url": ws_url})

    async def get_call_cost(self, call_id: str) -> Dict[str, Any]:
        return {"cost_usd": 0.0, "duration": 0, "status": "completed"}

    def parse_status_callback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "call_id": data.get("call_id"),
            "status": TelephonyCallStatus.COMPLETED,
            "extra": data,
        }

    async def handle_websocket(
        self,
        websocket: "WebSocket",
        workflow_id: int,
        organization_id: int,
        workflow_run_id: int,
    ) -> None:
        from api.services.pipecat.run_pipeline import run_pipeline_telephony
        
        # Voicelink websocket logic
        msg = await websocket.receive_text()
        start_data = json.loads(msg)
        stream_id = start_data.get("stream_id", "default")
        call_id = start_data.get("call_id", "default")

        await run_pipeline_telephony(
            websocket,
            provider_name=self.PROVIDER_NAME,
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            organization_id=organization_id,
            call_id=call_id,
            transport_kwargs={"stream_id": stream_id, "call_id": call_id},
        )

    @classmethod
    def can_handle_webhook(cls, webhook_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        return "voicelink" in headers.get("user-agent", "").lower() or "voicelink" in webhook_data

    @staticmethod
    def parse_inbound_webhook(webhook_data: Dict[str, Any]) -> NormalizedInboundData:
        return NormalizedInboundData(
            provider=VoicelinkProvider.PROVIDER_NAME,
            call_id=webhook_data.get("call_id", ""),
            from_number=webhook_data.get("from", ""),
            to_number=webhook_data.get("to", ""),
            direction="inbound",
            call_status="ringing",
            account_id=webhook_data.get("account_id", ""),
            from_country="",
            to_country="",
            raw_data=webhook_data,
        )

    @staticmethod
    def validate_account_id(config_data: dict, webhook_account_id: str) -> bool:
        return config_data.get("api_key") == webhook_account_id

    async def configure_inbound(self, address: str, webhook_url: Optional[str]) -> ProviderSyncResult:
        return ProviderSyncResult(ok=True)

    async def validate_phone_number(self, address: str) -> ProviderSyncResult:
        return ProviderSyncResult(ok=True)

    async def start_inbound_stream(
        self, *, websocket_url: str, workflow_run_id: int, normalized_data, backend_endpoint: str
    ):
        return Response(content=json.dumps({"action": "connect", "websocket_url": websocket_url}), media_type="application/json")

    @staticmethod
    def generate_error_response(error_type: str, message: str) -> tuple:
        return Response(content=json.dumps({"error": message}), media_type="application/json")

    @staticmethod
    def generate_validation_error_response(error_type) -> tuple:
        return Response(content=json.dumps({"error": "Validation failed"}), media_type="application/json")

    async def transfer_call(self, destination: str, transfer_id: str, conference_name: str, timeout: int = 30, **kwargs: Any) -> Dict[str, Any]:
        return {"status": "unsupported"}
