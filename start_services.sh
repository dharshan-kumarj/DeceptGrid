#!/bin/bash

# DeceptGrid Complete Startup Script
# Starts Backend API and mTLS Proxy in the correct order

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DeceptGrid Backend - Complete Startup Script   ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}\n"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $PROXY_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if [ ! -f "$BACKEND_DIR/.venv/bin/activate" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Run: cd backend && python3 -m venv .venv && pip install -r requirements.txt"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Run: cp .env.example .env && edit with your settings"
    exit 1
fi

if [ ! -d "$PROJECT_DIR/certs" ] || [ ! -f "$PROJECT_DIR/certs/server.crt" ]; then
    echo -e "${RED}❌ SSL certificates not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}\n"

# Stop any existing services on ports 8000 and 8443
echo -e "${BLUE}🧹 Cleaning up old processes...${NC}"
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8443 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1
echo -e "${GREEN}✅ Ports cleared${NC}\n"

# Start Backend API
echo -e "${BLUE}1️⃣  Starting Backend API (Port 8000)...${NC}"
cd "$BACKEND_DIR"
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"

# Wait for backend to start
sleep 3
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start!${NC}"
    echo "   Logs:"
    cat /tmp/backend.log
    exit 1
fi

# Verify backend is responding
for i in {1..10}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready${NC}\n"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Backend failed to respond!${NC}"
        cat /tmp/backend.log
        exit 1
    fi
    sleep 1
done

# Start mTLS Proxy
echo -e "${BLUE}2️⃣  Starting mTLS Proxy (Port 8443)...${NC}"
python mtls_proxy.py > /tmp/proxy.log 2>&1 &
PROXY_PID=$!
echo "   PID: $PROXY_PID"
sleep 2

if ! kill -0 $PROXY_PID 2>/dev/null; then
    echo -e "${RED}❌ Proxy failed to start!${NC}"
    echo "   Logs:"
    cat /tmp/proxy.log
    exit 1
fi

echo -e "${GREEN}✅ Proxy is ready${NC}\n"

# Display status
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🎉 All Services Running 🎉              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}📊 Service Status:${NC}"
echo -e "   Backend API:  ${GREEN}✅${NC} http://127.0.0.1:8000"
echo -e "   mTLS Proxy:   ${GREEN}✅${NC} https://0.0.0.0:8443"
echo -e "   Database:     ${GREEN}✅${NC} Connected"

echo -e "\n${YELLOW}🧪 Quick Test Commands:${NC}\n"

echo -e "${BLUE}Layer 1 - mTLS Certificate Auth:${NC}"
echo "curl --cert certs/client.crt \\"
echo "     --key certs/client.key \\"
echo "     --cacert certs/ca.crt \\"
echo "     https://localhost:8443/api/meter/voltage"

echo -e "\n${BLUE}Layer 2 - OTP Email Auth (requires Layer 1):${NC}"
echo "curl --cert certs/client.crt \\"
echo "     --key certs/client.key \\"
echo "     --cacert certs/ca.crt \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"target_meter\": \"SM-REAL-051\"}' \\"
echo "     https://localhost:8443/api/meter/otp"

echo -e "\n${BLUE}Health Check:${NC}"
echo "curl http://localhost:8000/api/health"

echo -e "\n${YELLOW}📝 Monitoring:${NC}"
echo -e "   Backend logs:  ${BLUE}tail -f /tmp/backend.log${NC}"
echo -e "   Proxy logs:    ${BLUE}tail -f /tmp/proxy.log${NC}"

echo -e "\n${YELLOW}🛑 To stop services: Press Ctrl+C${NC}\n"

# Wait for interrupt
wait
