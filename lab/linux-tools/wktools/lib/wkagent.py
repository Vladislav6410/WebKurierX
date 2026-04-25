#!/usr/bin/env python3
"""
wkagent.py — WebKurier AI Engineer Agent
Checks, analyzes, and fixes repositories using Codex/Claude.

Commands:
  wkagent check --repo .          # analyze repo
  wkagent fix   --repo .          # AI-powered fix in workspace
  wkagent report --repo . --out report.txt
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# ── Config ────────────────────────────────────────────────────
CFG_PATH = "/opt/wktools/conf/wkagent.json"
DEFAULT_CFG = {
    "log_file": "/opt/wktools/logs/wkagent.log",
    "report_dir": "/opt/wktools/logs/reports",
    "workspace": "/opt/wktools/workspace",
    "secrets_file": "/opt/wktools/conf/secrets.env",
    "checks": {
        "git_status_clean": True,
        "required_files": [".gitignore", "README.md"],
        "forbidden_patterns": ["sk-", "OPENAI_API_KEY=sk", "ANTHROPIC_API_KEY=sk"],
    },
    "commands": {
        "python_lint": "python3 -m compileall . -q",
        "node_lint": "[ -f package.json ] && npm test --if-present || true",
    },
}


def load_cfg():
    if os.path.exists(CFG_PATH):
        with open(CFG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CFG


def load_secrets(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def run_cmd(cmd, cwd=".", timeout=120):
    """Run shell command safely, return (rc, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd, cwd=cwd, shell=True,
            capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def now_slug():
    return time.strftime("%Y-%m-%d_%H-%M-%S")


# ── Checks ────────────────────────────────────────────────────

def check_git(repo_path):
    lines = []
    if not (Path(repo_path) / ".git").exists():
        lines.append("⚠️  Not a git repo (no .git directory)")
        return lines

    rc, out, err = run_cmd("git status --porcelain", cwd=repo_path)
    if rc != 0:
        lines.append(f"⚠️  git status failed: {err.strip()}")
    elif out.strip():
        lines.append("⚠️  Git working tree is NOT clean:")
        for l in out.strip().splitlines()[:20]:
            lines.append(f"     {l}")
    else:
        lines.append("✅ Git working tree is clean")

    rc2, branch, _ = run_cmd("git branch --show-current", cwd=repo_path)
    if rc2 == 0 and branch.strip():
        lines.append(f"   Branch: {branch.strip()}")

    return lines


def check_required_files(repo_path, required):
    lines = []
    missing = [f for f in required if not (Path(repo_path) / f).exists()]
    if missing:
        lines.append("⚠️  Missing required files:")
        for m in missing:
            lines.append(f"     - {m}")
    else:
        lines.append("✅ Required files OK: " + ", ".join(required))
    return lines


def scan_secrets(repo_path, patterns, max_bytes=500_000):
    """Scan for leaked secrets in all text files."""
    hits = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
    skip_exts = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".bin", ".zip",
                 ".tar", ".gz", ".mp4", ".mp3", ".pdf", ".woff", ".ttf"}

    for p in sorted(Path(repo_path).rglob("*")):
        if any(d in p.parts for d in skip_dirs):
            continue
        if p.suffix.lower() in skip_exts:
            continue
        if not p.is_file():
            continue
        try:
            if p.stat().st_size > max_bytes:
                continue
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pat in patterns:
            if pat in txt:
                # Find line numbers
                for i, line in enumerate(txt.splitlines(), 1):
                    if pat in line:
                        safe = re.sub(r'(sk-[A-Za-z0-9]{10})[A-Za-z0-9]+', r'\1***', line).strip()
                        hits.append(f"  {p.relative_to(repo_path)}:{i} → {safe[:80]}")
                        break
    return hits


def run_checks(repo_path, cfg):
    """Run all checks, return list of result lines."""
    checks = cfg.get("checks", {})
    lines = []
    lines.append(f"=== wkagent report | {ts()} ===")
    lines.append(f"Repository: {repo_path}")
    lines.append("")

    # Git
    if checks.get("git_status_clean", True):
        lines.append("── Git status ──")
        lines.extend(check_git(repo_path))
        lines.append("")

    # Required files
    req = checks.get("required_files", [])
    if req:
        lines.append("── Required files ──")
        lines.extend(check_required_files(repo_path, req))
        lines.append("")

    # Secrets scan
    forbidden = checks.get("forbidden_patterns", [])
    if forbidden:
        lines.append("── Secrets scan ──")
        hits = scan_secrets(repo_path, forbidden)
        if hits:
            lines.append(f"❌ POSSIBLE SECRETS FOUND ({len(hits)} hits):")
            lines.extend(hits[:50])
            if len(hits) > 50:
                lines.append(f"   ... +{len(hits)-50} more")
        else:
            lines.append("✅ No secrets/forbidden patterns detected")
        lines.append("")

    # Lint / test commands
    cmds = cfg.get("commands", {})
    if cmds:
        lines.append("── Lint & tests ──")
        for name, cmd in cmds.items():
            if not cmd:
                continue
            rc, out, err = run_cmd(cmd, cwd=repo_path)
            if rc == 0:
                lines.append(f"✅ {name}: passed")
            else:
                lines.append(f"⚠️  {name}: failed (rc={rc})")
            combined = (out + err).strip()
            if combined:
                for l in combined.splitlines()[:15]:
                    lines.append(f"   {l}")
        lines.append("")

    # Project structure overview (top 2 levels)
    lines.append("── Project structure ──")
    rc, tree_out, _ = run_cmd(
        "find . -maxdepth 2 -not -path '*/.git/*' -not -path '*/node_modules/*' "
        "-not -path '*/__pycache__/*' | sort | head -60",
        cwd=repo_path
    )
    if rc == 0 and tree_out.strip():
        for l in tree_out.strip().splitlines():
            lines.append(f"   {l}")
    lines.append("")

    return lines


