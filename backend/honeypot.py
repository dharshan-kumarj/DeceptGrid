"""
Layer 4: Honeypot Deception System
Fake smart meters that detect and log intrusion attempts.
"""

import logging
import random
import uuid
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class HoneypotResponse:
    """Standard response from honeypot."""
    meter_id: str
    voltage: float
    current: float
    power_factor: float
    status: str
    timestamp: str
    _canary_token: str  # Hidden tracking token


class HoneypotMeter:
    """Single honeypot meter with deceptive responses."""

    def __init__(self, meter_id: str, network: str = "192.168.10.x"):
        """
        Initialize honeypot meter.
        meter_id: identifier (SM-HONEY-001, etc)
        network: network segment where this meter is advertised
        """
        self.meter_id = meter_id
        self.network = network
        self.created_at = datetime.utcnow()
        self.request_count = 0

        # Baseline fake values
        self.baseline_voltage = random.uniform(215, 225)
        self.baseline_current = random.uniform(15, 25)
        self.baseline_power_factor = random.uniform(0.95, 0.99)

    def _generate_canary_token(self) -> str:
        """
        Generate tracking token embedded in response.
        If this token appears in attacker's data, we know they accessed honeypot.
        """
        data = f"{self.meter_id}:{self.request_count}:{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def generate_response(self) -> HoneypotResponse:
        """Generate realistic but fake meter data."""
        self.request_count += 1

        # Add realistic jitter
        voltage = self.baseline_voltage + random.gauss(0, 0.5)
        current = self.baseline_current + random.gauss(0, 0.3)
        power_factor = self.baseline_power_factor + random.gauss(0, 0.01)

        # Clip to realistic ranges
        voltage = max(210, min(230, voltage))
        current = max(0, min(50, current))
        power_factor = max(0.9, min(1.0, power_factor))

        return HoneypotResponse(
            meter_id=self.meter_id,
            voltage=round(voltage, 2),
            current=round(current, 2),
            power_factor=round(power_factor, 2),
            status="operational",
            timestamp=datetime.utcnow().isoformat(),
            _canary_token=self._generate_canary_token(),
        )

    def generate_status(self) -> Dict:
        """Generate fake status response."""
        return {
            "meter_id": self.meter_id,
            "status": "operational",
            "battery": random.uniform(80, 100),
            "signal_strength": random.randint(-60, -30),
            "last_reading": (datetime.utcnow()).isoformat(),
            "firmware_version": "2.4.1",
            "uptime_hours": random.randint(720, 8760),
            "_canary_token": self._generate_canary_token(),
        }

    def generate_config(self) -> Dict:
        """Generate fake configuration response."""
        return {
            "meter_id": self.meter_id,
            "model": "SmartMeter-3000X",
            "serial": f"SN-{self.meter_id}-{random.randint(10000, 99999)}",
            "utility_id": f"UTIL-{random.randint(1000, 9999)}",
            "service_address": f"123 Fake St, Honeypot City {random.randint(10000, 99999)}",
            "meter_type": "3-phase",
            "ct_ratio": "200:5",
            "pt_ratio": "480:120",
            "_canary_token": self._generate_canary_token(),
        }


