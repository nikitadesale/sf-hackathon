import os
from google.adk.agents import Agent
from tools.gcp_scanner import scan_cloud_run, scan_vertex_endpoints
from tools.bigquery_tools import write_agents
from tools.risk_classifier import score_all

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "waybackhome-rw9xuoxqhoap3wax3s")
REGION     = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def scan_and_register() -> dict:
    """
    Scans all Cloud Run services and Vertex AI endpoints in the GCP project,
    then writes every discovered agent to the BigQuery registry.
    Returns a summary of what was found.
    """
    print("[discovery] Scanning Cloud Run services...")
    cloud_run_agents = scan_cloud_run()

    print("[discovery] Scanning Vertex AI endpoints...")
    vertex_agents = scan_vertex_endpoints()

    all_agents = cloud_run_agents + vertex_agents

    # Score agents before writing so registry always has risk data
    print(f"[discovery] Scoring and writing {len(all_agents)} agents to registry...")
    scored = score_all(all_agents)
    write_agents(scored)

    shadow      = [a for a in scored if a["status"] == "shadow"]
    compromised = [a for a in scored if a["status"] == "compromised"]
    approved    = [a for a in scored if a["status"] == "approved"]

    return {
        "total_found":  len(scored),
        "approved":     len(approved),
        "shadow":       len(shadow),
        "compromised":  len(compromised),
        "names":        [a["name"] for a in scored],
    }


discovery_agent = Agent(
    name="DiscoveryAgent",
    model="gemini-2.5-flash-lite",
    instruction="""
    You are a GCP AI agent discovery and security scanner.

    When asked to scan, call scan_and_register() exactly once.
    It will discover all Cloud Run services and Vertex AI endpoints,
    apply risk scoring, and write everything to the BigQuery registry.

    After the tool returns, report results in plain text like:
    "Scan complete: X agents found — Y authorized, Z shadow, W compromised."
    Replace X, Y, Z, W with the actual numbers from the tool response.

    Do not call the tool more than once. Do not ask questions.
    """,
    tools=[scan_and_register],
)
