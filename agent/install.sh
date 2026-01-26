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
# ACTIVATE (REQUIRED)
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

if [ -z "$SESSION_ID" ]; then
  echo "❌ session_id missing"
  exit 1
fi

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
# WRITE AGENT CODE (INLINE)
# -----------------------
cat > "$AGENT_FILE" <<'PYCODE'
import time
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
import sys

STATE_DIR = Path.home() / ".trustlessproof"
CONFIG_PATH = STATE_DIR / "agent.json"
SESSION_PATH = STATE_DIR / "session.json"

if not CONFIG_PATH.exists() or not SESSION_PATH.exists():
    print("❌ Missing agent state. Exiting.")
    sys.exit(1)

with open(CONFIG_PATH) as f:
    cfg = json.load(f)

with open(SESSION_PATH) as f:
    sess = json.load(f)

ORG_ID = cfg["org_id"]
EMPLOYEE_ID = cfg["employee_id"]
API_BASE = cfg["api_base"]
SESSION_ID = sess["session_id"]

print("🟢 TrustlessProof Agent Running")
print("Org      :", ORG_ID)
print("Employee :", EMPLOYEE_ID)
print("Session  :", SESSION_ID)

while True:
    try:
        r = requests.post(
            f"{API_BASE}/agent/heartbeat",
            params={"session_id": SESSION_ID},
            timeout=5
        )

        if r.status_code == 200:
            print("💓 Heartbeat OK @", datetime.now(timezone.utc).isoformat())
        else:
            print("⚠ Heartbeat rejected:", r.status_code, r.text)

    except Exception as e:
        print("⚠ Heartbeat error:", e)

    time.sleep(30)
PYCODE

chmod +x "$AGENT_FILE"

# -----------------------
# CLEAN OLD AGENT
# -----------------------
pkill -f "$AGENT_FILE" || true

# -----------------------
# START AGENT
# -----------------------
echo "🚀 Starting agent in background…"
nohup python3 "$AGENT_FILE" >> "$LOG_FILE" 2>&1 &

echo "🟢 Agent running (logs: $LOG_FILE)"
echo "✅ Installation complete."
