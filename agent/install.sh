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
# ACTIVATE AGENT (ONE-TIME)
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
# INSTALL AGENT CODE
# SOURCE OF TRUTH: agent/agent.py
# -----------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$SCRIPT_DIR/agent.py" ]; then
  echo "❌ agent.py not found next to install.sh"
  exit 1
fi

cp "$SCRIPT_DIR/agent.py" "$AGENT_FILE"
chmod +x "$AGENT_FILE"

echo "✅ Agent code installed"

# -----------------------
# RESTART AGENT
# -----------------------
pkill -f "$AGENT_FILE" || true

echo "🚀 Starting agent in background…"
nohup python3 "$AGENT_FILE" >> "$LOG_FILE" 2>&1 &

echo "🟢 Agent running (logs: $LOG_FILE)"
echo "✅ Installation complete."
