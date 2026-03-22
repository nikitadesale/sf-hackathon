# ShadowAgentMap

> **Automatically discover, classify, and audit every AI agent running in your GCP environment — before your security team finds out the hard way.**

Built for the **Build with AI · SF Hackathon 2026** · Google ADK + Gemini 2.5 + Cloud Run

---

## The Problem

Enterprise teams are deploying AI agents faster than IT can track them. A developer spins up a Cloud Run service to process invoices. A data scientist deploys a Vertex AI endpoint for analysis. A contractor leaves behind an agent that was never decommissioned. None of these are in any registry. None are audited. All of them have IAM permissions.

These are **shadow agents** — and they represent the next generation of insider threat.

Traditional security tools scan for CVEs and misconfigurations in infrastructure. They don't know what an AI agent is, what it can access, or whether it was ever approved.

**ShadowAgentMap does.**

---

## What It Does

ShadowAgentMap continuously scans your GCP project and produces a live, visual threat map of every AI agent running in your environment — classified by risk, explained in plain English by Gemini, and audited in BigQuery.

| Capability | Detail |
|---|---|
| **Agent Discovery** | Scans Cloud Run and Vertex AI endpoints via GCP REST APIs |
| **Real IAM Detection** | Calls `GetIamPolicyRequest` to check for `allUsers` with `roles/run.invoker` — not inferred from ingress settings |
| **Risk Classification** | Rule-based engine: Authorized / Shadow / Compromised — no hallucination risk |
| **Live Security Briefing** | Gemini 2.5 Flash Lite streams a 3-sentence CISO-ready analysis per agent via WebSocket |
| **Persistent Audit Trail** | Every scan writes to BigQuery `agent_registry` for compliance and history |
| **Visual Threat Map** | React Flow graph with animated threat vectors between risky and trusted agents |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHADOWAGENTMAP SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Browser (React)                                                │
│      │                                                          │
│      ├── POST /api/scan ──────────────────────────────────┐     │
│      │                                                    ▼     │
│      │                                           FastAPI Backend │
│      │                                                    │     │
│      │                                    ┌───────────────┤     │
│      │                                    ▼               ▼     │
│      │                           ADK DiscoveryAgent    ADK      │
│      │                           scan_and_register()  RiskAgent │
│      │                                    │               │     │
│      │                           Cloud Run API      BigQuery    │
│      │                           Vertex AI API      agent_registry
│      │                           IAM Policy Check              │
│      │                                                          │
│      ├── GET /api/agents ──────── BigQuery ◀── scored agents    │
│      │                                    │                     │
│      │                           React Flow Graph               │
│      │                           (threat map)                   │
│      │                                                          │
│      └── WS /ws/monitor ──────── BehaviorMonitor               │
│                                  Gemini 2.5 Flash Lite          │
│                                  stream tokens → frontend       │
└─────────────────────────────────────────────────────────────────┘
```

### ADK Agent Pipeline

```
GCP Scanner ──▶ DiscoveryAgent ──▶ RiskScoringAgent ──▶ BigQuery ──▶ BehaviorMonitor ──▶ Frontend
                  (ADK)               (ADK)                              (ADK · Live)
