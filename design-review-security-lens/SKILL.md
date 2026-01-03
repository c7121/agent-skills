---
name: design-review-security-lens
description: Security-engineer technical design review for a specific proposal/change, explicitly anchored to an OWASP baseline (ASVS/API Top 10/MASVS as applicable) and supported by NIST SSDF expectations. Validates trust boundaries, authz model, data handling, abuse resistance, and security-relevant reliability. Produces a decision-focused report with P0/P1/P2 findings and proposed doc diffs (not applied).
metadata:
  short-description: AppSec design review (report-only)
  outputs:
    - REVIEW_DESIGN.md
  constraints:
    - report-only (no file edits)
    - propose changes as diffs inside the report
---

# Design Review (Security Engineer Lens, Standards-Backed)

Use this skill to review a **specific technical design proposal** (RFC/design doc/ADR/spec) with an application security lens and an **explicit control baseline**.

This is intentionally **change-scoped** and **decision-focused**:
- Are the security-critical decisions explicit and sound?
- Does the design meet the selected baseline (e.g., OWASP ASVS L2)?
- What’s missing or ambiguous?
- What must change before implementation?

This is not a full architecture review (`senior-architecture-review`) and not a full threat modeling workshop (`threat-modeling-qa`).

## When to use

Use when:
- a feature introduces new endpoints, integrations, permissions, or data flows,
- multi-tenancy boundaries or authz rules are changing,
- a migration/rollout could cause data exposure or integrity loss.

Do **not** use when:
- you primarily need systematic threat enumeration (use `threat-modeling-qa`),
- you are gating a release based on evidence/scans/tests (use `security-readiness-review`).

## Defaults

- **Primary input (required):** a design artifact path (e.g., `docs/design/*.md`, RFC, ADR, spec).
  - If multiple candidates exist, list them and ask the user to choose.
- **Baseline (preferred):** use `REVIEW_SCOPE_BASELINE.md` produced by `appsec-intake-and-baseline`.
  - If absent, select a reasonable baseline and label it **PROPOSED** (see “Baseline selection” below).
- **Scope (default):** the design artifact + directly referenced contracts/schemas + repo security standards/policies.
- **Output (default):** `REVIEW_DESIGN.md` at repo root (or alongside the design doc if repo convention says so).
- **Report-only hard rule:** write **only** `REVIEW_DESIGN.md`. Do not change any other files.

## Report-only rule (required)

If the design doc (or related docs) should be updated:
- do **not** apply changes,
- propose changes as **unified diffs** inside `REVIEW_DESIGN.md`,
- keep diffs minimal and limited to clarifying/closing security gaps (not expanding scope).

## Preflight (required)

1) Read and follow all applicable `AGENTS.md` instructions (treat as normative).
2) Locate repo security guidance (data classification, logging/PII rules, authn/authz conventions, secure SDLC expectations).
3) Ask before running shell commands unless the user explicitly pre-authorizes specific commands.

## Baseline selection (required)

Prefer to read baseline from `REVIEW_SCOPE_BASELINE.md`. If missing, pick and label as **PROPOSED**:
- Web/service default: **OWASP ASVS Level 2** for internet-facing or PII; Level 1 for low-risk internal; Level 3 for critical/regulatory.
- APIs: add **OWASP API Security Top 10** coverage.
- Mobile: add **OWASP MASVS** coverage.
Also note relevant **NIST SSDF** emphasis (process expectations) for the change (e.g., verification, vulnerability response).

## Review principles (AppSec lens)

- Focus on concrete attacker goals, plausible paths, and specific mitigations.
- Prefer design-level mitigations over “we’ll validate later.”
- Make trust boundaries explicit; if unknown, call it out as a blocker.
- Avoid false certainty: do not invent endpoints/config/SLOs.

## Workflow

### 1) Confirm scope and deltas (required)
From the design artifact, extract:
- goals / non-goals
- what changes (components, data flows, dependencies)
- public surface changes (APIs/events/config/schemas)
- data touched and sensitivity classification (per repo policy)
- rollout/migration plan

If any of these are missing and they block evaluation, record as **P0 doc gap**.

### 2) Scoping “coherence” check (folded in) (required)
Do a scoped check only for topics relevant to this change:
- identify the source-of-truth doc(s) for auth/authz, logging/PII, crypto, secrets, and API standards,
- detect contradictions that would change the design requirements,
- record contradictions as findings (P0/P1/P2) **only** if they plausibly lead to insecure implementation.

### 3) Security-critical decisions checklist (required)
Cover these and explicitly mark N/A where not applicable. Tag each section with baseline mapping.

#### Identity & access (ASVS V2/V3/V4; API Top 10)
- authn mechanism and token/session model
- authz model (RBAC/ABAC), resource scoping, tenant isolation
- object-level authorization rules (especially multi-tenant)
- service-to-service identity and least privilege
- admin/break-glass paths and auditability

