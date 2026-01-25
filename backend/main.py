from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

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
# Trust policy
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
# Internal: create invite token
# --------------------------------
@app.post("/internal/invite-token")
def create_invite_token(data: InviteTokenCreate):
    db = SessionLocal()

    org = db.query(Org).filter(Org.id == data.org_id).first()
    if not org:
        org = Org(id=data.org_id, name=data.org_id, active=True)
        db.add(org)

    token = InviteToken(
        id=f"tp_{uuid.uuid4().hex}",
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
# Agent: activate
# --------------------------------
from uuid import uuid4
from fastapi import HTTPException

@app.post("/agent/activate")
def activate_agent(payload: dict):
    token = payload.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    # 🔓 Phase 12B: permissive activation
    # NOTE: token validation will be added in Phase 13

    session_id = str(uuid4())

    return {
        "session_id": session_id
    }


# --------------------------------
# Agent: heartbeat
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
# Agent: status (org-scoped)
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
# Submit proof (ENFORCED)
# --------------------------------
@app.post("/submit_proof")
def submit_proof(proof: ProofIn):
    db = SessionLocal()

    session = db.query(AgentSession).filter(
        AgentSession.id == proof.session_id,
        AgentSession.active == True,
        AgentSession.expires_at > datetime.utcnow(),
    ).first()

    if not session:
        db.close()
        return Response(status_code=403)

    last = (
        db.query(Proof)
        .filter(Proof.user_id == session.employee_id)
        .order_by(Proof.id.desc())
        .first()
    )

    flags = proof.flags.copy()
    if last and proof.prev_hash != last.effort_hash:
        flags.append("chain_break")

    conf = min(proof.effort_score, 1.0)

    db.add(
        Proof(
            user_id=session.employee_id,
            effort_hash=proof.effort_hash,
            prev_hash=proof.prev_hash,
            effort_score=proof.effort_score,
            confidence=conf,
            flags=",".join(flags),
            timestamp=proof.timestamp,
        )
    )

    db.commit()
    db.close()

    return {"status": "proof accepted", "confidence": conf}


# --------------------------------
# Decision
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
# Proofs
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
# Health
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
