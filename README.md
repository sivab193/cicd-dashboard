# cicd.siv19.dev

A private engineering control plane for projects, deployments, security, health, infrastructure, logs, and audit activity. The repository includes a responsive React dashboard, a FastAPI API, a Redis-backed worker, PostgreSQL persistence, and an outbound-only Go host agent.

## Explore locally

```bash
npm install
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
./run.sh
```

Open `http://127.0.0.1:5173`. Sample mode is enabled by default and labels every simulated provider action. The local fallback database is SQLite; production uses PostgreSQL through `DATABASE_URL`.

Vercel can deploy the Vite dashboard and the FastAPI function from this repository. Set the Vercel project Root Directory to the repository root (the directory containing `package.json` and `vercel.json`) and provide `DATABASE_URL` (PostgreSQL) plus the production environment variables below for durable, live data. Without `DATABASE_URL`, Vercel uses an in-memory demo database because its function filesystem is ephemeral.

## Production configuration

Copy `.env.example` to `.env`, set `DEMO_MODE=false`, generate `SESSION_SECRET`, and generate a Fernet key for `MASTER_ENCRYPTION_KEY`. Set `APP_URL` to the exact public HTTPS origin. Never commit `.env` or the GitHub App private key.

Create two GitHub integrations:

1. A GitHub OAuth app for login. Set its callback URL to `https://cicd.siv19.dev/api/auth/callback` and list authorized accounts with roles in `GITHUB_ALLOWED_USERS`.
2. A GitHub App for repository discovery and Actions. Give it read access to metadata, contents, Actions, checks, and pull requests; give Actions write access only if dispatch, rerun, and cancel controls are required. Set its webhook URL to `https://cicd.siv19.dev/api/webhooks/github`, subscribe to workflow-run and installation/repository events, and mount the private key at `GITHUB_APP_PRIVATE_KEY_PATH`.

Configure provider fields per project in the Settings tab:

- Vercel: `project_id`, numeric GitHub `repo_id`, and optional `team_id`. Set `VERCEL_TOKEN` on the API and worker.
- GitHub Actions: `installation_id` and a dispatchable workflow filename.
- Docker Compose: registered `agent_id` and an allowlisted service name.

The agent only makes outbound HTTPS requests and only executes fixed Docker Compose operations for services in its local allowlist. Register a host through `POST /api/agents/register`, store the one-time token in `agent.json`, and map logical service names to absolute Compose file paths. It does not expose SSH or a general shell.

Run the full stack behind an HTTPS reverse proxy:

```bash
docker compose up --build -d
```

Run exactly one `scheduler` replica. Worker replicas may scale horizontally. Configure backups for the PostgreSQL volume before connecting production systems.

## Security pipeline and scanner imports

`.github/workflows/devsecops.yml` contains the requested V1 scanners: Semgrep, Gitleaks, Trivy, OSV-Scanner, and Syft/CycloneDX generation. Upload their JSON output to `POST /api/security/import` from a trusted CI job. Critical vulnerabilities and detected secrets block deployment by default; project settings can override those gates. Raw secret values from Gitleaks are never retained.

## Verification

```bash
npm run build
DATABASE_URL=sqlite:////private/tmp/cicd-test.db .venv/bin/pytest -q
GOCACHE=/private/tmp/cicd-go-cache go test ./agent/...
```

The browser smoke path covers desktop and mobile rendering, navigation, repository triage, project creation, and a sample deployment action.
