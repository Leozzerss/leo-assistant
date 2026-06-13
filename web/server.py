#!/usr/bin/env python3
"""
LEO Web — Tarayıcıdan erişilebilir AI asistan.
LEO — Proprietary. All rights reserved.
"""

from __future__ import annotations

import datetime
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app_config import get_app_config_value, get_default_location  # noqa: E402
from actions.weather import get_weather_summary  # noqa: E402

PROMPT_PATH = BASE_DIR / "core" / "prompt_web.txt"
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="LEO", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, list[dict]] = {}
_client = None


def get_api_key() -> str:
    return str(
        get_app_config_value("gemini_api_key", "")
        or os.environ.get("GEMINI_API_KEY", "")
        or ""
    )


def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = get_api_key()
    if not api_key:
        return None
    from google import genai  # type: ignore

    _client = genai.Client(api_key=api_key)
    return _client


def _load_web_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "Sen LEO'sun — kişisel AI asistanı. Kullanıcının konumu Arnavutluk (Lezhë). "
        "Kullanıcının isteklerini öncelikli yerine getir. Türkçe ve Arnavutça konuşabilirsin."
    )


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "name": "LEO",
        "location": get_default_location(),
        "api_ready": bool(_get_client()),
    }


@app.get("/api/weather")
def weather(location: str | None = None):
    return {"summary": get_weather_summary(location)}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    client = _get_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY ayarlanmamış. Sunucu ortam değişkenine ekleyin.",
        )

    session_id = (req.session_id or "default").strip() or "default"
    history = _sessions.setdefault(session_id, [])

    now = datetime.datetime.now()
    system = (
        f"[ŞU ANKİ ZAMAN — Europe/Tirane]\n"
        f"{now.strftime('%A, %d %B %Y — %H:%M')}\n"
        f"[KONUM]\n{get_default_location()}\n\n"
        f"{_load_web_prompt()}"
    )

    contents = []
    for turn in history[-12:]:
        contents.append({"role": turn["role"], "parts": [{"text": turn["text"]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    try:
        from google.genai import types  # type: ignore

        response = client.models.generate_content(
            model=os.environ.get("LEO_MODEL", "models/gemini-2.5-flash"),
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        reply = (response.text or "").strip() or "Yanıt oluşturulamadı."
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    history.append({"role": "user", "text": message})
    history.append({"role": "model", "text": reply})
    if len(history) > 40:
        _sessions[session_id] = history[-40:]

    return ChatResponse(reply=reply, session_id=session_id)


@app.get("/")
def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html bulunamadı.")
    return FileResponse(index_path)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main():
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("web.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
