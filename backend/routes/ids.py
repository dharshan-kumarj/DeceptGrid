"""
Layer 3 & 4 IDS and Honeypot API Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import numpy as np
from ids import IDS, RuleBasedScorer, UserBaseline, MLAnomalyDetector
from honeypot import HoneypotSystem

router = APIRouter()
ids_system = IDS("ml_models/ids_model.pkl")
honeypot_system = HoneypotSystem()


class RiskAssessmentRequest(BaseModel):
    """Request model for risk assessment."""
    user_id: str
    client_ip: str
    request_rate: float
    session_duration: float
    hour_of_day: int
    day_of_week: int
    unique_endpoints: int
    data_volume: float


class RuleScoreRequest(BaseModel):
    """Request for rule-based scoring test."""
    request_rate: float
    session_duration: float
    hour_of_day: int
    day_of_week: int
    unique_endpoints: int
    data_volume: float


class MLAnomalyRequest(BaseModel):
    """Request for ML anomaly detection test."""
    request_rate: float
    session_duration: float
    hour_of_day: int
    day_of_week: int
    unique_endpoints: int
    data_volume: float


# ============================================================================
# LAYER 3: IDS ENDPOINTS
# ============================================================================

@router.post("/assess-risk")
async def assess_risk(request: RiskAssessmentRequest):
    """
    Assess risk using hybrid IDS (ML 60% + Rules 40%).

    Returns risk score (0-100) and action (ALLOW/CHALLENGE/BLOCK).
    """
    try:
        # Create user baseline (default)
        baseline = UserBaseline(
            user_id=request.user_id,
            avg_request_rate=2.5,
            avg_session_duration=45,
            typical_hours=list(range(9, 18)),
            typical_days=list(range(0, 5)),
            avg_endpoints=3,
            avg_data_volume=5.0
        )

        rule_scorer = RuleBasedScorer(baseline)
        ml_detector = MLAnomalyDetector("ml_models/ids_model.pkl")

        # Get scores
        rule_score, rule_reasons = rule_scorer.compute_score(
            request_rate=request.request_rate,
            session_duration=request.session_duration,
            hour=request.hour_of_day,
            day=request.day_of_week,
            unique_endpoints=request.unique_endpoints,
            data_volume=request.data_volume
        )

        features = np.array([[
            request.request_rate,
            request.session_duration,
            request.hour_of_day,
            request.day_of_week,
            request.unique_endpoints,
            request.data_volume
        ]])

        ml_score = ml_detector.predict_anomaly_score(features)

        # Hybrid scoring
        hybrid_score = (ml_score * 0.6) + (rule_score * 0.4)

        # Decision
        if hybrid_score >= 80:
            action = "BLOCK"
        elif hybrid_score >= 50:
            action = "CHALLENGE"
        else:
            action = "ALLOW"

        return {
            "user_id": request.user_id,
            "client_ip": request.client_ip,
            "ml_score": round(ml_score, 1),
            "rule_score": round(rule_score, 1),
            "hybrid_score": round(hybrid_score, 1),
            "action": action,
            "rule_reasons": rule_reasons,
            "risk_level": "LOW" if hybrid_score < 50 else "MEDIUM" if hybrid_score < 80 else "HIGH"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rule-score")
async def test_rule_scoring(request: RuleScoreRequest):
    """
    Test rule-based scoring system only.
    """
    try:
        baseline = UserBaseline(
            user_id="test",
            avg_request_rate=2.5,
            avg_session_duration=45,
            typical_hours=list(range(9, 18)),
            typical_days=list(range(0, 5)),
            avg_endpoints=3,
            avg_data_volume=5.0
        )

        scorer = RuleBasedScorer(baseline)
        score, reasons = scorer.compute_score(
            request_rate=request.request_rate,
            session_duration=request.session_duration,
            hour=request.hour_of_day,
            day=request.day_of_week,
            unique_endpoints=request.unique_endpoints,
            data_volume=request.data_volume
        )

        return {
            "rule_score": round(score, 1),
            "reasons": reasons,
            "data": {
                "request_rate": request.request_rate,
                "session_duration": request.session_duration,
                "hour": request.hour_of_day,
                "day": request.day_of_week,
                "endpoints": request.unique_endpoints,
                "data_volume": request.data_volume
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml-anomaly")
async def test_ml_anomaly(request: MLAnomalyRequest):
    """
    Test ML anomaly detection system only.
    """
    try:
        detector = MLAnomalyDetector("ml_models/ids_model.pkl")

        features = np.array([[
            request.request_rate,
            request.session_duration,
            request.hour_of_day,
            request.day_of_week,
            request.unique_endpoints,
            request.data_volume
        ]])

        score = detector.predict_anomaly_score(features)

        return {
            "ml_score": round(score, 1),
            "classification": "ANOMALY" if score >= 50 else "NORMAL",
            "confidence": round(score, 1),
            "data": {
                "request_rate": request.request_rate,
                "session_duration": request.session_duration,
                "hour": request.hour_of_day,
                "day": request.day_of_week,
                "endpoints": request.unique_endpoints,
                "data_volume": request.data_volume
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LAYER 4: HONEYPOT ENDPOINTS
# ============================================================================

@router.get("/honeypot/meters")
async def get_honeypot_meters():
    """
    Get list of active honeypot meters.
    """
    try:
        meters = list(honeypot_system.meters.keys())
        return {
            "active_meters": meters,
            "count": len(meters),
            "status": "operational"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/honeypot/meter/{meter_id}/voltage")
async def get_honeypot_voltage(meter_id: str):
    """
    Get voltage data from honeypot meter.

    Available meters: SM-HONEY-001, SM-HONEY-002, SM-HONEY-003
    """
    try:
        if meter_id not in honeypot_system.meters:
            raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

        meter = honeypot_system.meters[meter_id]
        response = meter.generate_response()

        return {
            "meter_id": meter_id,
            "voltage": round(response.voltage, 2),
            "current": round(response.current, 2),
            "power_factor": round(response.power_factor, 3),
            "frequency": 50.0,
            "status": "operational",
            "canary_token": response._canary_token[:32]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/honeypot/meter/{meter_id}/status")
async def get_honeypot_status(meter_id: str):
    """
    Get status from honeypot meter.
    """
    try:
        if meter_id not in honeypot_system.meters:
            raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

        meter = honeypot_system.meters[meter_id]
        status = meter.generate_status()

        return {
            "meter_id": meter_id,
            **status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/honeypot/meter/{meter_id}/config")
async def get_honeypot_config(meter_id: str):
    """
    Get configuration from honeypot meter.
    """
    try:
        if meter_id not in honeypot_system.meters:
            raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

        meter = honeypot_system.meters[meter_id]
        config = meter.generate_config()

        return {
            "meter_id": meter_id,
            **config
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/honeypot/test")
async def test_honeypot_system():
    """
    Test all honeypot meters and return their responses.
    """
    try:
        results = {}

        for meter_id in honeypot_system.meters:
            meter = honeypot_system.meters[meter_id]
            response = meter.generate_response()
            status = meter.generate_status()
            config = meter.generate_config()

            results[meter_id] = {
                "voltage": round(response.voltage, 2),
                "current": round(response.current, 2),
                "power_factor": round(response.power_factor, 3),
                "battery": round(status.get("battery", 0), 1),
                "signal_strength": round(status.get("signal_strength", 0), 1),
                "model": config.get("model", "Unknown"),
                "serial": config.get("serial", "Unknown"),
                "token": response._canary_token[:20] + "..."
            }

        return {
            "system": "honeypot",
            "status": "operational",
            "meters_tested": len(results),
            "meters": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TESTING ENDPOINTS
# ============================================================================

@router.get("/test/scenarios")
async def get_test_scenarios():
    """
    Get predefined test scenarios for Layer 3 & 4 testing.
    """
    scenarios = {
        "normal_user": {
            "description": "Normal user during business hours",
            "data": {
                "request_rate": 2.5,
                "session_duration": 40,
                "hour_of_day": 14,
                "day_of_week": 2,
                "unique_endpoints": 3,
                "data_volume": 4.5
            },
            "expected_action": "ALLOW"
        },
        "high_request_rate": {
            "description": "Unusually high request rate (potential brute force)",
            "data": {
                "request_rate": 10,
                "session_duration": 120,
                "hour_of_day": 14,
                "day_of_week": 2,
                "unique_endpoints": 5,
                "data_volume": 20
            },
            "expected_action": "CHALLENGE or BLOCK"
        },
        "off_hours_scanning": {
            "description": "Off-hours access with endpoint scanning",
            "data": {
                "request_rate": 5,
                "session_duration": 90,
                "hour_of_day": 2,
                "day_of_week": 6,
                "unique_endpoints": 15,
                "data_volume": 50
            },
            "expected_action": "CHALLENGE"
        },
        "data_exfiltration": {
            "description": "Suspicious data transfer pattern",
            "data": {
                "request_rate": 3,
                "session_duration": 180,
                "hour_of_day": 13,
                "day_of_week": 1,
                "unique_endpoints": 8,
                "data_volume": 200
            },
            "expected_action": "BLOCK"
        },
        "brute_force": {
            "description": "Classic brute force attack pattern",
            "data": {
                "request_rate": 15,
                "session_duration": 30,
                "hour_of_day": 13,
                "day_of_week": 1,
                "unique_endpoints": 50,
                "data_volume": 500
            },
            "expected_action": "BLOCK"
        }
    }

    return {
        "scenarios": scenarios,
        "usage": "Pass scenario data to /ids/assess-risk or /ids/rule-score or /ids/ml-anomaly endpoints"
    }
