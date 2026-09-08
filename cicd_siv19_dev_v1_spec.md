# cicd.siv19.dev — V1 Product & Engineering Specification

## 1. Product Vision

`cicd.siv19.dev` should become a **private self-hosted DevSecOps control plane** for all actively maintained projects and infrastructure.

It should be the central place to answer:

- What projects do I own?
- What version is currently deployed?
- Did the build succeed?
- Is production healthy?
- Are there known vulnerabilities?
- Which machine or provider is running it?
- Can I deploy, restart, or roll back it?
- What changed recently?

The platform should **control deployments**, but it should not necessarily execute every build itself.

It should orchestrate and integrate with existing systems such as:

- GitHub
- GitHub Actions
- Vercel
- Docker / Docker Compose
- Self-hosted machines
- Security scanners
- Health checks

The platform should avoid becoming a custom Jenkins clone in V1.

---

# 2. Core Architectural Principle

`cicd.siv19.dev` is the **source of control and visibility**.

Actual work may run in different places depending on the project:

```text
GitHub
  |
  +--> GitHub Actions
  |
  +--> Vercel
  |
  +--> cicd.siv19.dev
          |
          +--> Docker / OMV
          |
          +--> Self-hosted agents
```

The UI and backend should normalize these systems behind common abstractions.

---

# 3. Health Monitoring Strategy

The functionality currently associated with `health.siv19.dev` should be merged into the CI/CD backend.

There should be only **one health-checking backend**.

However:

- `cicd.siv19.dev` = private operational dashboard
- `health.siv19.dev` = optional public/sanitized status page

Architecture:

```text
CI/CD Backend
    |
    +--> Health Check Engine
            |
            +--> cicd.siv19.dev/health
            |
            +--> health.siv19.dev
```

`health.siv19.dev` should not have a separate monitoring implementation.

---

# 4. GitHub Repository Discovery

The system should automatically discover repositories from:

- Personal GitHub account
- GitHub organizations the user has access to
- Organizations such as Aayvu and SplitLLM
- Future organizations

Use a **GitHub App**, not a long-lived personal access token.

The GitHub App should support installation on:

- All repositories
- Selected repositories

Repository discovery should support three states:

```text
Managed
Ignored
Unreviewed
```

This is important because many repos may be:

- Old college assignments
- Labs
- Experiments
- Archived work
- Junk/test repos

Newly discovered repositories should default to **Unreviewed**.

The system must not automatically manage every discovered repository.

---

# 5. Repository Filtering

Support repository ignore rules such as:

```text
Ignore archived repositories
Ignore forks

Ignore patterns:
assignment-*
lab-*
test-*
archive-*

Optional:
Ignore repositories with no activity in N years
```

Ignored repositories must remain visible in an "Ignored Repositories" section and must be re-enableable.

Do not permanently hide or delete ignored repos.

---

# 6. Project Model

The central object in the platform is a **Project**.

A GitHub repository is not necessarily the same thing as a project.

Example:

```text
Repository:
Aayvu

Projects:
- Aayvu Web
- Aayvu API
- Aayvu Worker
```

Therefore the data model must support:

```text
Repository 1 ----> N Projects
Project N ------> N Repositories (future-safe)
```

Do not enforce one-repo-equals-one-project.

---

# 7. Project Metadata

Each Project should support:

```text
Name
Description
Repository/repositories
Default branch
Deployment provider
Production URL
Preview URLs
Environments
Health checks
Security policy
Notification policy
Infrastructure mapping
```

Example:

```text
MediaVerse

Repository:
sivab193/mediaverse

Branch:
main

Environment:
Production

Provider:
Vercel

Production URL:
https://media-verse.in

Health:
Healthy

Security:
0 Critical
2 High

Latest commit:
fa41921
```

---

# 8. Environments

Support these environment types structurally from the beginning:

```text
Development
Preview
Staging
Production
```

Projects may initially use only Production.

Do not hardcode the data model around one environment.

---

# 9. Project Onboarding Flow

Suggested UX:

```text
Connect GitHub
    |
Choose personal account / organizations
    |
Discover repositories
    |
Choose:
Managed / Ignored
    |
Inspect repository
    |
Auto-detect stack
    |
Auto-detect deployment provider
    |
Auto-detect domains
    |
Suggest health check
    |
Suggest CI template
    |
Create Project
```

