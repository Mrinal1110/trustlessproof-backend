from sqlalchemy import Column, Integer, String, Float
from database import Base

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


class UserBaseline(Base):
    __tablename__ = "user_baselines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)

    avg_effort = Column(Float)
    avg_confidence = Column(Float)
    samples = Column(Integer)

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    band = Column(String)
    policy = Column(String)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
