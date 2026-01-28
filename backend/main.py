from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
from actions import resolve_action

# --------------------------------
# INIT DB
# --------------------------------
Base.metadata.create_all(bind=engine)

# --------------------------------
# APP
# --------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://trustlessproof.com",
        "https://dashboard.trustlessproof.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
# INVITE TOKEN
# --------------------------------
@app.post("/internal/invite-token")
def create_invite_token(data: dict):
    db = SessionLocal()
    try:
        token = InviteToken(
            id=f"tp_{uuid4().hex}",
            org_id=data["org_id"],
            employee_id=data["employee_id"],
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=data.get("expiry_days", 7)),
            used=False,
        )
        db.add(token)
        db.commit()
        return {"token": token.id}
    finally:
        db.close()

# --------------------------------
# AGENT ACTIVATE
# --------------------------------
@app.post("/agent/activate")
def activate_agent(data: dict):
    db = SessionLocal()
    try:
        invite = (
            db.query(InviteToken)
            .filter(
                InviteToken.id == data["token"],
                InviteToken.used == False,
                InviteToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

        if not invite:
            raise HTTPException(401, "Invalid or expired token")

        session = AgentSession(
            id=str(uuid4()),
            org_id=invite.org_id,
            employee_id=invite.employee_id,
            active=True,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            # version/platform filled on first proof
        )

        invite.used = True
        db.add(session)
        db.commit()

        return {
            "session_id": session.id,
            "expires_at": session.expires_at.isoformat(),
        }
    finally:
        db.close()

# --------------------------------
# HEARTBEAT
# --------------------------------
@app.post("/agent/heartbeat")
def heartbeat(session_id: str):
    db = SessionLocal()
    try:
        s = (
            db.query(AgentSession)
            .filter(
                AgentSession.id == session_id,
                AgentSession.active == True,
            )
            .first()
        )

        if not s:
            raise HTTPException(403)

        s.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()

        return {"status": "alive"}
    finally:
        db.close()

# --------------------------------
# PROOF INGESTION (stores version/platform)
# --------------------------------
@app.post("/agent/proof")
def ingest_proof(data: dict):
    db = SessionLocal()
    try:
        session = (
            db.query(AgentSession)
            .filter(
                AgentSession.id == data.get("session_id"),
                AgentSession.active == True,
            )
            .first()
        )

        if not session:
            raise HTTPException(403, "Invalid session")

        # 🆕 capture version & platform if provided
        if data.get("agent_version"):
            session.agent_version = data.get("agent_version")
        if data.get("platform"):
            session.platform = data.get("platform")

        proof = Proof(
            id=str(uuid4()),
            user_id=session.employee_id,
            effort_score=float(data.get("effort", 0)),
            created_at=datetime.now(timezone.utc),
        )

        db.add(proof)
        db.commit()

        return {"status": "recorded"}
    finally:
        db.close()

# --------------------------------
# AGENT STATUS (includes version/platform)
# --------------------------------
@app.get("/agent/status/{org_id}")
def agent_status(org_id: str):
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        sessions = (
            db.query(AgentSession)
            .filter(AgentSession.org_id == org_id)
            .all()
        )

        result = []
        for s in sessions:
            expires = s.expires_at
            if expires and expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)

            state = "ACTIVE" if expires and expires > now else "OFFLINE"

            result.append({
                "employee_id": s.employee_id,
                "state": state,
                "expires_at": expires.isoformat() if expires else None,
                # 🆕 fleet fields
                "agent_version": s.agent_version,
                "platform": s.platform,
            })

        return result

    except Exception as e:
        print("AGENT STATUS ERROR:", e)
        return []

    finally:
        db.close()

# --------------------------------
# TRUST DECISION
# --------------------------------
@app.get("/decision/{user_id}")
def decision(user_id: str):
    db = SessionLocal()
    try:
        proofs = (
            db.query(Proof)
            .filter(Proof.user_id == user_id)
            .all()
        )

        if len(proofs) < 3:
            band = "insufficient_data"
            confidence = None
        else:
            avg = sum(p.effort_score for p in proofs) / len(proofs)
            confidence = round(avg, 3)
            band = (
                "high_trust" if avg >= 0.7
                else "low_trust" if avg < 0.4
                else "normal"
            )

        action = resolve_action(band, confidence)

        return {
            "employee_id": user_id,
            "band": band,
            "confidence": confidence,
            "policy": action["policy"],
        }
    finally:
        db.close()

# --------------------------------
# PROOFS READ
# --------------------------------
@app.get("/proofs/{user_id}")
def get_proofs(user_id: str):
    db = SessionLocal()
    try:
        proofs = (
            db.query(Proof)
            .filter(Proof.user_id == user_id)
            .order_by(Proof.created_at.asc())
            .all()
        )

        return [
            {
                "confidence": p.effort_score,
                "timestamp": p.created_at.isoformat(),
            }
            for p in proofs
        ]
    except Exception as e:
        print("PROOFS READ ERROR:", e)
        return []
    finally:
        db.close()

# --------------------------------
# ACTION
# --------------------------------
@app.get("/action/{user_id}")
def action(user_id: str):
    db = SessionLocal()
    try:
        d = decision(user_id)
        a = resolve_action(d["band"], d["confidence"])

        log = ActionLog(
            user_id=user_id,
            band=d["band"],
            policy=a["policy"],
            message=a["message"],
            timestamp=datetime.utcnow(),
        )
        db.add(log)
        db.commit()

        return {
            "message": a["message"],
            "evaluated_at": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()

# --------------------------------
# HEALTH
# --------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