---

# 10. Stack Auto-Detection

Detect project type from repository contents.

Examples:

```text
package.json          -> Node.js
vite.config.*         -> Vite
next.config.*         -> Next.js
requirements.txt      -> Python
pyproject.toml        -> Python
Dockerfile            -> Docker
docker-compose.yml    -> Docker Compose
compose.yml           -> Docker Compose
vercel.json           -> Vercel
.github/workflows/*   -> GitHub Actions
```

Auto-detection should create recommendations, not silently change configuration.

---

# 11. Deployment Providers

Design the system around a provider interface.

Example abstraction:

```text
DeploymentProvider

- deploy()
- redeploy()
- rollback()
- restart()
- stop()
- get_status()
- get_logs()
- list_deployments()
```

V1 providers:

```text
GitHub Actions
Vercel
Docker Compose
```

Future providers:

```text
Cloudflare Pages
Railway
Fly.io
AWS
Kubernetes
SSH
```

Core business logic must not depend directly on a specific provider.

---

# 12. Deployment Controls

Projects should expose common controls where supported:

```text
Deploy
Redeploy
Rollback
Restart
Stop
```

Different providers can implement these differently.

Examples:

### Vercel

```text
Deploy
Redeploy
Promote deployment
Rollback production
```

### Docker Compose

```text
Pull image
docker compose up -d
Restart container/service
Stop service
Rollback to previous image/version
```

### GitHub Actions

```text
workflow_dispatch
re-run workflow
cancel workflow
```

The UI should remain consistent even if internals differ.

---

# 13. Deployment State Machine

Every deployment should follow a normalized lifecycle.

```text
Queued
  |
Building
  |
Security Scanning
  |
Deploying
  |
Verifying
  |
  +--> Failed
  |
Healthy
```

Possible statuses should include:

```text
queued
building
scanning
deploying
verifying
healthy
failed
cancelled
rolled_back
```

---

# 14. Deployment Record

Each deployment should store:

```text
Project
Environment
Commit SHA
Branch
Source
Triggered by
Provider
Start time
End time
Duration
Build status
Security status
Deploy status
Verification status
Overall status
Previous deployment
Rollback target
Artifact/image metadata
Logs references
```

Example:

```text
Deployment #102

Project:
MediaVerse

Commit:
fa41921

Triggered by:
Sivaganesh

Source:
Manual deploy

Build:
Passed

Security:
Passed

Deploy:
Passed

Verification:
Passed

Duration:
1m 52s

Status:
Healthy
```

---

# 15. Deployment History

Example:

```text
#105   fa41921   Healthy     <- Current
#104   2ab883c   Healthy
#103   d941cc8   Failed
#102   f732bae   Healthy
```

Each deployment should support:

```text
View changes
View logs
View commit
Deploy this version
Rollback to this version
```

---

# 16. Rollbacks

Rollback must be first-class.

A rollback must create a **new deployment record**.

Example:

```text
Deployment #106

Type:
Rollback

From:
#105

Target:
#104

Commit:
2ab883c
```

Do not mutate deployment history in-place.

Maintain complete auditability.

---

# 17. Optional Automatic Rollback

Support automatic rollback configuration per Project/Environment.

Default: OFF.

Example:

```text
Automatically rollback if Production becomes unhealthy
within 5 minutes after deployment
```

This should be configurable but disabled by default in V1.

---

# 18. CI Integration

For V1, do **not** replace GitHub Actions.

Integrate with it.

Read and display:

```text
Workflow runs
Jobs
Steps
Logs
Duration
Commit
Branch
Pull request
Actor
Status
```

Controls:

```text
Re-run
Cancel
View commit
View PR
View logs
```

---

# 19. Recommended CI Pipeline

Standard logical pipeline:

```text
Push / PR
   |
Lint
   |
Tests
   |
Security
   |
Build
   |
Artifact / Image
   |
Deploy
   |
Health Verification
```

Individual stages must be optional per project.

---

# 20. Security Stack — V1

Use only these scanners initially:

## Semgrep

Purpose:

```text
SAST
Source-code vulnerability detection
```

## Gitleaks

Purpose:

```text
Secret scanning
```