```

Three specialized ADK agents, each with a single responsibility:

| Agent | Role | Model |
|---|---|---|
| `DiscoveryAgent` | Calls `scan_and_register()` — discovers all Cloud Run + Vertex AI services | gemini-2.5-flash-lite |
| `RiskScoringAgent` | Calls `score_agents()` — applies rule-based classification, writes scores to BigQuery | gemini-2.5-flash-lite |
| `BehaviorMonitor` | Live WebSocket analysis — streams Gemini security briefings per agent | gemini-2.5-flash-lite |

---

## Risk Classification Logic

Classification is **rule-based, not LLM-based** — deterministic, auditable, no hallucination risk.

```python
# Three possible states
AUTHORIZED   → In IT-approved registry  + properly configured (private, limited SA)
SHADOW       → NOT in IT-approved registry (regardless of auth or risk score)
COMPROMISED  → In IT-approved registry  + misconfigured (public access, over-permissioned SA)
```

**Risk scoring factors:**

| Factor | Score | Signal |
|---|---|---|
| Public endpoint (`allUsers` invoker) | +30 | No authentication required |
| High-privilege service account | +25 | `editor`, `admin`, `owner` roles |
| Suspicious name pattern | +20 | `shadow`, `collector`, `exfil`, `scraper` |

Score ≥ 30 on an approved agent → **COMPROMISED**. Any unapproved agent → **SHADOW** regardless of score.

---

## Demo Agents

Three Cloud Run services deployed to demonstrate the three classification states:

| Service | Status | Why |
|---|---|---|
| `trusted-hr-processor` | ✅ AUTHORIZED | IT-approved, private ingress, minimal SA (`logging.logWriter` only) |
| `invoice-agent-v2` | 🔴 COMPROMISED | IT-approved, but redeployed publicly — `allUsers` has `roles/run.invoker` |
| `shadow-data-collector` | 🟠 SHADOW | Never in the IT registry. Just appeared. |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent Orchestration | Google Agent Development Kit (ADK) | Stateful agent pipeline with `InMemorySessionService` + `run_async()` |
| LLM | Gemini 2.5 Flash Lite via Vertex AI Express | Agent reasoning + live security analysis |
| Backend | FastAPI + uvicorn | REST API + WebSocket server |
| Discovery | Cloud Run v2 API + AI Platform API | Real-time service enumeration |
| Auth Detection | `google-iam-v1` `GetIamPolicyRequest` | Actual IAM policy inspection, not ingress inference |
| Storage | BigQuery (`agent_registry` table) | Persistent audit trail |
| Infrastructure | Terraform | Service accounts, IAM bindings, BigQuery schema |
| Frontend | React + React Flow | Live threat map with animated edges |
| Deployment | Cloud Run | Serverless, scales to zero |
| Pipeline Visualization | RocketRide | Visual pipeline canvas (Chat → Gemini → Output) |

---

## Project Structure

```
shadow-agent-map/
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI server, WebSocket handler
│       ├── agents/
│       │   ├── discovery_agent.py     # ADK DiscoveryAgent
│       │   ├── risk_agent.py          # ADK RiskScoringAgent
│       │   └── monitor_agent.py       # ADK BehaviorMonitor
│       └── tools/
│           ├── gcp_scanner.py         # Cloud Run + Vertex AI discovery
│           ├── risk_classifier.py     # Rule-based classification engine
│           └── bigquery_tools.py      # Registry read/write
├── frontend/
│   └── src/
│       ├── App.jsx                    # Main app, scan trigger, state
│       ├── components/
│       │   ├── AgentGraph.jsx         # React Flow threat map
│       │   ├── SidePanel.jsx          # Agent detail view
│       │   └── LiveMonitor.jsx        # Streaming Gemini output
│       └── hooks/
│           └── useAgentSocket.js      # WebSocket client with auto-reconnect
├── demo-agents/
│   ├── trusted-hr-processor/          # AUTHORIZED demo
│   ├── invoice-agent-v2/              # COMPROMISED demo
│   ├── shadow-data-collector/         # SHADOW demo
│   └── deploy.sh                      # One-command demo deployment
├── terraform/
│   ├── main.tf                        # GCP APIs, provider
│   ├── iam.tf                         # Service accounts + bindings
│   ├── bigquery.tf                    # Dataset + agent_registry table
│   └── variables.tf
├── pipelines/
│   └── monitor.pipe                   # RocketRide pipeline (Chat → Gemini → Output)
└── architecture/
    └── flow.html                      # Animated architecture diagram
```

---

## Getting Started

### Prerequisites

- GCP project with billing enabled
- `gcloud` CLI authenticated (`gcloud auth application-default login`)
- Python 3.11+, Node.js 18+
- Terraform (for infrastructure provisioning)

### 1. Provision Infrastructure

```bash
cd terraform
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

Creates:
- `shadowagentmap-sa` — scanner service account with minimum required roles
- `trusted-hr-agent-sa` — demo agent SA with `logging.logWriter` only
- BigQuery dataset `shadow_agent_map` + `agent_registry` table

### 2. Configure Environment

```bash
cp backend/app/.env.example backend/app/.env
```

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_API_KEY=your-vertex-ai-express-key
BQ_DATASET=shadow_agent_map
BQ_TABLE=agent_registry
PORT=8080
```

### 3. Deploy Demo Agents

```bash
cd demo-agents
bash deploy.sh
```

Deploys all three demo agents and removes any stale services.

### 4. Run Backend

```bash
cd backend
pip install -e .
python app/main.py
```

### 5. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` → click **Scan Now**.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/scan` | POST | Triggers full ADK pipeline: discover → score → write to BigQuery |
| `/api/agents` | GET | Returns all agents as React Flow nodes + edges |
| `/ws/monitor` | WebSocket | Accepts `{agent_id}`, streams Gemini security briefing |

---

## Security Design Decisions

**Why rule-based classification instead of LLM?**
Classification must be deterministic for security tooling. An LLM deciding whether something is "shadow" introduces non-determinism and audit risk. The classifier is pure Python, fully testable, and produces consistent results across every scan.

**Why real IAM policy checks instead of ingress flag?**
Cloud Run's `ingress` setting controls which networks can reach the service — it does not reflect the IAM authentication requirement. A service can have `ingress=internal` and still have `allUsers` as invoker. We use `GetIamPolicyRequest` to inspect the actual IAM bindings.

**Why a separate service account per agent?**
Principle of least privilege. The scanner SA has only `run.viewer`, `aiplatform.viewer`, `bigquery.dataEditor`. The HR demo agent SA has only `logging.logWriter`. Blast radius is contained.

---

## Team

Built in 8 hours at the **Build with AI · SF Hackathon 2026**.

- Nikita Desale
- Samadrita Roy Chowdhury

#google-adk  #gemini  #google-cloud  #cloud-run  #bigquery  #fastapi  #security  #ai-agents #builtwithgoogle #buildwithaisf
---


