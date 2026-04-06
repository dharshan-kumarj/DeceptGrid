from flask import Flask, render_template, jsonify, request
import time, json, random, os
from datetime import datetime

app = Flask(__name__)

# ─── Fake SCADA Devices ───────────────────────────────────────────────────────
DEVICES = [
    {"id": 1,  "ip": "192.168.10.1",  "host": "GATEWAY-MGMT",        "type": "Network Gateway",      "status": "open",     "ping": 1,  "ports": [22, 80, 443],       "honeypot": False},
    {"id": 2,  "ip": "192.168.10.5",  "host": "HMI-CONTROL-01",      "type": "HMI Workstation",      "status": "open",     "ping": 4,  "ports": [22, 3389, 5900],    "honeypot": False},
    {"id": 3,  "ip": "192.168.10.8",  "host": "HISTORIAN-SRV",        "type": "Data Historian",       "status": "filtered", "ping": 12, "ports": [1433, 8080],        "honeypot": False},
    {"id": 4,  "ip": "192.168.10.11", "host": "PLC-FEEDER-03",        "type": "Siemens S7-300 PLC",   "status": "open",     "ping": 3,  "ports": [102, 502],          "honeypot": False},
    {"id": 5,  "ip": "192.168.10.14", "host": "RTU-SUBSTATION-04",    "type": "Remote Terminal Unit", "status": "open",     "ping": 6,  "ports": [22, 502, 2404],     "honeypot": False},
    {"id": 6,  "ip": "192.168.10.17", "host": "SMART-METER-PROXY",    "type": "Meter Gateway",        "status": "open",     "ping": 8,  "ports": [22, 4059],          "honeypot": False},
    {"id": 7,  "ip": "192.168.10.22", "host": "FAKE-SCADA-HONEY",     "type": "SCADA Server",         "status": "open",     "ping": 2,  "ports": [22, 80, 502, 1911], "honeypot": True},
    {"id": 8,  "ip": "192.168.10.31", "host": "IED-PROTECTION-07",    "type": "Relay IED",            "status": "closed",   "ping": None,"ports": [],                  "honeypot": False},
    {"id": 9,  "ip": "192.168.10.40", "host": "ENG-WORKSTATION-02",   "type": "Engineering PC",       "status": "filtered", "ping": 18, "ports": [3389],              "honeypot": False},
    {"id": 10, "ip": "192.168.10.99", "host": "DECOY-HONEYPOT-NET",   "type": "Network Appliance",    "status": "open",     "ping": 1,  "ports": [22, 80, 443, 8443], "honeypot": True},
]

# ─── Wordlist ─────────────────────────────────────────────────────────────────
WORDLIST = [
    "123456", "password", "admin123", "scada2023", "root", "letmein",
    "grid@2024", "powerplant", "substation", "admin@123", "operator",
    "P@ssw0rd", "1234", "qwerty", "control123", "iec61850", "modbus!",
    "siemens1", "ABB$admin", "grid_op", "rtu_admin", "substationX",
    "Aa123456!", "FieldEng1", "default123"
]
CORRECT_PASSWORD = "grid_op"

# ─── Fake Files ───────────────────────────────────────────────────────────────
REMOTE_FILES = [
    {"name": "device_map.xml",        "size": "4.2 KB",   "type": "XML",  "path": "/var/scada/config/",  "desc": "Device topology and IP mapping"},
    {"name": "meter_config.json",     "size": "11.7 KB",  "type": "JSON", "path": "/var/scada/config/",  "desc": "Smart meter calibration parameters"},
    {"name": "modbus_map.csv",        "size": "2.8 KB",   "type": "CSV",  "path": "/var/scada/config/",  "desc": "Modbus register address map"},
    {"name": "auth.log",              "size": "88.3 KB",  "type": "LOG",  "path": "/var/scada/logs/",    "desc": "SSH auth events + failed logins"},
    {"name": "grid_events.log",       "size": "142.1 KB", "type": "LOG",  "path": "/var/scada/logs/",    "desc": "SCADA event stream — 30 days"},
    {"name": "meter_readings.db",     "size": "3.4 MB",   "type": "DB",   "path": "/var/scada/data/",    "desc": "SQLite: 90-day meter telemetry"},
    {"name": "substation_layout.pdf", "size": "1.1 MB",   "type": "PDF",  "path": "/var/scada/data/",    "desc": "Substation physical diagram"},
    {"name": "credentials_bak.txt",   "size": "0.4 KB",   "type": "TXT",  "path": "/var/scada/data/",    "desc": "⚠ PLAINTEXT CREDENTIALS BACKUP"},
]

