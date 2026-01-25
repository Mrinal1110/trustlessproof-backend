from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from database import SessionLocal, engine
from models import (
    Proof, UserBaseline, Base,
    Org, InviteToken, AgentSession
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
    "low_trust": "restricted"
}

# --------------------------------
# Helpers
# --------------------------------
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
        "explanation": explanation
    }


# --------------------------------
# Internal: create invite token
# --------------------------------
@app.post("/internal/invite-token")
def create_invite_token(data: InviteTokenCreate):
    db = SessionLocal()

    # auto-create org if missing (pilot convenience)
    org = db.query(Org).filter(Org.id == data.org_id).first()
    if not org:
        org = Org(id=data.org_id, name=data.org_id, active=True)
        db.add(org)

    token = InviteToken(
        id=f"tp_{uuid.uuid4().hex}",
        org_id=data.org_id,
        employee_id=data.employee_id,
        expires_at=datetime.utcnow() + timedelta(days=data.expiry_days),
        used=False
    )

    db.add(token)
    db.commit()
    
    token_id = token.id
    expires_at = token.expires_at.isoformat()

    db.close()

    return {
        "token": token.id,
        "expires_at": expires_at
    }


# --------------------------------
# Agent activation
# --------------------------------
@app.post("/agent/activate")
def activate_agent(data: AgentActivateIn):
    db = SessionLocal()

    token = db.query(InviteToken).filter(
        InviteToken.id == data.token,
        InviteToken.used == False
    ).first()

    if not token or token.expires_at < datetime.utcnow():
        db.close()
        return Response(status_code=403)

    org = db.query(Org).filter(
        Org.id == token.org_id,
        Org.active == True
    ).first()

    if not org:
        db.close()
        return Response(status_code=403)

    session = AgentSession(
        id=f"sess_{uuid.uuid4().hex}",
        org_id=token.org_id,
        employee_id=token.employee_id,
        expires_at=datetime.utcnow() + timedelta(days=1),
        active=True
    )

    token.used = True
    db.add(session)
    db.commit()

    session_id = session.id
    employee_id = session.employee_id
    expires_at = session.expires_at.isoformat()

    db.close()

    return {
        "session_id": session_id,
        "employee_id": employee_id,
        "expires_at": expires_at
    }


# --------------------------------
# Submit proof (ENFORCED)
# --------------------------------
@app.post("/submit_proof")
def submit_proof(proof: ProofIn):
    db = SessionLocal()

    session = db.query(AgentSession).filter(
        AgentSession.id == proof.session_id,
        AgentSession.active == True,
        AgentSession.expires_at > datetime.utcnow()
    ).first()

    if not session:
        db.close()
        return Response(status_code=403)

    user_id = session.employee_id

    last = (
        db.query(Proof)
        .filter(Proof.user_id == user_id)
        .order_by(Proof.id.desc())
        .first()
    )

    flags = proof.flags.copy()

    if last and proof.prev_hash != last.effort_hash:
        flags.append("chain_break")

    base_conf = min(proof.effort_score, 1.0)

    db.add(Proof(
        user_id=user_id,
        effort_hash=proof.effort_hash,
        prev_hash=proof.prev_hash,
        effort_score=proof.effort_score,
        confidence=base_conf,
        flags=",".join(flags),
        timestamp=proof.timestamp
    ))

    db.commit()
    db.close()

    return {"status": "proof accepted", "confidence": base_conf}

# --------------------------------
# Internal: End pilot (org off)
# --------------------------------
@app.post("/internal/org/{org_id}/deactivate")
def deactivate_org(org_id: str):
    db = SessionLocal()

    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        db.close()
        return {"status": "org_not_found"}

    org.active = False

    # kill all active sessions
    db.query(AgentSession).filter(
        AgentSession.org_id == org_id,
        AgentSession.active == True
    ).update({AgentSession.active: False})

    db.commit()
    db.close()

    return {
        "status": "pilot_ended",
        "org_id": org_id
    }

