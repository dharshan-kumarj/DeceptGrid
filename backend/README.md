# DeceptGrid Backend API - Person C

FastAPI backend implementing steganography and attack simulation capabilities for the DeceptGrid smart grid cybersecurity simulation.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start development server:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

3. Access API documentation:
- Swagger UI: http://127.0.0.1:8001/docs
- ReDoc: http://127.0.0.1:8001/redoc

## 📡 API Endpoints

### Steganography Routes (`/api/steg/`)
- `POST /encode` - Hide text message in image using LSB steganography
- `POST /decode` - Extract hidden message from LSB-encoded image
- `GET /capacity` - Check maximum text capacity for an image

### Attack Simulation Routes (`/api/attacks/`)
- `POST /inject` - Log false data injection attack (honeypot simulation)
- `POST /stolen-login` - Analyze login behavior for credential theft detection
- `GET /logs` - Retrieve recent attack log entries

### Health Check
- `GET /` - Service status
- `GET /api/health` - API health check

## 🏗️ Project Structure

```
backend/
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── data/
│   └── attack_logs.json    # Shared attack log storage
├── models/
│   └── request_models.py   # Pydantic data models
├── routes/
│   ├── steg.py            # Steganography endpoints
│   └── attack_extra.py    # Attack simulation endpoints
├── utils/
│   ├── steganography.py   # LSB steganography implementation
│   └── logging_utils.py   # Attack logging utilities
└── temp/                   # Temporary image processing files
```

## 🧪 Testing

Run the test suites:

```bash
# Test steganography functionality
python3 test_steganography.py

# Test backend components
python3 test_backend.py
```

## 📋 Shared Log Format

All attack logs follow this format for dashboard integration:

```json
{
  "time": "HH:MM",
  "ip": "192.168.1.45",
  "type": "FalseDataInjection",
  "severity": "HIGH",
  "target": "Honeypot_01",
  "details": "Attack-specific information"
}
```

## 🔒 Security Features

- **LSB Steganography**: Hide/extract messages in images for covert communication
- **Behavioral Analysis**: Detect stolen credentials via typing pattern analysis
- **Honeypot Responses**: Make attackers think they succeeded while logging attempts
- **Input Validation**: Comprehensive request validation with Pydantic models
- **File Upload Security**: Size limits and type validation for image uploads

## 🤝 Integration

This backend integrates with:
- **Person A's honeypot endpoints** (`/api/honeypot/`)
- **Person B's authentication & meter APIs** (`/api/auth/`, `/api/meter/`)
- **Shared attack logging system** (`attack_logs.json`)
- **React frontend** (CORS configured for dev servers)

## 🐛 Development

- CORS enabled for `localhost:3000` and `localhost:5173` (React dev servers)
- Auto-reload enabled in development mode
- Comprehensive error handling with consistent JSON responses
- Async file operations for performance
- Thread-safe logging with file locking