## Trivy

Purpose:

```text
Dependency vulnerabilities
Container image vulnerabilities
OS package vulnerabilities
IaC misconfigurations
```

## OSV-Scanner

Purpose:

```text
Dependency vulnerability scanning
```

## Syft

Purpose:

```text
SBOM generation
```

Do not add large numbers of additional scanners in V1.

---

# 21. Security Scan Triggers

Recommended defaults:

## Pull Requests

Run:

```text
Semgrep
Gitleaks
Trivy
OSV-Scanner
```

## Push to Main

Run:

```text
Semgrep
Gitleaks
Trivy
OSV-Scanner
Syft
```

## Nightly

Run against deployed/current production versions:

```text
Trivy
OSV-Scanner
```

This catches vulnerabilities disclosed after deployment.

---

# 22. Security Finding Normalization

Do not expose raw scanner outputs as the primary data model.

Normalize findings into a common schema.

Example:

```json
{
  "project": "MediaVerse",
  "environment": "production",
  "scanner": "trivy",
  "category": "dependency",
  "severity": "high",
  "package": "express",
  "file": "package-lock.json",
  "cve": "CVE-XXXX-YYYY",
  "installed_version": "x.y.z",
  "fixed_version": "a.b.c",
  "status": "open"
}
```

Possible categories:

```text
sast
dependency
secret
container
iac
license
```

Possible statuses:

```text
open
acknowledged
ignored
fixed
false_positive
```

---

# 23. Security Gates

Default deployment policy:

Block deployment when:

```text
Secret detected
Critical SAST finding
Critical dependency vulnerability
Critical container vulnerability
```

Warn but do not block:

```text
High
Medium
Low
```

Policies must be overridable per project/environment.

---

# 24. SBOM

Generate a CycloneDX SBOM for each production deployment.

Store it against:

```text
Project
Environment
Deployment
Commit SHA
Timestamp
```

Example:

```text
MediaVerse
Deployment #91
Commit 3273f3d

623 components
```

SBOMs should be downloadable from the deployment/security UI.

---

# 25. Security Dashboard

Global security view:

```text
Project        Critical   High   Medium   Low

MediaVerse        0        2       5      13
CollegeCal        0        0       1       7
JourneyAlert      1        3       8       4
Aayvu             0        1       2      16
```

Project-level security view should show:

```text
Finding
Severity
Source scanner
Package/file
CVE/rule
Fixed version
First seen
Last seen
Status
Affected deployment
```

---

# 26. Health Checks

Health monitoring should support multiple checks per project.

Example:

```text
MediaVerse

Website          Healthy
API              Healthy
Database         Healthy
Authentication   Healthy
Poster API       Healthy
```

Project status should be derived from its checks.

---

# 27. Health Check Levels

## Level 1 — Availability

Checks:

```text
DNS
TLS
HTTP status
Latency
```

## Level 2 — Application Health

Example:

```http
GET /api/health
```

Response:

```json
{
  "status": "healthy",
  "database": true,
  "version": "3273f3d"
}
```

## Level 3 — Dependency Health

Examples:

```text
PostgreSQL
MongoDB
Redis
S3
Email provider
AI provider
Authentication service
```

---

# 28. Health History

Track:

```text
24h uptime
7d uptime
30d uptime

Latency history

Incident history
Downtime duration
Check failures
Recovery time
```

Example incident:

```text
Sep 08

00:12 -> 00:19

Downtime:
7 minutes
```

---

# 29. Deployment Verification

After deployment:

```text
Deploy completed
    |
Run health checks
    |
    +--> Website
    +--> API
    +--> Database
    +--> Authentication
```

Only mark a deployment **Healthy** after required checks pass.

If verification fails:

```text
Deployment completed
Production unhealthy
```

Actions:

```text
View failing check
Retry verification
Rollback
Ignore
```

---

# 30. Correlate Health With Deployments

The system should detect and display relationships such as:

```text
MediaVerse became unhealthy
47 seconds after deployment fa41921
```

This correlation is a core reason health belongs inside the CI/CD system.

---

# 31. Public Status Page

`health.siv19.dev` can remain as a sanitized status page.

Each Project should have:

```text
Show on public status page: yes/no

Public name
Public description

Expose:
- Status
- Incident history
- Uptime
```

