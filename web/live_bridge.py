"""LEO Web — Gemini Live ses köprüsü (WebSocket)."""

from __future__ import annotations

import asyncio
import datetime
import json
import os
import re
import sys
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app_config import get_app_config_value, get_default_location  # noqa: E402
from actions.weather import get_weather_summary  # noqa: E402

LIVE_MODEL = os.environ.get(
    "LEO_LIVE_MODEL",
    "models/gemini-2.5-flash-native-audio-latest",
)
SEND_SAMPLE_RATE = 16000
RECV_SAMPLE_RATE = 24000

PROMPT_PATH = BASE_DIR / "core" / "prompt_web.txt"
CONTROL_TOKEN_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

WEB_TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "Anlik hava durumunu ozetler. Varsayilan konum Lezhe, Arnavutluk. "
            "Kullanici hava durumunu sordugunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "location": {
                    "type": "STRING",
                    "description": "Sehir veya konum. Bos birakilirsa Lezhe, Albania kullanilir.",
                }
            },
        },
    }
]


def _load_web_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "Sen LEO'sun — sesli kisisel AI asistani. Kullanicinin konumu Arnavutluk (Lezhe). "
        "Kullanicinin isteklerini oncelikli yerine getir."
    )


def _clean_transcript(text: str) -> str:
    raw = CONTROL_TOKEN_RE.sub(" ", str(text or ""))
    return " ".join(raw.split()).strip()


def _build_live_config():
    from google.genai import types  # type: ignore

    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(str(get_app_config_value("timezone", "Europe/Tirane") or "Europe/Tirane"))
        now = datetime.datetime.now(tz)
        time_ctx = (
            f"[ŞU ANKİ ZAMAN — Europe/Tirane]\n"
            f"{now.strftime('%A, %d %B %Y — %H:%M')}\n"
            f"[KONUM]\n{get_default_location()}\n\n"
        )
    except Exception:
        now = datetime.datetime.now()
        time_ctx = (
            f"[ŞU ANKİ ZAMAN]\n{now.strftime('%A, %d %B %Y — %H:%M')}\n"
            f"[KONUM]\n{get_default_location()}\n\n"
        )

    voice = str(get_app_config_value("voice", "Charon") or "Charon")
    system = time_ctx + _load_web_prompt()

    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        output_audio_transcription={},
        input_audio_transcription={},
        system_instruction=system,
        tools=[{"function_declarations": WEB_TOOLS}],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        ),
    )


async def _execute_web_tool(fc):
    from google.genai import types  # type: ignore

    name = fc.name
    args = dict(fc.args or {})
    if name == "get_weather":
        result = get_weather_summary(args.get("location"))
    else:
        result = (
            f"{name} web surumunde kullanilamiyor. "
            "Mac masaustu LEO uygulamasini kullanin veya metin olarak sorun."
        )
    return types.FunctionResponse(id=fc.id, name=name, response={"result": result})


async def _send_json(ws: WebSocket, payload: dict) -> None:
    await ws.send_text(json.dumps(payload, ensure_ascii=False))


async def handle_voice_session(websocket: WebSocket, api_key: str) -> None:
    from google import genai  # type: ignore

    await websocket.accept()
    await _send_json(websocket, {"type": "state", "value": "connecting"})

    client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
    config = _build_live_config()
    muted = False
    out_buf: list[str] = []
    in_buf: list[str] = []

    try:
        async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
            await _send_json(websocket, {"type": "state", "value": "listening"})
            await _send_json(
                websocket,
                {"type": "transcript", "role": "sys", "text": "LEO hazır. Konuşmaya başlayın."},
            )

            async def browser_to_gemini():
                nonlocal muted
                while True:
                    message = await websocket.receive()
                    if message.get("type") == "websocket.disconnect":
                        break

                    if message.get("bytes"):
                        if not muted:
                            await session.send_realtime_input(
                                media={"data": message["bytes"], "mime_type": "audio/pcm"}
                            )
                        continue

                    text = message.get("text")
                    if not text:
                        continue

                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue

                    msg_type = payload.get("type")
                    if msg_type == "mute":
                        muted = bool(payload.get("value", False))
                    elif msg_type == "ping":
                        await _send_json(websocket, {"type": "pong"})
                    elif msg_type == "text":
                        user_text = str(payload.get("message", "")).strip()
                        if user_text:
                            await session.send_client_content(
                                turns={"role": "user", "parts": [{"text": user_text}]},
                                turn_complete=True,
                            )

            async def gemini_to_browser():
                nonlocal out_buf, in_buf
                async for response in session.receive():
                    if response.data:
                        await _send_json(websocket, {"type": "state", "value": "speaking"})
                        await websocket.send_bytes(response.data)

                    if not response.server_content:
                        continue

                    sc = response.server_content

                    if sc.output_transcription and sc.output_transcription.text:
                        txt = _clean_transcript(sc.output_transcription.text)
                        if txt:
                            out_buf.append(txt)

                    if sc.input_transcription and sc.input_transcription.text:
                        txt = _clean_transcript(sc.input_transcription.text)
                        if txt:
                            in_buf.append(txt)

                    if sc.turn_complete:
                        full_in = " ".join(in_buf).strip()
                        if full_in:
                            await _send_json(
                                websocket,
                                {"type": "transcript", "role": "user", "text": full_in},
                            )
                        in_buf = []

                        full_out = " ".join(out_buf).strip()
                        if full_out:
                            await _send_json(
                                websocket,
                                {"type": "transcript", "role": "leo", "text": full_out},
                            )
                        out_buf = []
                        in_buf = []
                        await _send_json(websocket, {"type": "state", "value": "listening"})

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            await _send_json(websocket, {"type": "state", "value": "thinking"})
                            fr = await _execute_web_tool(fc)
                            fn_responses.append(fr)
                        await session.send_tool_response(function_responses=fn_responses)

            async with asyncio.TaskGroup() as tg:
                tg.create_task(browser_to_gemini())
                tg.create_task(gemini_to_browser())

    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await _send_json(websocket, {"type": "error", "message": str(exc)})
            await _send_json(websocket, {"type": "state", "value": "error"})
        except Exception:
            pass
        raise
