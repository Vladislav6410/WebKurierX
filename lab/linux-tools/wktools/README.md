# WebKurierX — wktools (Linux Tools Lab)

wktools — это набор локальных терминальных инструментов для безопасной работы с репозиториями:
- `wk` — пишешь словами → Codex CLI генерирует/правит файлы в репозитории (или через `--repo`)
- `wkdoc` — диагностика окружения (DNS/HTTP/toolchain/token presence)
- `wksetup` — установка/обновление + ввод ключа
- `wkagent` — проверка/автофикс через workspace-first (копия репозитория → Codex → diff/apply)
- `wkapply` — snapshots/diff/apply/rollback/pack/unpack

## Структура