#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import hashlib
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_ARTIFACT_DIRNAME = ".codex-review"
DEFAULT_POLL_INTERVAL_SECONDS = 30
DEFAULT_TIMEOUT_MINUTES = 90
DEFAULT_MAX_ZIP_BYTES = 100 * 1024 * 1024  # 100 MiB


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _run_git(repo_root: Path, args: list[str]) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo_root), *args])


def _git_repo_root(repo_path: Path) -> Path:
    try:
        top = subprocess.check_output(
            ["git", "-C", str(repo_path), "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"Not a git repository: {repo_path}") from exc
    return Path(top)


def _git_ls_files(repo_root: Path, extra_args: list[str]) -> list[str]:
    raw = _run_git(repo_root, ["ls-files", "-z", *extra_args])
    paths = [p.decode("utf-8", errors="surrogateescape") for p in raw.split(b"\0") if p]
    return paths


def _iter_repo_files_excluding_ignored(repo_root: Path) -> list[Path]:
    tracked = _git_ls_files(repo_root, [])
    untracked = _git_ls_files(repo_root, ["--others", "--exclude-standard"])
    seen: set[str] = set()
    ordered: list[Path] = []
    for rel in [*tracked, *untracked]:
        if not rel or rel in seen:
            continue
        seen.add(rel)
        ordered.append(repo_root / rel)
    return ordered


_HTTP_URL_WITH_USERINFO = re.compile(r"^(https?://)([^/@\s]+@)(.+)$")


def _sanitize_git_config(raw: str) -> str:
    sanitized_lines: list[str] = []
    for line in raw.splitlines():
        if re.search(r"(?i)\bextraheader\b", line):
            if "=" in line:
                prefix, _ = line.split("=", 1)
                sanitized_lines.append(f"{prefix}= <redacted>")
            else:
                sanitized_lines.append("<redacted>")
            continue

        match = re.search(r"^(\s*url\s*=\s*)(\S+)(\s*)$", line)
        if match:
            prefix, url, suffix = match.groups()
            url_match = _HTTP_URL_WITH_USERINFO.match(url)
            if url_match:
                url = f"{url_match.group(1)}{url_match.group(3)}"
            sanitized_lines.append(f"{prefix}{url}{suffix}".rstrip())
            continue

        sanitized_lines.append(line.rstrip())

    trailing_newline = "\n" if raw.endswith("\n") else ""
    return "\n".join(sanitized_lines) + trailing_newline


def _zip_add_file(zip_file: zipfile.ZipFile, repo_root: Path, file_path: Path, arcname: str) -> None:
    try:
        if file_path.is_symlink():
            link_target = os.readlink(file_path)
            info = zipfile.ZipInfo(arcname)
            info.create_system = 3  # Unix
            info.external_attr = (0o120777 << 16)  # symlink file type + perms
            zip_file.writestr(info, link_target)
            return

        zip_file.write(file_path, arcname=arcname)
    except FileNotFoundError:
        _eprint(f"[WARN] Skipping missing file: {file_path}")


def _zip_add_git_dir(
    zip_file: zipfile.ZipFile,
    repo_root: Path,
    include_git: str,
) -> None:
    git_path = repo_root / ".git"
    if include_git == "none":
        return

    if git_path.is_file():
        _eprint(
            "[WARN] .git is a file (worktree/submodule). Including only the .git file; not the referenced gitdir."
        )
        _zip_add_file(zip_file, repo_root, git_path, ".git")
        return

    if not git_path.is_dir():
        _eprint("[WARN] No .git directory found; skipping.")
        return

    if include_git == "metadata":
        allow_roots = [
            git_path / "HEAD",
            git_path / "packed-refs",
            git_path / "refs",
            git_path / "info" / "exclude",
            git_path / "description",
            git_path / "config",
        ]
        for root in allow_roots:
            if not root.exists():
                continue
            if root.is_dir():
                for child in sorted(root.rglob("*")):
                    if child.is_dir():
                        continue
                    rel = child.relative_to(repo_root).as_posix()
                    _zip_add_file(zip_file, repo_root, child, rel)
            else:
                rel = root.relative_to(repo_root).as_posix()
                if rel == ".git/config":
                    try:
                        sanitized = _sanitize_git_config(root.read_text(errors="replace"))
                        zip_file.writestr(rel, sanitized)
                    except OSError:
                        _eprint("[WARN] Failed to read .git/config; skipping.")
                else:
                    _zip_add_file(zip_file, repo_root, root, rel)
        return

    if include_git != "full":
        raise ValueError(f"Unknown --include-git value: {include_git}")

    for child in sorted(git_path.rglob("*")):
        if child.is_dir():
            continue
        if child.name.endswith(".lock"):
            continue
        rel = child.relative_to(repo_root).as_posix()
        _zip_add_file(zip_file, repo_root, child, rel)


def _create_repo_bundle_zip(
    repo_root: Path,
    artifact_dir: Path,
    include_git: str,
    max_zip_bytes: int,
) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    zip_path = artifact_dir / "bundle.zip"

    files = _iter_repo_files_excluding_ignored(repo_root)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            if file_path.is_dir():
                continue
            try:
                file_path.relative_to(artifact_dir)
                continue
            except ValueError:
                pass
            rel = file_path.relative_to(repo_root).as_posix()
            if rel.startswith(".git/") or rel == ".git":
                continue
            _zip_add_file(zf, repo_root, file_path, rel)

        _zip_add_git_dir(zf, repo_root, include_git)

    size = zip_path.stat().st_size
    if size > max_zip_bytes:
        raise RuntimeError(
            f"Bundle zip is {size} bytes, exceeds limit {max_zip_bytes}. "
            "Use --max-zip-bytes to raise the limit or set --include-git none."
        )
    return zip_path


class OpenAIClient:
    def __init__(self, api_key: str, base_url: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        timeout_seconds: int = 60,
    ) -> tuple[int, bytes]:
        all_headers = {"Authorization": f"Bearer {self._api_key}"}
        if headers:
            all_headers.update(headers)

        req = urllib.request.Request(
            f"{self._base_url}{path}",
            data=body,
            headers=all_headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                return resp.getcode(), resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def upload_zip(self, zip_path: Path, *, purpose: str = "assistants") -> str:
        boundary = f"----codex-{uuid.uuid4().hex}"
        zip_bytes = zip_path.read_bytes()

        def part(name: str, value: str) -> bytes:
            return (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")

        file_header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{zip_path.name}"\r\n'
            "Content-Type: application/zip\r\n\r\n"
        ).encode("utf-8")
        closing = f"\r\n--{boundary}--\r\n".encode("utf-8")
        body = b"".join([part("purpose", purpose), file_header, zip_bytes, closing])

        status, resp_body = self._request(
            "POST",
            "/files",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            body=body,
            timeout_seconds=300,
        )
        if status < 200 or status >= 300:
            raise RuntimeError(f"File upload failed ({status}): {resp_body.decode('utf-8', errors='replace')}")
        data = json.loads(resp_body.decode("utf-8"))
        file_id = data.get("id")
        if not file_id:
            raise RuntimeError(f"Unexpected upload response (missing id): {data}")
        return str(file_id)

    def delete_file(self, file_id: str) -> None:
        self._request("DELETE", f"/files/{file_id}", timeout_seconds=60)

    def create_response(self, payload: dict) -> dict:
        status, resp_body = self._request(
            "POST",
            "/responses",
            headers={"Content-Type": "application/json"},
            body=json.dumps(payload).encode("utf-8"),
            timeout_seconds=300,
        )
        if status < 200 or status >= 300:
            raise RuntimeError(f"Create response failed ({status}): {resp_body.decode('utf-8', errors='replace')}")
        return json.loads(resp_body.decode("utf-8"))

    def get_response(self, response_id: str) -> dict:
        status, resp_body = self._request("GET", f"/responses/{response_id}", timeout_seconds=300)
        if status < 200 or status >= 300:
            raise RuntimeError(f"Get response failed ({status}): {resp_body.decode('utf-8', errors='replace')}")
        return json.loads(resp_body.decode("utf-8"))


def _build_review_prompt(user_message: str) -> str:
    return f"""You are reviewing a git repository provided as a zip file attachment.

Tasks:
1) Read and understand the repository from the attached zip.
2) Provide actionable feedback (prioritized, concise).
3) Provide ONE unified diff patch suitable for `git apply` that implements the most valuable improvements.
   - Use paths relative to repo root.
   - Do NOT include changes under `.git/`.
4) Provide a short list of post-apply steps (commands/tests to run).

Output format (strict):
- A section titled: Feedback
- A section titled: Patch (use a single ```diff fenced block)
- A section titled: Post-apply steps

User request:
{user_message}
"""


def _manual_instructions(
    *,
    bundle_zip: Path,
    prompt_path: Path,
    response_path: Path,
) -> str:
    return "\n".join(
        [
            "",
            "Manual UI review mode (no API call).",
            "",
            "1) Open ChatGPT (web or desktop).",
            "2) Select the desired model/mode (e.g., GPT-5.2 Pro Thinking).",
            f"3) Upload this file: {bundle_zip}",
            f"4) Paste the prompt from: {prompt_path}",
            "5) Wait for the assistant to respond.",
            "",
            "Then save the ENTIRE response (including the ```diff fenced block) to:",
            f"  {response_path}",
            "",
            "Tip (paste into a file from the terminal):",
            f"  cat > {response_path}",
            "  # paste response, then press Ctrl-D",
            "",
            f"This script will keep waiting and will continue automatically once {response_path} contains a diff.",
            "",
        ]
    )


def _wait_for_manual_response(
    *,
    response_path: Path,
    poll_interval_seconds: int,
    timeout_minutes: int,
) -> str:
    deadline = time.time() + (timeout_minutes * 60)
    last_seen_digest: str | None = None

    while True:
        if time.time() > deadline:
            raise RuntimeError(f"Timed out waiting for manual response at: {response_path}")

        if response_path.exists() and response_path.is_file():
            try:
                text = response_path.read_text(errors="replace")
            except OSError:
                time.sleep(max(1, poll_interval_seconds))
                continue

            digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
            if last_seen_digest != digest:
                last_seen_digest = digest
                if _extract_patch(text):
                    return text
                if text.strip():
                    _eprint(
                        "[WARN] Response detected but no ```diff fenced patch found yet. "
                        "Update the response file with a unified diff in a ```diff block."
                    )

        time.sleep(max(1, poll_interval_seconds))


def _read_manual_response_from_stdin() -> str:
    _eprint("")
    _eprint("Paste the full model response now, then press Ctrl-D to finish.")
    try:
        return sys.stdin.read()
    except KeyboardInterrupt:
        raise RuntimeError("Canceled while waiting for manual stdin input.") from None


def _extract_output_text(response_json: dict) -> str:
    output_text = response_json.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    texts: list[str] = []
    for item in response_json.get("output", []) or []:
        for content in item.get("content", []) or []:
            content_type = content.get("type")
            if content_type not in {"output_text", "text"}:
                continue

            text_field = content.get("text")
            if isinstance(text_field, str):
                texts.append(text_field)
            elif isinstance(text_field, dict):
                value = text_field.get("value")
                if isinstance(value, str):
                    texts.append(value)

    return "\n".join(texts).strip()


_DIFF_FENCE = re.compile(r"```diff\s*(.*?)\s*```", re.DOTALL)


def _extract_patch(text: str) -> str | None:
    match = _DIFF_FENCE.search(text)
    if match:
        return match.group(1).strip() + "\n"

    idx = text.find("diff --git ")
    if idx != -1:
        return text[idx:].strip() + "\n"

    return None


def _extract_post_apply_steps(text: str) -> str | None:
    lines = text.splitlines()
    start_idx: int | None = None
    for i, line in enumerate(lines):
        if re.match(r"^\s*#+\s*Post-apply steps\s*$", line, re.IGNORECASE) or re.match(
            r"^\s*Post-apply steps\s*:?\s*$",
            line,
            re.IGNORECASE,
        ):
            start_idx = i + 1
            break

    if start_idx is None:
        return None

    collected: list[str] = []
    for line in lines[start_idx:]:
        if re.match(r"^\s*#+\s*\S+", line):
            break
        collected.append(line)

    steps = "\n".join(collected).strip()
    return steps if steps else None


def _diff_touches_git_dir(diff_text: str) -> bool:
    def is_git_dir_path(path: str) -> bool:
        return path == ".git" or path.startswith(".git/")

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                a_path = parts[2]
                b_path = parts[3]
                if a_path.startswith("a/"):
                    a_path = a_path[2:]
                if b_path.startswith("b/"):
                    b_path = b_path[2:]
                if is_git_dir_path(a_path) or is_git_dir_path(b_path):
                    return True
            continue

        if line.startswith("--- ") or line.startswith("+++ "):
            parts = line.split()
            if len(parts) >= 2:
                path = parts[1]
                if path == "/dev/null":
                    continue
                if path.startswith("a/") or path.startswith("b/"):
                    path = path[2:]
                if is_git_dir_path(path):
                    return True
    return False


def _apply_patch(repo_root: Path, patch_path: Path) -> None:
    cmd = ["git", "-C", str(repo_root), "apply", "--whitespace=fix", str(patch_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return

    cmd_3way = ["git", "-C", str(repo_root), "apply", "--3way", "--whitespace=fix", str(patch_path)]
    proc_3way = subprocess.run(cmd_3way, capture_output=True, text=True)
    if proc_3way.returncode == 0:
        return

    raise RuntimeError(
        "Failed to apply patch.\n"
        f"git apply error:\n{proc.stderr}\n"
        f"git apply --3way error:\n{proc_3way.stderr}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bundle a git repo (excluding ignored files), submit to OpenAI API for review+patch, and apply.",
    )
    parser.add_argument("--repo", default=".", help="Path to git repo (default: .)")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", ""), help="OpenAI model ID (or set OPENAI_MODEL)")
    parser.add_argument(
        "--message",
        default="Review this repository and propose a focused patch improving correctness, security, and maintainability.",
        help="Additional request context sent to the model.",
    )
    parser.add_argument(
        "--include-git",
        choices=["none", "metadata", "full"],
        default="metadata",
        help="Include .git (default: metadata).",
    )
    parser.add_argument(
        "--artifact-dir",
        default="",
        help=f"Where to write artifacts (default: <repo>/{DEFAULT_ARTIFACT_DIRNAME})",
    )
    parser.add_argument(
        "--max-zip-bytes",
        type=int,
        default=DEFAULT_MAX_ZIP_BYTES,
        help=f"Abort if bundle.zip exceeds this size (default: {DEFAULT_MAX_ZIP_BYTES}).",
    )
    parser.add_argument("--bundle-only", action="store_true", help="Only create bundle.zip and exit.")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Do not call the API. Print ChatGPT UI instructions and wait for a human-provided response.",
    )
    parser.add_argument(
        "--manual-input",
        choices=["file", "stdin"],
        default="file",
        help="In --manual mode, wait for a response file or read the response from stdin (default: file).",
    )
    parser.add_argument(
        "--manual-response-path",
        default="",
        help="In --manual --manual-input file, where the human will save the model response "
        "(default: <artifact-dir>/response.md).",
    )
    parser.add_argument("--no-background", action="store_true", help="Use a single synchronous request (more timeout-prone).")
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help=f"Polling interval when background is enabled (default: {DEFAULT_POLL_INTERVAL_SECONDS}).",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=int,
        default=DEFAULT_TIMEOUT_MINUTES,
        help=f"Stop polling after this many minutes (default: {DEFAULT_TIMEOUT_MINUTES}).",
    )
    parser.add_argument("--no-apply", action="store_true", help="Do not apply the patch; only save it.")
    parser.add_argument(
        "--allow-git-dir-changes",
        action="store_true",
        help="Allow diffs that touch .git/** (unsafe; default refuses).",
    )
    parser.add_argument("--no-cleanup", action="store_true", help="Do not delete uploaded files after completion.")
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL), help="OpenAI API base URL.")

    args = parser.parse_args()

    repo_root = _git_repo_root(Path(args.repo).resolve())
    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        if not artifact_dir.is_absolute():
            artifact_dir = repo_root / artifact_dir
    else:
        artifact_dir = repo_root / DEFAULT_ARTIFACT_DIRNAME
    artifact_dir = artifact_dir.resolve()

    bundle_zip = _create_repo_bundle_zip(
        repo_root=repo_root,
        artifact_dir=artifact_dir,
        include_git=args.include_git,
        max_zip_bytes=args.max_zip_bytes,
    )
    _eprint(f"[OK] Created bundle: {bundle_zip} ({bundle_zip.stat().st_size} bytes)")

    if args.bundle_only:
        print(f"Bundle:    {bundle_zip}")
        print(f"Artifacts: {artifact_dir}")
        return 0

    if args.manual:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = artifact_dir / "prompt.md"
        prompt_path.write_text(_build_review_prompt(args.message))

        if args.manual_response_path:
            response_path = Path(args.manual_response_path)
            if not response_path.is_absolute():
                response_path = repo_root / response_path
        else:
            response_path = artifact_dir / "response.md"
        response_path = response_path.resolve()
        response_path.parent.mkdir(parents=True, exist_ok=True)
        if not response_path.exists():
            response_path.write_text("")

        print(_manual_instructions(bundle_zip=bundle_zip, prompt_path=prompt_path, response_path=response_path))
        _eprint(f"[INFO] Waiting for response... (timeout={args.timeout_minutes} minutes)")

        if args.manual_input == "stdin":
            text = _read_manual_response_from_stdin()
            (artifact_dir / "response.md").write_text(text)
        else:
            text = _wait_for_manual_response(
                response_path=response_path,
                poll_interval_seconds=args.poll_interval_seconds,
                timeout_minutes=args.timeout_minutes,
            )
            if response_path != (artifact_dir / "response.md"):
                (artifact_dir / "response.md").write_text(text)

        patch = _extract_patch(text)
        if not patch:
            raise RuntimeError("No ```diff fenced patch found in the provided response.")

        if not args.allow_git_dir_changes and _diff_touches_git_dir(patch):
            raise RuntimeError("Refusing to apply patch that touches .git/** (use --allow-git-dir-changes to override).")

        patch_path = artifact_dir / "patch.diff"
        patch_path.write_text(patch)
        _eprint(f"[OK] Saved patch: {patch_path}")

        if not args.no_apply:
            _apply_patch(repo_root, patch_path)
            _eprint("[OK] Patch applied.")

        print(f"Artifacts: {artifact_dir}")
        print(f"Response:  {artifact_dir / 'response.md'}")
        print(f"Patch:     {patch_path}")
        steps = _extract_post_apply_steps(text)
        if steps:
            print("\nPost-apply steps (from model):")
            print(steps)
        return 0

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        _eprint("[ERROR] OPENAI_API_KEY is not set.")
        return 2

    if not args.model:
        _eprint("[ERROR] --model is required (or set OPENAI_MODEL).")
        return 2

    client = OpenAIClient(api_key=api_key, base_url=args.base_url)

    file_id = client.upload_zip(bundle_zip)
    try:
        _eprint(f"[OK] Uploaded bundle (file_id={file_id})")

        prompt = _build_review_prompt(args.message)
        payload = {
            "model": args.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_file", "file_id": file_id},
                    ],
                }
            ],
            "tools": [{"type": "code_interpreter"}],
            "temperature": 0,
        }

        payload["background"] = not args.no_background

        created = client.create_response(payload)
        response_id = created.get("id")
        if not response_id:
            raise RuntimeError(f"Unexpected create response payload (missing id): {created}")
        _eprint(f"[OK] Created response (id={response_id})")

        response_json = created
        if not args.no_background:
            deadline = time.time() + (args.timeout_minutes * 60)
            while True:
                status = response_json.get("status")
                if status in {"completed", "failed", "canceled"}:
                    break
                if time.time() > deadline:
                    raise RuntimeError(
                        f"Timed out waiting for response after {args.timeout_minutes} minutes. "
                        f"Response id: {response_id}"
                    )
                _eprint(f"[INFO] Waiting... status={status!r}")
                time.sleep(max(1, args.poll_interval_seconds))
                response_json = client.get_response(str(response_id))
    finally:
        if not args.no_cleanup:
            client.delete_file(file_id)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "response.json").write_text(json.dumps(response_json, indent=2, sort_keys=True))

    text = _extract_output_text(response_json)
    if not text:
        raise RuntimeError("No output text found in response.")

    (artifact_dir / "response.md").write_text(text)
    _eprint(f"[OK] Saved response: {artifact_dir / 'response.md'}")

    patch = _extract_patch(text)
    if not patch:
        raise RuntimeError("No ```diff fenced patch found in response.")

    if not args.allow_git_dir_changes and _diff_touches_git_dir(patch):
        raise RuntimeError("Refusing to apply patch that touches .git/** (use --allow-git-dir-changes to override).")

    patch_path = artifact_dir / "patch.diff"
    patch_path.write_text(patch)
    _eprint(f"[OK] Saved patch: {patch_path}")

    if not args.no_apply:
        _apply_patch(repo_root, patch_path)
        _eprint("[OK] Patch applied.")

    print(f"Artifacts: {artifact_dir}")
    print(f"Response:  {artifact_dir / 'response.md'}")
    print(f"Patch:     {patch_path}")
    steps = _extract_post_apply_steps(text)
    if steps:
        print("\nPost-apply steps (from model):")
        print(steps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
