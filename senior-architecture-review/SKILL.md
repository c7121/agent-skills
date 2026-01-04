---
name: senior-architecture-review
description: >-
  Senior-level architecture review (system/program scope). Evaluates architecture, boundaries, non-functional requirements, security posture, operability, delivery risk, and readiness gates. Includes a scoped documentation coherence check for architecture/security standards and maps major findings to OWASP ASVS (architecture/control areas) and NIST guidance (SSDF; optionally 800-53 family language). Report-only: proposes doc diffs inline without modifying repo files.
metadata:
  short-description: Senior architecture review (report-only)
  outputs:
    - REVIEW_ARCHITECTURE.md
  constraints:
    - report-only (no file edits)
    - propose changes as diffs inside the report
---

# Senior Architecture Review (Standards-Aware)

Use this skill to perform a **senior architecture review** across a system or major initiative, focusing on:
- system boundaries and responsibilities,
- security posture (at the right altitude),
- reliability/resilience/SLO readiness,
- operability (observability, runbooks, deploy/rollback, DR),
- delivery and migration risk,
- explicit readiness gates and a risk register.

This is broader than a per-change AppSec design review (`design-review-security-lens`) and is best used for multi-service or high-blast-radius initiatives.

If the primary goal is to **simplify** the architecture (fewer moving parts, fewer surfaces, clearer responsibilities) while preserving requirements, use `architecture-simplification`.


## When to use

Use when:
- the change spans multiple services/teams,
- you need confidence the system will work in production (security + reliability + operability),
- you need an explicit “what blocks implementation / launch” list.

Do **not** use when:
- you only need to review one change proposal (use `design-review-security-lens`),
- you want a detailed threat enumeration session (use `threat-modeling-qa`),
- you’re gating a specific release with evidence (use `security-readiness-review`).

## Defaults

- **Scope (default):** architecture docs, ADRs, service docs, contracts; optionally the whole `docs/` tree
- **Output (default):** `REVIEW_ARCHITECTURE.md` at repo root
- **Report-only hard rule:** write **only** `REVIEW_ARCHITECTURE.md`. Do not change any other files.

## Report-only rule (required)

If you believe repo files should be changed:
- do **not** apply changes,
- propose changes as **unified diffs** inside `REVIEW_ARCHITECTURE.md`,
- keep diffs minimal and focused on enabling/clarifying the architecture review (not expanding product scope).

## Preflight (required)

1) Read and follow all applicable `AGENTS.md` instructions (treat as normative).
2) Identify the system boundary being reviewed (component list and what’s in/out).
3) Identify in-repo standards/policies relevant to architecture (security, reliability, data retention, logging/PII).
4) Ask before running shell commands unless the user explicitly pre-authorizes specific commands.

## Framework vocabulary (useful, not mandatory)

- **OWASP ASVS:** use to anchor app/security architecture topics (especially ASVS V1 “Architecture, Design and Threat Modeling” and cross-cutting areas like V4/V7/V10).
- **NIST SSDF:** use to anchor SDLC/process expectations at program scale (governance, verification, vulnerability response).
- **NIST SP 800-53 (optional):** when stakeholders want control-family language (e.g., AC access control, AU audit, SC system communications, SI system integrity).

Do not turn this into a compliance artifact; use framework tags to make gaps legible and to reduce reviewer variance.

## Decision hygiene

- Prefer repo-local evidence (ADRs, contracts, standards) over external opinion.
- Do not invent missing SLO numbers, endpoints, or semantics.
- If a decision is missing, present options and label defaults as **PROPOSED** (or **NEEDS DECISION**).

## Review coverage (minimum)

Cover these areas and explicitly mark N/A where not applicable:

### A) Context and constraints
- goals / non-goals / assumptions
- stakeholders and dependencies
- data sensitivity / classification constraints

### B) Architecture and boundaries (ASVS V1)
- component responsibilities and dependency direction rules
- trust boundaries and data flows
- tenancy boundaries (if any)

### C) Contracts and public surface
- APIs/events/config/schemas and versioning/compatibility
- idempotency, retries/timeouts, error model

### D) Security posture (architecture level)
- authentication and authorization model (ASVS V2/V4)
- secrets/key management approach (high level) (ASVS V6)
- audit logging expectations (ASVS V7)
- top threats/abuse themes (do not replace a full threat model)
- security “non-negotiables” and invariants

