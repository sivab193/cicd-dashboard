# CI/CD Dashboard

A personal, Jenkins-style dashboard for GitHub Actions: an overview grid of every
repo on your GitHub account with its latest build status, drilling down into a
repo's run history, and a live per-job/per-step view of any run — all read
directly from the GitHub REST API via the signed-in user's own OAuth token.
No database, no webhooks — the UI polls GitHub on an interval.

## Architecture

- **Next.js 16 (App Router) + TypeScript**, deployed on Vercel.
- **Auth.js (NextAuth v5)** — GitHub OAuth login gated to a single allowed
  username (`lib/auth.ts`). The access token is stored in the session JWT and
  used server-side only; it's never sent to the browser.
- **Octokit**, used from Route Handlers (`app/api/**`) to call the GitHub API
  as the signed-in user (`lib/github.ts`).
- **SWR** on the client for polling: the dashboard refreshes every ~20s, a
  repo's run history every ~10s, and an open run's job/step view every ~4s
  while it's still in progress (stops once it completes).

Pages:

| Route | What it shows |
|---|---|
| `/` | Grid of all repos with their latest run status |
| `/repo/[owner]/[repo]` | Recent workflow run history for one repo |
| `/repo/[owner]/[repo]/run/[runId]` | Live jobs/steps for one run |

## Local setup

1. Install dependencies:
   ```bash
   npm install
   ```
2. Create a GitHub OAuth App at
   [github.com/settings/developers](https://github.com/settings/developers)
   with callback URL `http://localhost:3000/api/auth/callback/github`.
3. Copy `.env.example` to `.env.local` and fill in:
   - `AUTH_GITHUB_ID` / `AUTH_GITHUB_SECRET` from the OAuth App you just created
   - `AUTH_SECRET` — generate with `npx auth secret`
   - `AUTH_URL=http://localhost:3000`
   - `ALLOWED_GITHUB_LOGIN` — your GitHub username (only this account can sign in)
4. Run the dev server:
   ```bash
   npm run dev
   ```
5. Open [http://localhost:3000](http://localhost:3000) and sign in with GitHub.

## Deploying to cicd.siv19.dev (Vercel + Cloudflare)

1. Push this repo to GitHub and import it into [Vercel](https://vercel.com/new).
2. In the Vercel project → **Settings → Environment Variables**, add the same
   variables as `.env.example`, but with:
   - `AUTH_URL=https://cicd.siv19.dev`
   - Callback URL on the GitHub OAuth App (or create a second, separate OAuth
     App for production) set to
     `https://cicd.siv19.dev/api/auth/callback/github`
3. In the Vercel project → **Settings → Domains**, add `cicd.siv19.dev`.
   Vercel will give you a CNAME target (or A/ALIAS record).
4. In Cloudflare DNS for `siv19.dev`, add that record for the `cicd` subdomain.
   Set it to **DNS only** (grey cloud, not proxied) at least until Vercel
   shows the domain as verified/issued — Cloudflare's proxy can interfere with
   Vercel's TLS cert issuance and its own edge routing. You can switch it to
   proxied afterward if you want Cloudflare's CDN/WAF in front, but that's
   optional.
5. Redeploy. Visit `https://cicd.siv19.dev` and sign in.

## GitHub API rate limits

An OAuth user token has a 5,000 requests/hour limit. The dashboard fetches one
request per repo (for its latest run) on every dashboard poll, plus one
request for the repo list itself. If your account has a very large number of
repos and the default ~20s dashboard interval starts feeling rate-limit-tight,
increase `refreshInterval` in `app/page.tsx`.

## Known limitations / not built (yet)

- **View-only** — no re-run/cancel controls.
- **No persistence** — everything is read live from GitHub; there's no build
  history retained beyond what the GitHub API itself returns, and no trend
  charts. This was intentionally deferred; revisit if you want history beyond
  GitHub's own retention.
- **No step console logs** — the run view shows step-level status and timing
  (from the Jobs API), not the raw log text for each step.
