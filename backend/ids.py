"""
Layer 3: Machine Learning Intrusion Detection System (IDS)
Hybrid approach combining Isolation Forest anomaly detection with rule-based scoring.
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

import joblib
from sklearn.ensemble import IsolationForest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RiskAction(Enum):
    """Risk assessment actions."""
    ALLOW = "allow"
    CHALLENGE = "challenge"
    BLOCK = "block"


class RiskSeverity(Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UserBaseline:
    """Expected normal behavior for a user."""
    user_id: str
    avg_request_rate: float  # requests per hour
    avg_session_duration: float  # minutes
    typical_hours: List[int]  # 0-23 hours when user accesses
    typical_days: List[int]  # 0-6 days of week
    avg_endpoints: int  # typical unique endpoints per session
    avg_data_volume: float  # MB per session


@dataclass
class IDSAssessment:
    """Result of IDS analysis."""
    user_id: str
    client_ip: str
    timestamp: datetime
    risk_score: float  # 0-100
    action: RiskAction
    reasons: List[str]
    ml_score: float  # Isolation Forest anomaly score
    rule_score: float  # Rule-based score
    session_id: Optional[str] = None


class RuleBasedScorer:
    """Rule-based risk scoring system."""

    def __init__(self, baseline: UserBaseline):
        self.baseline = baseline

    def score_request_rate(self, current_rate: float) -> Tuple[float, str]:
        """Score based on request frequency."""
        if self.baseline.avg_request_rate == 0:
            return 0.0, "No baseline established"

        ratio = current_rate / max(self.baseline.avg_request_rate, 0.1)

        if ratio > 5:
            return 100.0, f"Extreme spike: {ratio:.1f}x normal rate"
        elif ratio > 3:
            return 80.0, f"High spike: {ratio:.1f}x normal rate"
        elif ratio > 1.5:
            return 40.0, f"Moderate increase: {ratio:.1f}x normal rate"
        else:
            return 0.0, "Normal request rate"

    def score_time_anomaly(self, current_hour: int, current_day: int) -> Tuple[float, str]:
        """Score based on unusual access times."""
        reasons = []
        score = 0.0

        # Weekend access scoring
        if current_day in [5, 6]:  # Saturday, Sunday
            if current_day not in self.baseline.typical_days:
                score += 30.0
                reasons.append("Weekend access (unusual for this user)")

        # Off-hours access
        if current_hour not in self.baseline.typical_hours:
            score += 25.0
            reasons.append(f"Off-hours access at {current_hour:02d}:00 (unusual)")

        # Extreme hours (midnight-4am)
        if 0 <= current_hour <= 4:
            score += 20.0
            reasons.append("Extreme off-hours (midnight-4am)")

        return min(score, 100.0), " | ".join(reasons) if reasons else "Normal access time"

    def score_endpoint_scanning(self, unique_endpoints: int) -> Tuple[float, str]:
        """Score based on endpoint enumeration attempts."""
        if unique_endpoints > self.baseline.avg_endpoints + 10:
            return 80.0, f"Endpoint scanning detected: {unique_endpoints} endpoints in single session"
        elif unique_endpoints > self.baseline.avg_endpoints + 5:
            return 50.0, f"Unusual endpoint access: {unique_endpoints} endpoints"
        elif unique_endpoints > self.baseline.avg_endpoints + 2:
            return 20.0, f"Slightly elevated endpoint access: {unique_endpoints}"
        else:
            return 0.0, "Normal endpoint access pattern"

    def score_data_transfer(self, data_volume_mb: float) -> Tuple[float, str]:
        """Score based on data volume."""
        baseline_volume = max(self.baseline.avg_data_volume, 0.1)

        if data_volume_mb > baseline_volume * 10:
            return 90.0, f"Extreme data exfiltration: {data_volume_mb:.1f} MB ({(data_volume_mb/baseline_volume):.0f}x normal)"
        elif data_volume_mb > baseline_volume * 5:
            return 70.0, f"Data exfiltration detected: {data_volume_mb:.1f} MB"
        elif data_volume_mb > baseline_volume * 2:
            return 40.0, f"High data transfer: {data_volume_mb:.1f} MB"
        else:
            return 0.0, "Normal data volume"

    def score_session_duration(self, duration_minutes: float) -> Tuple[float, str]:
        """Score based on session length."""
        baseline_duration = max(self.baseline.avg_session_duration, 1.0)

        if duration_minutes > baseline_duration * 5:
            return 60.0, f"Prolonged session: {duration_minutes:.0f} min ({(duration_minutes/baseline_duration):.0f}x normal)"
        elif duration_minutes > baseline_duration * 3:
            return 35.0, f"Extended session: {duration_minutes:.0f} minutes"
        else:
            return 0.0, "Normal session duration"

    def compute_score(
        self,
        request_rate: float,
        session_duration: float,
        hour: int,
        day: int,
        unique_endpoints: int,
        data_volume: float,
    ) -> Tuple[float, List[str]]:
        """Aggregate all rule-based scores."""
        scores = []
        reasons = []

        # Score each rule
        rate_score, rate_reason = self.score_request_rate(request_rate)
        scores.append(rate_score)
        reasons.append(f"Request rate: {rate_reason}")

        time_score, time_reason = self.score_time_anomaly(hour, day)
        scores.append(time_score)
        reasons.append(f"Time: {time_reason}")

        endpoint_score, endpoint_reason = self.score_endpoint_scanning(unique_endpoints)
        scores.append(endpoint_score)
        reasons.append(f"Endpoints: {endpoint_reason}")

        data_score, data_reason = self.score_data_transfer(data_volume)
        scores.append(data_score)
        reasons.append(f"Data: {data_reason}")

        duration_score, duration_reason = self.score_session_duration(session_duration)
        scores.append(duration_score)
        reasons.append(f"Duration: {duration_reason}")

        # Aggregate: average with weight toward highest score
        if not scores:
            return 0.0, reasons

        sorted_scores = sorted(scores, reverse=True)
        weighted_score = (sorted_scores[0] * 0.5 + sum(sorted_scores[1:]) / len(sorted_scores[1:]) * 0.5) if len(sorted_scores) > 1 else sorted_scores[0]

        return min(weighted_score, 100.0), [r for r in reasons if r]


class MLAnomalyDetector:
    """ML-based anomaly detection using Isolation Forest."""

    def __init__(self, model_path: Optional[str] = None):
        """Initialize detector with optional pre-trained model."""
        self.model = None
        self.scaler_stats = None

        if model_path:
            try:
                self.model = joblib.load(model_path)
                logger.info(f"Loaded pre-trained IDS model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}. Will use zero-score.")

    def train(self, training_data: np.ndarray):
        """Train Isolation Forest on normal behavior."""
        self.model = IsolationForest(
            contamination=0.1,  # Expect ~10% anomalies
            random_state=42,
            n_estimators=100,
        )
        self.model.fit(training_data)

        # Store statistics for normalization
        self.scaler_stats = {
            "mean": training_data.mean(axis=0),
            "std": training_data.std(axis=0),
        }

    def predict_anomaly_score(self, features: np.ndarray) -> float:
        """
        Predict anomaly score 0-100.
        Higher = more anomalous.
        """
        if self.model is None:
            return 0.0

        try:
            # Ensure features is 2D
            if features.ndim == 1:
                features = features.reshape(1, -1)

            # Get raw anomaly score (-1 for anomalies, +1 for normal)
            raw_score = self.model.score_samples(features)[0]

            # Convert to 0-100 scale (roughly)
            # Raw scores typically range -1 to +1
            normalized = (1 - raw_score) / 2  # Convert to 0-1
            anomaly_score = normalized * 100  # Scale to 0-100

            return float(np.clip(anomaly_score, 0, 100))
        except Exception as e:
            logger.error(f"Error computing anomaly score: {e}")
            return 0.0

    def save(self, path: str):
        """Save trained model."""
        if self.model:
            joblib.dump(self.model, path)
            logger.info(f"Saved IDS model to {path}")


class IDS:
    """Main Intrusion Detection System orchestrator."""

    def __init__(self, ml_model_path: Optional[str] = None):
        """Initialize IDS with optional pre-trained model."""
        self.ml_detector = MLAnomalyDetector(ml_model_path)
        self.logger = logger

    def _normalize_features(self, features: Dict[str, float]) -> np.ndarray:
        """Normalize features for ML model."""
        # Order matters: must match training data order
        return np.array([
            features.get("request_rate", 0),
            features.get("session_duration", 0),
            features.get("hour_of_day", 12),
            features.get("day_of_week", 3),
            features.get("unique_endpoints", 0),
            features.get("data_volume", 0),
        ], dtype=float)

    async def assess_risk(
        self,
        db: AsyncSession,
        user_id: str,
        client_ip: str,
        features: Dict[str, float],
        session_id: Optional[str] = None,
    ) -> IDSAssessment:
        """
        Assess risk for a request using hybrid ML + rules approach.
        Returns IDSAssessment with action recommendation.
        """
        from models.security import User  # Import here to avoid circular dependency

        # Get user baseline
        try:
            user_stmt = select(User).where(User.id == user_id)
            user = (await db.execute(user_stmt)).scalar_one_or_none()

            if not user:
                # Unknown user: elevated risk
                baseline = self._default_baseline(user_id)
                ml_score = 75.0
            else:
                baseline = await self._get_or_create_baseline(db, user_id)
                ml_features = self._normalize_features(features)
                ml_score = self.ml_detector.predict_anomaly_score(ml_features)

        except Exception as e:
            self.logger.error(f"Error fetching baseline: {e}")
            baseline = self._default_baseline(user_id)
            ml_score = 50.0

        # Compute rule-based score
        scorer = RuleBasedScorer(baseline)
        rule_score, reasons = scorer.compute_score(
            request_rate=features.get("request_rate", 0),
            session_duration=features.get("session_duration", 0),
            hour=int(features.get("hour_of_day", 12)),
            day=int(features.get("day_of_week", 3)),
            unique_endpoints=int(features.get("unique_endpoints", 0)),
            data_volume=features.get("data_volume", 0),
        )

        # Hybrid score: 60% ML, 40% rules
        final_score = (ml_score * 0.6) + (rule_score * 0.4)
        final_score = float(np.clip(final_score, 0, 100))

        # Determine action
        if final_score >= 80:
            action = RiskAction.BLOCK
        elif final_score >= 50:
            action = RiskAction.CHALLENGE
        else:
            action = RiskAction.ALLOW

        assessment = IDSAssessment(
            user_id=user_id,
            client_ip=client_ip,
            timestamp=datetime.utcnow(),
            risk_score=final_score,
            action=action,
            reasons=reasons,
            ml_score=ml_score,
            rule_score=rule_score,
            session_id=session_id,
        )

        # Log assessment
        await self._log_assessment(db, assessment)

        return assessment

    async def _get_or_create_baseline(self, db: AsyncSession, user_id: str) -> UserBaseline:
        """Get user baseline or create default."""
        from models.security import UserBaseline as UserBaselineModel

        stmt = select(UserBaselineModel).where(UserBaselineModel.user_id == user_id)
        result = await db.execute(stmt)
        baseline_row = result.scalar_one_or_none()

        if baseline_row:
            return UserBaseline(
                user_id=user_id,
                avg_request_rate=baseline_row.avg_request_rate,
                avg_session_duration=baseline_row.avg_session_duration,
                typical_hours=baseline_row.typical_hours or list(range(9, 18)),
                typical_days=baseline_row.typical_days or list(range(0, 5)),
                avg_endpoints=baseline_row.avg_endpoints,
                avg_data_volume=baseline_row.avg_data_volume,
            )

        return self._default_baseline(user_id)

    def _default_baseline(self, user_id: str) -> UserBaseline:
        """Default baseline for unknown users."""
        return UserBaseline(
            user_id=user_id,
            avg_request_rate=2.0,  # 2 req/hour
            avg_session_duration=30.0,  # 30 minutes
            typical_hours=list(range(9, 18)),  # 9 AM - 5 PM
            typical_days=list(range(0, 5)),  # Monday-Friday
            avg_endpoints=3,
            avg_data_volume=5.0,  # 5 MB
        )

    async def _log_assessment(self, db: AsyncSession, assessment: IDSAssessment):
        """Log IDS assessment to database."""
        try:
            from models.security import IDSLog, EventType, Severity

            severity_map = {
                RiskAction.ALLOW: Severity.INFO,
                RiskAction.CHALLENGE: Severity.WARN,
                RiskAction.BLOCK: Severity.CRIT,
            }

            log = IDSLog(
                user_id=assessment.user_id,
                client_ip=assessment.client_ip,
                risk_score=assessment.risk_score,
                action=assessment.action.value,
                reasons=assessment.reasons,
                ml_score=assessment.ml_score,
                rule_score=assessment.rule_score,
            )
            db.add(log)
            await db.flush()

            self.logger.info(
                f"IDS Assessment - User: {assessment.user_id}, IP: {assessment.client_ip}, "
                f"Score: {assessment.risk_score:.1f}, Action: {assessment.action.value}"
            )
        except Exception as e:
            self.logger.error(f"Failed to log IDS assessment: {e}")
