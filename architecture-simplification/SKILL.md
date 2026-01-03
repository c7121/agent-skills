---
name: architecture-simplification
description: Architecture simplification review that preserves requirements, reduces attack surface and operational complexity, and rewrites the architecture narrative to be concise and non-redundant. Uses explicit best-practice sources (OWASP, NIST SSDF, well-architected/SRE patterns). Report-only.
metadata:
  short-description: Architecture simplification (report-only)
  outputs:
    - REVIEW_ARCH_SIMPLIFICATION.md
  constraints:
    - report-only (no file edits)
    - must preserve explicit requirements unless clearly marked as a proposed change with trade-offs
    - must remove redundant language in the rewritten architecture narrative
---

# Architecture Simplification Review (Easy to Reason About, Easy to Maintain, Safer)

Use this skill to simplify a system architecture **without losing requirements**. The goal is to reduce:
- cognitive load (hard to understand → easy to understand),
- moving parts (many components → fewer, clearer components),
- attack surface (many entry points/privileged paths → minimized and intentional),
- operational burden (manual steps, brittle dependencies, unclear ownership).

This skill is appropriate when the current or proposed architecture feels “overbuilt,” hard to review, risky to operate, or difficult to secure.

It produces a single report: `REVIEW_ARCH_SIMPLIFICATION.md`.

---

## Non-negotiables (hard rules)

This skill:

### MUST
- **Preserve requirements**: Treat explicit requirements and constraints as binding unless the report clearly labels a requirement as “proposed to change” and explains the trade-off.
- **Use best practices explicitly**: Every major simplification recommendation must cite the *best-practice basis* (source + principle + how it applies).
- **Minimize net complexity**: Do not introduce new components unless there is a clear **net reduction** in complexity, failure modes, or security risk.
- **Remove redundant language**: Rewrite the architecture narrative into a concise canonical version (define terms once, avoid duplicated paragraphs, unify naming).
- **Be decision-oriented**: Provide a recommended target architecture and the smallest viable migration path.

### MAY
- Suggest removing or narrowing surfaces (endpoints, protocols, admin tools, background jobs, integrations).
- Suggest alternate designs and compare options.
- Scrutinize goals **only** when a meaningful simplification would require changing a requirement (or when two requirements are in tension).

### MUST NOT
- Claim compliance, test results, or tool execution unless evidence is provided.
- “Simplify” by dropping non-functional requirements silently (security, reliability, privacy, auditability, performance, latency, legal/regulatory).
- Optimize solely for cost at the expense of safety unless a requirement explicitly demands it.

---

## What “best practices” means in this skill (required)

A “best practice” is a design principle or control expectation that is:
1) **Recognized** (from a reputable, widely used standard/framework or your organization’s published standards),
2) **Applicable** to the system’s context,
3) **Verifiable** (observable in design, implementation, or operational evidence), and
4) **Risk-reducing** (reduces known security, reliability, or maintenance failure modes).

### Best-practice source hierarchy (precedence)

When sources conflict, use this precedence order:

1) **Explicit requirements and constraints**  
   Product, legal/regulatory, contractual, privacy, internal security policies, platform constraints.
2) **Security engineering frameworks (control baselines)**  
   - OWASP ASVS (web/service security requirements)  
   - OWASP API Security Top 10 (API-specific risk patterns)  
   - NIST SSDF (secure software development practices; evidence expectations)
3) **Architecture & operations guidance (well-architected patterns)**  
   - “Well-Architected” style guidance (security, reliability, operability, cost, sustainability)  
   - SRE-style practices (simplicity, clear ownership, automation, toil reduction)  
   - “12-factor” style service practices (config, statelessness, logging, disposability) where applicable
4) **Internal reference architectures / golden paths** (if provided)
5) **Local context evidence**  
   Past incidents, postmortems, performance data, abuse reports, penetration findings.

### How to cite a best practice in the report

For each major recommendation, include:

- **Source**: e.g., “OWASP ASVS (architecture, access control)”, “NIST SSDF (secure design & component reuse)”
- **Principle**: e.g., “minimize attack surface”, “least privilege”, “secure defaults”, “standardize cross-cutting concerns”
- **Application**: how the recommendation changes the system and why it reduces risk or complexity

---

## Inputs (provide whatever exists)