class HoneypotSystem:
    """Multi-meter honeypot system."""

    def __init__(self):
        """Initialize honeypot with 3 fake meters."""
        self.meters = {
            "SM-HONEY-001": HoneypotMeter("SM-HONEY-001"),
            "SM-HONEY-002": HoneypotMeter("SM-HONEY-002"),
            "SM-HONEY-003": HoneypotMeter("SM-HONEY-003"),
        }
        self.logger = logger

    async def process_request(
        self,
        db: AsyncSession,
        meter_id: str,
        endpoint: str,
        client_ip: str,
        headers: Dict,
        method: str = "GET",
    ) -> Optional[Dict]:
        """
        Process honeypot request and log intrusion.
        Returns fake data if meter exists, None otherwise.
        """
        if meter_id not in self.meters:
            return None

        meter = self.meters[meter_id]

        # Generate appropriate response
        if endpoint == "/voltage":
            response = meter.generate_response()
            response_dict = {
                "meter_id": response.meter_id,
                "voltage": response.voltage,
                "current": response.current,
                "power_factor": response.power_factor,
                "status": response.status,
                "timestamp": response.timestamp,
                "_canary_token": response._canary_token,
            }
        elif endpoint == "/status":
            response_dict = meter.generate_status()
        elif endpoint == "/config":
            response_dict = meter.generate_config()
        else:
            # Unknown endpoint - still respond believably
            response_dict = {
                "error": "unknown_endpoint",
                "message": f"Endpoint {endpoint} not recognized",
                "_canary_token": meter._generate_canary_token(),
            }

        # Log intrusion attempt
        await self._log_honeypot_access(
            db=db,
            meter_id=meter_id,
            endpoint=endpoint,
            client_ip=client_ip,
            headers=headers,
            method=method,
            response_token=response_dict.get("_canary_token", ""),
        )

        return response_dict

    async def _log_honeypot_access(
        self,
        db: AsyncSession,
        meter_id: str,
        endpoint: str,
        client_ip: str,
        headers: Dict,
        method: str,
        response_token: str,
    ):
        """Log honeypot access as security event."""
        try:
            from models.security import HoneypotLog, EventType, Severity

            # Extract useful headers
            user_agent = headers.get("user-agent", "unknown")
            auth_header = headers.get("authorization", "")

            log = HoneypotLog(
                meter_id=meter_id,
                client_ip=client_ip,
                endpoint=endpoint,
                method=method,
                user_agent=user_agent,
                auth_attempt=bool(auth_header),
                response_token=response_token,
                details={
                    "full_headers": dict(headers),
                    "alert": f"Honeypot {meter_id} accessed from {client_ip}",
                },
            )
            db.add(log)
            await db.flush()

            self.logger.critical(
                f"🚨 HONEYPOT INTRUSION: Meter={meter_id}, IP={client_ip}, "
                f"Endpoint={endpoint}, Method={method}, Token={response_token}"
            )

            # Also log to security_logs as CRITICAL event
            from models.security import SecurityLog, EventType as SECEventType, Severity as SECSeverity

            security_log = SecurityLog(
                event_type="HONEYPOT_ACCESS",
                severity=SECSeverity.CRIT,
                client_ip=client_ip,
                details={
                    "meter_id": meter_id,
                    "endpoint": endpoint,
                    "canary_token": response_token,
                    "alert_level": "CRITICAL",
                },
            )
            db.add(security_log)
            await db.flush()

        except Exception as e:
            self.logger.error(f"Failed to log honeypot access: {e}")

    async def get_honeypot_stats(self, db: AsyncSession) -> Dict:
        """Get honeypot statistics."""
        try:
            from models.security import HoneypotLog
            from sqlalchemy import func

            # Count total accesses
            total_stmt = select(func.count(HoneypotLog.id))
            total = (await db.execute(total_stmt)).scalar()

            # Count unique IPs
            unique_ips_stmt = select(func.count(func.distinct(HoneypotLog.client_ip)))
            unique_ips = (await db.execute(unique_ips_stmt)).scalar()

            # Count by meter
            by_meter_stmt = select(
                HoneypotLog.meter_id,
                func.count(HoneypotLog.id).label("count")
            ).group_by(HoneypotLog.meter_id)
            by_meter = (await db.execute(by_meter_stmt)).fetchall()

            return {
                "total_accesses": total,
                "unique_attackers": unique_ips,
                "by_meter": {meter_id: count for meter_id, count in by_meter},
                "active_meters": list(self.meters.keys()),
            }
        except Exception as e:
            self.logger.error(f"Error getting honeypot stats: {e}")
            return {"error": str(e)}
