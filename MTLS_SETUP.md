# DeceptGrid mTLS Fix - Complete Setup Guide

## Problem

Uvicorn's CLI SSL mode (`--ssl-*` flags) doesn't expose the SSL transport object in ASGI scope, making it impossible to verify client certificates directly. This is by ASGI design - transport is optional.

## Solution

Run Uvicorn in **HTTP-only mode** behind an **SSL proxy** (nginx) that:
1. Handles SSL/mTLS termination
2. Extracts the client certificate
3. Passes it to Uvicorn as the `X-Client-Cert` header

The auth layer (`auth.py`) already supports this approach.

## Quick Start (Local Testing)

### Step 1: Start the Backend (HTTP mode)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

This runs on `http://localhost:8000`

### Step 2: Start nginx with SSL/mTLS

In a new terminal:

```bash
cd /home/dharshan/projects/DeceptGrid
nginx -c $(pwd)/nginx.conf
```

This runs on `https://localhost:8443` and forwards to localhost:8000

### Step 3: Test with mTLS Client Certificate

```bash
# Should fail - no certificate
curl -sk https://127.0.0.1:8443/api/meter/voltage

# Should succeed - with certificate
curl -sk \
  --cert certs/client.crt \
  --key certs/client.key \
  https://127.0.0.1:8443/api/meter/voltage
```

## Production Deployment

For production, use one of:

1. **nginx** - See `nginx.conf` in this repo
2. **Traefik** - Docker-native SSL/mTLS proxy
3. **Caddy** - Simple SSL proxy with automatic cert handling
4. **AWS ALB** - Managed load balancer with mTLS support

All should:
- Terminate TLS with client cert verification
- Forward `X-Client-Cert` header to backend
- Run backend in HTTP mode

## How It Works

1. Client connects to nginx with client certificate
2. nginx verifies cert against CA (ca.crt)
3. nginx extracts cert and base64 encodes it
4. nginx forwards to backend with header: `X-Client-Cert: ...base64...`
5. `auth.py` decodes and validates the cert

## Files

- `nginx.conf` - nginx configuration with SSL/mTLS
- `backend/run.py` - Launcher script (HTTP mode)
- `test_mtls.sh` - Test script for mTLS
- `auth.py` - Auth layer (already supports X-Client-Cert)

## Troubleshooting

### "Client certificate required"
- Ensure nginx is running with `nginx -c $(pwd)/nginx.conf`
- Verify `ssl_client_certificate` points to correct CA in nginx.conf
- Check client cert is valid: `openssl x509 -in certs/client.crt -noout -subject`

### Connection refused on 8443
- Check nginx is running: `ps aux | grep nginx`
- Check port is available: `netstat -tlnp 2>/dev/null | grep 8443`

### Backend not receiving cert
- Add debug logging to `auth.py` to check X-Client-Cert header
- Verify nginx config has `proxy_set_header X-Client-Cert $ssl_client_cert;`

## Database Setup

Before testing, seed the database with the authorized certificate:

```bash
cd backend
python setup_database.py
```

This creates a `sarah` user and registers the client.crt fingerprint.