Do not expose publicly by default:

```text
Commit SHA
Deployment provider
Internal endpoints
Security findings
Infrastructure details
Logs
Secrets
```

---

# 32. Infrastructure Section

Infrastructure should be separate from software Projects.

Example:

```text
Infrastructure

Hosts
- OMV Server
- ASUS ROG
- Other future nodes

Services
- Jellyfin
- Vaultwarden
- Immich
- PostgreSQL
- Redis
```

Infrastructure services should support:

```text
Status
Restart
Stop
Logs
Health
Metrics
```

They should not appear in the Project list unless explicitly modeled as projects.

---

# 33. Self-Hosted Agent

Use a lightweight agent on self-hosted machines.

Suggested implementation language:

```text
Go
```

Reasoning:

```text
Small static binary
Low memory usage
Good Docker/system APIs
Easy deployment
Good concurrency
```

Agent responsibilities:

```text
Docker status
Docker logs
Pull image
docker compose up/down
Restart service
Stop service
Machine statistics
Disk usage
Execute approved deployment jobs
Run health probes
```

Do not expose raw SSH access directly through the web UI.

---

# 34. Agent Security

Each agent should have its own identity.

Example:

```text
Host:
omv-main

Capabilities:
Docker
Health
Deploy
Metrics

No unrestricted shell by default
```

Use signed/authenticated communication.

Possible model:

```text
Agent ID
Agent certificate/token
Allowed capabilities
Last seen
Version
Host metadata
```

The backend should only dispatch approved task types.

---

# 35. Logs

V1 log sources:

```text
GitHub Actions build logs
Deployment logs
Security scanner logs
Health-check logs
Docker/container logs
```

Do not attempt to build a full Datadog/Loki replacement in V1.

Container log retention should be configurable.

Suggested default:

```text
24 hours or 7 days
```

---

# 36. Secrets

Provide a minimal encrypted secrets store.

Each secret:

```text
Project
Environment
Name
Encrypted value
Created at
Updated at
```

Example UI:

```text
Production Secrets

DATABASE_URL     ********
JWT_SECRET       ********
OPENAI_KEY       ********
```

Allowed actions:

```text
Create
Replace
Delete
```

Do not allow revealing existing secret values in the UI.

Use a server-side master encryption key.

---

# 37. Activity Feed

All important events should generate activity records.

Examples:

```text
10:41 MediaVerse deployed
10:40 MediaVerse security scan passed
10:38 GitHub commit received
10:13 Jellyfin restarted
09:57 Aayvu vulnerability detected
08:22 CollegeCal deployment failed
```

This also acts as a lightweight audit log.

---

# 38. Notifications

V1 notification channels:

```text
Email
Telegram
```

Notify on:

```text
Production down
Deployment failed
Rollback triggered
Critical vulnerability
Secret detected
Host offline
```

Optional:

```text
Successful deployment
```

Successful deployment alerts should be disabled by default to avoid noise.

---

# 39. Authentication

Use GitHub authentication.

Preferred model:

```text
GitHub OAuth for login
GitHub App for repository/org integration
```

Initial roles:

```text
Owner
Admin
Developer
Viewer
```

Do not implement complex enterprise RBAC in V1.

---

# 40. Main Navigation

Suggested application sidebar:

```text
Overview

Projects
Deployments
Security
Health
Infrastructure

Activity

Settings
```

---

# 41. Project Navigation

Inside a Project:

```text
Overview
Builds
Deployments
Security
Health
Logs
Settings
```

---

# 42. Global Dashboard

Suggested dashboard:

```text
CI/CD

28 Managed Projects

Healthy               26
Degraded               1
Down                   1

Failed Builds          2

Critical Security      0
High Security          8
```

Then:

```text
Needs Attention

CollegeCal
Latest deployment failed

JourneyAlert
Production down 17m

Aayvu
2 high vulnerabilities
```

And:

```text
Recent Deployments

MediaVerse      Healthy     12m
SplitLLM API    Healthy     48m
Aayvu Web       Healthy     1h
JourneyAlert    Failed      2h
```

---

# 43. Project Overview UI

Example:

