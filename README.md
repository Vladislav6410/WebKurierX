# WKAgent — WebKurier AI Engineer

Автоматическая генерация кода, анализ и исправление репозитория через ИИ.

---

## Структура файлов



lab/linux-tools/wktools/
├── bin/
│   ├── wk              # главный инструмент (запуск Codex)
│   ├── wkagent         # AI-инженер (check / fix)
│   ├── wkdoc           # документация
│   ├── wksetup         # настройка
│   └── wkapply         # применить фикс из workspace
├── conf/
│   ├── wkagent.json              # конфиг агента
│   └── secrets.env.example       # шаблон ключей (НЕ хранить ключи в git!)
├── lib/
│   ├── wk.py
│   ├── wkagent.py      # ядро агента
│   └── wkapply.py      # применение workspace → репо
├── scripts/
│   ├── bootstrap_wkagent.sh      # первичная установка
│   └── install.sh                # переустановка
└── dashboard/
└── WKAgentDashboard.jsx      # веб-дашборд (React)


---

## Установка на Ubuntu 22.04

### Шаг 1 — Клонировать репозиторий

```bash
cd ~
git clone https://github.com/VladoExport/WebKurierX.git
cd WebKurierX


Шаг 2 — Запустить bootstrap

bash lab/linux-tools/wktools/scripts/bootstrap_wkagent.sh


Что делает bootstrap:
	∙	Устанавливает Node.js 20 LTS
	∙	Устанавливает OpenAI Codex CLI
	∙	Создаёт /opt/wktools/ с нужными правами
	∙	Копирует все инструменты
	∙	Создаёт secrets.env (шаблон)
	∙	Создаёт symlinks: wk, wkagent, wksetup, wkdoc, wkapply
Шаг 3 — Добавить API ключ

wksetup key


В редакторе nano — вставь нужные ключи:

CODEX_API_KEY=sk-xxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx


Сохранить: Ctrl+O → Enter → Ctrl+X
Шаг 4 — Проверить установку

wksetup status


Использование
Анализ репозитория

cd ~/WebKurierX
wkagent check --repo .


Выдаёт отчёт:
	∙	✅ Git статус
	∙	✅ Обязательные файлы (.gitignore, README.md)
	∙	✅ Скан на утечки секретов
	∙	✅ Lint (Python, Node)
	∙	✅ Структура проекта
Исправление через ИИ

wkagent fix --repo .


Что происходит:
	1.	Агент делает отчёт
	2.	Копирует репо в /opt/wktools/workspace/
	3.	ИИ исправляет файлы в workspace (безопасно)
	4.	Ты проверяешь diff и применяешь через wkapply
Применить фикс из workspace

# dry-run — только показать diff:
wkapply --repo . --workspace /opt/wktools/workspace/WebKurierX_ДАТА --dry-run

# применить с подтверждением:
wkapply --repo . --workspace /opt/wktools/workspace/WebKurierX_ДАТА

# применить без вопросов:
wkapply --repo . --workspace /opt/wktools/workspace/WebKurierX_ДАТА --yes


Закоммить результат

cd ~/WebKurierX
git add -A
git commit -m "fix: wkagent auto-fix"
git push


Безопасность



|Файл                 |Git                 |Локально            |
|---------------------|--------------------|--------------------|
|`secrets.env`        |❌ НЕТ (в .gitignore)|✅ /opt/wktools/conf/|
|`secrets.env.example`|✅ ДА (пустой шаблон)|✅                   |
|API ключи            |❌ НИКОГДА           |✅ только secrets.env|

Команды после клонирования (чек-лист)

# 1. Установка
bash lab/linux-tools/wktools/scripts/bootstrap_wkagent.sh

# 2. Ключи
wksetup key

# 3. Статус
wksetup status

# 4. Первый анализ
cd ~/WebKurierX
wkagent check --repo .

# 5. Фикс
wkagent fix --repo .

# 6. Применить
wkapply --repo . --workspace /opt/wktools/workspace/WebKurierX_ДАТА

# 7. Коммит
git add -A && git commit -m "fix: wkagent" && git push


Поддерживаемые ИИ движки



|Движок          |Переменная          |Статус     |
|----------------|--------------------|-----------|
|OpenAI Codex    |`CODEX_API_KEY`     |✅ основной |
|Anthropic Claude|`ANTHROPIC_API_KEY` |✅ подключён|
|Grok (xAI)      |`GROK_API_KEY`      |🔜 тест     |
|DeepSeek        |`DEEPSEEK_API_KEY`  |🔜 тест     |
|Qwen (Alibaba)  |`QWEN_API_KEY`      |🔜 тест     |
|Perplexity      |`PERPLEXITY_API_KEY`|🔜 тест     |

Файлы для GitHub (WebKurierX)
Эти файлы можно коммитить:
	∙	lab/linux-tools/wktools/bin/*
	∙	lab/linux-tools/wktools/lib/*.py
	∙	lab/linux-tools/wktools/conf/wkagent.json
	∙	lab/linux-tools/wktools/conf/secrets.env.example
	∙	lab/linux-tools/wktools/scripts/*.sh
	∙	lab/linux-tools/wktools/dashboard/*.jsx
Эти файлы нельзя коммитить (уже в .gitignore):
	∙	secrets.env
	∙	workspace/
	∙	
