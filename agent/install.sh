#!/usr/bin/env bash
set -e

echo "🔐 TrustlessProof Agent Installer"
echo "--------------------------------"

# --------
# REQUIRED ENV VARS
# --------
if [ -z "$ORG_ID" ] || [ -z "$USER_ID" ] || [ -z "$TOKEN" ]; then
  echo "❌ Missing required environment variables."
  echo "Required: ORG_ID, USER_ID, TOKEN"
  exit 1
fi

BACKEND_URL="https://trustlessproof-backend-production.up.railway.app"
AGENT_DIR="$HOME/.trustlessproof"
LOG_FILE="$AGENT_DIR/agent.log"

echo "Org: $ORG_ID"
echo "User: $USER_ID"
echo "Contacting TrustlessProof backend…"

# --------
# ACTIVATE AGENT (server-side validation)
# --------
ACTIVATION_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "$BACKEND_URL/agent/activate" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"org_id\": \"$ORG_ID\",
    \"user_id\": \"$USER_ID\"
  }"
)

BODY=$(echo "$ACTIVATION_RESPONSE" | head -n 1)
STATUS=$(echo "$ACTIVATION_RESPONSE" | tail -n 1)

if [ "$STATUS" != "200" ]; then
  echo "❌ Activation failed."
  echo "$BODY"
  exit 1
fi

SESSION_ID=$(echo "$BODY" | sed -n 's/.*"session_id":"\([^"]*\)".*/\1/p')

if [ -z "$SESSION_ID" ]; then
  echo "❌ session_id missing."
  exit 1
fi

echo "✅ Agent activated successfully"
echo "Session ID: $SESSION_ID"

# --------
# WRITE AGENT CONFIG
# --------
mkdir -p "$AGENT_DIR"

cat > "$AGENT_DIR/agent.json" <<EOF
{
  "org_id": "$ORG_ID",
  "employee_id": "$USER_ID",
  "token": "$TOKEN",
  "api_base": "$BACKEND_URL"
}
EOF

# --------
# START AGENT (BACKGROUND)
# --------
echo "🚀 Starting agent in background…"

nohup python3 "$(pwd)/agent.py" >> "$LOG_FILE" 2>&1 &

echo "🟢 Agent running (logs: $LOG_FILE)"
echo "✅ Installation complete."
