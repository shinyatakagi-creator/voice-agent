# Voice agent (Acme Cloud Backup support)

A small voice support agent. Callers ask about a support ticket or a how-to question. Claude answers, calling a `get_ticket_status` tool against synthetic data (`data/tickets.json`).

Built with Twilio webhooks, a FastAPI WebSocket server, an LLM tool call and TTS.

Two ways in, one brain:
- Browser: Chrome speech recognition, WebSocket `/ws`, spoken reply (ElevenLabs TTS attempted, not tested with real audio because the key hit its 10-credit cap; browser voice used).
- Phone: Twilio calls the webhooks `/voice` and `/gather`; Twilio does speech recognition and `<Say>`.

See `docs/writeup.md` for the diagram, latency table and failures.

## Status
What ran:
- Browser WebSocket version: 10 turns are tabulated in the write-up (5 ticket lookups, 5 how-to questions), from my local turn log, available on request.
- Twilio phone call: after the `<Gather>` fix, the full call worked. 4 phone turns are tabulated (LLM stage only; Twilio handles recognition and speaking).
- Break-it tests on the WebSocket: socket closed mid-reply, 2,000-word input, two questions back to back, unknown ticket 9999.

The TTS caveat: my ElevenLabs key had a 10-credit cap, so each TTS request failed fast with a quota error and the browser voice spoke instead. The TTS column measures that error, not real speech time. Real ElevenLabs speech time was not measured. Speech recognition time was not measured on the server either.

Not covered by automated tests: the Claude call and tool use, TTS, and the Twilio webhooks. Those were only run by hand, as described above.

## Run it
```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install fastapi "uvicorn[standard]" websockets anthropic httpx python-dotenv twilio pytest python-multipart elevenlabs
cp .env.example .env        # fill in your own keys
python -m pytest
uvicorn app.main:app --port 8000
```
Browser version: open http://localhost:8000, hold the button and speak (or type).

Phone version:
```bash
cloudflared tunnel --url http://localhost:8000   # put the printed URL in PUBLIC_URL
python call_me.py                                # Twilio calls MY_MOBILE
```
The tunnel URL changes on every restart.

## Tested
- `get_ticket_status` returns `found: True` for a known ticket.
- `get_ticket_status` returns `found: False` for an unknown ticket.

These two unit tests need no API keys and no network. Run them with `python -m pytest`.

## Not tested
No automated tests cover:
- The Claude call and tool-use loop
- TTS
- The Twilio webhooks and `call_me.py`

## Failures found and fixed
Details are in `docs/writeup.md`.
- A TTS quota error killed the WebSocket. Fix: catch it and fall back to the browser voice.
- A phone call ended after about 12 seconds. Fix: longer `<Gather>` timeout and barge-in.
- Every WebSocket turn is now logged, and long inputs keep their last 500 characters instead of their first.

## What it cannot do
Production telephony, SIP trunking, scaling, call streaming, or real customer data. Tickets are fake.

No authentication, no Twilio request-signature check and no rate limiting on /ws, /voice and /gather. It is a local demo behind a temporary tunnel, not safe to leave exposed.

## Not done yet
- Measure speech recognition time on the server. It is not measured today.
- Break down latency by stage (recognition, LLM, TTS, network) to diagnose slow or cut-off calls.

## License
MIT
