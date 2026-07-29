# Operations

Account inventory, domain/DNS, and hosting facts for the live project. Reference only — not a build doc. Passwords are never stored here.

**Pending real values.** Fill in once the GitHub account and repo exist — see `GETTING-STARTED.md` → Step 6.

## Domain & hosting

- Public URL: `https://{{GITHUB_ACCOUNT}}.github.io/{{REPO}}/` (GitHub Pages default subdomain — no custom domain/DNS needed)
- Hosting: GitHub Pages, deployed via `.github/workflows/deploy.yml` (GitHub Actions) — see `technical.md` → *Repo & deployment*
- One-time setup after the repo exists: Settings → Pages → *Source* = "GitHub Actions"

## Accounts

- **Project GitHub account**: — fill in once created.

## Repository

- `{{GITHUB_ACCOUNT}}/{{REPO}}` — single repo, holds source and `site/` output together (see `technical.md` → *Repo & deployment*). Can be private or public; either works with GitHub Actions Pages deployment.

### Push access

Pushing requires this machine to have git authenticated as the right account. No token or password is recorded here — only the requirement and how to check it, per `way-of-working.md` → *Local & session state*:
- Check: `gh auth status`
- Switch/add account: `gh auth login`
- Git on macOS typically caches HTTPS credentials via the `osxkeychain` credential helper (`git config credential.helper`), keyed by host (`github.com`) — not by account. Authenticating as a different GitHub account on the same machine replaces the cached credential for anyone using that helper.