#### Data protection & privacy (ASVS V6/V7/V8/V9; MASVS; NIST SSDF PS)
- encryption in transit and at rest expectations
- secrets handling (where stored, rotation expectations)
- retention/deletion behavior (including backups) where applicable
- logging: avoid PII/secrets; audit logs for sensitive actions

#### Input handling & injection resistance (ASVS V5; OWASP Top 10)
- schema validation and canonicalization
- injection risks relevant to the design (SQL/NoSQL/template/command)
- SSRF/egress controls if fetching remote URLs
- file upload/download constraints and isolation

#### Abuse resistance / “reliability as security” (ASVS V10; NIST SSDF PW/RV)
- rate limiting and quota posture for exposed surfaces
- idempotency, replay handling, retries/timeouts
- failure modes: fail-closed vs fail-open, degraded modes
- DoS risks: expensive operations, unbounded fanout, queue growth

#### Observability & incident readiness (ASVS V7/V10; NIST SSDF RV)
- audit logging for sensitive actions (who/what/when/where)
- abuse/attack signals and alerting expectations
- runbook/rollback implications from the design

### 4) Threat modeling (lightweight) (required)
This skill performs **lightweight** threat review:
- list the top 5–8 abuse cases relevant to the change,
- map each to required controls/mitigations and verification.

If the design is high-risk or complex, recommend running `threat-modeling-qa` and treat missing threat model as:
- **P0** if the change is externally exposed or crosses trust/tenant boundaries,
- **P1** otherwise.

### 5) Contracts and invariants (required)
For any public surface:
- define authorization invariant(s) (“who can do what to which resource”)
- define compatibility/versioning expectations
- confirm error model avoids information leaks
- confirm schema constraints (sizes, required fields, enum exhaustiveness)

### 6) Findings, decision, and gates (required)
Classify findings:
- **P0 (Blocker):** exploitable authz/authn weakness, cross-tenant data risk, secret exposure risk, undefined security invariant, or missing trust boundary definition.
- **P1:** likely abuse/incident without mitigation; significant monitoring/audit gaps; unclear contracts that affect security.
- **P2:** defense-in-depth and clarity improvements.

State an explicit outcome:
- **Approve**
- **Approve with changes**
- **Request changes**

### 7) Proposed doc diffs (not applied)
Propose minimal diffs to:
- add missing security sections,
- clarify invariants and responsibilities,
- align with repo policy,
- link to threat model and readiness steps.

## Deliverable: `REVIEW_DESIGN.md`

```md
# Design Review (Security Lens)

- Model: <model>
- Date: <YYYY-MM-DD>
- Design artifact: <path>
- Related artifacts: <paths>
- Scope notes: <what was / wasn’t reviewed>

## Baseline & framework mapping
- Risk tier (from REVIEW_SCOPE_BASELINE.md, if available): <tier or unknown>
- Baseline(s):
  - OWASP ASVS: <L1/L2/L3 or PROPOSED>
  - OWASP API Security Top 10: <Y/N>
  - OWASP MASVS: <Y/N>
- NIST SSDF emphasis: <high-level bullets>
- Repo standards used: <paths>

## Summary
- Outcome: Approve / Approve with changes / Request changes
- P0 count / P1 count:
- Top risks (1–3 bullets):

## What this design changes
- Goals:
- Non-goals:
- Public surface changes:
- Data touched:
- Key dependencies:
- Rollout/migration approach:

## Security-critical decisions (as documented)
### Identity & access (ASVS V2/V3/V4; API)
### Data protection & privacy (ASVS V6/V7/V8/V9; MASVS)
### Input handling (ASVS V5; OWASP Top 10)
### Abuse resistance & resilience (ASVS V10)
### Observability & incident readiness (ASVS V7/V10)

## Threat highlights (lightweight)
1) <abuse case> → <controls> → <validation>
...

## Findings (tagged to frameworks)
### P0
1. <title>
   - Evidence: <doc section or file:Lx-Ly>
   - Why it matters:
   - Required change:
   - Validation (tests/monitoring):
   - Framework tags: <ASVS Vx, API#, Top10 theme, SSDF area>

### P1
...

### P2
...

## Readiness gates
### Must fix before implementation
- [ ] ...
### Must fix before launch
- [ ] ...

## Proposed diffs (NOT APPLIED)
```diff
--- a/docs/design/...
+++ b/docs/design/...
@@ ...
- old
+ new
```
```

## One-shot prompt (optional)

If the user asks for a one-shot instruction, provide a prompt that:
- reviews a specific design doc against an explicit baseline (ASVS/API Top 10/MASVS),
- produces P0/P1/P2 findings with evidence and framework tags,
- outputs `REVIEW_DESIGN.md` only,
- includes proposed diffs (not applied),
- recommends `threat-modeling-qa` when needed.
