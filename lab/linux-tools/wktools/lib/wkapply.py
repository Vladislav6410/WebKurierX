import argparse, json, os, shutil, subprocess, time
from pathlib import Path

CFG = "/opt/wktools/conf/wkapply.json"

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def run(cmd, cwd=".", timeout=600):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr

def ts():
    return time.strftime("%Y-%m-%d_%H-%M-%S")

def log_line(log_file, msg):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def is_git_repo(repo):
    return (Path(repo) / ".git").exists()

def repo_name(repo):
    return Path(repo).resolve().name

def ensure_dirs(cfg):
    Path(cfg["snapshots_dir"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["archives_dir"]).mkdir(parents=True, exist_ok=True)

def snapshot_make(cfg, repo, source="manual", note=""):
    ensure_dirs(cfg)
    repo = str(Path(repo).resolve())
    name = repo_name(repo)
    snap_root = Path(cfg["snapshots_dir"]) / name
    snap_root.mkdir(parents=True, exist_ok=True)

    snap_id = f"{ts()}__src-{source}"
    snap_dir = snap_root / snap_id
    snap_dir.mkdir(parents=True, exist_ok=True)

    # copy repo excluding .git
    rc, _, _ = run("command -v rsync", cwd=".")
    if rc == 0:
        run(f'rsync -a --delete --exclude ".git" "{repo}/" "{snap_dir}/"', cwd=".")
    else:
        run(f'cp -r "{repo}/." "{snap_dir}/"', cwd=".")

    meta = {
        "repo": repo,
        "repo_name": name,
        "snapshot_id": snap_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "note": note
    }
    (snap_dir / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    log_line(cfg["log_file"], f"SNAPSHOT repo={repo} id={snap_id} source={source}")
    return str(snap_dir)

def snapshot_list(cfg, repo):
    repo = str(Path(repo).resolve())
    name = repo_name(repo)
    snap_root = Path(cfg["snapshots_dir"]) / name
    if not snap_root.exists():
        return []
    snaps = sorted([p for p in snap_root.iterdir() if p.is_dir()], reverse=True)
    return snaps

def snapshot_latest(cfg, repo):
    snaps = snapshot_list(cfg, repo)
    return snaps[0] if snaps else None

def rollback_to(cfg, repo, snap_dir):
    repo = str(Path(repo).resolve())
    snap_dir = Path(snap_dir).resolve()

    if not snap_dir.exists():
        raise SystemExit(f"Snapshot not found: {snap_dir}")

    # Safety: make pre-rollback snapshot
    pre = snapshot_make(cfg, repo, source="rollback_pre", note=f"before rollback to {snap_dir.name}")

    # restore snapshot => repo (excluding .git)
    rc, _, _ = run("command -v rsync", cwd=".")
    if rc == 0:
        run(f'rsync -a --delete --exclude ".git" "{str(snap_dir)}/" "{repo}/"', cwd=".")
        # remove meta file from repo if copied
        meta_in_repo = Path(repo) / "_meta.json"
        if meta_in_repo.exists():
            meta_in_repo.unlink()
    else:
        # fallback: delete files except .git and copy snapshot
        for p in Path(repo).iterdir():
            if p.name == ".git":
                continue
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        run(f'cp -r "{str(snap_dir)}/." "{repo}/"', cwd=".")
        meta_in_repo = Path(repo) / "_meta.json"
        if meta_in_repo.exists():
            meta_in_repo.unlink()

    log_line(cfg["log_file"], f"ROLLBACK repo={repo} to={snap_dir} pre={pre}")
    return pre

def diff_show(repo, ws_repo):
    # git diff only works in git repo; fallback to rsync dry-run list
    repo = str(Path(repo).resolve())
    ws_repo = str(Path(ws_repo).resolve())

    if is_git_repo(repo):
        # Create temporary patch by comparing working tree to workspace using git diff --no-index
        rc, out, err = run(f'git diff --no-index "{repo}" "{ws_repo}"', cwd=".")
        return rc, out, err
    else:
        rc, out, err = run(f'rsync -ain --delete "{ws_repo}/" "{repo}/" | head -n 200', cwd=".")
        return rc, out, err

def apply_workspace(cfg, repo, ws_repo, source="wkagent", note=""):
    repo = str(Path(repo).resolve())
    ws_repo = str(Path(ws_repo).resolve())

    # Snapshot BEFORE apply
    snap = snapshot_make(cfg, repo, source=f"apply_pre-{source}", note=note)

    # Apply: workspace -> repo (exclude .git and any _meta.json)
    rc, _, _ = run("command -v rsync", cwd=".")
    if rc == 0:
        run(f'rsync -a --delete --exclude ".git" --exclude "_meta.json" "{ws_repo}/" "{repo}/"', cwd=".")
    else:
        # fallback: copy over
        run(f'cp -r "{ws_repo}/." "{repo}/"', cwd=".")
        meta_in_repo = Path(repo) / "_meta.json"
        if meta_in_repo.exists():
            meta_in_repo.unlink()

    log_line(cfg["log_file"], f"APPLY repo={repo} ws={ws_repo} snap={snap} source={source}")
    return snap

def pack_old(cfg, repo, older_than_hours):
    ensure_dirs(cfg)
    repo = str(Path(repo).resolve())
    name = repo_name(repo)
    snap_root = Path(cfg["snapshots_dir"]) / name
    if not snap_root.exists():
        return []

    cutoff = time.time() - (older_than_hours * 3600)
    to_pack = []
    for snap in snap_root.iterdir():
        if not snap.is_dir():
            continue
        try:
            mtime = snap.stat().st_mtime
        except Exception:
            continue
        if mtime < cutoff:
            to_pack.append(snap)

    packed = []
    for snap in sorted(to_pack):
        archive_name = f"{name}__{snap.name}.tar.gz"
        archive_path = Path(cfg["archives_dir"]) / archive_name
        # tar snapshot folder
        rc, out, err = run(f'tar -czf "{archive_path}" -C "{snap_root}" "{snap.name}"', cwd=".")
        if rc == 0:
            # remove original snapshot dir after successful archive
            shutil.rmtree(snap)
            packed.append(str(archive_path))
            log_line(cfg["log_file"], f"PACK repo={repo} snap={snap} -> {archive_path}")
        else:
            log_line(cfg["log_file"], f"PACK_FAIL repo={repo} snap={snap} err={err.strip()[:300]}")

    return packed

def unpack_archive(cfg, archive_path):
    ensure_dirs(cfg)
    archive_path = Path(archive_path).resolve()
    if not archive_path.exists():
        raise SystemExit(f"Archive not found: {archive_path}")
    # archive name includes repo__snap.tar.gz, but we just extract into snapshots_dir
    rc, out, err = run(f'tar -xzf "{archive_path}" -C "{cfg["snapshots_dir"]}"', cwd=".")
    if rc != 0:
        raise SystemExit(f"Unpack failed: {err.strip()}")
    log_line(cfg["log_file"], f"UNPACK archive={archive_path}")
    return True

def main():
    ap = argparse.ArgumentParser(description="wkapply — snapshots + diff + apply + rollback + pack")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("snapshot", help="Create snapshot (restore point)")
    s1.add_argument("--repo", default=".", help="repo path")
    s1.add_argument("--source", default="manual", help="source label")
    s1.add_argument("--note", default="", help="note")

    s2 = sub.add_parser("list", help="List snapshots for repo")
    s2.add_argument("--repo", default=".", help="repo path")

    s3 = sub.add_parser("diff", help="Show diff between repo and workspace repo")
    s3.add_argument("--repo", default=".", help="repo path")
    s3.add_argument("--ws", required=True, help="workspace repo path")

    s4 = sub.add_parser("apply", help="Apply workspace repo to repo (with snapshot + confirmation)")
    s4.add_argument("--repo", default=".", help="repo path")
    s4.add_argument("--ws", required=True, help="workspace repo path")
    s4.add_argument("--source", default="wkagent", help="source label")
    s4.add_argument("--note", default="", help="note")
    s4.add_argument("--yes", action="store_true", help="skip confirmation")
    s4.add_argument("--dry-run", action="store_true", help="only show diff, do not apply")

    s5 = sub.add_parser("rollback", help="Rollback repo to snapshot")
    s5.add_argument("--repo", default=".", help="repo path")
    s5.add_argument("--to", default="latest", help="snapshot path or 'latest'")

    s6 = sub.add_parser("pack", help="Pack snapshots older than N hours into tar.gz and delete originals")
    s6.add_argument("--repo", default=".", help="repo path")
    s6.add_argument("--older-than-hours", type=int, default=None, help="hours (default from config)")

    s7 = sub.add_parser("unpack", help="Unpack an archive back into snapshots")
    s7.add_argument("archive", help="path to .tar.gz")

    args = ap.parse_args()
    cfg = load_json(CFG)
    ensure_dirs(cfg)

    if args.cmd == "snapshot":
        p = snapshot_make(cfg, args.repo, source=args.source, note=args.note)
        print("✅ Snapshot created:", p)
        return

    if args.cmd == "list":
        snaps = snapshot_list(cfg, args.repo)
        if not snaps:
            print("No snapshots.")
            return
        print("Snapshots:")
        for s in snaps[:200]:
            meta = s / "_meta.json"
            extra = ""
            if meta.exists():
                try:
                    m = json.loads(meta.read_text(encoding="utf-8"))
                    extra = f'  src={m.get("source","")}  note={m.get("note","")}'
                except Exception:
                    pass
            print(" -", s, extra)
        return

    if args.cmd == "diff":
        rc, out, err = diff_show(args.repo, args.ws)
        print(out if out.strip() else "(no diff output)")
        if err.strip():
            print("\n[stderr]\n", err[:2000])
        return

    if args.cmd == "apply":
        rc, out, err = diff_show(args.repo, args.ws)
        print("=== DIFF (preview) ===")
        print(out if out.strip() else "(no diff output)")
        if err.strip():
            print("\n[stderr]\n", err[:2000])

        if args.dry_run:
            print("\n✅ Dry-run only. Nothing applied.")
            return

        if not args.yes:
            ans = input("\nApply these changes? Type YES to continue: ").strip()
            if ans != "YES":
                print("Cancelled.")
                return

        snap = apply_workspace(cfg, args.repo, args.ws, source=args.source, note=args.note)
        print("✅ Applied. Pre-apply snapshot:", snap)
        return

    if args.cmd == "rollback":
        target = args.to
        if target == "latest":
            s = snapshot_latest(cfg, args.repo)
            if not s:
                raise SystemExit("No snapshots found to rollback.")
            target = str(s)
        pre = rollback_to(cfg, args.repo, target)
        print("✅ Rolled back to:", target)
        print("✅ Safety snapshot made before rollback:", pre)
        return

    if args.cmd == "pack":
        hours = args.older_than_hours or int(cfg.get("default_pack_after_hours", 24))
        packed = pack_old(cfg, args.repo, older_than_hours=hours)
        if not packed:
            print("No snapshots to pack.")
        else:
            print("✅ Packed archives:")
            for a in packed:
                print(" -", a)
        return

    if args.cmd == "unpack":
        unpack_archive(cfg, args.archive)
        print("✅ Unpacked:", args.archive)
        return

if __name__ == "__main__":
    main()