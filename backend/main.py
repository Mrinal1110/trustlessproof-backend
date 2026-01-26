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

# -------------------------------
# DB INIT (SAFE RESET FOR PILOT)
# -------------------------------
RESET_DB = os.getenv("RESET_DB") == "true"

if RESET_DB:
    print("⚠️ RESET_DB enabled — dropping all tables")
    Base.metadata.drop_all(bind=engine)

Base.metadata.create_all(bind=engine)

# -------------------------------
# APP
# -------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# SCHEMAS
# -------------------------------
class InviteTokenCreate(BaseModel):
    org_id: str
    employee_id: str
    expiry_days: int = 7

class AgentActivateIn(BaseModel):
    token: str
    org_id: str
    user_id: str

# -------------------------------
# CREATE INVITE TOKEN
# -------------------------------
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

    out = {"token": token.id, "expires_at": token.expires_at.isoformat()}
    db.close()
    return out

# -------------------------------
# 🔐 AGENT ACTIVATE (FINAL)
# -------------------------------
@app.post("/agent/activate")
def activate_agent(data: AgentActivateIn):
    db = SessionLocal()

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
        db.close()
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    session = AgentSession(
        id=str(uuid4()),
        org_id=invite.org_id,
        user_id=invite.employee_id,
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        active=True,
    )

    invite.used = True
    db.add(session)
    db.commit()

    response = {
        "status": "activated",
        "session_id": session.id,
        "org_id": session.org_id,
        "user_id": session.user_id,
    }

    db.close()
    return response

# -------------------------------
# HEALTH
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
