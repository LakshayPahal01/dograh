from typing import List, Optional
from pydantic import BaseModel, Field

class VoicelinkConfigurationRequest(BaseModel):
    """Request model for saving Voicelink configuration."""
    api_key: str = Field(..., description="Voicelink API Key")
    api_secret: str = Field(..., description="Voicelink API Secret")
    from_numbers: List[str] = Field(
        default_factory=list, description="Voicelink phone numbers for inbound and outbound calls"
    )

class VoicelinkConfigurationResponse(BaseModel):
    """Response model for retrieving Voicelink configuration."""
    api_key: str = Field(..., description="Voicelink API Key (Masked)")
    from_numbers: List[str] = Field(
        default_factory=list, description="Voicelink phone numbers for inbound and outbound calls"
    )