### E) Reliability, resilience, and scale
- failure modes, dependency outages, overload behavior
- backpressure and rate limiting expectations (ASVS V10)
- capacity/performance assumptions and cost drivers
- DR/backup/restore, RPO/RTO where applicable

### F) Operability (NIST SSDF emphasis)
- observability: logs/metrics/traces, dashboards, alerts
- runbooks, on-call ownership, incident hooks
- deployment, rollback, configuration management
- vulnerability/patch response posture for critical components

### G) Delivery plan
- migration and rollout strategy (phases, flags, compatibility)
- test strategy (unit/integration/contract/e2e/load)
- key risks and sequencing

### H) Scoped documentation coherence (folded in)
- identify the “source of truth” docs for architecture/security standards relevant to this initiative,
- flag contradictions that would affect implementation or operations,
- recommend a canonical stance and propose minimal diffs (not applied).

## Workflow

### 1) Inventory and map the architecture
- List canonical docs and ADRs relevant to the system.
- Produce a component map and boundary description grounded in docs.
- If diagrams are missing:
  - propose a minimal Mermaid diagram as a diff (not applied), or
  - list “unknowns required for review.”

### 2) Evaluate against quality attributes
For each area above:
- state what the docs claim,
- cite evidence (paths/lines),
- identify gaps, contradictions, and risky assumptions.

### 3) Produce risks and readiness gates
- Create a risk register with likelihood/impact and mitigations.
- Define readiness gates:
  - must-fix-before-implementation,
  - must-fix-before-launch,
  - post-launch hardening.

### 4) Propose minimal doc diffs (not applied)
Only propose edits to:
- clarify missing decisions,
- align contradictory architectural guidance,
- add missing “must have” sections (trust boundaries, error model, rollout plan, ownership).

## Severity guide (architecture)

- **P0:** credible security/data-loss/cross-tenant risk, undefined contract semantics, no rollback/migration path, missing trust boundary definition, or missing operational ownership that blocks safe launch.
- **P1:** significant reliability/operability/scaling gaps likely to cause incidents or major rework.
- **P2:** clarity, completeness, and defense-in-depth improvements.

## Report template: `REVIEW_ARCHITECTURE.md`

```md
# Senior Architecture Review

- Model: <model>
- Date: <YYYY-MM-DD>
- Scope: <system/components>
- Artifacts reviewed: <paths>

## Baseline & framework mapping (high level)
- Risk tier (if known):
- Framework tags used in this report: <ASVS areas, SSDF themes, optional 800-53 families>
- Relevant internal standards: <paths>

## Executive summary
- Outcome: Support / Support with changes / Request changes
- Top 3 risks:
- P0 count / P1 count:

## Architecture overview (as documented)
### Components and responsibilities
### Boundaries and trust boundaries
### Key data flows
### Missing or unclear areas

## Findings (tagged)
### P0
1. <title>
   - Evidence: <file:Lx-Ly>
   - Why it matters:
   - Recommendation:
   - Validation:
   - Framework tags: <ASVS V1/V4/V7/V10; SSDF theme; optional AC/AU/SC/SI>

### P1
...

### P2
...

## Scoped doc coherence issues
1. <contradiction>
   - Evidence: <file:Lx-Ly> vs <file:Lx-Ly>
   - Canonical stance:
   - Proposed minimal diff (NOT APPLIED):

## Risk register
| Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|

## Readiness gates
### Must fix before implementation
- [ ] ...
### Must fix before launch
- [ ] ...
### Post-launch hardening
- [ ] ...

## Recommended follow-up ADRs/specs
- <path> — <purpose>

## Proposed diffs (NOT APPLIED)
```diff
--- a/docs/...
+++ b/docs/...
@@ ...
- old
+ new
```
```

## One-shot prompt (optional)

If the user asks for a one-shot instruction, provide a prompt that:
- scopes the architecture review boundary,
- requires evidence-cited findings and risks,
- tags key findings to ASVS/SSDF (and optional 800-53 families),
- outputs `REVIEW_ARCHITECTURE.md` only,
- includes proposed diffs (not applied),
- stops after writing the report.
