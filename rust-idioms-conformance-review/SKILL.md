---
name: rust-idioms-conformance-review
description: Read Microsoft Pragmatic Rust Guidelines (agents/all.txt) as a normative baseline, then perform a *line-by-line* conformance audit of a Rust repository (scoped by crate/path/PR) and produce an evidence-backed report with a guideline conformance matrix and proposed diffs (not applied).
metadata:
  short-description: Line-by-line idiomatic Rust conformance review using Microsoft Pragmatic Rust Guidelines
  outputs:
    - REVIEW_RUST_IDIOMS.md
  constraints:
    - report-only (no file edits)
    - MUST read and apply the full Microsoft baseline text (agents/all.txt)
    - MUST perform line-by-line audit for all in-scope Rust-relevant files
    - MUST include an audit coverage manifest proving what was audited vs excluded
baseline:
  primary_url: https://microsoft.github.io/rust-guidelines/agents/all.txt
---

# Rust Idioms Conformance Review (Line-by-Line)

## Purpose

This skill teaches and enforces idiomatic Rust by:

1) **Reading** the Microsoft Pragmatic Rust Guidelines baseline in full (agents/all.txt), and  
2) **Auditing every line** of all in-scope Rust-relevant files to assess conformance, with evidence and concrete remediation.

Overarching goals:
- easy to reason about,
- easy to maintain,
- safer (especially around `unsafe`, API design, and correctness boundaries).

## Definitions (required)

### What “best practices” means here
A recommendation is a “best practice” only if it is:
- **Recognized** in the Microsoft baseline (agents/all.txt) or a source it explicitly endorses,
- **Applicable** to the repo’s context (library vs app, async vs sync, FFI vs no FFI),
- **Verifiable** in code/config/tests/CI,
- **Risk-reducing** for correctness/safety/maintainability/operability.

### Source precedence (required)
When guidance conflicts, resolve in this order:
1) Repo-local normative docs (e.g., `AGENTS.md`, `CONTRIBUTING.md`, `docs/standards/*`, lint policy)
2) Microsoft Pragmatic Rust Guidelines (agents/all.txt) — baseline for this skill
3) Sources explicitly referenced/endorsed by the baseline (e.g., Rust API Guidelines)
4) Tooling reality (rustc lints, Clippy, rustfmt, semver norms)
5) Local evidence (incidents, regressions, perf data)

If the repo intentionally deviates, record:
- deviation,
- rationale,
- and mitigating controls (tests, lint gates, safety comments, etc.).

## Scope mechanism (required)

This skill supports three scope modes. You MUST pick one and document it in the report.

### Mode A: Workspace-wide (default)
Audit **all crates** in the workspace (all members in the root `Cargo.toml`, plus any nested crates used by path dependencies).

### Mode B: By crate
Audit only the named crate(s) (and optionally their local path-dependency crates if required to assess conformance at boundaries).

### Mode C: By paths / PR-diff
Audit only specified paths and files, plus any additional files necessary to validate conformance claims (e.g., public API signatures referenced by changed code, feature flags, or unsafe helpers).

#### Mandatory scoping rules
- “Line-by-line audit” applies to **all files in-scope**.
- If a file is **excluded**, it must appear in the coverage manifest with a reason.
- You must NOT claim “full audit complete” unless every in-scope file is audited line-by-line.

### Standard exclusions (allowed, but must be recorded)
These can be excluded from *line-by-line Rust idiom conformance* if documented:
- `target/`, `.git/`, vendored dependency directories, `node_modules/`
- generated files (but record generator + whether generated output is checked-in)
- `Cargo.lock` (review only for policy/hygiene, not line-by-line idioms)

If generated Rust is checked in and acts as a public surface (e.g., bindings), prefer auditing it; otherwise, mark excluded with explicit rationale.

## Required baseline: Microsoft Pragmatic Rust Guidelines

This skill MUST NOT merely reference the baseline. You must read it and apply it.

### Baseline acquisition (required)
1) Retrieve and read the full text at:
   - `https://microsoft.github.io/rust-guidelines/agents/all.txt`
2) Confirm you have the whole document (not just a snippet).
3) Build a **Guideline Inventory**:
   - guideline ID (e.g., `M-CANONICAL-DOCS`)
   - title
   - modality (`must` / `should` / `may`, or numeric strength if used)
   - applicability notes (when N/A)

### Baseline provenance (required in report)
Include:
- URL
- retrieval date
- a simple fingerprint (e.g., total line count + first header + last guideline ID encountered)

This demonstrates you actually loaded the baseline.

## Preflight (required)

1) Read and follow repo-local agent instructions first (`AGENTS.md`, etc.).
2) Determine repo shape:
   - workspace vs single crate
   - library crates vs binary/application crates
   - presence of: `unsafe`, FFI, async runtime, feature flags, proc-macros
3) Decide whether to run commands.
   - Ask before running shell commands unless pre-authorized.

