#!/usr/bin/env bash
set -e

# список модулей
MODULES=(
  "next"
  "labs"
  "vision"
  "ai-cluster"
  "quantum"
  "neuro"
  "holoshow"
  "holospace"
  "hyper"
  "fusion"
  "nova"
)

echo "Creating WebKurierX module structure..."

for m in "${MODULES[@]}"; do
  mkdir -p "$m"
  if [ ! -f "$m/README.md" ]; then
    cat > "$m/README.md" <<EOF
# WebKurierX / ${m}

This directory is part of the **WebKurierX** future-tech hub.

> Status: In development.

TODO: add specs, architecture and prototypes for the **${m}** module.
EOF
    echo "Created: $m/README.md"
  else
    echo "Skip (exists): $m/README.md"
  fi
done

echo "Done."