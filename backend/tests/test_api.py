import os

os.environ.setdefault("DEMO_MODE", "true")

from fastapi.testclient import TestClient
from backend.app.main import app


def test_dashboard_and_project_workflow():
    with TestClient(app) as client:
        dashboard = client.get("/api/dashboard")
        assert dashboard.status_code == 200
        assert dashboard.json()["demo"] is True
        assert len(dashboard.json()["project"]) >= 6

        client.post("/api/repositories/discover").raise_for_status()
        managed = client.patch(
            "/api/repositories/state",
            json={"id": "sample/new-project", "state": "managed"},
        )
        assert managed.json()["state"] == "managed"

        project = client.post(
            "/api/projects",
            json={
                "name": "API test project",
                "repositories": ["sample/new-project"],
                "provider": "GitHub Actions",
                "branch": "main",
            },
        )
        project.raise_for_status()
        assert project.json()["environments"] == [
            "development",
            "preview",
            "staging",
            "production",
        ]


def test_security_gate_and_rollback_validation():
    with TestClient(app) as client:
        blocked = client.post(
            "/api/projects/journeyalert/deployments",
            json={"action": "deploy", "environment": "production"},
        )
        assert blocked.status_code == 409
        assert "Security gate" in blocked.json()["detail"]

        invalid = client.post(
            "/api/projects/mediaverse/deployments",
            json={
                "action": "rollback",
                "environment": "production",
                "target": "deploy-3-0",
            },
        )
        assert invalid.status_code == 400


def test_sample_health_and_secret_boundary():
    with TestClient(app) as client:
        check = client.post("/api/health/checks/check-0-0/run")
        check.raise_for_status()
        assert check.json()["sample"] is True

        secret = client.post(
            "/api/projects/mediaverse/secrets",
            json={"name": "DATABASE_URL", "value": "never-store-plaintext"},
        )
        assert secret.status_code == 503
        assert "MASTER_ENCRYPTION_KEY" in secret.json()["detail"]
