import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


SECRETS = "/opt/wktools/conf/secrets.env"


def load_env_file(p: str) -> dict:
    env = {}
    if not os.path.exists(p):
        return env
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def sh(cmd: str, cwd=".", env=None, timeout=900):
    p = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return p.returncode, p.stdout, p.stderr


def ensure_codex():
    rc, out, err = sh("codex --version", cwd=".")
    if rc != 0:
        return False, "Codex CLI not found. Install: sudo npm i -g @openai/codex"
    return True, out.strip() or "codex OK"


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(50):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    # not a git repo; fallback to start
    return start.resolve()


def build_prompt(user_text: str, repo_path: str) -> str:
    return f"""
You are WebKurier Codex Runner.

Workspace:
Repository path: {repo_path}

Rules:
- Do NOT add or print secrets, tokens, or API keys.
- Prefer minimal, safe edits.
- If you create files, keep them small and documented.
- If you are unsure, add TODO comments.

User request:
{user_text}

Deliver:
- Apply changes directly in the repository workspace.
"""


def main():
    ap = argparse.ArgumentParser(description="wk — natural prompt -> Codex edits repo")
    ap.add_argument("text", nargs="*", help="Your instruction in plain language")
    ap.add_argument("--repo", default=None, help="Repo path (default: auto-detect from cwd)")
    ap.add_argument("--dry-run", action="store_true", help="Do not execute codex, only print prompt")
    args = ap.parse_args()

    user_text = " ".join(args.text).strip()
    if not user_text:
        print("Usage:\n  wk \"Create hello.txt and write 'WK is alive'\"")
        sys.exit(1)

    ok, info = ensure_codex()
    if not ok:
        print("❌", info)
        sys.exit(2)

    repo = Path(args.repo).resolve() if args.repo else find_repo_root(Path.cwd())
    repo_path = str(repo)

    secrets = load_env_file(SECRETS)
    key = (secrets.get("CODEX_API_KEY") or "").strip()
    if not key:
        print("❌ No CODEX_API_KEY in /opt/wktools/conf/secrets.env")
        print("Fix:\n  wksetup key")
        sys.exit(3)

    prompt = build_prompt(user_text, repo_path)

    if args.dry_run:
        print(prompt.strip())
        return

    env = os.environ.copy()
    env["CODEX_API_KEY"] = key

    print("== wk ==")
    print("repo:", repo_path)
    print("codex:", info)
    print("time:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("------")

    p = subprocess.run(
        ["codex", "exec", prompt],
        cwd=repo_path,
        env=env,
        text=True,
    )
    if p.returncode != 0:
        print("❌ Codex failed.")
        sys.exit(p.returncode)

    print("✅ Done. Review changes:")
    print(f"  cd \"{repo_path}\" && git status")
    print("Tip: if you want safe apply/rollback, use wkagent + wkapply.")


if __name__ == "__main__":
    main()