```text
MediaVerse                             Healthy

Production
https://media-verse.in

fa41921
Fix watch-link caching

Deployed 12 minutes ago

[ Deploy ] [ Rollback ] [ Restart ]

---------------------------------------

Deployment

Build           Passed
Security        Passed
Deploy          Passed
Verification    Passed

---------------------------------------

Health

Website         Healthy      121 ms
API             Healthy       89 ms
Mongo           Healthy
Authentication  Healthy

---------------------------------------

Security

Critical        0
High            2
Medium          8

---------------------------------------

Recent Activity

12m   Production deployment
14m   Security scan passed
19m   Commit fa41921
```

---

# 44. Infrastructure UI

Example:

```text
Infrastructure

Hosts

OMV Server                 Online
CPU                        12%
RAM                        3.2 / 16 GB
Disk                       1.3 / 256 GB

ASUS ROG                   Offline

Services

Jellyfin                   Healthy
Vaultwarden                Healthy
Immich                     Healthy
PostgreSQL                 Healthy
Redis                      Healthy
```

---

# 45. Recommended Technology Stack

## Frontend

```text
React
TypeScript
Vite
shadcn/ui
Tailwind CSS
TanStack Query
Recharts
xterm.js
```

## Backend

```text
FastAPI
SQLAlchemy
PostgreSQL
Redis
Dramatiq
WebSockets
```

## Self-hosted Agent

```text
Go
```

---

# 46. Suggested Database Tables

```text
users

github_installations
github_organizations
repositories

projects
project_repositories

environments

builds
build_jobs

deployments
deployment_steps
deployment_artifacts

security_scans
security_findings
sboms

health_checks
health_results
incidents

hosts
agents
services

secrets

notification_rules
notifications

activity_events
```

---

# 47. High-Level Backend Architecture

```text
                     GitHub
                        |
                     Webhooks
                        |
                        v
+--------------------------------------------------+
|              cicd.siv19.dev API                  |
|                                                  |
| Projects                                         |
| Deployments                                      |
| Builds                                           |
| Security                                         |
| Health                                           |
| Infrastructure                                   |
| Authentication                                   |
+-------------------------+------------------------+
                          |
                     PostgreSQL
                          |
                        Redis
                          |
                  Background Workers
                    /      |       \
                   /       |        \
                  v        v         v
              Vercel    GitHub     Agents
                                   |
                                   v
                              OMV / ROG
```

---

# 48. V1 Implementation Milestones

## Milestone A — Foundation

Build:

```text
GitHub login
GitHub App integration
Organization discovery
Repository discovery
Managed / Ignored / Unreviewed states
Projects
Environments
Database
Basic dashboard shell
```

Acceptance criteria:

- User can login with GitHub.
- Personal and organization repositories are discovered.
- User can mark repos Managed or Ignored.
- Newly discovered repositories appear as Unreviewed.
- Projects can be created from managed repos.
- Ignored repos remain recoverable.

---

## Milestone B — Build & Deploy

Build:

```text
GitHub Actions integration
Workflow/build history
Build logs
Vercel integration
Docker Compose provider
Self-hosted agent
Deploy
Redeploy
Rollback
Restart
Deployment history
```

Acceptance criteria:

- User can see latest builds.
- User can inspect workflow/job logs.
- User can trigger supported deployments.
- User can redeploy.
- User can rollback to a previous deployment.
- Rollbacks create new deployment records.
- Docker services can be restarted through the agent.
- No direct unrestricted SSH is exposed.

---

## Milestone C — Health

Build:

```text
HTTP checks
API checks
Latency tracking
Uptime tracking
Incident tracking
Health history
Deployment verification
Deployment-health correlation
Public status backend
```

Acceptance criteria:

- Multiple checks can be attached to a Project.
- Health status is stored historically.
- Deployments enter verification after deployment.
- Deployments are only marked Healthy when required checks pass.
- Health failures can be correlated to recent deployments.
- `health.siv19.dev` can consume sanitized status data from the same backend.

---

## Milestone D — DevSecOps

Build:

```text
Semgrep
Trivy
Gitleaks
OSV-Scanner
Syft
Normalized findings
Security dashboard
Security gates
Nightly scans
SBOM storage
```

Acceptance criteria:

- Security scans can run on PR, main, and scheduled triggers.
- Findings from different scanners use a common schema.
- Critical issues can block deployment.
- Security policy can be overridden per Project/Environment.
- SBOM exists for each production deployment.

