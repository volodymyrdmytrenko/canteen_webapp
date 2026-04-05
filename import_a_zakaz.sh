#!/bin/bash

set -euo pipefail

URL="https://food.konsort.space/a_zakaz.sql"
TMP_FILE="/tmp/a_zakaz.sql"
LOG_FILE="/var/log/a_zakaz_import.log"

DB_HOST="10.0.0.217"
DB_PORT="3306"
DB_USER="canteen"
DB_PASS="GNgfvPeRNX0c5n"
DB_NAME="canteen"

echo "[$(date '+%F %T')] start import" >> "$LOG_FILE"

wget -q -O "$TMP_FILE" "$URL"

if [ ! -s "$TMP_FILE" ]; then
  echo "[$(date '+%F %T')] ERROR: file is empty" >> "$LOG_FILE"
  exit 1
fi

grep -q "INSERT INTO" "$TMP_FILE" || {
  echo "[$(date '+%F %T')] ERROR: invalid sql dump" >> "$LOG_FILE"
  exit 1
}

mysql \
  -h"$DB_HOST" \
  -P"$DB_PORT" \
  -u"$DB_USER" \
  -p"$DB_PASS" \
  "$DB_NAME" < "$TMP_FILE"

echo "[$(date '+%F %T')] import done" >> "$LOG_FILE"