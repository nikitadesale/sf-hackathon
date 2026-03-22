from google.adk.agents import Agent
from tools.bigquery_tools import get_all_agents, write_agents
from tools.risk_classifier import score_all


def compute_all_risk_scores() -> dict:
    """
    Reads all agents from the BigQuery registry, applies rule-based risk scoring
    to each one, and writes the scores back. Returns a summary of risk findings.
    """
    print("[risk] Reading agents from registry...")
    agents = get_all_agents()

    if not agents:
        return {"error": "No agents found in registry. Run discovery first."}

    print(f"[risk] Scoring {len(agents)} agents...")
    scored = score_all(agents)

    print("[risk] Writing scores back to registry...")
    write_agents(scored)

    shadow = [a for a in scored if a["status"] == "shadow"]
    compromised = [a for a in scored if a["status"] == "compromised"]
    approved = [a for a in scored if a["status"] == "approved"]

    return {
        "total": len(scored),
        "approved": len(approved),
        "shadow": len(shadow),
        "compromised": len(compromised),
        "high_risk": [
            {"name": a["name"], "score": a["risk_score"], "status": a["status"]}
            for a in scored
            if a["risk_score"] > 50
        ],
    }


risk_agent = Agent(
    name="RiskScoringAgent",
    model="gemini-2.5-flash-lite",
    instruction="""
    You are an enterprise AI security risk analyzer.

    When asked to score agents, call compute_all_risk_scores() exactly once.
    It reads all agents from the registry, applies rule-based scoring,
    and writes the results back to BigQuery.

    After the tool returns, report in plain text like:
    "Risk scoring complete: X agents total. Y authorized, Z shadow, W compromised.
    High risk agents: [list names and scores from the tool response]."
    Replace X, Y, Z, W with actual numbers from the tool response.

    Do not call the tool more than once. Do not ask questions.
    """,
    tools=[compute_all_risk_scores],
)
