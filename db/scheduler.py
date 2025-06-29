import logging
import os
from datetime import datetime, timedelta

import paramiko
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from config import get_settings
from .database import SessionLocal
from .models import Server, Metric

settings = get_settings()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

FETCH_INTERVAL = settings.FETCH_INTERVAL
RETENTION_DAYS = 30


def _parse_loadavg(output: str):
    parts = output.split()
    return float(parts[0]), float(parts[1]), float(parts[2])


def _parse_free(output: str):
    lines = output.splitlines()
    for line in lines:
        if line.startswith("Mem:"):
            tokens = line.split()
            total = float(tokens[1]) / 1024
            used = float(tokens[2]) / 1024
            return used, total
    return 0.0, 0.0


def fetch_metrics_for_server(session: Session, server: Server):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            hostname=server.host,
            port=server.port,
            username=server.username,
            password=server.password,
            timeout=10,
        )
        _, stdout_load, _ = ssh.exec_command("cat /proc/loadavg")
        load_output = stdout_load.read().decode()

        _, stdout_free, _ = ssh.exec_command("free -k")
        free_output = stdout_free.read().decode()

        cpu1, cpu5, cpu15 = _parse_loadavg(load_output)
        mem_used, mem_total = _parse_free(free_output)

        metric = Metric(
            server_id=server.id,
            timestamp=datetime.utcnow(),
            cpu_load_1m=cpu1,
            cpu_load_5m=cpu5,
            cpu_load_15m=cpu15,
            memory_used_mb=mem_used,
            memory_total_mb=mem_total,
        )
        session.add(metric)
        session.commit()
        logger.info("Metrics collected for server %s", server.name)
    except Exception as e:
        logger.error("Failed to collect metrics for %s: %s", server.name, e)
    finally:
        ssh.close()


def cleanup_old_metrics(session: Session):
    threshold = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    deleted = session.query(Metric).filter(Metric.timestamp < threshold).delete()
    if deleted:
        logger.info("Deleted %d old metric records", deleted)
    session.commit()


def fetch_all_metrics():
    session: Session = SessionLocal()
    try:
        servers = session.query(Server).all()
        for server in servers:
            fetch_metrics_for_server(session, server)
        cleanup_old_metrics(session)
    finally:
        session.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_all_metrics, IntervalTrigger(seconds=FETCH_INTERVAL))
    scheduler.start()
    logger.info("Scheduler started (%d s)", FETCH_INTERVAL)
    return scheduler 