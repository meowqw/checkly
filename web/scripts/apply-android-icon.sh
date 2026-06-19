#!/usr/bin/env bash
# Генерирует mipmap-иконки из исходника (сохраняет пропорции, без растягивания).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$ROOT/resources/checkly-icon-512.png}"

if [[ ! -f "$SRC" ]]; then
  echo "Не найден $SRC"
  exit 1
fi

python3 "$ROOT/scripts/generate_android_icons.py" "$SRC"
