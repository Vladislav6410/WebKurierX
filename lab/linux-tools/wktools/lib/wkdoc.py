import argparse
import os
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


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


def sh(cmd: str, timeout=30):
    p = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def check_cmd(name: str, version_cmd: str):
    rc, out, err = sh(f"command -v {name} >/dev/null 2>&1 && {version_cmd} || true")
    if out:
        return True, out
    return False, err or f"{name}: NOT FOUND"


def dns_check(host: str):
    try:
        ips = socket.gethostbyname_ex(host)[2]
        return True, ", ".join(ips) if ips else "no ip"
    except Exception as e:
        return False, str(e)


def http_get(url: str, timeout=15):
    try:
        req = Request(url, headers={"User-Agent": "wkdoc/1.0"})
        with urlopen(req, timeout=timeout) as r:
            return True, f"HTTP {r.status}"
    except HTTPError as e:
        return False, f"HTTPError {e.code}"
    except URLError as e:
        return False, f"URLError {e}"
    except Exception as e:
        return False, str(e)


def token_test():
    secrets = load_env_file(SECRETS)
    key = (secrets.get("CODEX_API_KEY") or "").strip()
    if not key:
        return False, "No CODEX_API_KEY in secrets.env (run: wksetup key)"
    # We can't safely call external API here without knowing provider settings,
    # so we only validate presence + basic format not empty.
    if len(key) < 10:
        return False, "CODEX_API_KEY looks too short"
    return True, "CODEX_API_KEY present (length OK)"


def main():
    ap = argparse.ArgumentParser(description="wkdoc — diagnostics")
    ap.add_argument("--dns", default="github.com", help="DNS host to resolve (default: github.com)")
    ap.add_argument("--http", default="https://github.com", help="HTTP URL to test (default: https://github.com)")
    ap.add_argument("--token-test", action="store_true", help="Check that CODEX_API_KEY is present")
    ap.add_argument("--full", action="store_true", help="Run full diagnostics")
    args = ap.parse_args()

    full = args.full or args.token_test

    print("== wkdoc ==")
    print("time:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("user:", os.getenv("USER", "?"))
    print("cwd :", os.getcwd())
    print("------")

    # Toolchain checks
    for name, cmd in [
        ("python3", "python3 --version"),
        ("node", "node --version"),
        ("npm", "npm --version"),
        ("git", "git --version"),
        ("rsync", "rsync --version | head -n 1"),
        ("tar", "tar --version | head -n 1"),
        ("codex", "codex --version"),
    ]:
        ok, info = check_cmd(name, cmd)
        print(("✅" if ok else "⚠️"), f"{name}: {info}")

    print("------")

    # DNS
    ok, info = dns_check(args.dns)
    print(("✅" if ok else "❌"), f"DNS {args.dns}: {info}")

    # HTTP
    ok, info = http_get(args.http)
    print(("✅" if ok else "❌"), f"HTTP {args.http}: {info}")

    # Token
    if full:
        ok, info = token_test()
        print(("✅" if ok else "❌"), f"TOKEN: {info}")

    print("------")
    print("Installed /opt/wktools:")
    rc, out, err = sh("ls -la /opt/wktools 2>/dev/null || true")
    if out:
        print(out)
    else:
        print("/opt/wktools not installed (run: wksetup install)")

    # Exit code: if any critical checks fail in full mode, return non-zero
    if full:
        # minimal: token must be present if full mode used
        ok, _ = token_test()
        if not ok:
            sys.exit(2)


if __name__ == "__main__":
    main()