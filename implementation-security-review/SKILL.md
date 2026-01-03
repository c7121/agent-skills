---
name: implementation-security-review
description: Implementation-level AppSec review for code/config/IaC changes. Reviews a PR/diff (preferred) or a component directory for common vulnerability classes (authz invariants, injection, SSRF, secrets, crypto misuse, multi-tenant data access, unsafe deserialization, insecure config/IAM). Produces a report with P0/P1/P2 findings, concrete remediation guidance, and explicit mapping to OWASP (ASVS/Top 10/API Top 10/MASVS as applicable) and NIST SSDF verification expectations. Report-only.
metadata:
  short-description: Code/config/IaC security review (report-only)
  outputs:
    - REVIEW_IMPLEMENTATION_SECURITY.md
  constraints:
    - report-only (no file edits)
    - do not claim tests/scans ran unless evidence is provided
---

# Implementation Security Review (Code / Config / IaC)

Use this skill to review **what actually got built**. It’s the missing link between “design is sound” and “release is safe.”

This skill is optimized for:
- PR/diff review,
- endpoint/handler review,
- config/IaC changes that alter exposure or privilege.

It complements:
- `appsec-intake-and-baseline` (tier + baseline),
- `design-review-security-lens` (design correctness),
- `threat-modeling-qa` (abuse cases),
- `security-readiness-review` (evidence-based go-live gate).

## When to use

Use when:
- reviewing a PR before merge,
- reviewing a set of changes before launch,
- validating that mitigations from the threat model/design review were implemented correctly.

Do **not** use when:
- you only have a high-level proposal and no code (use `design-review-security-lens`),
- you need an evidence-based release gate (use `security-readiness-review`).

## Defaults

- **Preferred input:** PR link/diff/patch or a commit range.
- **Fallback input:** list of files/dirs to review and a short description of the feature.
- **Baseline (preferred):** `REVIEW_SCOPE_BASELINE.md`.
  - If absent, select baseline and label it **PROPOSED**.
- **Output (default):** `REVIEW_IMPLEMENTATION_SECURITY.md` at repo root.
- **Report-only hard rule:** write **only** `REVIEW_IMPLEMENTATION_SECURITY.md`. Do not change any other files.

## Evidence rules (required)

- You may assert findings based on **code/config evidence you can cite**.
- Do not claim you ran tests/scans unless the user provides outputs or the repo contains captured artifacts.
- If a claim depends on runtime behavior (e.g., WAF policy, ingress config), ask for evidence or mark as “unknown.”

## Preflight (required)

1) Read and follow all applicable `AGENTS.md` instructions (treat as normative).
2) Identify the exact change set (PR/commit range/files).
3) Read `REVIEW_SCOPE_BASELINE.md` if present (risk tier + baseline + required evidence).
4) Ask before running shell commands unless the user explicitly pre-authorizes specific commands.

## Workflow

### 1) Identify security invariants (required)
From design/threat model/intake (or infer conservatively from the feature), write down:
- authz invariants (“who can do what to which resource”),
- tenancy invariants (“a tenant can never access another tenant’s data”),
- data handling invariants (what must never be logged/stored),
- trust boundaries (where validation must occur).

If invariants are missing and you cannot evaluate authz correctness, record a **P0 doc gap** and recommend `design-review-security-lens` / `threat-modeling-qa`.

### 2) Walk the request/data paths (required)
For each entry point affected (endpoint/handler/job/consumer):
- identify inputs (user-controlled fields, headers, URLs, file uploads),
- identify authorization decision points,
- identify data stores touched (queries, key-space, tenant scoping),
- identify outputs and error handling.

### 3) Targeted vulnerability checklist (required)
Mark N/A where irrelevant; don’t force-fit.

#### AuthN/AuthZ & multi-tenancy (ASVS V2/V3/V4; API Top 10)
- Broken object level authorization (IDOR): verify resource lookup is tenant-scoped and authz checked
- Broken function level authorization: ensure role checks are centralized and consistent
- Privilege escalation paths (admin-only endpoints, feature flags)
- Service-to-service auth: verify identity, audience, mTLS where applicable

