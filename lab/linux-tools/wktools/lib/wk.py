#!/usr/bin/env python3
"""
wk.py — WebKurier Codex launcher.
Loads API key from secrets.env and calls Codex CLI.

Usage:
  wk "напиши функцию hello world на Python"
  wk --doc "объясни как работает bootstrap.sh"
"""
import argparse
import os
import subprocess
import sys

SECRETS_FILE = "/opt/wktools/conf/secrets.env"


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


def main():
    ap = argparse.ArgumentParser(description="wk — WebKurier Codex launcher")
    ap.add_argument("prompt", nargs="*", help="Задача для Codex")
    ap.add_argument("--doc", action="store_true", help="Режим документации")
    ap.add_argument("--token-test", action="store_true", help="Проверить ключ")
    args = ap.parse_args()

    secrets = load_secrets(SECRETS_FILE)
    key = secrets.get("CODEX_API_KEY", "").strip()

    if not key:
        print("❌ Нет CODEX_API_KEY в secrets.env")
        print("   Запусти: wksetup key")
        sys.exit(1)

    if args.token_test:
        print("✅ CODEX_API_KEY найден:", key[:8] + "***")
        sys.exit(0)

    if not args.prompt:
        ap.print_help()
        sys.exit(0)

    prompt_text = " ".join(args.prompt)

    if args.doc:
        prompt_text = (
            "You are a documentation assistant for WebKurier project. "
            "Explain clearly in Russian:\n\n" + prompt_text
        )

    env = os.environ.copy()
    env["OPENAI_API_KEY"] = key
    env["CODEX_API_KEY"] = key

    check = subprocess.run("command -v codex", shell=True, capture_output=True)
    if check.returncode != 0:
        print("❌ Codex CLI не найден")
        print("   Установи: sudo npm install -g @openai/codex")
        sys.exit(2)

    print(f"▶ wk → Codex: {prompt_text[:80]}{'...' if len(prompt_text) > 80 else ''}")
    print()

    result = subprocess.run(["codex", "exec", prompt_text], env=env, text=True)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
