#!/bin/bash

set -euo pipefail

URL="https://site.com/a_zakaz.sql"
TMP_FILE="/tmp/a_zakaz.sql"
LOG_FILE="/var/log/a_zakaz_import.log"
LOCK_FILE="/tmp/a_zakaz_import.lock"

echo "[$(date '+%F %T')] START" >> "$LOG_FILE"

# щоб скрипт не запускався одночасно двічі
if [ -f "$LOCK_FILE" ]; then
    echo "[$(date '+%F %T')] ERROR: script already running" >> "$LOG_FILE"
    exit 1
fi

trap 'rm -f "$LOCK_FILE"' EXIT
touch "$LOCK_FILE"

# скачати дамп
wget -q -O "$TMP_FILE" "$URL"

# перевірка що файл не пустий
if [ ! -s "$TMP_FILE" ]; then
    echo "[$(date '+%F %T')] ERROR: empty file" >> "$LOG_FILE"
    exit 1
fi

# перевірка що це SQL
grep -q "INSERT INTO" "$TMP_FILE" || {
    echo "[$(date '+%F %T')] ERROR: invalid SQL dump" >> "$LOG_FILE"
    exit 1
}

# імпорт
mysql < "$TMP_FILE"

echo "[$(date '+%F %T')] DONE" >> "$LOG_FILE"