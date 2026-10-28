import asyncio
import time

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from twilio.twiml.voice_response import Gather, VoiceResponse

from app import brain, tts
from app.log import log_turn

app = FastAPI()
MAX_INPUT = 500  # chars; caps cost/latency from huge inputs


@app.get("/")
def index():
    return FileResponse("web/index.html")


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = (await websocket.receive_text())[-MAX_INPUT:]  # keep the end: the question is usually last
            t0 = time.perf_counter()
            reply = await asyncio.to_thread(brain.answer, text)  # blocking call -> thread
            llm_ms = int((time.perf_counter() - t0) * 1000)
            tts_ms = None
            try:
                await websocket.send_json({"type": "text", "text": reply, "audio": tts.ENABLED})
                if tts.ENABLED:
                    t1 = time.perf_counter()
                    try:
                        audio = await asyncio.to_thread(tts.speak, reply)
                        await websocket.send_bytes(audio)
                    except WebSocketDisconnect:
                        raise
                    except Exception as e:  # e.g. ElevenLabs quota: client falls back to browser voice
                        print("tts failed:", e, flush=True)
                        await websocket.send_json({"type": "tts_error", "text": reply})
                    tts_ms = int((time.perf_counter() - t1) * 1000)
            finally:  # log even if the client left before the reply was sent
                log_turn(channel="ws", input=text, reply=reply, llm_ms=llm_ms,
                         tts_ms=tts_ms, total_ms=llm_ms + (tts_ms or 0))
    except WebSocketDisconnect:
        print("client disconnected", flush=True)


def twiml(vr: VoiceResponse) -> Response:
    return Response(content=str(vr), media_type="application/xml")


def gather() -> Gather:
    return Gather(input="speech", action="/gather", method="POST",
                  speech_timeout="auto", language="en-AU",
                  timeout=10, barge_in=True)


@app.post("/voice")
async def voice():
    vr = VoiceResponse()
    g = gather()
    g.say("Hi, this is Acme support. How can I help?")
    vr.append(g)
    vr.say("I didn't hear anything. Goodbye.")
    return twiml(vr)


@app.post("/gather")
async def gather_result(SpeechResult: str = Form(default="")):
    vr = VoiceResponse()
    if not SpeechResult.strip():
        g = gather()
        g.say("Sorry, I didn't catch that. Could you say it again?")
        vr.append(g)
        return twiml(vr)

    t0 = time.perf_counter()
    reply = await asyncio.to_thread(brain.answer, SpeechResult[-MAX_INPUT:])
    llm_ms = int((time.perf_counter() - t0) * 1000)
    log_turn(channel="phone", input=SpeechResult, reply=reply, llm_ms=llm_ms,
             tts_ms=None, total_ms=llm_ms)

    g = gather()
    g.say(reply)
    vr.append(g)
    return twiml(vr)