FILE_PREVIEWS = {
    "device_map.xml": '<?xml version="1.0"?>\n<DeviceMap>\n  <Device id="RTU-04">\n    <ip>192.168.10.14</ip>\n    <type>RTU</type>\n    <vendor>ABB</vendor>\n  </Device>\n</DeviceMap>',
    "meter_config.json": '{\n  "meter_id": "SM-4472",\n  "calibration": 1.0023,\n  "interval_s": 15,\n  "endpoint": "192.168.10.17:502"\n}',
    "modbus_map.csv": "Address,Type,Description\n40001,HOLDING_REG,Output voltage\n40002,HOLDING_REG,Current (A)\n40003,COIL,Breaker status",
    "auth.log": "Apr 07 09:14:22 sshd[3312]: Failed password for admin from 10.0.0.5\nApr 07 09:14:25 sshd[3318]: Accepted password for admin from 10.0.0.5",
    "grid_events.log": "2025-04-07T09:00:01Z BREAKER_OPEN  CB-14A\n2025-04-07T09:01:34Z VOLTAGE_ALARM 11.2kV\n2025-04-07T09:05:00Z BREAKER_CLOSE CB-14A",
    "meter_readings.db": "SQLite 3.x binary database\nTables: readings, meters, alarms\nRows: 518,400 (90-day window)",
    "substation_layout.pdf": "PDF Binary (cannot preview)\nPages: 14 | Size: 1.1 MB\nEncrypted: No | Version: PDF 1.5",
    "credentials_bak.txt": "## SUBSTATION-04 CREDENTIALS BACKUP\nadmin:grid_op\noperator:FieldEng1\nroot:ABB$admin",
}

# ─── In-memory honeypot log ────────────────────────────────────────────────────
honeypot_logs = []

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/scanner")
def scanner():
    return render_template("scanner.html")

@app.route("/brute")
def brute():
    return render_template("brute.html")

@app.route("/theft")
def theft():
    return render_template("theft.html")

# ─── API: Scan ────────────────────────────────────────────────────────────────
@app.route("/api/scan", methods=["POST"])
def api_scan():
    target = request.json.get("target", "192.168.10.0/24")
    logs = [
        f"Initializing Nmap aggressive scan on {target}...",
        "Sending SYN packets to port range 1–65535...",
        "ARP probing subnet for live hosts...",
    ]
    for d in DEVICES:
        if d["status"] == "open":
            logs.append(f"[+] Host {d['ip']} — ALIVE (RTT: {d['ping']}ms)")
        if d["honeypot"]:
            logs.append(f"[WARN] Unusual banner on {d['ip']} — possible deception asset")
    logs += [
        "Fingerprinting OS and services...",
        f"Scan complete. {len(DEVICES)} hosts discovered, 23 open ports found.",
    ]
    return jsonify({
        "logs": logs,
        "devices": DEVICES,
        "stats": {
            "hosts": len(DEVICES),
            "open_ports": 23,
            "honeypots": sum(1 for d in DEVICES if d["honeypot"]),
        }
    })

# ─── API: Brute Force ─────────────────────────────────────────────────────────
@app.route("/api/brute", methods=["POST"])
def api_brute():
    data = request.json
    username = data.get("username", "admin")
    password = data.get("password", "")
    attempt_num = data.get("attempt_num", 0)
    target_ip = data.get("target_ip", "192.168.10.14")

    # Log to honeypot if attempt #8
    honeypot_triggered = False
    if attempt_num == 8:
        honeypot_logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "ip": target_ip,
            "username": username,
            "password": password,
            "event": "HONEYPOT_TRIGGER",
        })
        honeypot_triggered = True

    success = (password == CORRECT_PASSWORD)
    if success:
        honeypot_logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "ip": target_ip,
            "username": username,
            "password": password,
            "event": "CREDENTIAL_FOUND",
        })

    return jsonify({
        "password": password,
        "username": username,
        "success": success,
        "honeypot_triggered": honeypot_triggered,
        "attempt_num": attempt_num,
    })

@app.route("/api/wordlist", methods=["GET"])
def api_wordlist():
    return jsonify({"wordlist": WORDLIST, "correct": CORRECT_PASSWORD})

# ─── API: File Preview ────────────────────────────────────────────────────────
@app.route("/api/files", methods=["GET"])
def api_files():
    return jsonify({"files": REMOTE_FILES})

@app.route("/api/preview/<filename>", methods=["GET"])
def api_preview(filename):
    content = FILE_PREVIEWS.get(filename, f"[Binary or unknown file type: {filename}]")
    return jsonify({"filename": filename, "content": content})

# ─── API: Exfiltrate ─────────────────────────────────────────────────────────
@app.route("/api/exfil", methods=["POST"])
def api_exfil():
    files = request.json.get("files", [])
    honeypot_logs.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "ip": "192.168.10.14",
        "username": "admin",
        "password": "grid_op",
        "event": "DATA_EXFILTRATION",
        "files": [f["name"] for f in files],
    })
    return jsonify({
        "status": "success",
        "files_transferred": len(files),
        "tunnel": "AES-256 / Tor",
        "c2": "185.220.101.x",
        "timestamp": datetime.now().isoformat(),
    })

# ─── API: Honeypot Logs (for Part 2 - Engineer Dashboard) ────────────────────
@app.route("/api/honeypot-logs", methods=["GET"])
def api_honeypot_logs():
    return jsonify({"logs": honeypot_logs})

if __name__ == "__main__":
    print("\n  ██████  DECEPTGRID — Part 1  ██████")
    print("  Running on http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
