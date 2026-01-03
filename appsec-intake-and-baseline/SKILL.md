---
name: appsec-intake-and-baseline
description: AppSec intake that tiers an application/change by risk, selects an explicit control baseline (OWASP ASVS / OWASP API Security Top 10 / OWASP MASVS) and supporting NIST guidance (SSDF), and defines the minimum evidence bar for later reviews. Also performs a scoped “doc coherence” check for the standards it relies on. Report-only.
metadata:
  short-description: AppSec intake + baseline selection (report-only)
  outputs:
    - REVIEW_SCOPE_BASELINE.md
  constraints:
    - report-only (no file edits)
---

# AppSec Intake & Baseline Selection

Use this skill **first** when you want application reviews to be repeatable and anchored to recognized standards.
It produces a single artifact that answers:

- What are we reviewing (scope)?
- How risky is it (tier)?
- What “good” looks like (baseline)?
- What evidence is minimally required before launch (evidence bar)?
- What internal guidance is the source of truth (scoped doc coherence)?

This skill sets up the rest of the review flow:
- `design-review-security-lens` (design correctness against baseline)
- `threat-modeling-qa` (threats/abuse cases + mitigations)
- `implementation-security-review` (code/config/IaC verification)
- `security-readiness-review` (go-live gate based on evidence)
- `senior-architecture-review` (large initiative / multi-service review)

## When to use

Use when:
- a new service/app is being created,
- a change introduces new public surface, sensitive data, or tenant boundaries,
- you want a consistent baseline and a defensible evidence bar.

Skip when:
- you already have a current `REVIEW_SCOPE_BASELINE.md` for the exact release/system and risk hasn’t changed.

## Defaults

- **Output (default):** `REVIEW_SCOPE_BASELINE.md` at repo root (or alongside the main RFC if repo convention says so).
- **Scope (default):** one deployable unit (service/app) or one major feature; explicitly list what’s in/out.
- **Report-only hard rule:** write **only** `REVIEW_SCOPE_BASELINE.md`. Do not change any other files.

## Preflight (required)

1) Read and follow all applicable `AGENTS.md` instructions (treat as normative).
2) Find repo/org security guidance (data classification, logging/PII rules, authn/authz conventions, secure SDLC expectations).
3) Ask before running shell commands unless the user explicitly pre-authorizes specific commands.

## Inputs to request (ask in one batch)

If not already present in docs, ask for:

### Exposure & runtime
- Internet-facing, partner-facing, internal-only, or admin-only?
- Entry points: web UI, public API, webhooks, batch jobs, mobile, CLI.
- Hosting: cloud provider / k8s / serverless / on-prem.
- Any network egress to the internet or to customer-controlled destinations?

### Identity & privilege
- AuthN method (SSO, OIDC, sessions, mTLS/service identity).
- AuthZ model (RBAC/ABAC), including tenant model (single vs multi-tenant).
- Admin/break-glass functions?

### Data & compliance
- Data types: PII, credentials/secrets, financial, regulated (HIPAA/PCI), telemetry-only, none.
- Storage locations (DB/object store/cache/logs).
- Retention/deletion requirements.

### Change scope
- New dependencies (vendors/SaaS), new packages, new infra modules.
- Migration/rollout plan (flags, canary, backfill).

### Existing assurance (if any)
- Prior threat model/design review links
- Prior pen test / security test coverage
- CI security scans (SAST/SCA/secrets/image/IaC)

## Risk tiering rubric (required)

Assign a tier using the best available info; if unknown, choose the more conservative tier and list unknowns.

### Dimensions
- **Exposure:** Public internet > partner > internal > admin-only
- **Data sensitivity:** Regulated/secrets/financial > PII > internal > none
- **Privilege:** Admin/critical actions > standard user actions
- **Tenancy:** Multi-tenant > single-tenant
- **Blast radius:** Shared infra / cross-customer > isolated

### Suggested tiers
- **Tier 0 (Low):** internal-only, no sensitive data, low privilege, single-tenant.
- **Tier 1 (Moderate):** internal or limited partner exposure and/or handles PII; standard privilege.
- **Tier 2 (High):** internet-facing OR multi-tenant OR privileged actions OR sensitive data (PII at scale).
- **Tier 3 (Critical):** regulated (PCI/HIPAA), credentials/secrets, money movement, high-value admin, cross-tenant risk, or very large blast radius.

## Baseline selection (required)

Pick the baseline(s) that match the product shape.

### OWASP baselines
- **Web apps & services:** OWASP **ASVS** (Application Security Verification Standard)
  - Default: **ASVS Level 2** for Tier 2+ and anything internet-facing or handling PII.
  - Use **ASVS Level 1** for Tier 0/1 internal tools with low sensitivity.
  - Use **ASVS Level 3** for Tier 3/critical systems.
