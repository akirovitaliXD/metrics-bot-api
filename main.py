from fastapi import FastAPI, Depends, HTTPException
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import get_settings
from db.database import Base, engine, SessionLocal
from db.models import Server, Metric
from db.scheduler import start_scheduler
from bot import start_bot_background

settings = get_settings()

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Server Metrics API")

# start background jobs
scheduler = start_scheduler()

@app.on_event("startup")
async def startup():
    import asyncio
    loop = asyncio.get_event_loop()
    start_bot_background(loop)

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ServerCreate(BaseModel):
    name: str = Field(...)
    host: str
    username: str
    password: str
    port: int = 22

class ServerOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    class Config:
        orm_mode = True

class MetricOut(BaseModel):
    timestamp: datetime
    cpu_load_1m: float
    memory_used_mb: float
    memory_total_mb: float
    class Config:
        orm_mode = True


@app.post("/servers", response_model=ServerOut)
def add_server(server: ServerCreate, db: Session = Depends(get_db)):
    if db.query(Server).filter(Server.name == server.name).first():
        raise HTTPException(status_code=400, detail="Server exists")
    srv = Server(**server.dict())
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return srv

@app.get("/servers", response_model=List[ServerOut])
def list_servers(db: Session = Depends(get_db)):
    return db.query(Server).all()

@app.get("/servers/{server_id}/metrics", response_model=List[MetricOut])
def get_metrics(server_id: int, start: Optional[datetime] = None, end: Optional[datetime] = None, limit: int = 288, db: Session = Depends(get_db)):
    if not db.query(Server).filter(Server.id == server_id).first():
        raise HTTPException(status_code=404, detail="Server not found")
    query = db.query(Metric).filter(Metric.server_id == server_id)
    if start:
        query = query.filter(Metric.timestamp >= start)
    if end:
        query = query.filter(Metric.timestamp <= end)
    metrics = query.order_by(Metric.timestamp.desc()).limit(limit).all()
    return list(reversed(metrics))

@app.get("/health")
def health():
    return {"status": "ok"} 