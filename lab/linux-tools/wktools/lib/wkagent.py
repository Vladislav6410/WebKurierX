import argparse, json, os, re, subprocess, time
from pathlib import Path

CFG = "/opt/wktools/conf/wkagent.json"

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def load_env_file(p):
    env = {}
    if not os.path.exists(p):
        return env
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k,v=line.split("=",1)
            env[k.strip()] = v.strip()
    return env

def run(cmd, cwd, env=None, timeout=600):
    """Run shell command; return (rc, stdout, stderr)."""
    p = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return p.returncode, p.stdout, p.stderr

def now():
    return time.strftime("%Y-%m-%d_%H-%M-%S")

def write_report(report_dir, name, content):
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    path = Path(report_dir) / name
    path.write_text(content, encoding="utf-8")
    return str(path)

def git_is_repo(path):
    return (Path(path) / ".git").exists()

def git_status(path):
    rc, out, err = run("git status --porcelain", cwd=path)
    if rc != 0:
        return False, f"git status failed: {err.strip()}"
    return True, out.strip()

def scan_forbidden(repo_path, patterns):
    """
    Scan tracked files (fast) + also scan working tree files excluding .git.
    We keep it simple and safe.
    """
    bad_hits = []
    # limit size per file (prevent scanning huge binaries)
    max_bytes = 800_000

    for p in Path(repo_path).rglob("*"):
        if ".git" in p.parts:
            continue
        if p.is_dir():
            continue
        try:
            if p.stat().st_size > max_bytes:
                continue
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pat in patterns:
            if pat in txt:
                bad_hits.append(f"{p}: contains '{pat}'")
    return bad_hits

def ensure_codex_present():
    rc, out, err = run("codex --version", cwd=".")
    if rc != 0:
        return False, "Codex CLI not found. Install: sudo npm i -g @openai/codex"
    return True, out.strip()

def build_fix_prompt(report_text, repo_path):
    """
    This is what we'll send to Codex via wk (so Codex edits files in workspace).
    """
    return f"""
You are WebKurier CodeFixer.

Goal:
Fix issues reported by wkagent for repository at:
{repo_path}

Rules:
- Do NOT include secrets or API keys.
- Keep changes minimal and safe.
- If tests/linters are missing, add lightweight placeholders and explain in comments.

wkagent report:
{report_text}

Deliver:
- Apply changes to files in the workspace so they can be reviewed and copied back.
"""

