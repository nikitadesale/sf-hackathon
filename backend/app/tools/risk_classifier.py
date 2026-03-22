"""
Rule-based risk classification. Pure Python — no LLM involved.

Status meanings:
  approved    — IT-sanctioned agent, in allowlist, properly configured
  shadow      — Never approved by IT, just appeared in the environment
  compromised — Was approved but is now misconfigured or behaving dangerously
"""

# ── Our own scanner + ADK agents — always AUTHORIZED, never flagged ──────────
OWN_TOOL_KEYWORDS = [
    "shadowagentmap",
    "shadow-agent-map",
    "discoverygent",       # ADK DiscoveryAgent
    "riskscoringagent",    # ADK RiskScoringAgent
    "behaviourmonitor",    # ADK BehaviorMonitorAgent
]

# ── Allowlist: agents officially approved by IT ───────────────────────────────
# These are agents that IT has explicitly sanctioned.
# approved + private access  = AUTHORIZED
# approved + public access   = COMPROMISED (misconfigured)
APPROVED_AGENTS = [
    "trusted-hr-processor",   # HR payroll data processor — approved, private
    "invoice-agent-v2",       # Finance invoice processor — approved, but left public (compromised)
    "payroll-processor",      # Alternative name variant
]

# High-privilege service accounts that indicate over-permissioned deployment
HIGH_RISK_SA_KEYWORDS = ["editor", "admin", "owner", "superuser"]

# Names that suggest exfiltration or shadow behaviour
SHADOW_NAME_KEYWORDS  = ["exfil", "collector", "shadow", "external", "scraper"]


def _is_own_tool(name: str) -> bool:
    name_lower = name.lower()
    return any(kw in name_lower for kw in OWN_TOOL_KEYWORDS)

def _in_allowlist(name: str) -> bool:
    name_lower = name.lower()
    return any(approved in name_lower for approved in APPROVED_AGENTS)


def score_agent(agent: dict) -> dict:
    name        = agent.get("name", "").lower()
    ingress     = agent.get("ingress", "internal")
    deployed_by = agent.get("deployed_by", "").lower()

    # Our own scanner is always clean — never flag it
    if _is_own_tool(name):
        return {"risk_score": 0.0, "status": "approved", "risk_reasons": []}

    risk_score   = 0
    risk_reasons = []
    in_allowlist = _in_allowlist(name)

    # ── Risk factor scoring ────────────────────────────────────────────────────

    # Publicly accessible with no authentication
    if ingress == "public":
        risk_score   += 30
        risk_reasons.append("No authentication required — publicly accessible endpoint")

    # High-privilege service account
    if any(kw in deployed_by for kw in HIGH_RISK_SA_KEYWORDS):
        risk_score   += 25
        risk_reasons.append(f"High-privilege service account: {deployed_by}")

    # Name matches known suspicious patterns
    if any(kw in name for kw in SHADOW_NAME_KEYWORDS):
        risk_score   += 20
        risk_reasons.append("Agent name matches shadow/exfil naming patterns")

    risk_score = min(risk_score, 100)

    # ── Status classification ─────────────────────────────────────────────────
    #
    #   approved    → in allowlist AND no critical risk factors
    #   compromised → in allowlist BUT has been misconfigured / risky
    #   shadow      → NOT in allowlist (regardless of auth / risk score)

    if not in_allowlist:
        status = "shadow"
        if "Agent not found in approved registry" not in risk_reasons:
            risk_reasons.insert(0, "Not in IT-approved agent registry")
    elif risk_score >= 30:
        # Approved agent but now misconfigured or behaving dangerously
        status = "compromised"
    else:
        status = "approved"
        risk_score = 0   # clean bill of health

    return {
        "risk_score":   float(risk_score),
        "status":       status,
        "risk_reasons": risk_reasons,
    }


def score_all(agents: list[dict]) -> list[dict]:
    """Applies score_agent to every agent and returns the enriched list."""
    return [{**agent, **score_agent(agent)} for agent in agents]
