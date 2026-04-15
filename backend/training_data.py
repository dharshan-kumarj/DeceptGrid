"""
Training Data Generator for IDS ML Model
Simulates 30 days of normal user behavior for model training.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generate synthetic normal user behavior for IDS training."""

    def __init__(self, num_samples: int = 1000, random_seed: int = 42):
        """
        Initialize generator.
        num_samples: Number of behavior records to generate (default 30 days * ~33 sessions/day)
        random_seed: For reproducibility
        """
        self.num_samples = num_samples
        self.random_seed = random_seed
        np.random.seed(random_seed)

    def generate_training_data(self) -> np.ndarray:
        """
        Generate realistic normal user behavior data.

        Features:
        1. request_rate (requests/hour): 1-5
        2. session_duration (minutes): 10-120
        3. hour_of_day: 0-23
        4. day_of_week: 0-6
        5. unique_endpoints: 1-10
        6. data_volume (MB): 1-50

        Returns: numpy array of shape (num_samples, 6)
        """
        data = []

        for _ in range(self.num_samples):
            # 1. Request rate: typically 2-4 req/hour during work hours
            request_rate = np.random.normal(2.5, 0.8)
            request_rate = np.clip(request_rate, 0.5, 6.0)

            # 2. Session duration: typically 20-60 minutes
            session_duration = np.random.normal(45, 20)
            session_duration = np.clip(session_duration, 5, 180)

            # 3. Hour of day: concentrated on work hours (9-17)
            hour = np.random.normal(13, 2.5)  # Peak at 1pm
            hour = int(np.clip(hour, 0, 23))

            # 4. Day of week: mostly weekdays (0-4)
            day = np.random.choice(
                [0, 1, 2, 3, 4, 5, 6],
                p=[0.25, 0.25, 0.2, 0.15, 0.1, 0.03, 0.02],  # Weighted toward weekdays
            )

            # 5. Unique endpoints: typically 2-5 per session
            # Normal users access meter/voltage, meter/status, maybe config
            unique_endpoints = np.random.normal(3, 1.2)
            unique_endpoints = int(np.clip(unique_endpoints, 1, 8))

            # 6. Data volume: typically 0.5-10 MB per session
            # (includes meter readings, logs, maybe historical data)
            data_volume = np.random.lognormal(1, 1)  # Log-normal distribution
            data_volume = np.clip(data_volume, 0.1, 25.0)

            data.append([
                request_rate,
                session_duration,
                hour,
                day,
                unique_endpoints,
                data_volume,
            ])

        return np.array(data, dtype=np.float32)

    def generate_baseline_profiles(self, num_users: int = 50) -> dict:
        """
        Generate baseline profiles for multiple users.

        Returns dict mapping user_id -> baseline features
        """
        profiles = {}

        for user_id in range(num_users):
            # Each user has slightly different patterns
            profiles[f"user_{user_id}"] = {
                "avg_request_rate": np.random.uniform(1.0, 4.0),
                "avg_session_duration": np.random.uniform(20, 80),
                "avg_endpoints": int(np.random.uniform(2, 6)),
                "avg_data_volume": np.random.uniform(1, 15),
                # Typical access hours (e.g., 9-17 for business user)
                "typical_hours": list(range(int(np.random.uniform(8, 10)), int(np.random.uniform(16, 18)))),
                # Typical days (mostly weekdays)
                "typical_days": [0, 1, 2, 3, 4] if np.random.rand() > 0.3 else list(range(7)),
            }

        return profiles

    def generate_anomaly_samples(self, num_anomalies: int = 100) -> np.ndarray:
        """
        Generate synthetic anomalous behavior.

        Anomalies include:
        - High request rates (10+ req/hour)
        - Off-hours access (midnight-5am)
        - Weekend access
        - Endpoint scanning (10+ endpoints)
        - Data exfiltration (50+ MB)
        - Extended sessions (3+ hours)
        """
        anomalies = []

        for _ in range(num_anomalies):
            anomaly_type = np.random.choice([
                "high_request_rate",
                "off_hours",
                "endpoint_scan",
                "data_exfil",
                "long_session",
                "weekend_access",
            ])

            if anomaly_type == "high_request_rate":
                request_rate = np.random.uniform(8, 15)  # Way above normal
                session_duration = np.random.uniform(30, 120)
                hour = np.random.randint(0, 23)
                day = np.random.randint(0, 6)
                unique_endpoints = np.random.randint(2, 6)
                data_volume = np.random.uniform(5, 20)

            elif anomaly_type == "off_hours":
                request_rate = np.random.uniform(2, 5)
                session_duration = np.random.uniform(15, 60)
                hour = np.random.choice([0, 1, 2, 3, 4])  # Midnight-5pm
                day = np.random.randint(0, 6)
                unique_endpoints = np.random.randint(2, 8)
                data_volume = np.random.uniform(3, 15)

            elif anomaly_type == "endpoint_scan":
                request_rate = np.random.uniform(5, 12)
                session_duration = np.random.uniform(45, 180)
                hour = np.random.randint(0, 23)
                day = np.random.randint(0, 6)
                unique_endpoints = np.random.randint(15, 30)  # Way above normal
                data_volume = np.random.uniform(10, 40)

            elif anomaly_type == "data_exfil":
                request_rate = np.random.uniform(4, 10)
                session_duration = np.random.uniform(60, 240)
                hour = np.random.randint(0, 23)
                day = np.random.randint(0, 6)
                unique_endpoints = np.random.randint(5, 15)
                data_volume = np.random.uniform(100, 500)  # Extreme data transfer

            elif anomaly_type == "long_session":
                request_rate = np.random.uniform(3, 8)
                session_duration = np.random.uniform(300, 600)  # 5-10 hours
                hour = np.random.randint(0, 23)
                day = np.random.randint(0,6)
                unique_endpoints = np.random.randint(10, 25)
                data_volume = np.random.uniform(50, 150)

            else:  # weekend_access
                request_rate = np.random.uniform(3, 8)
                session_duration = np.random.uniform(30, 150)
                hour = np.random.randint(0, 23)
                day = np.random.choice([5, 6])  # Saturday or Sunday
                unique_endpoints = np.random.randint(5, 15)
                data_volume = np.random.uniform(10, 50)

            anomalies.append([
                request_rate,
                session_duration,
                hour,
                day,
                unique_endpoints,
                data_volume,
            ])

        return np.array(anomalies, dtype=np.float32)


def create_training_dataset() -> np.ndarray:
    """
    Create full training dataset combining normal and anomalous behavior.
    """
    logger.info("Generating IDS training data...")

    generator = TrainingDataGenerator(num_samples=800)
    normal_data = generator.generate_training_data()

    anomalies = generator.generate_anomaly_samples(num_anomalies=200)

    # Combine
    training_data = np.vstack([normal_data, anomalies])

    # Shuffle
    np.random.shuffle(training_data)

    logger.info(f"Training dataset shape: {training_data.shape}")
    return training_data


def create_baseline_profiles() -> dict:
    """Create user baseline profiles for reference."""
    generator = TrainingDataGenerator()
    return generator.generate_baseline_profiles(num_users=50)
