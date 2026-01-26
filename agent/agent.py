import time
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
import sys

CONFIG_PATH = Path.home() / ".trustlessproof" / "agent.json"

# -----------------------
# Load config
# -----------------------
if not CONFIG_PATH.exists():
    print("❌ Agent config not found:", CONFIG_PATH)
    sys.exit(1)

with open(CONFIG_PATH) as f:
    cfg = json.load(f)

ORG_ID = cfg["org_id"]
EMPLOYEE_ID = cfg["employee_id"]
TOKEN = cfg["token"]
API_BASE = cfg["api_base"]

print("🟢 TrustlessProof Agent Started")
print("Org      :", ORG_ID)
print("Employee :", EMPLOYEE_ID)

# -----------------------
# Activate agent
# -----------------------
r = requests.post(
    f"{API_BASE}/agent/activate",
    json={
        "token": TOKEN,
        "org_id": ORG_ID,
        "user_id": EMPLOYEE_ID
    },
    timeout=10
)

if r.status_code != 200:
    print("❌ Activation failed:", r.text)
    sys.exit(1)

session = r.json()["session_id"]
print("🔐 Session:", session)

# -----------------------
# Heartbeat loop
# -----------------------
while True:
    try:
        hb = requests.post(
            f"{API_BASE}/agent/heartbeat",
            params={"session_id": session},
            timeout=5
        )

        if hb.status_code == 200:
            print(
                "💓 Heartbeat OK @",
                datetime.now(timezone.utc).isoformat()
            )
        else:
            print("⚠ Heartbeat rejected:", hb.status_code)

    except Exception as e:
        print("⚠ Heartbeat error:", e)

    time.sleep(30)
