import time
import json
import requests
import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path
import threading
import sys

# -----------------------
# State paths
# -----------------------
STATE_DIR = Path.home() / ".trustlessproof"
CONFIG_PATH = STATE_DIR / "agent.json"
SESSION_PATH = STATE_DIR / "session.json"
CHAIN_PATH = STATE_DIR / "chain.json"

# -----------------------
# Load state
# -----------------------
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

# -----------------------
# Proof chain helpers
# -----------------------
def load_prev_hash():
    if CHAIN_PATH.exists():
        with open(CHAIN_PATH) as f:
            return json.load(f).get("last_hash")
    return None

def save_prev_hash(h):
    with open(CHAIN_PATH, "w") as f:
        json.dump({"last_hash": h}, f)

# -----------------------
# Heartbeat loop
# -----------------------
def heartbeat_loop():
    while True:
        try:
            requests.post(
                f"{API_BASE}/agent/heartbeat",
                params={"session_id": SESSION_ID},
                timeout=5
            )
        except Exception as e:
            pass
        time.sleep(30)

# -----------------------
# Proof emission loop
# -----------------------
def proof_loop():
    prev_hash = load_prev_hash()

    while True:
        # Synthetic effort (Phase 17 placeholder)
        effort = round(random.uniform(0.4, 0.95), 3)

        # Use timezone-aware timestamp (no deprecation)
        now = datetime.now(timezone.utc)

        payload_str = f"{EMPLOYEE_ID}|{effort}|{prev_hash}|{now}"
        effort_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        payload = {
            "user_id": EMPLOYEE_ID,
            "effort_hash": effort_hash,
            "prev_hash": prev_hash,
            "effort_score": effort,
            "flags": [],
            "timestamp": now.isoformat()
        }

        try:
            r = requests.post(
                f"{API_BASE}/submit_proof",
                json=payload,
                timeout=10
            )

            if r.status_code == 200:
                save_prev_hash(effort_hash)
                prev_hash = effort_hash
        except Exception:
            pass

        time.sleep(60)

# -----------------------
# Start loops
# -----------------------
threading.Thread(target=heartbeat_loop, daemon=True).start()
threading.Thread(target=proof_loop, daemon=True).start()

# Keep process alive
while True:
    time.sleep(3600)
