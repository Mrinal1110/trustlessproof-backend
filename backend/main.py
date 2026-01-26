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
    Proof,
    UserBaseline,
    Base,
    Org,
    InviteToken,
    AgentSession,
)

# --------------------------------
# 🔥 DB INIT (SAFE RESET FOR PILOT)
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


class AgentActivateIn(BaseModel):
    token: str
    agent_fingerprint: Optional[str] = None


class ProofIn(BaseModel):
    session_id: str
    effort_hash: str
    prev_hash: Optional[str] = None
    effort_score: float
    flags: List[str] = []
    timestamp: str


# --------------------------------
# TRUST POLICY
# --------------------------------
TRUST_POLICY_MAP = {
    "verified": "full_access",
    "probable": "monitor",
    "uncertain": "review_required",
    "low_trust": "restricted",
}


def trust_band(conf: float) -> dict:
    if conf >= 0.65:
        band, explanation = "verified", "Strong continuous evidence of real human work."
    elif conf >= 0.45:
        band, explanation = "probable", "Work is likely genuine with minor irregularities."
    elif conf >= 0.25:
        band, explanation = "uncertain", "Mixed signals; optional manager review recommended."
    else:
        band, explanation = "low_trust", "Insufficient evidence in this session."

    return {
        "band": band,
        "label": band.replace("_", " ").title(),
        "action": "accept" if band in ("verified", "probable") else "review",
        "policy": TRUST_POLICY_MAP[band],
        "explanation": explanation,
    }


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
# 🔐 AGENT — ACTIVATE (FINAL)
# --------------------------------
@app.post("/agent/activate")
def activate_agent(payload: AgentActivateIn):
    db = SessionLocal()

    try:
        invite = (
            db.query(InviteToken)
            .filter(InviteToken.id == payload.token)
            .first()
        )

        if not invite:
            raise HTTPException(status_code=403, detail="Invalid token")

        if invite.used:
            raise HTTPException(status_code=403, detail="Token already used")

        if invite.expires_at and invite.expires_at < datetime.utcnow():
            raise HTTPException(status_code=403, detail="Token expired")

        session_id = str(uuid4())

        session = AgentSession(
            id=session_id,
            org_id=invite.org_id,
            employee_id=invite.employee_id,
            active=True,
            created_at=datetime.utcnow(),
            last_heartbeat=None,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        db.add(session)
        invite.used = True
        db.commit()

        return {
            "session_id": session_id,
            "org_id": invite.org_id,
            "employee_id": invite.employee_id,
        }

    except HTTPException:
        raise

    except Exception as e:
        print("ACTIVATION ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Activation failed")

    finally:
        db.close()


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
# AGENT — STATUS (ORG SCOPED)
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
# DECISION
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
            "decision": trust_band(0.0),
        }

    avg = sum(p.confidence for p in proofs) / len(proofs)
    db.close()

    return {
        "session_confidence": round(avg, 3),
        "windows": len(proofs),
        "decision": trust_band(avg),
    }


# --------------------------------
# PROOFS
# --------------------------------
@app.get("/proofs/{user_id}")
def get_user_proofs(user_id: str):
    db = SessionLocal()

    proofs = (
        db.query(Proof)
        .filter(Proof.user_id == user_id)
        .order_by(Proof.id.asc())
        .all()
    )

    db.close()
    return proofs


# --------------------------------
# HEALTH
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
