from typing import List, Optional
from pydantic import BaseModel, Field

class ZadarmaConfigurationRequest(BaseModel):
    """Request model for saving Zadarma configuration."""
    api_key: str = Field(..., description="Zadarma API Key")
    api_secret: str = Field(..., description="Zadarma API Secret")
    from_numbers: List[str] = Field(
        default_factory=list, description="Zadarma phone numbers for inbound and outbound calls"
    )

class ZadarmaConfigurationResponse(BaseModel):
    """Response model for retrieving Zadarma configuration."""
    api_key: str = Field(..., description="Zadarma API Key (Masked)")
    from_numbers: List[str] = Field(
        default_factory=list, description="Zadarma phone numbers for inbound and outbound calls"
    )
