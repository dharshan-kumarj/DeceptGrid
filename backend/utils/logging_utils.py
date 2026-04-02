"""
Attack Logging System Utilities for DeceptGrid
Handles attack logging, behavioral analysis, and JSON file operations.
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles
import re


class AttackLogger:
    """Handles attack logging operations with thread-safe JSON file access."""

    def __init__(self, log_file: str = "data/attack_logs.json"):
        self.log_file = Path(log_file)
        self._file_lock = asyncio.Lock()

    async def log_attack(self, attack_data: Dict[str, Any]) -> bool:
        """
        Log attack data to the JSON file.

        Args:
            attack_data: Dictionary containing attack information

        Returns:
            True if logged successfully, False otherwise
        """
        # Validate required fields
        required_fields = ["time", "ip", "type", "severity", "target", "details"]
        for field in required_fields:
            if field not in attack_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate IP address format
        if not self._is_valid_ip(attack_data["ip"]):
            raise ValueError(f"Invalid IP address format: {attack_data['ip']}")

        # Validate severity level
        valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if attack_data["severity"] not in valid_severities:
            raise ValueError(f"Invalid severity level. Must be one of: {valid_severities}")

        async with self._file_lock:
            try:
                # Read existing logs
                existing_logs = await self._read_logs()

                # Add new log entry
                existing_logs.append(attack_data)

                # Write back to file
                await self._write_logs(existing_logs)
                return True

            except Exception as e:
                print(f"Error logging attack: {e}")
                return False

    async def get_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve attack logs.

        Args:
            limit: Maximum number of logs to retrieve (most recent first)

        Returns:
            List of attack log entries
        """
        async with self._file_lock:
            logs = await self._read_logs()

            # Return most recent logs first
            logs.reverse()

            if limit:
                return logs[:limit]
            return logs

    async def _read_logs(self) -> List[Dict[str, Any]]:
        """Read logs from JSON file."""
        try:
            if not self.log_file.exists():
                return []

            async with aiofiles.open(self.log_file, 'r') as f:
                content = await f.read()
                if not content.strip():
                    return []
                return json.loads(content)

        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or missing, return empty list
            return []

    async def _write_logs(self, logs: List[Dict[str, Any]]) -> None:
        """Write logs to JSON file."""
        # Ensure parent directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(self.log_file, 'w') as f:
            await f.write(json.dumps(logs, indent=2))

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Validate IPv4 address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False

        # Check each octet is 0-255
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)


class BehavioralAnalyzer:
    """Analyzes typing patterns and behavioral characteristics."""

    @staticmethod
    def analyze_typing_pattern(typing_speed: float, username: str) -> Dict[str, Any]:
        """
        Analyze typing patterns to detect potential credential theft.

        Args:
            typing_speed: Characters per second
            username: Username being analyzed

        Returns:
            Analysis results with behavior score and classification
        """
        # Convert to behavior score (0-100 scale)
        behavior_score = min(int(typing_speed * 100), 100)

        # Threshold for suspicious behavior (less than 0.6 chars/second = 60 score)
        suspicious_threshold = 60

        analysis_result = {
            "behavior_score": behavior_score,
            "typing_speed": typing_speed,
            "username": username,
            "is_suspicious": behavior_score < suspicious_threshold,
            "confidence": "HIGH" if behavior_score < 40 else "MEDIUM" if behavior_score < 60 else "LOW"
        }

        # Add classification reason
        if behavior_score < suspicious_threshold:
            analysis_result["reason"] = "Typing pattern mismatch - significantly slower than baseline"
            analysis_result["risk_level"] = "HIGH" if behavior_score < 40 else "MEDIUM"
        else:
            analysis_result["reason"] = "Normal typing pattern detected"
            analysis_result["risk_level"] = "LOW"

        return analysis_result

    @staticmethod
    def generate_log_entry(
        ip: str,
        attack_type: str,
        severity: str,
        target: str,
        details: str,
        custom_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a properly formatted log entry.

        Args:
            ip: Attacker IP address
            attack_type: Type of attack
            severity: Attack severity level
            target: Target system
            details: Attack details
            custom_time: Optional custom timestamp (HH:MM format)

        Returns:
            Formatted log entry dictionary
        """
        if custom_time:
            log_time = custom_time
        else:
            log_time = datetime.now().strftime("%H:%M")

        return {
            "time": log_time,
            "ip": ip,
            "type": attack_type,
            "severity": severity,
            "target": target,
            "details": details
        }


# Singleton instance for global use
attack_logger = AttackLogger()
behavioral_analyzer = BehavioralAnalyzer()