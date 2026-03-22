import os
from datetime import datetime, timezone
from google.cloud import bigquery

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "waybackhome-rw9xuoxqhoap3wax3s")
DATASET = os.getenv("BQ_DATASET", "shadow_agent_map")
TABLE = os.getenv("BQ_TABLE", "agent_registry")
FULL_TABLE = f"{PROJECT_ID}.{DATASET}.{TABLE}"

_client = None


def get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=PROJECT_ID)
    return _client


def write_agents(agents: list[dict]) -> None:
    """Inserts or replaces agents in BigQuery. Uses DELETE + INSERT to keep data fresh."""
    client = get_client()
    now = datetime.now(timezone.utc).isoformat()

    rows = [
        {
            "agent_id": a["agent_id"],
            "name": a["name"],
            "endpoint": a.get("endpoint", ""),
            "deployed_by": a.get("deployed_by", "unknown"),
            "source": a.get("source", "unknown"),
            "ingress": a.get("ingress", "unknown"),
            "risk_score": a.get("risk_score", 0.0),
            "status": a.get("status", "approved"),
            "risk_reasons": "|".join(a.get("risk_reasons", [])),
            "last_seen": now,
        }
        for a in agents
    ]

    if not rows:
        return

    # Truncate and reload for a clean scan result
    client.query(f"TRUNCATE TABLE `{FULL_TABLE}`").result()
    errors = client.insert_rows_json(FULL_TABLE, rows)
    if errors:
        print(f"[bigquery] Insert errors: {errors}")


def get_all_agents() -> list[dict]:
    """Reads all agents from BigQuery and returns them as a list of dicts."""
    client = get_client()
    query = f"SELECT * FROM `{FULL_TABLE}` ORDER BY risk_score DESC"
    try:
        rows = client.query(query).result()
        agents = []
        for row in rows:
            agents.append(
                {
                    "agent_id": row.agent_id,
                    "name": row.name,
                    "endpoint": row.endpoint,
                    "deployed_by": row.deployed_by,
                    "source": row.source,
                    "ingress": row.ingress,
                    "risk_score": row.risk_score,
                    "status": row.status,
                    "risk_reasons": row.risk_reasons.split("|") if row.risk_reasons else [],
                    "last_seen": row.last_seen.isoformat() if row.last_seen else "",
                }
            )
        return agents
    except Exception as e:
        print(f"[bigquery] Read error: {e}")
        return []
