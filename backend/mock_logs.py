"""
mock_logs.py — Generates 20 realistic mock attack log entries
into ../shared/attack_logs.json so the dashboard works standalone.
"""

import json
import random
import os
from datetime import datetime, timedelta

TARGETS = [
    "Honeypot_01", "Honeypot_01", "Honeypot_01",
    "Honeypot_02", "Honeypot_02",
    "RealMeter_01",
]

TYPES = [
    "BruteForce", "BruteForce", "BruteForce",
    "LoginBlocked", "LoginBlocked",
    "LoginSuccess",
    "RateLimited", "RateLimited",
]

SEVERITIES = ["HIGH", "HIGH", "MEDIUM", "MEDIUM", "LOW"]

IP_POOLS = [
    "192.168.1.", "10.0.0.", "172.16.5.", "203.0.113.", "198.51.100.",
]


def random_ip():
    return random.choice(IP_POOLS) + str(random.randint(1, 254))


def generate_mock_logs(count=20):
    logs = []
    now = datetime.now()

    for i in range(count):
        delta = timedelta(minutes=random.randint(0, 60))
        t = now - delta
        target = random.choice(TARGETS)
        attack_type = random.choice(TYPES)
        severity = random.choice(SEVERITIES)

        # Real meter should mostly be LoginSuccess or rare BruteForce
        if target == "RealMeter_01":
            attack_type = random.choice(["LoginSuccess", "LoginSuccess", "BruteForce"])
            severity = random.choice(["LOW", "MEDIUM"])

        entry = {
            "time": t.strftime("%H:%M"),
            "ip": random_ip(),
            "type": attack_type,
            "severity": severity,
            "target": target,
        }
        logs.append(entry)

    # Sort by time descending (newest first)
    logs.sort(key=lambda x: x["time"], reverse=True)
    return logs


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "..", "shared", "attack_logs.json")
    log_path = os.path.normpath(log_path)

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logs = generate_mock_logs(20)

    # Write as newline-delimited JSON (NDJSON)
    with open(log_path, "w") as f:
        for entry in logs:
            f.write(json.dumps(entry) + "\n")

    print(f"✅ Generated {len(logs)} mock log entries → {log_path}")
    for entry in logs[:5]:
        print(f"   {entry}")
    print("   ...")


if __name__ == "__main__":
    main()