#### Injection & parsing (ASVS V5; OWASP Top 10)
- SQL/NoSQL injection: parameterization, query builders, escaping correctness
- Template injection / expression language usage
- Command injection / unsafe shell usage
- Deserialization and unsafe reflection/dynamic eval
- XML entity expansion (XXE) if XML parsing exists

#### SSRF / egress / URL fetch (ASVS V5; Top 10)
- Any HTTP client that accepts user-controlled URLs?
- DNS rebinding / IP literal / redirect handling
- Allowlist/denylist strategy + network egress controls

#### Secrets & cryptography (ASVS V6/V7/V8/V9; NIST SSDF PS)
- Secrets in code/logs/config
- Token handling, signing/verification, key rotation expectations
- Crypto misuse (homegrown crypto, weak primitives, incorrect modes)
- Password handling if applicable (hashing & policy)

#### File handling (ASVS V5/V12)
- Upload validation, content-type sniffing, size limits, storage isolation
- Path traversal and archive extraction (zip slip)
- Malware scanning hooks (if required by baseline)

#### Error handling & logging (ASVS V7/V10)
- PII/secrets in logs
- Overly detailed errors (stack traces, internal IDs)
- Audit logging for sensitive actions (who/what/when/where)

#### Config / IAM / IaC (ASVS V1/V14; NIST SSDF; cloud posture)
- Public exposure changes (ingress, security groups, buckets)
- IAM broadening (wildcards, overly-wide resource scope)
- KMS/key policies and secret store permissions
- Default-allow network policies / missing egress restrictions

#### Supply chain deltas (NIST SSDF + practical AppSec)
- New dependencies: known-vuln risk, maintainer risk, critical transitive deps
- Build changes: unsigned artifacts, unpinned versions, new download scripts

### 4) Map findings to frameworks (required)
For each finding, include:
- **ASVS section** tag (e.g., V4 Access Control)
- and/or **OWASP Top 10** theme
- and/or **OWASP API Top 10** theme
- and/or **MASVS** category (if mobile)
- optionally a **CWE** reference if it helps communication.

### 5) Decide gates (required)
- **P0:** exploitable authz/authn weakness, cross-tenant access, secret exposure, critical injection, insecure public exposure/IAM, or easy SSRF with metadata access.
- **P1:** meaningful risk likely to lead to abuse/incident; missing auditability; unsafe defaults.
- **P2:** defense-in-depth improvements.

Include:
- must-fix-before-merge (if reviewing a PR),
- must-fix-before-launch.

## Deliverable: `REVIEW_IMPLEMENTATION_SECURITY.md`

```md
# Implementation Security Review

- Model: <model>
- Date: <YYYY-MM-DD>
- Change set: <PR link / commit range / files>
- System: <name>
- Risk tier & baseline: <from REVIEW_SCOPE_BASELINE.md or PROPOSED>

## Summary
- Outcome (for PR): Approve / Approve with changes / Request changes
- P0 count / P1 count:
- Highest-risk areas reviewed:
- Areas not reviewed (and why):

## Invariants assessed
- AuthZ invariants:
- Tenancy invariants:
- Data handling invariants:
- Trust boundaries:

## Entry points and flows reviewed
- <endpoint/job> → <authz check> → <datastore> → <outputs/logging>

## Findings (tagged)
### P0
1. <title>
   - Evidence: <file:Lx-Ly>
   - Impact:
   - Exploit sketch (high level):
   - Recommended fix:
   - Verification:
   - Framework tags: <ASVS Vx; OWASP Top 10 / API Top 10; SSDF area; CWE optional>

### P1
...

### P2
...

## Gates
### Must fix before merge
- [ ] ...
### Must fix before launch
- [ ] ...

## Notes for readiness review (evidence to collect)
- ...
```

## One-shot prompt (optional)

If the user asks for a one-shot instruction, provide a prompt that:
- requests a PR/diff/commit range,
- identifies invariants and walks entry points,
- checks the targeted vuln checklist,
- tags findings to ASVS/OWASP and notes SSDF-style evidence expectations,
- outputs `REVIEW_IMPLEMENTATION_SECURITY.md` only.
