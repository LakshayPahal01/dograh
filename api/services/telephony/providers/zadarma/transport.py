"""Zadarma transport factory."""

from typing import Any
from api.services.telephony.providers.twilio.serializers import TwilioFrameSerializer
from pipecat.transports.network.websocket_server import (
    WebsocketServerParams,
    WebsocketServerTransport,
)

async def create_transport(
    websocket: Any,
    stream_id: str,
    call_id: str,
    workflow_id: int,
    workflow_run_id: int,
    organization_id: int,
    telephony_configuration_id: int,
    **kwargs: Any,
) -> WebsocketServerTransport:
    """Create a transport for Zadarma connections."""
    
    # We use TwilioFrameSerializer as a baseline for audio processing
    serializer = TwilioFrameSerializer(stream_sid=stream_id)
    
    params = WebsocketServerParams(
        audio_out_enabled=True,
        add_wav_header=False,
        audio_out_sample_rate=8000,
        audio_in_sample_rate=8000,
        audio_in_channels=1,
        audio_out_channels=1,
    )
    
    transport = WebsocketServerTransport(
        websocket_client=websocket,
        params=params,
        serializer=serializer,
    )
    
    return transport
