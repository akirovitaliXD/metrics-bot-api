from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    host = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    port = Column(Integer, default=22)

    metrics = relationship("Metric", back_populates="server", cascade="all, delete-orphan")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    cpu_load_1m = Column(Float)
    cpu_load_5m = Column(Float)
    cpu_load_15m = Column(Float)
    memory_used_mb = Column(Float)
    memory_total_mb = Column(Float)

    server = relationship("Server", back_populates="metrics") 