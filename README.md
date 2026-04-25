# WKAgent — WebKurier AI Engineer

Автоматическая генерация кода, анализ и исправление репозитория через ИИ.

-----

## Структура файлов

```
lab/linux-tools/wktools/
├── bin/
│   ├── wk              # главный инструмент (запуск Codex)
│   ├── wkagent         # AI-инженер (check / fix)
│   ├── wkdoc           # документация
│   └── wksetup         # настройка
├── conf/
│   ├── wkagent.json              # конфиг агента
│   └── secrets.env.example       # шаблон ключей (НЕ хранить ключи в git!)
├── lib/
│   ├── wk.py
│   └── wkagent.py      # ядро агента
└── scripts/
    ├── bootstrap_wkagent.sh      # первичная установка
    └── install.sh                # переустановка
```

-----

## Установка на Ubuntu 22.04

### Шаг 1 — Клонировать репозиторий

```bash
cd ~
git clone https://github.com/VladoExport/WebKurierX.git
cd WebKurierX
```

### Шаг 2 — Запустить bootstrap

```bash
bash lab/linux-tools/wktools/scripts/bootstrap_wkagent.sh
```

Что делает bootstrap:

- Устанавливает Node.js 20 LTS
- Устанавливает OpenAI Codex CLI
- Создаёт `/opt/wktools/` с нужными правами
- Копирует все инструменты
- Создаёт `secrets.env` (шаблон)
- Создаёт symlinks: `wk`, `wkagent`, `wksetup`, `wkdoc`

### Шаг 3 — Добавить API ключ

```bash
wksetup key
```

В редакторе nano — вставь ключ:

```
CODEX_API_KEY=sk-xxxxxxxxxxxxxxxx
```

Сохранить: `Ctrl+O` → `Enter` → `Ctrl+X`

### Шаг 4 — Проверить установку

```bash
wksetup status
```

-----

## Использование

### Анализ репозитория

```bash
# В папке репозитория:
cd ~/WebKurierX
wkagent check --repo .

# Или указать путь явно:
wkagent check --repo ~/WebKurierX
```

Выдаёт отчёт:

- ✅ Git статус
- ✅ Обязательные файлы (.gitignore, README.md)
- ✅ Скан на утечки секретов
- ✅ Lint (Python, Node)
- ✅ Структура проекта

### Исправление через ИИ (Codex)

```bash
wkagent fix --repo .
```

Что происходит:

1. Агент делает отчёт
1. Копирует репо в `/opt/wktools/workspace/`
1. Codex исправляет файлы в workspace (безопасно)
1. Ты проверяешь diff и копируешь нужное

### Проверить diff и применить

```bash
# Посмотреть что изменилось:
diff -rq --exclude='.git' ~/WebKurierX/ /opt/wktools/workspace/WebKurierX_ДАТА/

# Скопировать конкретный файл:
cp /opt/wktools/workspace/WebKurierX_ДАТА/README.md ~/WebKurierX/

# Закоммить:
cd ~/WebKurierX
git add -A
git commit -m "fix: wkagent auto-fix"
git push
```

-----

## Безопасность

|Файл                 |Git                 |Локально            |
|---------------------|--------------------|--------------------|
|`secrets.env`        |❌ НЕТ (в .gitignore)|✅ /opt/wktools/conf/|
|`secrets.env.example`|✅ ДА (пустой шаблон)|✅                   |
|API ключи            |❌ НИКОГДА           |✅ только secrets.env|

-----

## Команды после клонирования (чек-лист)

```bash
# 1. Установка
bash lab/linux-tools/wktools/scripts/bootstrap_wkagent.sh

# 2. Ключ
wksetup key

# 3. Статус
wksetup status

# 4. Первый анализ
cd ~/WebKurierX
wkagent check --repo .

# 5. Если нужен фикс
wkagent fix --repo .
```

-----

## Поддерживаемые ИИ движки

|Движок          |Переменная         |Статус     |
|----------------|-------------------|-----------|
|OpenAI Codex    |`CODEX_API_KEY`    |✅ основной |
|Anthropic Claude|`ANTHROPIC_API_KEY`|🔜 следующий|
|Qwen            |`QWEN_API_KEY`     |🔜 тест     |

-----

## Файлы для GitHub (WebKurierX)

Эти файлы **можно** коммитить:

- `lab/linux-tools/wktools/bin/*`
- `lab/linux-tools/wktools/lib/wkagent.py`
- `lab/linux-tools/wktools/conf/wkagent.json`
- `lab/linux-tools/wktools/conf/secrets.env.example`
- `lab/linux-tools/wktools/scripts/bootstrap_wkagent.sh`

Эти файлы **нельзя** коммитить (уже в .gitignore):

- `secrets.env`
- `workspace/`
- `logs/`