import time
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
import sys

STATE_DIR = Path.home() / ".trustlessproof"
CONFIG_PATH = STATE_DIR / "agent.json"
SESSION_PATH = STATE_DIR / "session.json"

# -----------------------
# Load config
# -----------------------
if not CONFIG_PATH.exists() or not SESSION_PATH.exists():
    print("❌ Agent config or session missing")
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

# -----------------------
# Heartbeat loop
# -----------------------
while True:
    try:
        hb = requests.post(
            f"{API_BASE}/agent/heartbeat",
            params={"session_id": SESSION_ID},
            timeout=5
        )

        if hb.status_code == 200:
            print(
                "💓 Heartbeat OK @",
                datetime.now(timezone.utc).isoformat()
            )
        else:
            print(
                "⚠ Heartbeat rejected:",
                hb.status_code,
                hb.text
            )

    except Exception as e:
        print("⚠ Heartbeat error:", e)

    time.sleep(30)