- **APIs:** OWASP **API Security Top 10** (in addition to ASVS)
- **Mobile apps:** OWASP **MASVS** (plus relevant ASVS items for backend APIs)

### NIST guidance (supporting, not a checklist-by-itself)
- **NIST SSDF (Secure Software Development Framework):** use as the SDLC “process lens” to ensure the program has:
  - preparation/governance (roles, policies),
  - secure development (requirements, design, implementation),
  - verification (testing/scanning),
  - vulnerability response.
- Optionally reference **NIST SP 800-53** control families for enterprise environments (e.g., AC, AU, SC, SI) when stakeholders need control-family language.

## Evidence bar selection (required)

Define the *minimum evidence* expected at `security-readiness-review` time, based on tier and baseline.

This is not “run every tool.” It’s: “what proof do we need that baseline controls are implemented and working?”

### Minimum evidence (suggested)
- **All tiers (baseline hygiene):**
  - Dependency/SCA scan results and vuln triage
  - Secrets scanning (repo + CI)
  - Logging/PII review evidence (policy alignment)
- **Tier 1+:**
  - SAST results (or equivalent)
  - AuthZ tests for critical endpoints (unit/contract/integration)
  - Abuse controls evidence if any external surface exists (rate limits, quotas)
- **Tier 2+:**
  - Container/image scan (if containerized)
  - IaC scan (if IaC changes)
  - Audit logging validation for sensitive actions
  - Threat model for externally reachable or trust-boundary-crossing changes
- **Tier 3:**
  - Independent security testing (targeted review or pen test) OR documented compensating controls
  - Stronger supply-chain evidence where feasible (e.g., signed artifacts/provenance)
  - Explicit risk acceptance workflow for any deviation

## Scoped doc coherence (folded in) (required)

Instead of a repo-wide coherence sweep, do a **scoped** coherence check:
- Identify “source of truth” docs for: authn/authz, logging/PII, data classification, crypto, secure SDLC, incident response.
- For those topics, detect contradictions that would affect this review’s baseline or evidence bar.
- Record contradictions as **P0/P1/P2** only if they plausibly cause implementation mistakes for this system.

Do not propose broad doc refactors; keep it scoped to what matters for this app/release.

## Deliverable: `REVIEW_SCOPE_BASELINE.md`

```md
# AppSec Review Scope & Baseline

- Model: <model>
- Date: <YYYY-MM-DD>
- System / Change: <name>
- Owner: <team>
- Primary artifact(s): <RFC/design path or link>

## 1) Scope
### In scope
- ...
### Out of scope
- ...

## 2) Context summary
- Exposure: <public/partner/internal/admin-only>
- Entry points: <UI/API/webhook/job/mobile/...>
- Tenancy: <single/multi> and isolation approach:
- AuthN/AuthZ: <summary>
- Data types: <PII/secrets/regulated/...>
- Key dependencies: <internal/external>

## 3) Risk tier
- Tier: 0 / 1 / 2 / 3
- Rationale:
- Unknowns (assumed conservatively):
  - ...

## 4) Selected baselines (explicit)
- OWASP ASVS: Level <1/2/3> (rationale)
- OWASP API Security Top 10: <Yes/No> (if API)
- OWASP MASVS: <Yes/No> (if mobile)
- NIST SSDF: applicable practices to emphasize (high-level)

## 5) Minimum evidence bar (for readiness gate)
### Required artifacts (must have)
- [ ] ...
### Recommended artifacts (should have)
- [ ] ...
### Acceptable substitutes / compensating controls
- ...

## 6) Review plan (which skills to run)
- [ ] design-review-security-lens
- [ ] threat-modeling-qa (required? Y/N)
- [ ] implementation-security-review (required? Y/N)
- [ ] security-readiness-review (required? Y/N)
- [ ] senior-architecture-review (optional escalation)

## 7) Sources of truth (scoped)
- AuthN/AuthZ: <path#section>
- Data classification/PII: <path#section>
- Logging/Audit: <path#section>
- Crypto/Key mgmt: <path#section>
- Secure SDLC / scanning: <path#section>

## 8) Coherence issues that affect this review (scoped)
### P0 / P1 / P2
1. <contradiction>
   - Evidence: <file:Lx-Ly> vs <file:Lx-Ly>
   - Impact on this review:
   - Proposed resolution (doc pointer or minimal diff suggestion):

## 9) Open questions / decisions needed
- ...
```

## One-shot prompt (optional)

If the user asks for a one-shot instruction, provide a prompt that:
- collects intake info in one batch,
- assigns a risk tier,
- selects explicit OWASP baseline(s) + NIST SSDF emphasis,
- defines the minimum evidence bar,
- outputs `REVIEW_SCOPE_BASELINE.md` only.
