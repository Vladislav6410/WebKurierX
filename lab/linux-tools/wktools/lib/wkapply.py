#!/usr/bin/env python3
"""
wkapply.py — Apply workspace fixes back to repo.

Usage:
  wkapply --repo ~/WebKurierX --workspace /opt/wktools/workspace/WebKurierX_DATE
  wkapply --repo . --workspace /opt/wktools/workspace/WebKurierX_DATE --dry-run
  wkapply --repo . --workspace /opt/wktools/workspace/WebKurierX_DATE --yes
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd="."):
    p = subprocess.run(
        cmd, cwd=cwd, shell=True,
        capture_output=True, text=True
    )
    return p.returncode, p.stdout, p.stderr


def get_changed_files(repo, workspace):
    rc, out, _ = run(
        f'diff -rq --exclude=".git" --exclude="__pycache__" '
        f'"{repo}/" "{workspace}/"'
    )
    files = []
    for line in out.strip().splitlines():
        if line.startswith("Files ") and "differ" in line:
            parts = line.split(" and ")
            ws_file = parts[1].replace(" differ", "").strip()
            files.append(ws_file)
        elif line.startswith("Only in " + str(workspace)):
            name = line.split(": ")[-1].strip()
            folder = line.split(":")[0].replace("Only in ", "").strip()
            files.append(str(Path(folder) / name))
    return files


def show_full_diff(repo, workspace):
    rc, out, _ = run(
        f'diff -ru --exclude=".git" --exclude="__pycache__" '
        f'"{repo}/" "{workspace}/"'
    )
    if not out.strip():
        return False
    lines = out.strip().splitlines()
    for l in lines[:100]:
        print(l)
    if len(lines) > 100:
        print(f"... +{len(lines)-100} строк")
    return True


def apply_file(ws_file, repo, workspace):
    rel = Path(ws_file).relative_to(workspace)
    dest = Path(repo) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    rc, _, err = run(f'cp -f "{ws_file}" "{dest}"')
    if rc == 0:
        print(f"  ✅ {rel}")
    else:
        print(f"  ❌ {rel}: {err.strip()}")


def main():
    ap = argparse.ArgumentParser(
        description="wkapply — apply workspace fixes to repo"
    )
    ap.add_argument("--repo", required=True, help="Путь к репозиторию")
    ap.add_argument("--workspace", required=True, help="Путь к workspace")
    ap.add_argument("--dry-run", action="store_true",
                    help="Только показать diff, не применять")
    ap.add_argument("--yes", action="store_true",
                    help="Применить без подтверждения")
    args = ap.parse_args()

    repo = str(Path(args.repo).resolve())
    workspace = str(Path(args.workspace).resolve())

    if not Path(repo).exists():
        print(f"❌ Репо не найдено: {repo}")
        sys.exit(1)
    if not Path(workspace).exists():
        print(f"❌ Workspace не найден: {workspace}")
        sys.exit(1)

    print(f"Репо:      {repo}")
    print(f"Workspace: {workspace}")
    print()

    print("=== DIFF ===")
    has_diff = show_full_diff(repo, workspace)

    if not has_diff:
        print("✅ Различий нет — workspace идентичен репо")
        sys.exit(0)

    print()

    if args.dry_run:
        print("-- dry-run: изменения не применены --")
        sys.exit(0)

    changed = get_changed_files(repo, workspace)
    if not changed:
        sys.exit(0)

    print(f"Изменено файлов: {len(changed)}")
    for f in changed:
        try:
            rel = Path(f).relative_to(workspace)
        except ValueError:
            rel = f
        print(f"  • {rel}")

    print()
    if not args.yes:
        answer = input("Применить изменения? [y/N]: ").strip().lower()
        if answer != "y":
            print("Отменено.")
            sys.exit(0)

    print("\n▶ Применяю...")
    for f in changed:
        apply_file(f, repo, workspace)

    print("\n✅ Готово! Закоммить:")
    print(f"  cd {repo}")
    print(f"  git add -A")
    print(f"  git diff --cached")
    print(f"  git commit -m 'fix: wkagent apply'")
    print(f"  git push")


if __name__ == "__main__":
    main()
