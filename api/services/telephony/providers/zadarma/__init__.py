"""Zadarma telephony provider package."""

from typing import Any, Dict

from api.services.telephony.registry import (
    ProviderSpec,
    ProviderUIField,
    ProviderUIMetadata,
    register,
)

from .config import ZadarmaConfigurationRequest, ZadarmaConfigurationResponse
from .provider import ZadarmaProvider
from .transport import create_transport


def _config_loader(value: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": "zadarma",
        "api_key": value.get("api_key"),
        "api_secret": value.get("api_secret"),
        "from_numbers": value.get("from_numbers", []),
    }


_UI_METADATA = ProviderUIMetadata(
    display_name="Zadarma",
    docs_url="https://docs.dograh.com/integrations/telephony/zadarma",
    fields=[
        ProviderUIField(
            name="api_key",
            label="API Key",
            type="text",
            sensitive=True,
            description="Zadarma API Key",
        ),
        ProviderUIField(
            name="api_secret",
            label="API Secret",
            type="password",
            sensitive=True,
            description="Zadarma API Secret",
        ),
        ProviderUIField(
            name="from_numbers",
            label="Phone Numbers",
            type="string-array",
            description="Zadarma phone numbers used for inbound and outbound calls",
        ),
    ],
)


SPEC = ProviderSpec(
    name="zadarma",
    provider_cls=ZadarmaProvider,
    config_loader=_config_loader,
    transport_factory=create_transport,
    transport_sample_rate=8000,
    config_request_cls=ZadarmaConfigurationRequest,
    ui_metadata=_UI_METADATA,
    config_response_cls=ZadarmaConfigurationResponse,
    account_id_credential_field="api_key",
)

register(SPEC)

__all__ = [
    "SPEC",
    "ZadarmaConfigurationRequest",
    "ZadarmaConfigurationResponse",
    "ZadarmaProvider",
    "create_transport",
]