Prefer:
- Architecture/design doc(s) (current and/or proposed), ADRs, runbooks
- Diagrams (C4, sequence diagrams, data flow diagrams)
- Requirements (functional + non-functional) and constraints
- Threat model (if available)
- Operational data (SLOs, incident history, on-call pain points)
- For PR reviews: the PR description + relevant diffs + links to docs

If requirements are missing or scattered, extract them from available artifacts and label them as **Assumptions**.

---

## Workflow

### 1) Build a requirements ledger (MUST)

Create a normalized list:
- **Functional requirements** (FR-1, FR-2, …)
- **Non-functional requirements** (NFR-1, NFR-2, …): security, privacy, availability, latency, auditability, compliance, cost ceilings, etc.
- **Constraints** (C-1, C-2, …): platform, language, regulatory, dependency limitations

Then:
- Deduplicate (“same requirement stated 3 ways”)  
- Resolve terminology conflicts (choose one canonical term; define it)
- Identify tensions (“NFR-availability” vs “NFR-strong consistency”) and call them out

Deliverable in report: **Requirements Ledger** + **Assumptions**.

### 2) Produce a canonical “current architecture” summary (MUST)

Write a short, non-redundant description:
- System boundary and external actors
- Components and responsibilities (one line per component)
- Data stores and data classification
- Trust boundaries and identities/credentials
- Key flows (happy path + critical flows)

Deliverable in report: **Current Architecture (Canonical)**.

### 3) Inventory surfaces and complexity drivers (MUST)

Create inventories (tables are encouraged):

- **Surface inventory**: APIs, webhooks, UI/admin surfaces, background jobs, file upload/download, partner integrations, protocols, ports
- **Identity & privilege inventory**: service accounts, roles, scopes, secrets, KMS keys, cross-account access
- **Data inventory**: sources of truth, caches, replicas, event streams, retention, deletion paths
- **Dependency inventory**: internal services, third parties, SDKs, infra primitives

Then identify **complexity drivers** such as:
- duplicated responsibilities across components
- multiple ways to authenticate/authorize the same action
- excessive synchronous fan-out (fragile call chains)
- cross-service transactions without clear consistency model
- multiple data stores containing overlapping “truth”
- bespoke cryptography or bespoke auth/session/token logic
- unclear ownership (“who maintains this?”)
- too many configuration modes / feature-flag branching

Deliverable in report: **Surface & Complexity Inventory**.

### 4) Generate simplification candidates (MAY, but recommended)

Create a set of candidate changes. Prefer “remove/merge/standardize” over “add.”

Common candidate categories:

**A) Surface reduction**
- remove unused endpoints
- replace “public” with “private” where feasible
- consolidate multiple similar endpoints into one resource model
- remove admin surfaces or gate behind strong auth + audit
- remove custom protocols; prefer one (e.g., HTTPS/JSON) unless a requirement dictates otherwise

**B) Component consolidation**
- merge services that do not justify separate operational lifecycles
- remove “pass-through” services that add hops but no clear responsibility
- eliminate duplicate schedulers/workers if one can own the domain

**C) Standardize cross-cutting concerns**
- one authn pattern, one authorization policy model, one token story
- consistent request validation, consistent logging/audit
- consistent rate limiting / abuse protection where needed

**D) Data model simplification**
- reduce “sources of truth” to one per domain entity
- make consistency model explicit (strong vs eventual) per flow
- remove redundant caches/replicas unless they satisfy a stated NFR

**E) Operational simplification**
- fewer deployment units, fewer runtime config permutations
- simplify rollout/rollback (flags, canary), reduce irreversible migrations
- strengthen observability in fewer places (standard logging/metrics/tracing)

Deliverable in report: **Candidate Set**.

### 5) Evaluate candidates against requirements (MUST)

For each candidate:
- **Requirements impact**: which FR/NFR/C it satisfies, risks, or threatens
- **Security impact**: attack surface, trust boundaries, privilege, data exposure
- **Reliability impact**: coupling, failure domains, backpressure, retries, timeouts
- **Maintainability impact**: ownership, testability, complexity
- **Implementation cost**: migration steps, compatibility, data migration risk
- **Best-practice basis**: source + principle + application

Deliverable in report: **Option Evaluation Table**.

### 6) Select a recommended target architecture (MUST)

