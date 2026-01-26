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

echo "Org: $ORG_ID"
echo "User: $USER_ID"
echo "Contacting TrustlessProof backend…"

# --------
# ACTIVATE AGENT (JSON BODY — IMPORTANT)
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

# --------
# HANDLE RESPONSE
# --------
if [ "$STATUS" != "200" ]; then
  echo "❌ Activation failed."
  echo "Backend response:"
  echo "$BODY"
  exit 1
fi

SESSION_ID=$(echo "$BODY" | sed -n 's/.*"session_id":"\([^"]*\)".*/\1/p')

if [ -z "$SESSION_ID" ]; then
  echo "❌ Activation succeeded but session_id missing."
  echo "$BODY"
  exit 1
fi

echo "✅ Agent activated successfully"
echo "Session ID: $SESSION_ID"

# --------
# (Optional) persist session for agent runtime
# --------
mkdir -p ~/.trustlessproof
cat > ~/.trustlessproof/session.json <<EOF
{
  "session_id": "$SESSION_ID",
  "org_id": "$ORG_ID",
  "user_id": "$USER_ID"
}
EOF

echo "🟢 Installation complete."
