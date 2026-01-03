---
name: security-readiness-review
description: Application security go-live readiness review (release gate). Evidence-driven check that baseline controls (OWASP ASVS/API Top 10/MASVS as applicable) are implemented, P0/P1 threats are mitigated, and operational readiness exists. Explicitly aligned to NIST SSDF (process/evidence expectations). Produces a Go/No-go report with proposed doc diffs (not applied).
metadata:
  short-description: AppSec go-live readiness review (report-only)
  outputs:
    - REVIEW_SECURITY_READINESS.md
  constraints:
    - report-only (no file edits)
    - evidence-driven (do not assume scans/tests exist)
    - propose changes as diffs inside the report
---

# Security Readiness Review (Go‑Live / Release Gate, Evidence-Driven)

Use this skill for an AppSec team’s **pre-launch / go-live security readiness review**.

This is distinct from:
- **Intake/baseline:** picks tier, baseline, and evidence bar (`appsec-intake-and-baseline`).
- **Design review:** assesses whether the proposal is safe and complete (`design-review-security-lens`).
- **Threat modeling:** enumerates threats/abuse cases and mitigations (`threat-modeling-qa`).
- **Implementation review:** confirms mitigations and invariants in code/config (`implementation-security-review`).
- **Readiness review (this skill):** verifies implementation and verification **evidence** and gates the release.

## When to use

Use when:
- deciding if a release/service can ship (GA / production exposure),
- you need an explicit Go / Go-with-conditions / No-go decision,
- you need to map baseline/threats → mitigations → evidence.

Do **not** use when:
- you’re still deciding what mitigations are required (use `threat-modeling-qa` + `design-review-security-lens`).

## Defaults

- **Output (default):** `REVIEW_SECURITY_READINESS.md` at repo root (or release folder if repo convention says so).
- **Scope:** one release, service, or deployable unit; explicitly state versions/commit if provided.
- **Baseline source (preferred):** `REVIEW_SCOPE_BASELINE.md`.
  - If absent, infer baseline and label it **PROPOSED**.
- **Report-only hard rule:** write **only** `REVIEW_SECURITY_READINESS.md`. Do not change any other files.

## Report-only rule (required)

If you identify missing docs/runbooks/config guidance:
- do **not** apply changes,
- propose updates as **unified diffs** inside `REVIEW_SECURITY_READINESS.md`,
- clearly label them as **NOT APPLIED**.

## Evidence-driven rule (required)

- Do not claim a scan/test/control exists unless:
  - the user provides evidence, or
  - the repo contains a clearly identifiable artifact (and you cite it).
- If evidence is missing, record an “evidence missing” finding and gate accordingly.

## Framework alignment (intent)

- **OWASP ASVS / API Top 10 / MASVS:** defines “what controls should exist.”
- **NIST SSDF:** defines “what practices/evidence should exist in the SDLC” (requirements, secure build, verification, vulnerability response).

You are not writing a compliance report; you are using these frameworks to avoid gaps and to communicate clearly.

## Preflight (required)

1) Read and follow all applicable `AGENTS.md` instructions (treat as normative).
2) Identify release scope:
   - component/service name(s),
   - what changed (high-level),
   - exposure (public internet? internal? admin-only?),
   - data sensitivity (PII? secrets? regulated?).
3) Read `REVIEW_SCOPE_BASELINE.md` if present:
   - risk tier,
   - selected baselines,
   - minimum evidence bar.
4) Ask the user for evidence artifacts where needed (links, screenshots, pipeline outputs, scan reports, dashboards).

## Inputs to request (ask in one batch)

As available:
- `REVIEW_SCOPE_BASELINE.md` (or the tier/baseline info)
- latest threat model(s) and design review(s) for the change (or links/paths)
- implementation review output (if done)
- list of externally reachable endpoints and their auth requirements
- dependency changes (new packages/services/integrations)
- ownership (on-call) and runbooks
- evidence artifacts (any subset is acceptable, but compare against the minimum evidence bar):
  - SAST results
  - dependency/vulnerability scan results (SCA)
  - container/image scan results
  - IaC scan results (if applicable)
  - secrets scan results
  - security tests (unit/integration/contract/e2e)
  - audit logging validation evidence
  - rate limiting / abuse prevention config evidence
  - dashboards/alerts evidence
  - penetration test results (if performed)
  - rollback plan / feature flags

## Workflow

### 1) Baseline confirmation (required)
- State the selected baseline(s) (ASVS level, API Top 10, MASVS).
- Restate the minimum evidence bar from `REVIEW_SCOPE_BASELINE.md`.
- If missing, propose an evidence bar consistent with exposure/data/tier and label **PROPOSED**.

### 2) Threat closure mapping (required)
- Enumerate P0/P1 threats from the latest threat model/design review (or infer and label **INFERRED** if missing).
- For each threat, map:
  - mitigation(s),
  - implementation status,
  - evidence (links/artifacts),
  - owner.

