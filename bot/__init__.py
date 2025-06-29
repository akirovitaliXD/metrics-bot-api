# bot package: sets up aiogram Bot and Dispatcher, handlers are attached here

import asyncio
import io
import os
from datetime import datetime, timedelta
from typing import List, Optional

import matplotlib.pyplot as plt
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import get_settings

settings = get_settings()

API_BASE_URL = settings.API_BASE_URL
TELEGRAM_TOKEN = settings.TELEGRAM_TOKEN
SUPER_ADMIN_ID = settings.SUPER_ADMIN_ID

# USER_ACCESS mapping parsed
_raw_access = settings.USER_ACCESS_RAW
ACCESS_MAP = {}
for part in _raw_access.split(";"):
    part = part.strip()
    if not part:
        continue
    try:
        uid_str, servers_str = part.split(":")
        uid = int(uid_str)
        server_ids = [int(s) for s in servers_str.split(",") if s]
        ACCESS_MAP[uid] = server_ids
    except ValueError:
        continue

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN env var required")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# --- utils ---

async def fetch_json(url: str, params: Optional[dict] = None):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()

async def fetch_servers() -> List[dict]:
    return await fetch_json(f"{API_BASE_URL}/servers")

async def fetch_metrics(server_id: int, start: datetime, end: datetime):
    params = {"start": start.isoformat(), "end": end.isoformat(), "limit": 2000}
    return await fetch_json(f"{API_BASE_URL}/servers/{server_id}/metrics", params=params)


def _make_plot(metrics: List[dict], title: str):
    if not metrics:
        return None
    times = [datetime.fromisoformat(m["timestamp"]) for m in metrics]
    cpu = [m["cpu_load_1m"] for m in metrics]
    mem = [m["memory_used_mb"] for m in metrics]
    mem_total = metrics[0]["memory_total_mb"] if metrics else 0

    fig, ax1 = plt.subplots()
    ax1.plot(times, cpu, color="tab:blue")
    ax1.set_ylabel("CPU load", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(times, mem, color="tab:red")
    ax2.set_ylabel("Mem MB", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")
    ax2.set_ylim(0, mem_total)

    plt.title(title)
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

async def generate_plot(metrics: List[dict], title: str, loop):
    return await loop.run_in_executor(None, _make_plot, metrics, title)

# --- access helper ---

def is_allowed(user_id: int, server_id: int) -> bool:
    if SUPER_ADMIN_ID and user_id == SUPER_ADMIN_ID:
        return True
    return server_id in ACCESS_MAP.get(user_id, [])

# --- handlers ---

@dp.message_handler(commands=["start", "help"])
async def h_start(message: types.Message):
    user_id = message.from_user.id
    servers = await fetch_servers()
    if SUPER_ADMIN_ID and user_id == SUPER_ADMIN_ID:
        allowed = servers
    else:
        allowed_ids = ACCESS_MAP.get(user_id, [])
        allowed = [s for s in servers if s["id"] in allowed_ids]

    if not allowed:
        await message.reply("У вас нет доступа к серверам")
        return

    kb = [[InlineKeyboardButton(s["name"], callback_data=f"srv:{s['id']}")] for s in allowed]
    await message.reply("Выберите сервер:", reply_markup=InlineKeyboardMarkup(kb))

@dp.callback_query_handler(lambda c: c.data.startswith("srv:"))
async def h_choose_server(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    server_id = int(cb.data.split(":")[1])
    if not is_allowed(user_id, server_id):
        await cb.answer("Нет доступа", show_alert=True)
        return
    kb = [[
        InlineKeyboardButton("1 час", callback_data=f"time:{server_id}:1h"),
        InlineKeyboardButton("24 часа", callback_data=f"time:{server_id}:24h"),
        InlineKeyboardButton("7 дней", callback_data=f"time:{server_id}:7d"),
    ]]
    await cb.message.edit_text("Выберите период:", reply_markup=InlineKeyboardMarkup(kb))
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("time:"))
async def h_choose_period(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    _, server_id_str, period = cb.data.split(":")
    server_id = int(server_id_str)
    if not is_allowed(user_id, server_id):
        await cb.answer("Нет доступа", show_alert=True)
        return
    now = datetime.utcnow()
    start = now - timedelta(hours=1) if period == "1h" else (now - timedelta(hours=24) if period == "24h" else now - timedelta(days=7))
    end = now
    await cb.answer("Генерирую график…")
    metrics = await fetch_metrics(server_id, start, end)
    loop = asyncio.get_event_loop()
    buf = await generate_plot(metrics, f"Server {server_id} – {period}", loop)
    if buf is None:
        await cb.message.edit_text("Нет данных")
        return
    await cb.message.edit_media(types.InputMediaPhoto(buf, caption=f"Сервер {server_id} ({period})"))

# --- start background ---

def start_bot_background(loop: asyncio.AbstractEventLoop):
    async def _run():
        await dp.start_polling()
    loop.create_task(_run()) 