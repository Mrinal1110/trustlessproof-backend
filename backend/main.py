import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import uuid4

from database import SessionLocal, engine
from models import (
    Proof,
    UserBaseline,
    Base,
    Org,
    InviteToken,
    AgentSession,
)

# --------------------------------
# 🔥 DB INIT (PILOT SAFE RESET)
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
# SCHEMAS
# --------------------------------
class InviteTokenCreate(BaseModel):
    org_id: str
    employee_id: str
    expiry_days: int = 7


# --------------------------------
# INTERNAL — CREATE INVITE TOKEN
# --------------------------------
@app.post("/internal/invite-token")
def create_invite_token(data: InviteTokenCreate):
    db = SessionLocal()

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

    out = {
        "token": token.id,
        "expires_at": token.expires_at.isoformat(),
    }

    db.close()
    return out


# --------------------------------
# 🔐 AGENT — ACTIVATE (FINAL + SAFE)
# --------------------------------
@app.post("/agent/activate")
async def activate_agent(request: Request):
    payload = await request.json()

    token = payload.get("token")
    org_id = payload.get("org_id")
    user_id = payload.get("user_id")  # kept for validation only

    if not token or not org_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing activation fields")

    db = SessionLocal()

    invite = (
        db.query(InviteToken)
        .filter(
            InviteToken.id == token,
            InviteToken.used == False,
            InviteToken.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not invite:
        db.close()
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # 🔒 HARD BIND: org + employee must match
    if invite.org_id != org_id or invite.employee_id != user_id:
        db.close()
        raise HTTPException(status_code=403, detail="Token/org/user mismatch")

    session = AgentSession(
        id=str(uuid4()),
        org_id=invite.org_id,
        employee_id=invite.employee_id,
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        active=True,
    )

    invite.used = True
    db.add(session)
    db.commit()

    out = {
        "status": "activated",
        "session_id": session.id,
        "org_id": session.org_id,
        "employee_id": session.employee_id,
        "expires_at": session.expires_at.isoformat(),
    }

    db.close()
    return out


# --------------------------------
# AGENT — HEARTBEAT
# --------------------------------
@app.post("/agent/heartbeat")
def agent_heartbeat(session_id: str):
    db = SessionLocal()

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
        db.close()
        return Response(status_code=403)

    session.last_heartbeat = datetime.utcnow()
    session.expires_at = datetime.utcnow() + timedelta(minutes=10)

    db.commit()

    out = {
        "status": "alive",
        "session_id": session.id,
        "expires_at": session.expires_at.isoformat(),
    }

    db.close()
    return out


# --------------------------------
# AGENT — STATUS
# --------------------------------
@app.get("/agent/status/{org_id}")
def agent_status(org_id: str):
    db = SessionLocal()
    now = datetime.utcnow()

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

    db.close()
    return result


# --------------------------------
# HEALTH
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
