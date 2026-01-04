---
name: repo-bundle-review-apply
description: Bundle a local git repository into a zip excluding .gitignored files (optionally include sanitized .git metadata), submit it to an OpenAI API model for a long-running review, extract a unified diff patch from the response, apply the patch locally, and capture follow-up instructions.
---

# Repo Bundle Review Apply

## Goal

Bundle a repo (without ignored files), send it to an OpenAI API model for feedback + a `git apply`-compatible patch, apply the patch, then follow the model’s post-apply instructions.

## Prerequisites

- Set `OPENAI_API_KEY` (API access is separate from ChatGPT Pro/Plus UI subscriptions).
- Choose a model ID your API project can access (optionally: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`).

## Run

Review + apply:

`python3 $CODEX_HOME/skills/repo-bundle-review-apply/scripts/repo_bundle_review_apply.py --repo . --model <model-id> --message "Request feedback + a unified diff patch"`

Fetch/save patch but don’t apply:

`python3 $CODEX_HOME/skills/repo-bundle-review-apply/scripts/repo_bundle_review_apply.py --repo . --model <model-id> --message "..." --no-apply`

## Outputs

Writes artifacts to `<repo>/.codex-review/` by default:

- `bundle.zip`
- `response.md`
- `patch.diff`

## Common options

- `--include-git none|metadata|full` (default: `metadata`; metadata sanitizes `.git/config` URLs)
- `--artifact-dir <path>` (default: `.codex-review` under the repo root)
- `--bundle-only` (only write `bundle.zip` and exit)
- `--no-background` (single synchronous request; more timeout-prone)
- `--allow-git-dir-changes` (unsafe; default refuses diffs touching `.git/**`)
