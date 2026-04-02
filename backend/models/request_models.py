"""
Pydantic Models for DeceptGrid API Endpoints
Defines request/response schemas and validation rules.
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, Literal
from datetime import datetime
import re


# === Steganography Models ===

class StegDecodeResponse(BaseModel):
    """Response model for steganography decode endpoint."""
    message: str = Field(..., description="Decoded message from image")
    success: bool = True


class StegErrorResponse(BaseModel):
    """Error response for steganography operations."""
    message: str
    success: bool = False
    error_type: str


# === Attack Simulation Models ===

class AttackInjectRequest(BaseModel):
    """Request model for attack injection simulation."""
    target: str = Field(..., description="Target meter ID", example="Meter_01")
    value: str = Field(..., description="Injected value", example="999V")
    attacker_ip: str = Field(..., description="Attacker IP address", example="192.168.1.45")

    @validator('attacker_ip')
    def validate_ip(cls, v):
        """Validate IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid IP address format')

        # Check each octet is 0-255
        octets = v.split('.')
        if not all(0 <= int(octet) <= 255 for octet in octets):
            raise ValueError('IP address octets must be 0-255')

        return v

    @validator('target')
    def validate_target(cls, v):
        """Validate target format."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Target cannot be empty')
        return v.strip()


class AttackInjectResponse(BaseModel):
    """Response model for attack injection."""
    status: Literal["accepted"] = "accepted"
    message: str = "Tampering successful"
    logged: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M"))


class StolenLoginRequest(BaseModel):
    """Request model for stolen credential detection."""
    username: str = Field(..., description="Username attempting login", example="engineer_01")
    password: str = Field(..., description="Password provided", example="grid@2024")
    typing_speed: float = Field(
        ...,
        description="Typing speed in characters per second",
        example=0.24,
        ge=0.0,  # Must be >= 0
        le=10.0  # Reasonable upper limit
    )

    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        """Validate password is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v


class StolenLoginResponse(BaseModel):
    """Response model for stolen credential analysis."""
    status: Literal["blocked", "allowed"]
    behavior_score: int = Field(..., description="Behavioral analysis score (0-100)")
    reason: str = Field(..., description="Analysis reason")
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    logged: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M"))


# === Attack Log Models ===

class AttackLogEntry(BaseModel):
    """Model for attack log entries."""
    time: str = Field(..., description="Time in HH:MM format")
    ip: str = Field(..., description="Attacker IP address")
    type: str = Field(..., description="Attack type")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(..., description="Attack severity")
    target: str = Field(..., description="Target system")
    details: str = Field(..., description="Attack details")

    @validator('ip')
    def validate_ip_format(cls, v):
        """Validate IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid IP address format')
        return v

    @validator('time')
    def validate_time_format(cls, v):
        """Validate time format (HH:MM)."""
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM format')


# === General Response Models ===

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# === File Upload Models ===

class FileUploadLimits:
    """Constants for file upload limits."""
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/bmp", "image/tiff"}
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


# === Validation Helpers ===

def validate_image_file(content_type: str, file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded image file.

    Args:
        content_type: MIME type of the file
        file_size: Size of the file in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if file_size > FileUploadLimits.MAX_IMAGE_SIZE:
        return False, f"File too large. Maximum size: {FileUploadLimits.MAX_IMAGE_SIZE // (1024*1024)}MB"

    # Check content type
    if content_type not in FileUploadLimits.ALLOWED_IMAGE_TYPES:
        return False, f"Invalid file type. Allowed types: {', '.join(FileUploadLimits.ALLOWED_IMAGE_TYPES)}"

    return True, None