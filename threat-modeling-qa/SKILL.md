---
name: threat-modeling-qa
description: Interactive threat modeling session (Q&A) for an application/system change. Lets the user pick a methodology (STRIDE, attacker stories, LINDDUN, or hybrid), models trust boundaries/data flows, enumerates threats, prioritizes risks, maps threats to OWASP baselines (ASVS/API Top 10/MASVS) as applicable, and records verification steps aligned with NIST SSDF. Report-only.
metadata:
  short-description: Interactive threat modeling Q&A (report-only)
  outputs:
    - THREAT_MODEL.md
  constraints:
    - report-only (no file edits)
    - propose changes as diffs inside the report
---

# Threat Modeling Q&A (Interactive, Standards-Backed)

Use this skill to run a structured threat modeling workshop for a **specific system/design/change**. It is intentionally interactive: ask targeted questions, then produce a concrete threat model artifact with prioritized threats, mitigations, verification steps, and **explicit mapping to baselines**.

This complements:
- `appsec-intake-and-baseline` (risk tier + baseline + evidence bar),
- `design-review-security-lens` (decision-focused design correctness),
- `security-readiness-review` (evidence-based go-live gate).

## Defaults

- **Output (default):** `THREAT_MODEL.md` at repo root (or alongside the design doc if repo convention says so).
- **Scope:** one system, feature, or change request (explicitly stated in the output).
- **Baseline (preferred):** read from `REVIEW_SCOPE_BASELINE.md` if it exists; otherwise label your baseline selection as **PROPOSED**.
- **Report-only hard rule:** write **only** `THREAT_MODEL.md`. Do not change any other files.

## Report-only rule (required)

If you think the design doc should be updated to reference the threat model or to fix gaps:
- do **not** apply changes,
- include proposed doc updates as **unified diffs** inside `THREAT_MODEL.md`,
- keep diffs minimal and clearly labeled **NOT APPLIED**.

## Preflight (required)

1) Read and follow all applicable `AGENTS.md` instructions (treat as normative).
2) Find any repo/org security standards and data classification rules (if available).
3) Identify the design artifact (if any) and treat it as the primary source of truth for the model inputs.

## Step 0: Ask the user which approach they prefer (required)

Ask the user to choose one (explain each in one sentence):

1) **STRIDE:** systematic per-component/per-flow threats; best when architecture is known.
2) **Attacker stories:** narrative abuse cases; best early when architecture is fuzzy.
3) **LINDDUN (privacy):** best when PII/regulated data is central.
4) **Hybrid (default):** attacker stories first, then STRIDE on highest-risk flows.

If the user doesn’t choose, default to **Hybrid**.

Also ask:
- “Lightweight (fast) or thorough?”
If they don’t choose, default to **lightweight**.

## Step 1: Context capture (required)

Batch questions to reduce back-and-forth. Minimum set:

- Goals and non-goals
- Actors/roles (users, services, admins)
- Assets (data, secrets, integrity/availability)
- Entry points (APIs, UI, webhooks, jobs, imports)
- Data stores (and data types/sensitivity)
- Dependencies (internal/external), third parties
- Tenancy boundary (single-tenant/multi-tenant; how isolated)
- Where identity and secrets come from
- Any security invariants that must never be violated (authz, integrity rules)

If a design doc exists, only ask what’s missing.

## Step 2: Model the system (DFD + trust boundaries) (required)

Produce, in the output:
- components and responsibilities
- data stores and data types
- named trust boundaries
- authn/authz boundary points

If information is sufficient, include a Mermaid diagram grounded only in provided details. If not, list what’s missing.

## Step 3: Threat enumeration (required)

### If using Attacker Stories
Generate at least **8** abuse cases, each with:
- attacker goal
- preconditions
- path (steps)
- impact (C/I/A + blast radius)
- mitigations
- verification (tests/telemetry)

### If using STRIDE
Enumerate threats per:
- entry point,
- trust boundary crossing,
- data store,
- privileged/admin paths.

Cover STRIDE categories where relevant:
Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege.

### If using LINDDUN
Enumerate privacy threats where relevant:
Linkability, Identifiability, Detectability, Information Disclosure, Unawareness, Non-compliance.

### If using Hybrid
Start with attacker stories, then STRIDE only on the top 3–5 highest-risk flows.

## Step 4: Prioritize (required)

Use a simple rubric:
- **Likelihood:** Low / Medium / High
- **Impact:** Low / Medium / High
- **Severity:** P0 / P1 / P2
  - **P0:** credible exploit → severe confidentiality/integrity impact, cross-tenant risk, secret exposure, unauth access, irreversible data corruption, or severe DoS.
  - **P1:** likely abuse/incident without mitigation; significant privacy harm.
  - **P2:** defense-in-depth and monitoring.

## Step 5: Map to baselines and controls (required)

For each **P0/P1** threat:
- map to baseline area(s), e.g.:
  - **OWASP ASVS sections** (e.g., V2 AuthN, V4 Access Control, V5 Validation, V7 Error/Logging)
  - **OWASP API Security Top 10** themes (e.g., Broken Object Level Authorization)
  - **OWASP MASVS** categories (if mobile)
- map to “process expectations” for verification aligned with **NIST SSDF**:
  - what must be implemented (protect/produce well-secured software),
  - what evidence must exist (verify),
  - what monitoring/response is required (respond to vulnerabilities/incidents).

Do not turn this into a compliance checklist. Use mapping to ensure completeness and shared vocabulary.

## Step 6: Mitigations and verification (required)

For each P0/P1 threat:
- mitigation(s) (design-level preferred)
- verification steps:
  - tests (unit/contract/integration)
  - monitoring/audit signals
  - operational controls (rate limits, alerts, runbooks)

Flag platform/product decisions as **NEEDS DECISION**.

## Deliverable: `THREAT_MODEL.md`

```md
# Threat Model

- Model: <model>
- Date: <YYYY-MM-DD>
- Method: STRIDE / Attacker Stories / LINDDUN / Hybrid
- Scope: <system/change>
- Inputs: <design doc paths / Q&A summary>

## Baseline & framework mapping
- Risk tier (from REVIEW_SCOPE_BASELINE.md, if available): <tier or unknown>
- Baseline(s): ASVS <L1/L2/L3>, API Top 10 <Y/N>, MASVS <Y/N> (or PROPOSED)
- NIST SSDF emphasis: <high-level bullets>

## 1) Overview
### Goals
### Non-goals
### Actors
### Assets
### Entry points
### Dependencies

## 2) Trust boundaries and data flows
### Trust boundaries
### Data stores and data types
### Diagram (if available)

## 3) Threats, mitigations, verification (tagged)
| ID | Surface / Flow | Threat | Likelihood | Impact | Severity | Mitigations | Verification | Framework tags |
|---|---|---|---|---|---|---|---|---|

Framework tags examples:
- ASVS: V2/V4/V5/V7/V10...
- API: Broken Object Level Authorization, Broken Authentication...
- MASVS: <category>
- SSDF: verification / supply chain / vulnerability response

## 4) Top risks
1) ...
2) ...
3) ...

## 5) Open questions / unknowns
- ...

## 6) Readiness gates
### Must fix before implementation
- [ ] ...
### Must fix before launch
- [ ] ...

## Proposed diffs (NOT APPLIED) (optional)
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
- lets the user choose a method (or defaults to Hybrid),
- collects context questions in one batch,
- maps P0/P1 threats to ASVS/API Top 10/MASVS and SSDF-style verification expectations,
- outputs `THREAT_MODEL.md` only,
- includes proposed diffs (not applied) if doc updates are needed.