---

## Milestone E — Polish

Build:

```text
Email notifications
Telegram notifications
Activity feed
Host metrics
Log UI
Onboarding wizard
Role permissions
Charts
Filters
Search
```

Acceptance criteria:

- Important operational events create activity records.
- Notification rules are configurable.
- Hosts expose CPU/RAM/disk status.
- Project and global dashboards are useful without external tools.
- Basic roles are enforced.

---

# 49. V1 Explicit Non-Goals

Do NOT build these in V1:

```text
Kubernetes management
Custom Git hosting
Custom Docker registry
npm/Maven package registry
Artifact repository replacement
Custom CI YAML/DSL
Full Prometheus replacement
Full Datadog/Loki replacement
Distributed tracing
AI assistant
Multi-region runners
Billing
Enterprise SSO
Complex RBAC
Full HashiCorp Vault replacement
```

If needed, integrate existing tools later rather than rebuilding them.

---

# 50. Phase 2 Ideas

Only after V1 data quality and workflows are reliable.

Possible features:

```text
AI: Explain deployment failure
AI: Explain vulnerability
AI: Suggest fix
AI: Compare failed deployment to last healthy deployment
AI: Summarize logs
AI: Generate patch suggestions

Dependency-Track integration
Checkov
Grype
CodeQL
SonarQube
Prometheus
Grafana
Loki
OpenTelemetry
Cloud provider adapters
Kubernetes adapter
Advanced approvals
Manual deployment gates
Canary deployments
Blue/green deployments
```

---

# 51. AI Design Principle

Do not add AI merely as a chatbot.

When AI is eventually added, provide structured context such as:

```text
Commit diff
Previous healthy deployment
Build logs
Security findings
Runtime logs
Health-check results
Deployment metadata
```

Example capability:

```text
Why did this deployment fail?
```

The answer should be derived from actual project evidence.

---

# 52. Product Boundary

The goal is NOT:

```text
"Build my own Jenkins"
```

The goal IS:

```text
"Build my own engineering control plane"
```

The final product should unify:

```text
GitHub
Builds
Deployments
Security
Health
Infrastructure
Logs
Notifications
```

into one coherent private platform.

---

# 53. Final V1 Scope Summary

V1 should include:

1. GitHub login
2. GitHub App integration
3. Personal + organization repo discovery
4. Managed / Ignored / Unreviewed repository states
5. Project registry
6. Environment support
7. Stack auto-detection
8. GitHub Actions build integration
9. Build logs
10. Deployment provider abstraction
11. Vercel deployment support
12. Docker Compose deployment support
13. Self-hosted Go agent
14. Deploy
15. Redeploy
16. Restart
17. Stop where supported
18. Rollback
19. Deployment history
20. Health checks
21. Health history
22. Deployment verification
23. Deployment-health correlation
24. Public health/status backend
25. Semgrep
26. Trivy
27. Gitleaks
28. OSV-Scanner
29. Syft
30. Normalized security findings
31. Security gates
32. Nightly security scans
33. SBOM storage
34. Infrastructure hosts
35. Infrastructure services
36. Basic host metrics
37. Unified activity feed
38. Email alerts
39. Telegram alerts
40. Minimal encrypted secrets store
41. Owner/Admin/Developer/Viewer roles
42. Global dashboard
43. Project dashboard
44. Logs view
45. Search/filtering

---

# 54. Codex Implementation Guidance

When implementing:

- Prefer modular provider interfaces over provider-specific business logic.
- Keep GitHub, Vercel, Docker, scanners, health checks, and notifications behind adapters.
- Avoid hardcoding personal repository names.
- Support GitHub organizations from the beginning.
- Preserve auditability for deployments and rollbacks.
- Do not store plaintext secrets.
- Do not expose unrestricted shell access from the web UI.
- Keep health monitoring and public status rendering on one backend.
- Keep infrastructure services separate from software Projects.
- Treat a Project as the primary product entity.
- Treat repository discovery and project onboarding as separate steps.
- Default newly discovered repositories to Unreviewed.
- Make Ignored repositories reversible.
- Keep V1 focused. Do not add Phase 2 features unless the V1 foundations require them.
