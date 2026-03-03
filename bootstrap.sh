#!/usr/bin/env bash
set -e

BASE="lab/linux-tools/wktools"

echo "== WebKurierX bootstrap =="

mkdir -p $BASE/{bin,conf,lib,scripts,logs}

########################################
# .gitignore
########################################
cat > $BASE/.gitignore <<'EOF'
conf/secrets.env
logs/
workspace/
__pycache__/
*.pyc
.venv/
EOF

########################################
# secrets example
########################################
cat > $BASE/conf/secrets.env.example <<'EOF'
CODEX_API_KEY=sk-PASTE-YOUR-KEY-HERE
EOF

########################################
# wk.json
########################################
cat > $BASE/conf/wk.json <<'EOF'
{
  "workdir": "/opt/wktools/workspace",
  "codex_model": "",
  "max_prompt_len": 12000,
  "log_file": "/opt/wktools/logs/wk.log",
  "secrets_file": "/opt/wktools/conf/secrets.env"
}
EOF

########################################
# wkdoc.json
########################################
cat > $BASE/conf/wkdoc.json <<'EOF'
{
  "log_file": "/opt/wktools/logs/wkdoc.log",
  "secrets_file": "/opt/wktools/conf/secrets.env",
  "checks": {
    "dns": ["api.openai.com"],
    "http": [
      { "name": "OpenAI Models", "url": "https://api.openai.com/v1/models", "timeout_sec": 10 }
    ]
  }
}
EOF

########################################
# wk launcher
########################################
cat > $BASE/bin/wk <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
PROMPT="${*:-}"
if [[ -z "$PROMPT" ]]; then
  echo 'Usage: wk "<prompt>"'
  exit 1
fi
python3 /opt/wktools/lib/wk.py --prompt "$PROMPT"
EOF

########################################
# wkdoc launcher
########################################
cat > $BASE/bin/wkdoc <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
python3 /opt/wktools/lib/wkdoc.py "$@"
EOF

########################################
# wksetup
########################################
cat > $BASE/bin/wksetup <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
CMD="${1:-help}"

case "$CMD" in
  help)
    echo "wksetup install | key | status"
    ;;
  install)
    sudo bash "$(dirname "$0")/../scripts/install.sh"
    ;;
  key)
    sudo nano /opt/wktools/conf/secrets.env
    sudo chmod 600 /opt/wktools/conf/secrets.env
    ;;
  status)
    command -v codex && codex --version || echo "Codex not found"
    ;;
  *)
    echo "Unknown command"
    ;;
esac
EOF

########################################
# wk.py
########################################
cat > $BASE/lib/wk.py <<'EOF'
import argparse, json, os, subprocess
from pathlib import Path

CFG = "/opt/wktools/conf/wk.json"

def load_json(p):
    with open(p,"r") as f:
        return json.load(f)

def load_env(p):
    env={}
    with open(p) as f:
        for line in f:
            if "=" in line:
                k,v=line.strip().split("=",1)
                env[k]=v
    return env

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--prompt",required=True)
    args=ap.parse_args()

    cfg=load_json(CFG)
    Path(cfg["workdir"]).mkdir(parents=True,exist_ok=True)

    sec=load_env(cfg["secrets_file"])
    key=sec.get("CODEX_API_KEY","")
    if not key:
        raise SystemExit("No CODEX_API_KEY")

    env=os.environ.copy()
    env["CODEX_API_KEY"]=key

    p=subprocess.run(
        ["codex","exec",args.prompt],
        cwd=cfg["workdir"],
        env=env
    )

    raise SystemExit(p.returncode)

if __name__=="__main__":
    main()
EOF

########################################
# wkdoc.py
########################################
cat > $BASE/lib/wkdoc.py <<'EOF'
import json, socket, os
from urllib.request import Request, urlopen

CFG="/opt/wktools/conf/wkdoc.json"

def load(p):
    with open(p) as f:
        return json.load(f)

def dns(host):
    try:
        socket.getaddrinfo(host,None)
        print("DNS OK:",host)
    except:
        print("DNS FAIL:",host)

def main():
    cfg=load(CFG)
    for h in cfg["checks"]["dns"]:
        dns(h)

    if "--token-test" in os.sys.argv:
        sec=cfg["secrets_file"]
        if not os.path.exists(sec):
            print("No secrets.env")
            return
        key=None
        with open(sec) as f:
            for l in f:
                if "CODEX_API_KEY" in l:
                    key=l.split("=",1)[1].strip()
        if not key:
            print("No key")
            return
        try:
            req=Request("https://api.openai.com/v1/models",
                        headers={"Authorization":f"Bearer {key}"})
            with urlopen(req,timeout=10) as r:
                print("TOKEN OK:",r.status)
        except Exception as e:
            print("TOKEN FAIL:",e)

if __name__=="__main__":
    main()
EOF

########################################
# install.sh
########################################
cat > $BASE/scripts/install.sh <<'EOF'
#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sudo mkdir -p /opt/wktools/{bin,conf,lib,logs,workspace}
sudo chown -R $USER:$USER /opt/wktools

cp -f $ROOT/bin/* /opt/wktools/bin/
cp -f $ROOT/lib/* /opt/wktools/lib/
cp -f $ROOT/conf/*.json /opt/wktools/conf/

if [[ ! -f /opt/wktools/conf/secrets.env ]]; then
  cp -f $ROOT/conf/secrets.env.example /opt/wktools/conf/secrets.env
fi

chmod +x /opt/wktools/bin/*

sudo ln -sf /opt/wktools/bin/wk /usr/local/bin/wk
sudo ln -sf /opt/wktools/bin/wkdoc /usr/local/bin/wkdoc
sudo ln -sf /opt/wktools/bin/wksetup /usr/local/bin/wksetup

echo "Installed wktools"
EOF

########################################

echo "Bootstrap complete."
echo "Next steps:"
echo "git add ."
echo "git commit -m 'Add wktools lab'"
echo "git push"
echo "cd lab/linux-tools/wktools && sudo bash scripts/install.sh"