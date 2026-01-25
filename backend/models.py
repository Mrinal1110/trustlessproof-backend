from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from database import Base
from datetime import datetime

# -------------------------
# Proofs
# -------------------------
class Proof(Base):
    __tablename__ = "proofs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)

    effort_hash = Column(String, index=True)
    prev_hash = Column(String, nullable=True)

    effort_score = Column(Float)
    confidence = Column(Float)

    flags = Column(String, default="")
    timestamp = Column(String)


# -------------------------
# Adaptive Baseline
# -------------------------
class UserBaseline(Base):
    __tablename__ = "user_baselines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)

    avg_effort = Column(Float)
    avg_confidence = Column(Float)
    samples = Column(Integer)


# -------------------------
# Action Log (future)
# -------------------------
class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    band = Column(String)
    policy = Column(String)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


# =============================
# 🔐 IDENTITY & AUTHORITY
# =============================
class Org(Base):
    __tablename__ = "orgs"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    active = Column(Boolean, default=True)


class InviteToken(Base):
    __tablename__ = "invite_tokens"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, index=True)
    employee_id = Column(String, index=True)

    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, index=True)
    employee_id = Column(String, index=True)

    expires_at = Column(DateTime)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
