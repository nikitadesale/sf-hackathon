import asyncio
import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from google.adk.runners import Runner, InMemorySessionService
from google.genai import types, Client as GenaiClient

from agents.discovery_agent import discovery_agent
from agents.risk_agent import risk_agent
from agents.monitor_agent import monitor_agent
from tools.bigquery_tools import get_all_agents

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "waybackhome-rw9xuoxqhoap3wax3s")
REGION     = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
PORT       = int(os.getenv("PORT", 8080))
APP_NAME     = "shadow-agent-map"
GEMINI_MODEL = "gemini-2.5-flash-lite"
# Single shared client — reads GOOGLE_API_KEY + GOOGLE_GENAI_USE_VERTEXAI from env
_gemini = GenaiClient()

# In-memory cache — used as fallback when BigQuery isn't set up yet
_agent_cache: list[dict] = []

app = FastAPI(title="ShadowAgentMap API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# One shared session service, one Runner per agent
session_service   = InMemorySessionService()
discovery_runner  = Runner(app_name=APP_NAME, agent=discovery_agent, session_service=session_service)
risk_runner       = Runner(app_name=APP_NAME, agent=risk_agent,      session_service=session_service)
monitor_runner    = Runner(app_name=APP_NAME, agent=monitor_agent,   session_service=session_service)


# ── Helpers ──────────────────────────────────────────────────────────────────

async def run_agent(runner: Runner, prompt: str) -> str:
    """Runs a batch ADK agent (discovery / risk) and returns the final text."""
    user_id    = "system"
    session_id = f"batch-{uuid.uuid4().hex[:8]}"

    await session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    result = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    result += part.text
    return result


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.post("/api/scan")
async def trigger_scan():
    """
    Full ADK pipeline:
      1. DiscoveryAgent  — scans Cloud Run + Vertex AI, writes raw agents to BigQuery
      2. RiskScoringAgent — reads registry, scores every agent, writes scores back
    Both agents use Gemini to orchestrate their tool calls via ADK Runner.
    Results are also cached in memory as fallback.
    """
    global _agent_cache

    # ── Step 1: ADK DiscoveryAgent ──────────────────────────────────────────
    print("[scan] Running DiscoveryAgent...")
    try:
        discovery_summary = await run_agent(
            discovery_runner,
            "Scan the GCP project for all running AI agents and register them."
        )
        print(f"[scan] Discovery: {discovery_summary[:120]}")
    except Exception as e:
        print(f"[scan] DiscoveryAgent failed, falling back to direct scan: {e}")
        # Fallback: call tools directly if Gemini quota/error
        from tools.gcp_scanner import scan_cloud_run, scan_vertex_endpoints
        from tools.bigquery_tools import write_agents
        agents_raw = scan_cloud_run() + scan_vertex_endpoints()
        try:
            write_agents(agents_raw)
        except Exception:
            pass

    # ── Step 2: ADK RiskScoringAgent ────────────────────────────────────────
    print("[scan] Running RiskScoringAgent...")
    try:
        risk_summary = await run_agent(
            risk_runner,
            "Score all discovered agents for security risk and update the registry."
        )
        print(f"[scan] Risk: {risk_summary[:120]}")
    except Exception as e:
        print(f"[scan] RiskScoringAgent failed, falling back to direct scoring: {e}")
        # Fallback: score directly
        from tools.bigquery_tools import get_all_agents, write_agents
        from tools.risk_classifier import score_all
        agents_raw = get_all_agents()
        if agents_raw:
            scored = score_all(agents_raw)
            try:
                write_agents(scored)
            except Exception:
                pass

    # ── Step 3: Read final state + populate memory cache ────────────────────
    from tools.bigquery_tools import get_all_agents as _get
    final_agents = _get()

    # If BigQuery write worked, cache from there; otherwise run scoring in-memory
    if final_agents:
        _agent_cache = final_agents
    else:
        from tools.gcp_scanner import scan_cloud_run, scan_vertex_endpoints
        from tools.risk_classifier import score_all
        _agent_cache = score_all(scan_cloud_run() + scan_vertex_endpoints())
        final_agents = _agent_cache

    shadow      = [a for a in final_agents if a["status"] == "shadow"]
    compromised = [a for a in final_agents if a["status"] == "compromised"]
    approved    = [a for a in final_agents if a["status"] == "approved"]

    return {
        "total":       len(final_agents),
        "approved":    len(approved),
        "shadow":      len(shadow),
        "compromised": len(compromised),
        "agents":      [a["name"] for a in final_agents],
    }


@app.get("/api/agents")
async def get_agents():
    """Returns all agents as React Flow nodes + edges."""
    agents = get_all_agents()
    # Fall back to in-memory cache if BigQuery is empty / not set up
    if not agents and _agent_cache:
        agents = sorted(_agent_cache, key=lambda a: a.get("risk_score", 0), reverse=True)

    nodes = []
    for i, agent in enumerate(agents):
        col, row = i % 3, i // 3
        nodes.append({
            "id":   agent["agent_id"],
            "type": "agentNode",
            "position": {"x": 280 * col + 60, "y": 200 * row + 60},
            "data": {
                "name":         agent["name"],
                "status":       agent["status"],
                "risk_score":   agent["risk_score"],
                "endpoint":     agent["endpoint"],
                "deployed_by":  agent["deployed_by"],
                "source":       agent["source"],
                "ingress":      agent["ingress"],
                "risk_reasons": agent["risk_reasons"],
                "last_seen":    agent["last_seen"],
            },
        })

    approved_ids = [a["agent_id"] for a in agents if a["status"] == "approved"]
    risky_ids    = [a["agent_id"] for a in agents if a["status"] in ("shadow", "compromised")]
    edges = [
        {"id": f"e-{r}-{a}", "source": r, "target": a,
         "animated": True, "style": {"stroke": "#d93025"}}
        for r in risky_ids for a in approved_ids
    ]

    return {"nodes": nodes, "edges": edges, "total": len(agents)}


# ── WebSocket — direct Gemini streaming (1 API call per analysis) ─────────────

SYSTEM_PROMPT = """You are a real-time AI security analyst for enterprise environments.
When given details about an AI agent, provide a concise 3-sentence security briefing:
1. What this agent can access and what it is doing
2. Why it poses a security risk (or why it is safe)
3. What the security team should do right now
Be direct. Sound like a real analyst briefing a CISO. No fluff."""

@app.websocket("/ws/monitor")
async def monitor_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text(json.dumps({"type": "ready"}))

    try:
        while True:
            raw      = await websocket.receive_text()
            message  = json.loads(raw)
            agent_id = message.get("agent_id", "")

            agents = _agent_cache or get_all_agents()
            agent  = next((a for a in agents if a["agent_id"] == agent_id), None)

            if not agent:
                await websocket.send_text(json.dumps({"type": "error", "content": "Agent not found."}))
                continue

            prompt = (
                f"Analyze this AI agent:\n"
                f"Name: {agent['name']}\n"
                f"Status: {agent['status']}\n"
                f"Risk score: {agent['risk_score']}/100\n"
                f"Auth: {'None — public' if agent['ingress'] == 'public' else 'Required'}\n"
                f"Service account: {agent['deployed_by']}\n"
                f"Risk factors: {', '.join(agent['risk_reasons']) if agent['risk_reasons'] else 'None'}\n\n"
                f"Give your 3-sentence security briefing now."
            )

            try:
                # Single streaming call — no session overhead, no extra API calls
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: _gemini.models.generate_content_stream(
                        model=GEMINI_MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.4,
                            max_output_tokens=300,
                        ),
                    )
                )
                for chunk in response:
                    text = chunk.text if hasattr(chunk, "text") else ""
                    if text:
                        await websocket.send_text(json.dumps({"type": "text", "content": text}))

            except Exception as model_err:
                err_msg = str(model_err)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    hint = "Rate limit hit — wait 60 seconds and click Analyze again."
                elif "404" in err_msg or "NOT_FOUND" in err_msg:
                    hint = f"Model '{GEMINI_MODEL}' not found. Check GOOGLE_API_KEY in .env."
                elif "401" in err_msg or "403" in err_msg or "API_KEY" in err_msg:
                    hint = "Invalid API key — check GOOGLE_API_KEY in .env."
                else:
                    hint = err_msg[:200]
                print(f"[WS monitor] {err_msg[:200]}")
                await websocket.send_text(json.dumps({"type": "error", "content": hint}))

            await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS monitor] {e}")


# ── Serve React frontend in production ───────────────────────────────────────

FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(FRONTEND_DIST / "index.html")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