Provide:
- Recommended option (and a smaller “least-change” option if relevant)
- A **target canonical architecture narrative** (concise, non-redundant)
- A simplified diagram (ASCII is acceptable if images aren’t available)
- Explicit invariants:
  - authorization invariants (“who can do what”)
  - data invariants (“source of truth”, retention)
  - reliability invariants (timeouts, retries, idempotency)

Deliverable in report: **Recommended Target Architecture**.

### 7) Scrutinize goals only when required (MAY)

If a simplification would require dropping or weakening a requirement:
- state it explicitly: “This conflicts with NFR-3…”
- propose alternatives that preserve the requirement
- if no alternative exists, ask the minimum set of decision questions:
  - “Is requirement X mandatory, or can it be scoped/narrowed?”
  - “Is requirement X time-bound (MVP) or permanent?”
  - “Which is the priority: latency vs consistency vs auditability?”

Deliverable in report: **Goal Trade-offs & Questions**.

### 8) Remove redundant language and propose doc diffs (MUST)

Provide:
- A rewritten **canonical architecture section** (short, consistent terms)
- A **glossary** for ambiguous terms (component names, domain entities)
- Inline diffs that:
  - delete duplicated paragraphs
  - unify terminology (one name per thing)
  - move repeated content into a single “source of truth” section
  - remove contradictions (or flag them clearly)

Deliverable in report: **Documentation Diffs (Proposed)**.

---

## Explicit framework hooks (how to apply OWASP / NIST here)

Use these frameworks as guardrails to ensure simplification improves safety rather than creating blind spots:

### OWASP (ASVS / API Security Top 10)
Use OWASP expectations to validate that simplification does not weaken:
- access control model clarity and correctness (object-level and function-level authorization)
- input validation and request handling consistency
- secure defaults and configuration hardening
- logging/auditing for sensitive actions
- cryptographic key management and secret handling
- API-specific abuse risks (overexposure, excessive data, lack of rate limits, weak auth)

In practice: when you propose removing/merging a component or endpoint, explicitly state how access control, validation, logging, and data handling are preserved or improved.

### NIST SSDF
Use SSDF as the “secure SDLC” evidence anchor:
- simplification should reduce the number of places requiring secure design, review, and testing
- prefer reuse of vetted components/patterns over bespoke implementations
- make verification easier: fewer components → clearer test ownership and security regression coverage

In practice: include a “verification plan delta” (what becomes easier to test and what must be added).

---

## Severity and decision model

Use P0/P1/P2 to prioritize simplification items:

- **P0**: complexity or surface creates a clear, high-likelihood safety/security failure mode (e.g., ambiguous authz, duplicate sources of truth causing privilege drift, multiple public entry points without uniform controls).
- **P1**: meaningful risk or maintenance burden that will predictably cause outages/incidents or security regressions.
- **P2**: worthwhile cleanup/hardening; improves readability and reduces future risk.

Decision:
- **Recommend** (adopt target architecture)
- **Recommend with conditions** (must resolve specific questions or add safeguards)
- **Not recommended** (benefits do not justify risk/cost; propose minimal alternative)

---

## Output format (write exactly one file)

Write **only** `REVIEW_ARCH_SIMPLIFICATION.md` with this structure:

1. **Executive Summary**
   - What is being simplified and why
   - Recommended option
   - Top P0/P1 items

2. **Requirements Ledger**
   - FR / NFR / Constraints
   - Assumptions (clearly marked)

3. **Current Architecture (Canonical, non-redundant)**
   - Components + responsibilities
   - Trust boundaries + identities
   - Data stores + data classification
   - Key flows

4. **Surface & Complexity Inventory**
   - Surface table
   - Identity/privilege table
   - Data table
   - Top complexity drivers

5. **Simplification Options**
   - Option A / Option B (and optional “least-change”)
   - Best-practice basis for each (source + principle + application)

6. **Option Evaluation**
   - Requirements preservation matrix
   - Security / reliability / maintainability impacts
   - Trade-offs and open questions (only where necessary)

7. **Recommended Target Architecture**
   - Concise canonical narrative (non-redundant)
   - Simplified diagram
   - Explicit invariants

8. **Migration Plan**
   - Phased steps
   - Compatibility / rollout / rollback
   - Risks + mitigations

9. **Verification & Evidence Delta**
   - What tests/controls must exist after simplification
   - What becomes simpler to verify

10. **Documentation Diffs (Proposed)**
   - Inline diffs to remove redundant language and contradictions
   - Glossary updates

