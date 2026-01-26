import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import uuid4

from database import SessionLocal, engine
from models import (
    Base,
    Org,
    InviteToken,
    AgentSession,
    Proof,
    UserBaseline,
)

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
    prev_hash: Optional[str]
    effort_score: float
    flags: list = []
    timestamp: str


class ProofOut(BaseModel):
    effort_hash: str
    effort_score: float
    confidence: float
    timestamp: str

# --------------------------------
# CREATE INVITE TOKEN
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
            expires_at=datetime.utcnow() + timedelta(days=data.expiry_days),
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
                InviteToken.expires_at > datetime.utcnow(),
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
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10),
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
                AgentSession.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not session:
            return Response(status_code=403)

        session.expires_at = datetime.utcnow() + timedelta(minutes=10)
        db.commit()

        return {
            "status": "alive",
            "expires_at": session.expires_at.isoformat(),
        }
    finally:
        db.close()

# --------------------------------
# AGENT STATUS
# --------------------------------
@app.get("/agent/status/{org_id}")
def agent_status(org_id: str):
    db = SessionLocal()
    now = datetime.utcnow()
    try:
        sessions = db.query(AgentSession).filter(
            AgentSession.org_id == org_id
        ).all()

        return [
            {
                "employee_id": s.employee_id,
                "state": "ACTIVE" if s.expires_at > now else "EXPIRED",
                "expires_at": s.expires_at.isoformat(),
            }
            for s in sessions
        ]
    finally:
        db.close()

# --------------------------------
# 🧠 SUBMIT PROOF (Phase 15.1)
# --------------------------------
@app.post("/submit_proof")
def submit_proof(data: ProofIn):
    db = SessionLocal()
    try:
        # Load or init baseline
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
            confidence = data.effort_score
            db.add(baseline)
        else:
            confidence = (
                baseline.avg_confidence * baseline.samples + data.effort_score
            ) / (baseline.samples + 1)

            baseline.avg_confidence = confidence
            baseline.avg_effort = (
                baseline.avg_effort * baseline.samples + data.effort_score
            ) / (baseline.samples + 1)
            baseline.samples += 1

        proof = Proof(
            user_id=data.user_id,
            effort_hash=data.effort_hash,
            prev_hash=data.prev_hash,
            effort_score=data.effort_score,
            confidence=confidence,
            flags=",".join(data.flags),
            timestamp=data.timestamp,
        )

        db.add(proof)
        db.commit()

        return {
            "status": "accepted",
            "confidence": confidence,
        }
    finally:
        db.close()

# --------------------------------
# 📤 GET PROOFS
# --------------------------------
@app.get("/proofs/{user_id}", response_model=List[ProofOut])
def get_proofs(user_id: str):
    db = SessionLocal()
    try:
        proofs = (
            db.query(Proof)
            .filter(Proof.user_id == user_id)
            .order_by(Proof.id.asc())
            .all()
        )

        if not proofs:
            raise HTTPException(status_code=404, detail="No proofs found")

        return [
            {
                "effort_hash": p.effort_hash,
                "effort_score": p.effort_score,
                "confidence": p.confidence,
                "timestamp": p.timestamp,
            }
            for p in proofs
        ]
    finally:
        db.close()

# --------------------------------
# HEALTH
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