Recommended (ask first):  
- `cargo fmt --check`  
- `cargo clippy --all-targets --all-features`  
- `cargo test --all`  
- `cargo doc --no-deps`  
- if relevant: `cargo audit`, `cargo hack`, `cargo udeps`, `cargo miri test`

## Line-by-line audit procedure (required)

### 1) Build the audit file list (required)
Construct the definitive in-scope file list before auditing:
- All `Cargo.toml` in-scope (workspace + crates)
- All Rust source: `**/*.rs` in-scope
- Build scripts: `build.rs`
- CI/tooling config impacting Rust style/quality (e.g., GitHub Actions)
- Lint config: `rustfmt.toml`, `.clippy.toml` if present, workspace lint sections in `Cargo.toml`

Record the file list (or a summarized manifest) in the report.

### 2) Audit coverage manifest (required)
Maintain a table with at least:
- path
- file type (`rust`, `toml`, `ci`, `doc`, `generated`)
- lines (approx is ok if exact is hard, but be consistent)
- status: `Audited` / `Excluded`
- reason if excluded

You must update this as you audit so you can prove completeness.

### 3) File-by-file audit (required)
For each **Audited** file, do a line-by-line pass and capture issues with:
- evidence (path + line or line-range)
- related guideline ID(s)
- severity (P0/P1/P2)
- recommended fix + verification

#### What to check while reading every line
You are not required to *report on every line*, but you are required to *read every line* and ensure any relevant guideline checks are applied. Focus on detecting:
- `unsafe` blocks/traits/FFI boundaries
- public API design and ergonomics
- error handling and `Result` conventions
- panics (`panic!`, `unwrap`, `expect`, `todo!`, `unimplemented!`)
- docs and doc sections (`# Examples`, `# Errors`, `# Panics`, `# Safety`, etc.)
- module docs `//!` for public modules
- re-exports, especially glob re-exports
- feature flags and cfg complexity
- logging patterns and sensitive data handling
- statics/global state and initialization patterns
- performance anti-patterns explicitly covered by baseline

### 4) Two-pass discipline (recommended)
To reduce misses in full audits:
- **Pass 1 (structure):** map modules, public surfaces, unsafe/FFI hotspots, feature topology.
- **Pass 2 (conformance):** evaluate line-by-line against the derived guideline checklist.

If you cannot do a second pass, state that clearly and avoid overclaiming confidence.

## Severity model (required)

- **P0 (Blocker):** likely unsoundness/UB risk, unsafe without safety contract, FFI portability hazards, incorrect Send/Sync, panic in contexts that can cause systemic failure, security-sensitive leaks.
- **P1:** major maintainability/API ergonomics issues that will compound; missing lint/tooling gates; inconsistent error model; docs gaps on public surfaces.
- **P2:** style/consistency improvements; idiomatic polish.

## Conformance matrix (required)

Produce a guideline-by-guideline table:
- Guideline ID
- Status: `Pass / Partial / Fail / N/A`
- Evidence pointers (paths + line ranges)
- Notes/remediation summary

If a guideline is not applicable, mark `N/A` with a short justification.

## Proposed diffs (NOT APPLIED)
Include minimal unified diffs for fixes. Prefer small, reviewable changes:
- doc section additions
- lint/CI enforcement
- API signature improvements
- unsafe safety docs + tests
- feature gating simplification
- removing glob re-exports, excessive wrapper types, or confusing patterns

Avoid giant refactors unless required to resolve P0/P1; if needed, propose a staged plan.

Example diff formatting (in the report):

```diff
--- a/crates/foo/src/lib.rs
+++ b/crates/foo/src/lib.rs
@@
- old
+ new
```

## Output: `REVIEW_RUST_IDIOMS.md` (required)

Write only this file, structured as follows.

### Header
- Date
- Repo/path
- Scope mode + scope details
- Commands executed (if any)

### Baseline provenance (required)
- Baseline URL
- Retrieved date
- Fingerprint (line count + first header + last guideline ID seen)

### Summary
- Overall posture
- P0/P1/P2 counts
- Top issues

### Repo profile
- Crates and roles (lib/bin, public/internal)
- Hotspots: unsafe/FFI/async/features

### Audit coverage manifest (required)
A table listing every in-scope file and whether it was audited.

### Conformance matrix (required)
A table mapping guideline IDs to Pass/Partial/Fail/N/A with evidence pointers.

### Findings
Group by severity (P0, P1, P2). Each finding must include:
- Guideline(s)
- Evidence (path + line-range)
- Why it matters
- Recommendation
- Verification

### Cross-cutting recommendations
Summarize themes: tooling, docs, API, errors, unsafe/soundness.

### Proposed diffs (NOT APPLIED)
Include minimal diffs for the most important fixes.

### Follow-ups
If needed: staged refactor plan for large issues.

## Guardrails (required)
- Do not claim a “full audit” unless every in-scope file is marked **Audited** in the coverage manifest.
- If you cannot finish, still produce the report with:
  - completed coverage,
  - remaining file list,
  - and a clearly-labeled partial conformance matrix.