Status must be one of:
- **Mitigated (evidence)**
- **Partially mitigated**
- **Not mitigated**
- **Risk accepted** (must include approver + rationale; otherwise treat as not mitigated)

### 3) Baseline control checklist (required)
Assess what’s relevant, and explicitly mark N/A. Prefer to organize by ASVS sections for clarity.

#### Identity & access (ASVS V2/V3/V4; API Top 10)
- least-privilege authz implemented and tested
- object-level authorization enforced (tenant/resource scoping)
- service-to-service identity and secret handling
- admin/break-glass path defined and audited

#### Data protection & privacy (ASVS V6/V7/V8/V9; MASVS)
- encryption in transit/at rest as required
- retention/deletion behavior matches policy
- PII/secrets not logged; audit logs for sensitive actions

#### Input handling & injection (ASVS V5)
- validation and canonicalization in place
- high-risk parsers/features controlled (uploads, templates, deserialization)
- SSRF/egress protections if applicable

#### Abuse prevention and resilience (ASVS V10)
- rate limiting / throttling for exposed surfaces
- timeouts/retries/backoff; idempotency where needed
- safe failure modes (fail closed where appropriate)

#### Supply chain and build security (NIST SSDF; practical AppSec)
- dependency scanning performed; critical vulns addressed/approved
- image scanning performed; base images maintained
- secrets scanning performed; no exposed credentials
- provenance/signing evidence if required by tier (optional)

#### Observability and incident readiness (ASVS V7/V10; NIST SSDF)
- dashboards and alerts exist for abuse signals and key errors
- runbooks exist (including rollback)
- ownership and escalation path defined
- vulnerability/patch response expectations documented for critical components

### 4) Compare evidence to minimum bar (required)
Create a table of required evidence items vs what was provided. Missing required evidence becomes a finding (often P0/P1 depending on tier).

### 5) Gate the release (required)
- **P0 (Blocker):** unmitigated critical risk, missing/weak authz, cross-tenant exposure risk, secret exposure, or critical vuln without explicit approval; or missing required evidence for Tier 2/3.
- **P1:** significant risk or missing monitoring/auditability likely to cause harm.
- **P2:** hygiene improvements and follow-ups.

Output a decision:
- **Go**
- **Go with conditions**
- **No-go**

## Deliverable: `REVIEW_SECURITY_READINESS.md`

```md
# Security Readiness Review

- Model: <model>
- Date: <YYYY-MM-DD>
- Release / Component: <name>
- Version / Commit: <if provided>
- Exposure: <public/internal/admin-only>
- Data sensitivity: <classification>

## Baseline & framework mapping
- Risk tier: <from REVIEW_SCOPE_BASELINE.md or PROPOSED>
- Baseline(s): ASVS <L1/L2/L3>, API Top 10 <Y/N>, MASVS <Y/N>
- NIST SSDF focus: <verification, supply chain, vuln response, etc.>
- Minimum evidence bar: <copied from scope doc or PROPOSED>

## Decision
- Outcome: Go / Go with conditions / No-go
- P0 count:
- P1 count:
- Notes:

## Scope and evidence
### Reviewed artifacts
- ...
### Evidence provided
- ...

## Threat closure status
| Threat ID / Link | Severity | Status | Mitigation summary | Evidence | Owner |
|---|---|---|---|---|---|

## Evidence bar check
| Evidence item (required?) | Provided? | Link / artifact | Notes |
|---|---|---|---|

## Findings (tagged)
### P0
1. ...
   - Framework tags: <ASVS/API/MASVS/SSDF>
### P1
...
### P2
...

## Control checklist (high-level)
- [ ] AuthN/AuthZ implemented and tested (or N/A)
- [ ] Secrets handled safely (no leaks; rotation plan)
- [ ] Vuln scans performed; criticals addressed/approved
- [ ] Rate limiting/abuse prevention configured (if exposed)
- [ ] Audit logging and monitoring/alerts in place
- [ ] Runbooks + rollback plan exist; ownership defined

## Follow-ups and deadlines
| Item | Severity | Owner | Due date | Notes |
|---|---|---|---|---|

## Proposed diffs (NOT APPLIED) (optional)
```diff
--- a/docs/runbooks/...
+++ b/docs/runbooks/...
@@ ...
- old
+ new
```
```

## One-shot prompt (optional)

If the user asks for a one-shot instruction, provide a prompt that:
- requests baseline + evidence artifacts in one batch,
- maps threats/baseline controls → mitigations → evidence,
- produces Go/No-go with P0/P1/P2 findings tagged to frameworks,
- outputs `REVIEW_SECURITY_READINESS.md` only,
- includes proposed diffs (not applied) for missing docs/runbooks.
