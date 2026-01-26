#!/usr/bin/env bash
set -e

echo "🔐 TrustlessProof Agent Installer"
echo "--------------------------------"

if [ -z "$ORG_ID" ] || [ -z "$USER_ID" ] || [ -z "$TOKEN" ]; then
  echo "❌ Missing required env vars: ORG_ID USER_ID TOKEN"
  exit 1
fi

BACKEND_URL="https://trustlessproof-backend-production.up.railway.app"
STATE_DIR="$HOME/.trustlessproof"
LOG_FILE="$STATE_DIR/agent.log"
AGENT_FILE="$STATE_DIR/agent.py"

mkdir -p "$STATE_DIR"

echo "Org: $ORG_ID"
echo "User: $USER_ID"
echo "Contacting TrustlessProof backend…"

# -----------------------
# ACTIVATE (ONE TIME)
# -----------------------
RESP=$(curl -s -w "\n%{http_code}" \
  -X POST "$BACKEND_URL/agent/activate" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"org_id\": \"$ORG_ID\",
    \"user_id\": \"$USER_ID\"
  }"
)

BODY=$(echo "$RESP" | head -n 1)
STATUS=$(echo "$RESP" | tail -n 1)

if [ "$STATUS" != "200" ]; then
  echo "❌ Activation failed:"
  echo "$BODY"
  exit 1
fi

SESSION_ID=$(echo "$BODY" | sed -n 's/.*"session_id":"\([^"]*\)".*/\1/p')

echo "✅ Agent activated successfully"
echo "Session ID: $SESSION_ID"

# -----------------------
# WRITE STATE
# -----------------------
cat > "$STATE_DIR/agent.json" <<EOF
{
  "org_id": "$ORG_ID",
  "employee_id": "$USER_ID",
  "api_base": "$BACKEND_URL"
}
EOF

cat > "$STATE_DIR/session.json" <<EOF
{
  "session_id": "$SESSION_ID"
}
EOF

# -----------------------
# WRITE AGENT (PHASE 15.1)
# -----------------------
cat > "$AGENT_FILE" <<'PYCODE'
import time
import json
import requests
import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path
import threading
import sys

STATE_DIR = Path.home() / ".trustlessproof"
CONFIG_PATH = STATE_DIR / "agent.json"
SESSION_PATH = STATE_DIR / "session.json"
CHAIN_PATH = STATE_DIR / "chain.json"

with open(CONFIG_PATH) as f:
    cfg = json.load(f)

with open(SESSION_PATH) as f:
    sess = json.load(f)

ORG_ID = cfg["org_id"]
EMPLOYEE_ID = cfg["employee_id"]
API_BASE = cfg["api_base"]
SESSION_ID = sess["session_id"]

def load_prev():
    if CHAIN_PATH.exists():
        with open(CHAIN_PATH) as f:
            return json.load(f).get("last_hash")
    return None

def save_prev(h):
    with open(CHAIN_PATH, "w") as f:
        json.dump({"last_hash": h}, f)

def heartbeat():
    while True:
        try:
            requests.post(
                f"{API_BASE}/agent/heartbeat",
                params={"session_id": SESSION_ID},
                timeout=5
            )
        except:
            pass
        time.sleep(30)

def emit_proof():
    prev = load_prev()
    while True:
        effort = round(random.uniform(0.4, 0.95), 3)
        payload_str = f"{EMPLOYEE_ID}|{effort}|{prev}|{datetime.utcnow()}"
        h = hashlib.sha256(payload_str.encode()).hexdigest()

        payload = {
            "user_id": EMPLOYEE_ID,
            "effort_hash": h,
            "prev_hash": prev,
            "effort_score": effort,
            "flags": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            r = requests.post(
                f"{API_BASE}/submit_proof",
                json=payload,
                timeout=10
            )
            if r.status_code == 200:
                save_prev(h)
                prev = h
        except:
            pass

        time.sleep(60)

threading.Thread(target=heartbeat, daemon=True).start()
threading.Thread(target=emit_proof, daemon=True).start()

while True:
    time.sleep(3600)
PYCODE

chmod +x "$AGENT_FILE"

# -----------------------
# RESTART AGENT
# -----------------------
pkill -f "$AGENT_FILE" || true

echo "🚀 Starting agent in background…"
nohup python3 "$AGENT_FILE" >> "$LOG_FILE" 2>&1 &

echo "🟢 Agent running (logs: $LOG_FILE)"
echo "✅ Installation complete."