def main():
    ap = argparse.ArgumentParser(description="wkagent — repo supervisor (check/fix/report)")
    ap.add_argument("cmd", choices=["check","fix"], help="check or fix repo")
    ap.add_argument("--repo", default=".", help="Path to repo to check")
    ap.add_argument("--workspace", default=None, help="Workspace path (default from config)")
    ap.add_argument("--report", default=None, help="Optional report file path")
    ap.add_argument("--auto-apply", action="store_true", help="(optional) apply workspace changes back to repo (advanced)")
    args = ap.parse_args()

    cfg = load_json(CFG)
    repo_path = str(Path(args.repo).resolve())

    workspace = args.workspace or cfg.get("workspace", "/opt/wktools/workspace")
    workspace = str(Path(workspace).resolve())

    report_dir = cfg.get("report_dir", "/opt/wktools/logs/reports")
    log_file = cfg.get("log_file", "/opt/wktools/logs/wkagent.log")

    Path(workspace).mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append(f"wkagent cmd={args.cmd}")
    lines.append(f"repo={repo_path}")
    lines.append(f"workspace={workspace}")
    lines.append("")

    # Basic repo checks
    if cfg.get("checks", {}).get("git_status_clean", True):
        if git_is_repo(repo_path):
            ok, status = git_status(repo_path)
            if ok and status:
                lines.append("⚠️ Git working tree is NOT clean:")
                lines.append(status)
                lines.append("")
            elif ok:
                lines.append("✅ Git working tree clean")
                lines.append("")
            else:
                lines.append("⚠️ " + status)
                lines.append("")
        else:
            lines.append("⚠️ Not a git repo (no .git). Skipping git checks.")
            lines.append("")

    # Required files
    required = cfg.get("checks", {}).get("required_files", [])
    missing = []
    for rf in required:
        if not (Path(repo_path) / rf).exists():
            missing.append(rf)
    if missing:
        lines.append("⚠️ Missing required files:")
        for m in missing:
            lines.append(f"  - {m}")
        lines.append("")
    else:
        lines.append("✅ Required files OK")
        lines.append("")

    # Forbidden patterns scan
    forbidden = cfg.get("checks", {}).get("forbidden_patterns", [])
    if forbidden:
        hits = scan_forbidden(repo_path, forbidden)
        if hits:
            lines.append("❌ Forbidden patterns found (possible secrets leak):")
            lines.extend([f"  - {h}" for h in hits[:80]])
            if len(hits) > 80:
                lines.append(f"  ... +{len(hits)-80} more")
            lines.append("")
        else:
            lines.append("✅ No forbidden patterns found")
            lines.append("")

    # Run commands (best effort)
    cmds = cfg.get("commands", {})
    for name, cmd in cmds.items():
        if not cmd:
            continue
        rc, out, err = run(cmd, cwd=repo_path)
        if rc == 0:
            lines.append(f"✅ {name}: OK")
        else:
            lines.append(f"⚠️ {name}: FAILED/Skipped (rc={rc})")
        if out.strip():
            lines.append("--- stdout ---")
            lines.append(out.strip()[:2000])
        if err.strip():
            lines.append("--- stderr ---")
            lines.append(err.strip()[:2000])
        lines.append("")

    report_text = "\n".join(lines)
    report_path = args.report or write_report(report_dir, f"wkagent_report_{now()}.txt", report_text)

    # log
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] report={report_path} repo={repo_path}\n")

    print("=== WKAgent Report ===")
    print(report_text)
    print(f"\nReport saved: {report_path}")

    if args.cmd == "check":
        return

    # cmd == fix
    ok, codex_info = ensure_codex_present()
    if not ok:
        print("❌", codex_info)
        print("Install: sudo npm i -g @openai/codex")
        raise SystemExit(2)

    # Build prompt and call codex directly in workspace.
    # We copy repo into workspace first (so codex edits safely).
    ws_repo = Path(workspace) / Path(repo_path).name
    if ws_repo.exists():
        # keep previous, but do not delete silently; create new timestamp folder
        ws_repo = Path(workspace) / f"{Path(repo_path).name}_{now()}"
    ws_repo.mkdir(parents=True, exist_ok=True)

    # Copy repo to workspace (excluding .git)
    # Using rsync if available; fallback to cp -r.
    rc, _, _ = run("command -v rsync", cwd=".")
    if rc == 0:
        run(f'rsync -a --delete --exclude ".git" "{repo_path}/" "{str(ws_repo)}/"', cwd=".")
    else:
        run(f'cp -r "{repo_path}/." "{str(ws_repo)}/"', cwd=".")

    # Load key for codex from secrets (same as wk.py uses)
    secrets = load_env_file(cfg.get("secrets_file", "/opt/wktools/conf/secrets.env"))
    key = secrets.get("CODEX_API_KEY", "").strip()
    if not key:
        print("❌ No CODEX_API_KEY in secrets.env. Run: wksetup key")
        raise SystemExit(3)

    env = os.environ.copy()
    env["CODEX_API_KEY"] = key

    fix_prompt = build_fix_prompt(report_text, repo_path)

    # Run codex inside copied repo workspace
    print(f"\n=== Running Codex fix in workspace: {ws_repo} ===")
    p = subprocess.run(["codex", "exec", fix_prompt], cwd=str(ws_repo), env=env, text=True)
    if p.returncode != 0:
        print("❌ Codex failed.")
        raise SystemExit(p.returncode)

    print("\n✅ Fix generated in workspace.")
    print(f"Workspace repo: {ws_repo}")
    print("Next: review diff and copy/apply changes back to repo manually (safe).")

if __name__ == "__main__":
    main()