# ── Fix pipeline ─────────────────────────────────────────────

def copy_repo_to_workspace(repo_path, workspace):
    """Copy repo into workspace (excluding .git), return dest path."""
    repo_name = Path(repo_path).name
    dest = Path(workspace) / f"{repo_name}_{now_slug()}"
    dest.mkdir(parents=True, exist_ok=True)

    rc, _, err = run_cmd("command -v rsync")
    if rc == 0:
        run_cmd(
            f'rsync -a --exclude ".git" --exclude "node_modules" '
            f'--exclude "__pycache__" "{repo_path}/" "{dest}/"'
        )
    else:
        run_cmd(f'cp -r "{repo_path}/." "{dest}/"')
        # Remove .git from copy
        run_cmd(f'rm -rf "{dest}/.git"')

    return str(dest)


def build_fix_prompt(report_text, repo_path):
    return (
        f"You are WebKurier CodeFixer for repository: {repo_path}\n\n"
        "RULES:\n"
        "- NEVER include secrets, API keys, passwords\n"
        "- Keep changes minimal and safe\n"
        "- Add comments in Russian for non-obvious code\n"
        "- For missing required files: create lightweight versions\n"
        "- For shell scripts: always use set -euo pipefail\n\n"
        f"REPORT:\n{report_text}\n\n"
        "Fix all issues listed in the report. Apply changes to files in the workspace."
    )


def do_fix(repo_path, workspace, cfg, report_lines):
    secrets = load_secrets(cfg.get("secrets_file", "/opt/wktools/conf/secrets.env"))
    key = secrets.get("CODEX_API_KEY", "").strip()
    if not key:
        print("❌ Нет CODEX_API_KEY в secrets.env")
        print("   Запусти: wksetup key")
        print("   Добавь: CODEX_API_KEY=sk-xxxxxxxx")
        sys.exit(3)

    print(f"\n▶ Копирую репо в workspace...")
    ws_path = copy_repo_to_workspace(repo_path, workspace)
    print(f"  Workspace: {ws_path}")

    report_text = "\n".join(report_lines)
    prompt = build_fix_prompt(report_text, repo_path)

    env = os.environ.copy()
    env["CODEX_API_KEY"] = key
    env["OPENAI_API_KEY"] = key  # Codex uses OPENAI_API_KEY

    print(f"\n▶ Запускаю Codex fix...")
    p = subprocess.run(
        ["codex", "exec", prompt],
        cwd=ws_path, env=env, text=True
    )
    if p.returncode != 0:
        print(f"❌ Codex вернул rc={p.returncode}")
        sys.exit(p.returncode)

    print(f"\n✅ Исправления сгенерированы в workspace!")
    print(f"   Папка: {ws_path}")
    print(f"\n📋 Следующий шаг — проверь diff:")
    print(f"   diff -rq --exclude='.git' {repo_path}/ {ws_path}/")
    print(f"\n   Затем скопируй нужные файлы обратно:")
    print(f"   cp {ws_path}/YOUR_FILE {repo_path}/")
    print(f"\n   Закоммить изменения:")
    print(f"   cd {repo_path} && git add -A && git commit -m 'fix: wkagent auto-fix'")


# ── Main ──────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="wkagent — WebKurier AI Engineer Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wkagent check --repo .
  wkagent check --repo ~/WebKurierX
  wkagent fix   --repo . 
  wkagent report --repo . --out /tmp/report.txt
        """
    )
    ap.add_argument("cmd", choices=["check", "fix", "report"],
                    help="check=анализ | fix=исправление | report=только отчёт")
    ap.add_argument("--repo", default=".", help="Путь к репозиторию")
    ap.add_argument("--workspace", default=None, help="Путь к workspace (default: из конфига)")
    ap.add_argument("--out", default=None, help="Куда сохранить отчёт")
    args = ap.parse_args()

    cfg = load_cfg()
    repo_path = str(Path(args.repo).resolve())
    workspace = str(Path(args.workspace or cfg.get("workspace", "/opt/wktools/workspace")).resolve())
    report_dir = cfg.get("report_dir", "/opt/wktools/logs/reports")
    log_file = cfg.get("log_file", "/opt/wktools/logs/wkagent.log")

    if not Path(repo_path).exists():
        print(f"❌ Репозиторий не найден: {repo_path}")
        sys.exit(1)

    # Run checks
    report_lines = run_checks(repo_path, cfg)

    # Print report
    for line in report_lines:
        print(line)

    # Save report
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    report_file = args.out or str(Path(report_dir) / f"wkagent_report_{now_slug()}.txt")
    Path(report_file).write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n📄 Отчёт сохранён: {report_file}")

    # Log
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts()}] cmd={args.cmd} repo={repo_path} report={report_file}\n")

    if args.cmd in ("check", "report"):
        return

    # Fix
    do_fix(repo_path, workspace, cfg, report_lines)


if __name__ == "__main__":
    main()