# --------------------------------
# Agent: renew session
# --------------------------------
@app.post("/agent/renew")
def renew_session(session_id: str):
    db = SessionLocal()

    session = db.query(AgentSession).filter(
        AgentSession.id == session_id,
        AgentSession.active == True
    ).first()

    if not session:
        db.close()
        return Response(status_code=403)

    org = db.query(Org).filter(
        Org.id == session.org_id,
        Org.active == True
    ).first()

    if not org:
        db.close()
        return Response(status_code=403)

    session.expires_at = datetime.utcnow() + timedelta(days=1)
    db.commit()

    expires_at = session.expires_at.isoformat()
    db.close()

    return {
        "session_id": session.id,
        "expires_at": expires_at
    }

# --------------------------------
# Pilot Outcome (Executive Summary)
# --------------------------------
@app.get("/pilot/outcome/{org_id}")
def pilot_outcome(org_id: str):
    db = SessionLocal()

    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        db.close()
        return {"status": "org_not_found"}

    # collect all employees seen under this org
    sessions = db.query(AgentSession).filter(
        AgentSession.org_id == org_id
    ).all()

    employee_ids = list(set(s.employee_id for s in sessions))

    results = []
    band_counts = {
        "verified": 0,
        "probable": 0,
        "uncertain": 0,
        "low_trust": 0
    }

    confidences = []

    for user_id in employee_ids:
        proofs = db.query(Proof).filter(
            Proof.user_id == user_id
        ).order_by(Proof.id.desc()).limit(50).all()

        if not proofs:
            band = "low_trust"
            avg_conf = 0.0
        else:
            avg_conf = sum(p.confidence for p in proofs) / len(proofs)
            band = trust_band(avg_conf)["band"]

        band_counts[band] += 1
        confidences.append(avg_conf)

        results.append({
            "employee_id": user_id,
            "band": band,
            "confidence": round(avg_conf, 3)
        })

    avg_confidence = round(
        sum(confidences) / max(len(confidences), 1), 3
    )

    summary = {
        "org_id": org_id,
        "employees_evaluated": len(employee_ids),
        "average_confidence": avg_confidence,
        "band_distribution": band_counts,
        "executive_summary": (
            "Overall trust signals are strong."
            if band_counts["low_trust"] == 0
            else "Some trust risks detected. Review recommended."
        ),
        "results": results
    }

    db.close()
    return summary

# --------------------------------
# Pilot Export (CSV)
# --------------------------------
@app.get("/pilot/export/{org_id}")
def export_pilot(org_id: str):
    db = SessionLocal()

    sessions = db.query(AgentSession).filter(
        AgentSession.org_id == org_id
    ).all()

    employee_ids = list(set(s.employee_id for s in sessions))

    output = []
    output.append("employee_id,band,confidence")

    for user_id in employee_ids:
        proofs = db.query(Proof).filter(
            Proof.user_id == user_id
        ).order_by(Proof.id.desc()).limit(50).all()

        if not proofs:
            avg_conf = 0.0
            band = "low_trust"
        else:
            avg_conf = sum(p.confidence for p in proofs) / len(proofs)
            band = trust_band(avg_conf)["band"]

        output.append(f"{user_id},{band},{round(avg_conf,3)}")

    csv_data = "\n".join(output)
    db.close()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=trustlessproof_{org_id}_pilot.csv"
        }
    )


# --------------------------------
# Decision
# --------------------------------
@app.get("/decision/{user_id}")
def decision(user_id: str):
    db = SessionLocal()
    proofs = db.query(Proof).filter(
        Proof.user_id == user_id
    ).order_by(Proof.id.desc()).limit(50).all()

    if not proofs:
        db.close()
        return {"session_confidence": 0.0, "windows": 0, "decision": trust_band(0.0)}

    avg = sum(p.confidence for p in proofs) / len(proofs)
    db.close()
    return {
        "session_confidence": round(avg, 3),
        "windows": len(proofs),
        "decision": trust_band(avg)
    }


# --------------------------------
# Health
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
