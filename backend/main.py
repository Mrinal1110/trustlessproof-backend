import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from database import SessionLocal, engine
from models import (
    Base,
    Org,
    InviteToken,
    AgentSession,
    Proof,
    UserBaseline,
    ActionLog,
)

from backend.actions import resolve_action

# --------------------------------
# DB INIT
# --------------------------------
RESET_DB = os.getenv("RESET_DB") == "true"

if RESET_DB:
    print("⚠️ RESET_DB enabled — dropping all tables")
    Base.metadata.drop_all(bind=engine)

Base.metadata.create_all(bind=engine)

# --------------------------------
# APP
# --------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
# SCHEMAS
# --------------------------------
class InviteTokenCreate(BaseModel):
    org_id: str
    employee_id: str
    expiry_days: int = 7


class AgentActivateIn(BaseModel):
    token: str
    org_id: str
    user_id: str


class ProofIn(BaseModel):
    user_id: str
    effort_hash: str
    prev_hash: Optional[str] = None
    effort_score: float
    flags: List[str] = []
    timestamp: str


# --------------------------------
# INVITE TOKEN
# --------------------------------
@app.post("/internal/invite-token")
def create_invite_token(data: InviteTokenCreate):
    db = SessionLocal()
    try:
        org = db.query(Org).filter(Org.id == data.org_id).first()
        if not org:
            org = Org(id=data.org_id, name=data.org_id, active=True)
            db.add(org)

        token = InviteToken(
            id=f"tp_{uuid4().hex}",
            org_id=data.org_id,
            employee_id=data.employee_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=data.expiry_days),
            used=False,
        )

        db.add(token)
        db.commit()

        return {
            "token": token.id,
            "expires_at": token.expires_at.isoformat(),
        }
    finally:
        db.close()


# --------------------------------
# AGENT ACTIVATE
# --------------------------------
@app.post("/agent/activate")
def activate_agent(data: AgentActivateIn):
    db = SessionLocal()
    try:
        invite = (
            db.query(InviteToken)
            .filter(
                InviteToken.id == data.token,
                InviteToken.used == False,
                InviteToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

        if not invite:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        if invite.org_id != data.org_id or invite.employee_id != data.user_id:
            raise HTTPException(status_code=403, detail="Token/org/user mismatch")

        session = AgentSession(
            id=str(uuid4()),
            org_id=invite.org_id,
            employee_id=invite.employee_id,
            active=True,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )

        invite.used = True
        db.add(session)
        db.commit()

        return {
            "status": "activated",
            "session_id": session.id,
            "expires_at": session.expires_at.isoformat(),
        }
    finally:
        db.close()


# --------------------------------
# AGENT HEARTBEAT
# --------------------------------
@app.post("/agent/heartbeat")
def agent_heartbeat(session_id: str):
    db = SessionLocal()
    try:
        session = (
            db.query(AgentSession)
            .filter(
                AgentSession.id == session_id,
                AgentSession.active == True,
                AgentSession.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

        if not session:
            return Response(status_code=403)

        session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()

        return {
            "status": "alive",
            "expires_at": session.expires_at.isoformat(),
        }
    finally:
        db.close()


# --------------------------------
# SUBMIT PROOF
# --------------------------------
@app.post("/submit_proof")
def submit_proof(data: ProofIn):
    db = SessionLocal()
    try:
        proof = Proof(
            user_id=data.user_id,
            effort_hash=data.effort_hash,
            prev_hash=data.prev_hash,
            effort_score=data.effort_score,
            confidence=data.effort_score,
            flags=",".join(data.flags),
            timestamp=data.timestamp,
        )

        db.add(proof)

        baseline = (
            db.query(UserBaseline)
            .filter(UserBaseline.user_id == data.user_id)
            .first()
        )

        if not baseline:
            baseline = UserBaseline(
                user_id=data.user_id,
                avg_effort=data.effort_score,
                avg_confidence=data.effort_score,
                samples=1,
            )
            db.add(baseline)
        else:
            n = baseline.samples + 1
            baseline.avg_effort = (
                baseline.avg_effort * baseline.samples + data.effort_score
            ) / n
            baseline.avg_confidence = baseline.avg_effort
            baseline.samples = n

        db.commit()

        return {
            "status": "accepted",
            "confidence": baseline.avg_confidence,
        }
    finally:
        db.close()


# --------------------------------
# TRUST DECISION (15.3)
# --------------------------------
def compute_window(db, user_id: str, since: datetime):
    proofs = (
        db.query(Proof)
        .filter(
            Proof.user_id == user_id,
            Proof.timestamp >= since.isoformat(),
        )
        .all()
    )

    if not proofs:
        return {"samples": 0, "average": None}

    avg = sum(p.effort_score for p in proofs) / len(proofs)
    return {"samples": len(proofs), "average": round(avg, 3)}


@app.get("/decision/{user_id}")
def decision_engine(user_id: str):
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        windows = {
            "short": compute_window(db, user_id, now - timedelta(minutes=15)),
            "medium": compute_window(db, user_id, now - timedelta(hours=2)),
            "long": compute_window(db, user_id, now - timedelta(days=7)),
        }

        total_samples = sum(w["samples"] for w in windows.values())

        if total_samples < 3:
            band = "insufficient_data"
            label = "Insufficient Data"
        else:
            avg = windows["medium"]["average"] or 0
            if avg < 0.4:
                band = "low_trust"
                label = "Low Trust Detected"
            elif avg < 0.7:
                band = "normal"
                label = "Normal"
            else:
                band = "high_trust"
                label = "High Trust"

        return {
            "employee_id": user_id,
            "band": band,
            "label": label,
            "confidence": windows["medium"]["average"],
            "windows": windows,
        }

    finally:
        db.close()


# --------------------------------
# 🔥 ACTION RESOLUTION (PHASE 16.1)
# --------------------------------
@app.get("/action/{user_id}")
def resolve_user_action(user_id: str):
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        decision = decision_engine(user_id)
        action_data = resolve_action(
            decision["band"],
            decision["confidence"],
        )

        # idempotent log: only log if band changed
        last = (
            db.query(ActionLog)
            .filter(ActionLog.user_id == user_id)
            .order_by(ActionLog.timestamp.desc())
            .first()
        )

        if not last or last.band != decision["band"]:
            log = ActionLog(
                user_id=user_id,
                band=decision["band"],
                policy=action_data["policy"],
                message=action_data["message"],
                timestamp=now,
            )
            db.add(log)
            db.commit()

        return {
            "employee_id": user_id,
            "band": decision["band"],
            "action": action_data["action"],
            "policy": action_data["policy"],
            "message": action_data["message"],
            "evaluated_at": now.isoformat(),
        }

    finally:
        db.close()


# --------------------------------
# HEALTH
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
