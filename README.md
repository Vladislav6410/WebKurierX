# WebKurierX — Linux Tools Laboratory

WebKurierX is the experimental Linux tools lab of the WebKurier ecosystem.

This repository is dedicated to building and testing local terminal agents.

WebKurierCore/
└── engine/
    └── agents/
        └── engineer/
            ├── engineer-agent.js
            ├── engineer-config.json
            ├── prompts/
            │   └── engineer-system.prompt.txt
            ├── ui/
            │   ├── engineer-core.html
            │   └── engineer-ui.js
            ├── api/
            │   └── engineer-api.js
            └── README.md

## Current focus

- `wk` — natural language → code generation via Codex
- `wkdoc` — system doctor (DNS, HTTP, token diagnostics)
- `wksetup` — installer and configuration tool

## Structure

All tools are located in:

lab/linux-tools/wktools

## Installation (Ubuntu 22.04)

```bash
cd lab/linux-tools/wktools
sudo bash scripts/install.sh
wksetup key
wkdoc --token-test
wk "Create hello.txt and write WK is alive"