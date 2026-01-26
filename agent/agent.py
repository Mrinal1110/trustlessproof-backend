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
