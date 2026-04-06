# DeceptGrid — Part 1 (Flask)

Smart Grid security simulation — Attacker flow with honeypot backend.

## Project Structure

```
deceptgrid/
├── app.py                  ← Flask backend (all API routes + data)
├── requirements.txt
└── templates/
    ├── base.html           ← Shared layout, styles, topbar
    ├── home.html           ← Page 1: Role selector
    ├── scanner.html        ← Page 2: Network scanner
    ├── brute.html          ← Page 3: Brute force login
    └── theft.html          ← Page 4: Data theft / exfiltration
```

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open browser
http://127.0.0.1:5000
```

## Pages

| URL        | Page                    |
|------------|-------------------------|
| `/`        | Role Selector (home)    |
| `/scanner` | Network Scanner         |
| `/brute`   | Brute Force Login       |
| `/theft`   | Data Theft / Exfil      |

## API Endpoints (for Part 2 / Engineer Dashboard)

| Endpoint              | Method | Description                             |
|-----------------------|--------|-----------------------------------------|
| `/api/scan`           | POST   | Returns fake SCADA device list + logs   |
| `/api/brute`          | POST   | Validates credential attempt            |
| `/api/wordlist`       | GET    | Returns password wordlist               |
| `/api/files`          | GET    | Returns remote file listing             |
| `/api/preview/<name>` | GET    | Returns fake file content preview       |
| `/api/exfil`          | POST   | Records exfiltration event              |
| `/api/honeypot-logs`  | GET    | Returns all honeypot events (for Part 2)|

## Integration with Part 2 (Engineer Dashboard)

Person B's engineer dashboard can poll `/api/honeypot-logs` to get live attack events
written by this Part 1 backend. All brute force attempts, honeypot triggers, and
data exfiltration events are stored in memory and served via that endpoint.
