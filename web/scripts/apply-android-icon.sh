#!/usr/bin/env bash
# Генерирует mipmap-иконки из исходника 512×512 (sips на macOS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$ROOT/resources/checkly-icon-512.png}"

if [[ ! -f "$SRC" ]]; then
  echo "Не найден $SRC"
  exit 1
fi

RES="$ROOT/android/app/src/main/res"

apply() {
  local density="$1"
  local launcher="$2"
  local foreground="$3"
  local dir="$RES/mipmap-$density"
  sips -z "$launcher" "$launcher" "$SRC" --out "$dir/ic_launcher.png" >/dev/null
  sips -z "$launcher" "$launcher" "$SRC" --out "$dir/ic_launcher_round.png" >/dev/null
  sips -z "$foreground" "$foreground" "$SRC" --out "$dir/ic_launcher_foreground.png" >/dev/null
}

apply mdpi 48 108
apply hdpi 72 162
apply xhdpi 96 216
apply xxhdpi 144 324
apply xxxhdpi 192 432

echo "✅ Иконки обновлены из $SRC"
