from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

import csv
import io

from database import SessionLocal, engine
from models import Proof, UserBaseline, Base

# =================================
# TRUST POLICY (PHASE 8.1)
# =================================
TRUST_POLICY_MAP = {
    "verified": "full_access",
    "probable": "monitor",
    "uncertain": "review_required",
    "low_trust": "restricted"
}

# --------------------------------
# DB init
# --------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --------------------------------
# CORS
# --------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://trustlessproof.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
# Schemas
# --------------------------------
class ProofIn(BaseModel):
    user_id: str
    effort_hash: str
    prev_hash: Optional[str] = None
    effort_score: float
    flags: List[str] = []
    timestamp: str

# --------------------------------
# Fraud checks
# --------------------------------
def fraud_checks(db, proof: ProofIn) -> list[str]:
    flags = []

    last = (
        db.query(Proof)
        .filter(Proof.user_id == proof.user_id)
        .order_by(Proof.id.desc())
        .first()
    )

    if last and proof.prev_hash != last.effort_hash:
        flags.append("chain_break")

    if db.query(Proof).filter(
        Proof.effort_hash == proof.effort_hash
    ).first():
        flags.append("replay_detected")

    if last:
        try:
            t1 = datetime.fromisoformat(last.timestamp)
            t2 = datetime.fromisoformat(proof.timestamp)
            if (t2 - t1).seconds > 1800:
                flags.append("large_time_gap")
        except Exception:
            flags.append("timestamp_parse_error")

    return flags

# --------------------------------
# Confidence logic
# --------------------------------
def compute_base_confidence(effort_score: float, flags: list[str]) -> float:
    c = effort_score

    if "chain_break" in flags:
        c *= 0.4
    if "replay_detected" in flags:
        c *= 0.2
    if "large_time_gap" in flags:
        c *= 0.7
    if "machine_like_rhythm" in flags:
        c *= 0.6
    if "edit_spam" in flags:
        c *= 0.8
    if "near_idle" in flags:
        c *= 0.5

    return round(min(c, 1.0), 3)

# --------------------------------
# Adaptive baseline
# --------------------------------
def apply_adaptive(db, user_id: str, base_conf: float, effort: float) -> float:
    baseline = (
        db.query(UserBaseline)
        .filter(UserBaseline.user_id == user_id)
        .first()
    )

    if not baseline:
        baseline = UserBaseline(
            user_id=user_id,
            avg_effort=effort,
            avg_confidence=base_conf,
            samples=1
        )
        db.add(baseline)
        db.commit()
        return base_conf

    norm = effort / max(baseline.avg_effort, 0.1)
    norm = min(max(norm, 0.7), 1.3)

    adaptive_conf = round(base_conf * norm, 3)

    alpha = 0.1
    baseline.avg_effort = (
        (1 - alpha) * baseline.avg_effort + alpha * effort
    )
    baseline.avg_confidence = (
        (1 - alpha) * baseline.avg_confidence + alpha * adaptive_conf
    )
    baseline.samples += 1

    db.commit()
    return min(adaptive_conf, 1.0)

# --------------------------------
# Trust band + policy
# --------------------------------
def trust_band(conf: float) -> dict:
    if conf >= 0.65:
        band = {
            "band": "verified",
            "label": "🟢 Verified",
            "action": "accept",
            "explanation": "Strong continuous evidence of real human work."
        }
    elif conf >= 0.45:
        band = {
            "band": "probable",
            "label": "🟡 Probable",
            "action": "accept",
            "explanation": "Work is likely genuine with minor irregularities."
        }
    elif conf >= 0.25:
        band = {
            "band": "uncertain",
            "label": "🟠 Uncertain",
            "action": "review",
            "explanation": "Mixed signals; optional manager review recommended."
        }
    else:
        band = {
            "band": "low_trust",
            "label": "🔴 Low Trust",
            "action": "clarify",
            "explanation": "Insufficient evidence in this session."
        }

    # Phase 8.1 — declarative policy binding
    band["policy"] = TRUST_POLICY_MAP.get(band["band"], "monitor")
    return band

# --------------------------------
# Submit proof
# --------------------------------
@app.post("/submit_proof")
def submit_proof(proof: ProofIn):
    db = SessionLocal()

    existing = (
        db.query(Proof)
        .filter(Proof.effort_hash == proof.effort_hash)
        .first()
    )
    if existing:
        db.close()
        return {
            "status": "duplicate_ignored",
            "confidence": existing.confidence,
            "fraud_flags": existing.flags.split(",") if existing.flags else []
        }

    backend_flags = fraud_checks(db, proof)
    all_flags = sorted(set(proof.flags + backend_flags))

    base_conf = compute_base_confidence(
        proof.effort_score,
        all_flags
    )

    adaptive_conf = apply_adaptive(
        db,
        proof.user_id,
        base_conf,
        proof.effort_score
    )

    record = Proof(
        user_id=proof.user_id,
        effort_hash=proof.effort_hash,
        prev_hash=proof.prev_hash,
        effort_score=proof.effort_score,
        confidence=adaptive_conf,
        flags=",".join(all_flags),
        timestamp=proof.timestamp,
    )

    db.add(record)
    db.commit()
    db.close()

    return {
        "status": "proof accepted",
        "confidence": adaptive_conf,
        "fraud_flags": all_flags
    }

# --------------------------------
# Proofs
# --------------------------------
@app.get("/proofs")
def get_proofs():
    db = SessionLocal()
    proofs = db.query(Proof).order_by(Proof.id.asc()).all()
    db.close()
    return proofs

# --------------------------------
# Decision (NOW WITH POLICY)
# --------------------------------
@app.get("/decision/{user_id}")
def decision(user_id: str):
    db = SessionLocal()

    proofs = (
        db.query(Proof)
        .filter(Proof.user_id == user_id)
        .order_by(Proof.id.desc())
        .limit(50)
        .all()
    )

    if not proofs:
        db.close()
        return {
            "session_confidence": 0.0,
            "windows": 0,
            "decision": trust_band(0.0)
        }

    avg_conf = sum(p.confidence for p in proofs) / len(proofs)
    db.close()

    return {
        "session_confidence": round(avg_conf, 3),
        "windows": len(proofs),
        "decision": trust_band(avg_conf)
    }

# --------------------------------
# POLICY — READ ONLY (PHASE 8.1)
# --------------------------------
@app.get("/policy")
def policy():
    return {
        "version": "pilot-default-v1",
        "description": "Declarative trust policy mapping (no enforcement)",
        "policy_map": TRUST_POLICY_MAP
    }

# --------------------------------
# Health
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
