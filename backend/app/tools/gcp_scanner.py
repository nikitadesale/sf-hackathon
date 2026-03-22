import os
from google.cloud import run_v2
from google.cloud import aiplatform

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "waybackhome-rw9xuoxqhoap3wax3s")
REGION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def _is_public(svc_resource_name: str, iam_client: run_v2.ServicesClient) -> bool:
    """
    Returns True only if allUsers has roles/run.invoker — the real auth check.
    Uses GetIamPolicyRequest (correct v2 API signature).
    """
    try:
        from google.iam.v1 import iam_policy_pb2
        request = iam_policy_pb2.GetIamPolicyRequest(resource=svc_resource_name)
        policy  = iam_client.get_iam_policy(request=request)
        for binding in policy.bindings:
            if binding.role == "roles/run.invoker" and "allUsers" in binding.members:
                return True
    except Exception as e:
        print(f"[scanner] IAM check error for {svc_resource_name}: {e}")
    return False


def scan_cloud_run() -> list[dict]:
    """
    Returns all Cloud Run services in the project.
    Auth status is determined by IAM policy (allUsers invoker = public),
    not by the network ingress setting.
    """
    client = run_v2.ServicesClient()
    parent = f"projects/{PROJECT_ID}/locations/{REGION}"
    services = []

    try:
        for svc in client.list_services(parent=parent):
            name    = svc.name.split("/")[-1]
            sa      = svc.template.service_account or "default-compute@developer.gserviceaccount.com"
            is_pub  = _is_public(svc.name, client)
            ingress = "public" if is_pub else "internal"

            services.append({
                "agent_id":    svc.uid or name,
                "name":        name,
                "endpoint":    svc.uri or "",
                "deployed_by": sa,
                "source":      "cloud_run",
                "ingress":     ingress,
            })
    except Exception as e:
        print(f"[scanner] Cloud Run scan error: {e}")

    return services


def scan_vertex_endpoints() -> list[dict]:
    """Returns all Vertex AI endpoints in the project."""
    endpoints = []
    try:
        aiplatform.init(project=PROJECT_ID, location=REGION)
        for ep in aiplatform.Endpoint.list():
            endpoints.append(
                {
                    "agent_id": ep.name.split("/")[-1],
                    "name": ep.display_name,
                    "endpoint": ep.resource_name,
                    "deployed_by": "vertex-ai-service",
                    "source": "vertex_ai",
                    "ingress": "internal",
                }
            )
    except Exception as e:
        print(f"[scanner] Vertex AI scan error: {e}")

    return endpoints
