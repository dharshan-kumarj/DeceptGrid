"""
Layer 6: Physics-Based Anomaly Detection on Meter Readings
Validates meter readings against real-world physical constraints
"""

import logging
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class MeterReading:
    """Represents a meter reading with physics validation."""
    meter_id: str
    voltage: float  # Volts
    current: float  # Amps
    power: float  # Watts
    power_factor: float = 0.95  # 0.9-1.0 typical


class PhysicsValidator:
    """Validates meter readings against physical laws and baselines."""

    # Historical baseline data (in production: from database)
    BASELINE_DATA = {
        "SM-REAL-051": {
            "voltage": {"mean": 220.5, "std": 5.2},
            "current": {"mean": 18.5, "std": 3.2},
            "power": {"mean": 4100.0, "std": 650.0}
        },
        "SM-REAL-052": {
            "voltage": {"mean": 219.8, "std": 4.9},
            "current": {"mean": 17.2, "std": 2.8},
            "power": {"mean": 3800.0, "std": 580.0}
        },
        "SM-REAL-053": {
            "voltage": {"mean": 221.2, "std": 5.1},
            "current": {"mean": 19.3, "std": 3.5},
            "power": {"mean": 4350.0, "std": 700.0}
        }
    }

    # Transformer topology: meters on same transformer
    TRANSFORMER_TOPOLOGY = {
        "TX-01": ["SM-REAL-051", "SM-REAL-052"],
        "TX-02": ["SM-REAL-053"]
    }

    def __init__(self):
        """Initialize physics validator."""
        self.anomalies = []
        self.validation_notes = []

    def reset(self):
        """Reset anomaly tracking for new validation."""
        self.anomalies = []
        self.validation_notes = []

    def validate_reading(self, reading: MeterReading) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive physics validation on a meter reading.

        Returns:
            (is_valid, validation_notes)
        """
        self.reset()

        # 1. Statistical baseline check
        self._check_statistical_baseline(reading)

        # 2. Ohm's Law validation
        self._check_ohms_law(reading)

        # 3. Adjacent meter correlation
        self._check_adjacent_meters(reading)

        # 4. Load consistency check
        self._check_load_consistency(reading)

        is_valid = len(self.anomalies) == 0

        if not is_valid:
            logger.warning(f"PHYSICS_VALIDATION_FAILED: {reading.meter_id}")
            logger.warning(f"  Anomalies: {self.anomalies}")

        return is_valid, self.validation_notes

    def _check_statistical_baseline(self, reading: MeterReading):
        """
        Statistical Check: Z-score analysis.
        Flag if reading > 6 standard deviations from mean.
        """
        baseline = self.BASELINE_DATA.get(reading.meter_id)

        if not baseline:
            self.validation_notes.append("No historical baseline for meter")
            return

        # Check voltage
        v_mean = baseline["voltage"]["mean"]
        v_std = baseline["voltage"]["std"]
        v_zscore = abs((reading.voltage - v_mean) / max(v_std, 0.1))

        if v_zscore > 6:
            self.anomalies.append(f"Voltage Z-score: {v_zscore:.2f} (threshold: 6)")
            self.validation_notes.append(f"⚠️ Voltage anomaly detected")
            logger.warning(f"  ANOMALOUS_READING_DETECTED: Voltage Z-score {v_zscore:.2f}")

        # Check current
        i_mean = baseline["current"]["mean"]
        i_std = baseline["current"]["std"]
        i_zscore = abs((reading.current - i_mean) / max(i_std, 0.1))

        if i_zscore > 6:
            self.anomalies.append(f"Current Z-score: {i_zscore:.2f} (threshold: 6)")
            self.validation_notes.append(f"⚠️ Current anomaly detected")
            logger.warning(f"  ANOMALOUS_READING_DETECTED: Current Z-score {i_zscore:.2f}")

    def _check_ohms_law(self, reading: MeterReading):
        """
        Ohm's Law Validation: Power ≈ Voltage × Current.
        Allow ≤ 10% error (accounts for power factor).
        """
        # Expected power: P = V × I × PF (with power factor correction)
        expected_power = reading.voltage * reading.current * reading.power_factor
        actual_power = reading.power

        # Calculate percentage error
        error_pct = abs(actual_power - expected_power) / max(expected_power, 1) * 100

        if error_pct > 10:
            self.anomalies.append(
                f"Power calculation mismatch: {error_pct:.1f}% "
                f"(expected: {expected_power:.0f}W, actual: {actual_power:.0f}W)"
            )
            self.validation_notes.append(f"⚠️ Power mismatch: {error_pct:.1f}%")
            logger.warning(f"  ANOMALOUS_READING_DETECTED: Power mismatch {error_pct:.1f}%")
        else:
            self.validation_notes.append(f"✓ Power valid (error: {error_pct:.1f}%)")

    def _check_adjacent_meters(self, reading: MeterReading):
        """
        Adjacent Meter Correlation: Meters on same transformer have similar voltage.
        Flag if deviation > 20V.
        """
        # Find transformer for this meter
        transformer = None
        for tx, meters in self.TRANSFORMER_TOPOLOGY.items():
            if reading.meter_id in meters:
                transformer = tx
                break

        if not transformer:
            return

        # Get adjacent meters
        adjacent_meters = self.TRANSFORMER_TOPOLOGY[transformer]
        adjacent_meters = [m for m in adjacent_meters if m != reading.meter_id]

        for adjacent_meter in adjacent_meters:
            baseline = self.BASELINE_DATA.get(adjacent_meter)
            if baseline:
                voltage_diff = abs(reading.voltage - baseline["voltage"]["mean"])

                if voltage_diff > 20:
                    self.anomalies.append(
                        f"Voltage deviation from adjacent meter {adjacent_meter}: {voltage_diff:.1f}V"
                    )
                    self.validation_notes.append(f"⚠️ Adjacent meter voltage mismatch: {voltage_diff:.1f}V")
                    logger.warning(
                        f"  ANOMALOUS_READING_DETECTED: Adjacent meter mismatch {voltage_diff:.1f}V"
                    )
                else:
                    self.validation_notes.append(f"✓ Adjacent meter voltage OK ({adjacent_meter})")

    def _check_load_consistency(self, reading: MeterReading):
        """
        Load Consistency: Compare current load vs historical average.
        Flag if change > 20% (without external justification).
        """
        baseline = self.BASELINE_DATA.get(reading.meter_id)

        if not baseline:
            return

        i_mean = baseline["current"]["mean"]
        load_change_pct = abs(reading.current - i_mean) / max(i_mean, 0.1) * 100

        if load_change_pct > 20:
            self.validation_notes.append(f"⚠️ Load change: {load_change_pct:.1f}% (needs investigation)")
            logger.warning(f"  Load change detected: {load_change_pct:.1f}%")
            # Don't flag as anomaly yet - may have legitimate reason (weather, device activation, etc.)
        else:
            self.validation_notes.append(f"✓ Load consistent (change: {load_change_pct:.1f}%)")

    def format_validation_response(
        self,
        reading: MeterReading,
        is_valid: bool,
        notes: List[str]
    ) -> Dict:
        """Format validation result for API response."""
        return {
            "meter_id": reading.meter_id,
            "voltage": round(reading.voltage, 2),
            "current": round(reading.current, 2),
            "power": round(reading.power, 1),
            "power_factor": round(reading.power_factor, 3),
            "physics_valid": is_valid,
            "validation_notes": notes,
            "status": "OPERATIONAL" if is_valid else "ANOMALY_DETECTED"
        }


# Global validator instance
_physics_validator = None


def get_physics_validator() -> PhysicsValidator:
    """Get or initialize the global PhysicsValidator instance."""
    global _physics_validator
    if _physics_validator is None:
        _physics_validator = PhysicsValidator()
    return _physics_validator
