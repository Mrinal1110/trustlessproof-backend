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
)

# --------------------------------
# DB INIT (SAFE)
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
# 🔐 AGENT ACTIVATE (FINAL)
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

        # Hard bind org + employee
        if invite.org_id != data.org_id or invite.employee_id != data.user_id:
            raise HTTPException(status_code=403, detail="Token/org/user mismatch")

        session = AgentSession(
            id=str(uuid4()),
            org_id=invite.org_id,
            employee_id=invite.employee_id,
            active=True,
            created_at=datetime.utcnow(),
            last_heartbeat=None,
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

        session.last_heartbeat = datetime.utcnow()
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
        sessions = db.query(AgentSession).filter(
            AgentSession.org_id == org_id
        ).all()

        result = []

        for s in sessions:
            if not s.active:
                state = "OFFLINE"
            elif not s.last_heartbeat:
                state = "INSTALLED"
            elif now - s.last_heartbeat > timedelta(minutes=5):
                state = "STALE"
            else:
                state = "ACTIVE"

            result.append({
                "employee_id": s.employee_id,
                "state": state,
                "last_heartbeat": (
                    s.last_heartbeat.isoformat()
                    if s.last_heartbeat else None
                ),
            })

        return result

    finally:
        db.close()


# --------------------------------
# HEALTH
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
