"""
Attack Simulation Routes for DeceptGrid API
Handles false data injection and stolen credential detection.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from models.request_models import (
    AttackInjectRequest,
    AttackInjectResponse,
    StolenLoginRequest,
    StolenLoginResponse,
    ErrorResponse
)
from utils.logging_utils import attack_logger, behavioral_analyzer

router = APIRouter()


@router.post("/inject",
            response_model=AttackInjectResponse,
            responses={
                400: {"model": ErrorResponse, "description": "Invalid request data"},
                500: {"model": ErrorResponse, "description": "Logging failed"}
            },
            summary="Simulate false data injection attack",
            description="Log a false data injection attack attempt for honeypot simulation")
async def inject_attack(request: AttackInjectRequest):
    """
    Simulate a false data injection attack and log it for monitoring.

    This endpoint makes attackers believe they successfully injected false data
    into the smart grid system, while actually logging the attempt and protecting
    the real infrastructure.
    """
    try:
        # Generate log entry for the false data injection
        log_entry = behavioral_analyzer.generate_log_entry(
            ip=request.attacker_ip,
            attack_type="FalseDataInjection",
            severity="HIGH",
            target="Honeypot_01",  # Convert meter target to honeypot target
            details=f"Attempted to set {request.target} to {request.value}"
        )

        # Log the attack attempt
        log_success = await attack_logger.log_attack(log_entry)

        if not log_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log attack attempt"
            )

        # Return honeypot response - make attacker think they succeeded
        return AttackInjectResponse(
            status="accepted",
            message="Tampering successful",
            logged=True,
            timestamp=log_entry["time"]
        )

    except ValueError as e:
        # Handle validation errors from logging utility
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Attack logging failed: {str(e)}"
        )


@router.post("/stolen-login",
            response_model=StolenLoginResponse,
            responses={
                400: {"model": ErrorResponse, "description": "Invalid request data"},
                500: {"model": ErrorResponse, "description": "Analysis failed"}
            },
            summary="Detect stolen credential attempts",
            description="Analyze login behavior to detect potential credential theft")
async def detect_stolen_login(request: StolenLoginRequest):
    """
    Analyze login attempt for behavioral anomalies that suggest credential theft.

    Uses typing pattern analysis to detect if credentials might have been stolen.
    Suspicious behavior (slow typing) results in login being blocked and logged.
    """
    try:
        # Perform behavioral analysis
        analysis = behavioral_analyzer.analyze_typing_pattern(
            typing_speed=request.typing_speed,
            username=request.username
        )

        # Determine if login should be blocked
        is_blocked = analysis["is_suspicious"]
        login_status = "blocked" if is_blocked else "allowed"

        # If suspicious behavior detected, log it as an attack
        if is_blocked:
            log_entry = behavioral_analyzer.generate_log_entry(
                ip="Unknown",  # Request doesn't include IP, could be enhanced
                attack_type="StolenCredential",
                severity="HIGH" if analysis["behavior_score"] < 40 else "MEDIUM",
                target="AuthenticationSystem",
                details=f"Suspicious login attempt for {request.username} "
                       f"(typing speed: {request.typing_speed:.2f} chars/sec, "
                       f"score: {analysis['behavior_score']})"
            )

            # Log the suspicious attempt
            log_success = await attack_logger.log_attack(log_entry)

            if not log_success:
                # Still return analysis even if logging fails
                pass

        # Return analysis results
        return StolenLoginResponse(
            status=login_status,
            behavior_score=analysis["behavior_score"],
            reason=analysis["reason"],
            confidence=analysis["confidence"],
            risk_level=analysis["risk_level"],
            logged=is_blocked,  # Only log if blocked
            timestamp=datetime.now().strftime("%H:%M")
        )

    except ValueError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Behavioral analysis failed: {str(e)}"
        )


@router.get("/logs",
           summary="Get recent attack logs",
           description="Retrieve recent attack log entries (for testing/debugging)")
async def get_attack_logs(limit: int = 10):
    """
    Retrieve recent attack log entries.

    This endpoint is useful for testing and debugging to verify that attacks
    are being logged correctly.
    """
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )

        logs = await attack_logger.get_logs(limit=limit)

        return {
            "success": True,
            "logs": logs,
            "count": len(logs),
            "timestamp": datetime.now().strftime("%H:%M")
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}"
        )