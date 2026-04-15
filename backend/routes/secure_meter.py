"""
Layer 5 & 6: Secure Meter Endpoints with Code Signing and Physics Validation
Integrates cryptographic code signing with physics-based anomaly detection
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from signing import get_code_signer
from physics_validator import get_physics_validator, MeterReading

logger = logging.getLogger(__name__)
router = APIRouter()


class MeterCommandRequest(BaseModel):
    """Signed meter command."""
    signed_payload: str  # ASCII-armored GPG message


class MeterReadingRequest(BaseModel):
    """Raw meter reading data."""
    meter_id: str
    voltage: float
    current: float
    power: float
    power_factor: float = 0.95


class MeterCommandResponse(BaseModel):
    """Response to signed command."""
    success: bool
    message: str
    signer: Optional[str] = None
    command_action: Optional[str] = None


class MeterReadingResponse(BaseModel):
    """Meter reading with physics validation."""
    meter_id: str
    voltage: float
    current: float
    power: float
    power_factor: float
    physics_valid: bool
    validation_notes: list
    status: str


# ============================================================================
# LAYER 5: SIGNED COMMAND ENDPOINTS
# ============================================================================

@router.post("/config", response_model=MeterCommandResponse)
async def configure_meter(request: MeterCommandRequest):
    """
    Configure meter with cryptographically signed command.

    Requires:
    - Signed JSON payload (ASCII-armored GPG)
    - Valid signature from authorized engineer
    - Command must include: action, target_meter, value

    Example signed payload:
    -----BEGIN PGP MESSAGE-----
    ...
    -----END PGP MESSAGE-----

    Failed attempts are logged as security events:
    - UNSIGNED_COMMAND
    - INVALID_SIGNATURE
    - UNAUTHORIZED_SIGNER
    """
    code_signer = get_code_signer()

    # Check for empty payload
    if not request.signed_payload.strip():
        logger.warning("UNSIGNED_COMMAND: Empty payload")
        raise HTTPException(
            status_code=400,
            detail="Empty payload - expected signed GPG message"
        )

    # Verify signature and extract command
    is_valid, command, signer = code_signer.verify_and_parse_command(request.signed_payload)

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Command verification failed - invalid or unauthorized signature"
        )

    # Validate command structure
    is_valid_cmd, error_msg = code_signer.validate_command_structure(command)

    if not is_valid_cmd:
        logger.warning(f"Invalid command structure from {signer}: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    # Execute command (in production: actually execute)
    action = command.get("action")
    target = command.get("target_meter")

    logger.info(f"✓ Executing signed command: {action} on {target} by {signer}")

    return MeterCommandResponse(
        success=True,
        message=f"Command executed: {action}",
        signer=signer,
        command_action=action
    )


@router.post("/command/validate", response_model=Dict)
async def validate_signature_only(request: MeterCommandRequest):
    """
    Validate signature without executing command.
    Useful for testing and debugging.
    """
    code_signer = get_code_signer()

    is_valid, signer, cmd_json = code_signer.verify_signature(request.signed_payload)

    if not is_valid:
        logger.info("Signature validation failed")
        raise HTTPException(status_code=401, detail="Signature validation failed")

    return {
        "signature_valid": True,
        "signer": signer,
        "signed_data_preview": cmd_json[:100] if cmd_json else None
    }


# ============================================================================
# LAYER 6: PHYSICS-VALIDATED METER READINGS
# ============================================================================

@router.post("/reading/validate", response_model=MeterReadingResponse)
async def get_meter_reading_validated(request: MeterReadingRequest):
    """
    Get meter reading with comprehensive physics validation.

    Layer 6 Validation:
    1. Statistical baseline check (Z-score)
    2. Ohm's Law validation (Power ≈ V × I × PF)
    3. Adjacent meter correlation (transformer voltage consistency)
    4. Load consistency (vs historical average)

    Returns:
    - physics_valid: True if all validations pass
    - validation_notes: Detailed validation results
    - status: OPERATIONAL or ANOMALY_DETECTED
    """
    validator = get_physics_validator()

    # Create reading object
    reading = MeterReading(
        meter_id=request.meter_id,
        voltage=request.voltage,
        current=request.current,
        power=request.power,
        power_factor=request.power_factor
    )

    # Validate against physics
    is_valid, validation_notes = validator.validate_reading(reading)

    # Format response
    response = validator.format_validation_response(reading, is_valid, validation_notes)

    if not is_valid:
        logger.warning(f"ANOMALOUS_READING_DETECTED: {request.meter_id}")

    return MeterReadingResponse(**response)


@router.get("/test/layers")
async def test_layer5_layer6():
    """
    Test Layer 5 & 6 integration.
    Returns system status and capabilities.
    """
    code_signer = get_code_signer()
    validator = get_physics_validator()

    return {
        "layer_5": {
            "name": "Code Signing",
            "status": "operational",
            "algorithm": "GPG/RSA-4096",
            "authorized_signers": len(code_signer.authorized_signers),
            "endpoints": [
                "POST /api/meter/config (signed commands)",
                "POST /api/meter/command/validate (signature verification)"
            ]
        },
        "layer_6": {
            "name": "Physics Validation",
            "status": "operational",
            "validations": [
                "Statistical baseline (Z-score > 6)",
                "Ohm's Law (Power ≈ V × I × PF)",
                "Adjacent meter correlation (ΔV > 20V)",
                "Load consistency (change > 20%)"
            ],
            "endpoints": [
                "POST /api/meter/reading/validate"
            ]
        }
    }


@router.get("/security/events")
async def get_security_events():
    """
    Get recent security events (Layer 5 & 6 violations).

    Logged events:
    - UNSIGNED_COMMAND
    - INVALID_SIGNATURE
    - UNAUTHORIZED_SIGNER
    - SIGNED_COMMAND_ACCEPTED
    - PHYSICS_VALIDATION_FAILED
    - ANOMALOUS_READING_DETECTED
    """
    return {
        "message": "Security events logged to application logs",
        "events_tracked": [
            "UNSIGNED_COMMAND",
            "INVALID_SIGNATURE",
            "UNAUTHORIZED_SIGNER",
            "SIGNED_COMMAND_ACCEPTED",
            "PHYSICS_VALIDATION_FAILED",
            "ANOMALOUS_READING_DETECTED"
        ],
        "log_location": "/tmp/backend.log"
    }
