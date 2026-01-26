import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from uuid import uuid4
from statistics import mean

from database import SessionLocal, engine
from models import Base, Org, InviteToken, AgentSession, Proof

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
            "org_id": session.org_id,
            "employee_id": session.employee_id,
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
            "session_id": session.id,
            "expires_at": session.expires_at.isoformat(),
        }
    finally:
        db.close()


# --------------------------------
# AGENT STATUS (ORG SCOPED)
# --------------------------------
@app.get("/agent/status/{org_id}")
def agent_status(org_id: str):
    db = SessionLocal()
    now = datetime.utcnow()

    try:
        sessions = (
            db.query(AgentSession)
            .filter(AgentSession.org_id == org_id)
            .all()
        )

        result = []

        for s in sessions:
            if not s.active:
                state = "OFFLINE"
            elif s.expires_at < now:
                state = "EXPIRED"
            else:
                state = "ACTIVE"

            result.append({
                "employee_id": s.employee_id,
                "state": state,
                "expires_at": s.expires_at.isoformat(),
            })

        return result
    finally:
        db.close()


# --------------------------------
# PROOFS (READ)
# --------------------------------
@app.get("/proofs/{employee_id}")
def get_proofs(employee_id: str):
    db = SessionLocal()
    try:
        proofs = (
            db.query(Proof)
            .filter(Proof.user_id == employee_id)
            .order_by(Proof.id.desc())
            .limit(50)
            .all()
        )

        if not proofs:
            return {"detail": "No proofs found"}

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
# 🔥 PHASE 15.2 — DECISION ENGINE
# --------------------------------
@app.get("/decision/{employee_id}")
def decision(employee_id: str):
    db = SessionLocal()
    try:
        proofs = (
            db.query(Proof)
            .filter(Proof.user_id == employee_id)
            .order_by(Proof.id.desc())
            .limit(10)
            .all()
        )

        if not proofs:
            return {
                "employee_id": employee_id,
                "band": "low_trust",
                "label": "Low Trust Detected",
                "confidence": None,
                "windows": 0,
                "explanation": "No verified work signals yet"
            }

        confidences = [p.confidence for p in proofs if p.confidence is not None]
        avg_conf = mean(confidences)
        windows = len(confidences)

        if avg_conf >= 0.75:
            band = "verified"
            label = "Verified Trust"
            explanation = "Consistent strong effort across recent activity"
        elif avg_conf >= 0.55:
            band = "probable"
            label = "Probable Trust"
            explanation = "Reliable effort with minor variation"
        elif avg_conf >= 0.35:
            band = "uncertain"
            label = "Trust Requires Review"
            explanation = "Inconsistent effort detected"
        else:
            band = "low_trust"
            label = "Low Trust Detected"
            explanation = "Insufficient or weak effort signals"

        return {
            "employee_id": employee_id,
            "band": band,
            "label": label,
            "confidence": round(avg_conf, 3),
            "windows": windows,
            "explanation": explanation
        }
    finally:
        db.close()


# --------------------------------
# HEALTH
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
