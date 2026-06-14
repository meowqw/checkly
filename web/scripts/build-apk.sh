#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# JDK 17 для Gradle (Homebrew на Apple Silicon / Intel)
if [[ -z "${JAVA_HOME:-}" ]]; then
  if /usr/libexec/java_home -v 17 &>/dev/null; then
    export JAVA_HOME="$(/usr/libexec/java_home -v 17)"
  elif [[ -d "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home" ]]; then
    export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
  elif [[ -d "/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home" ]]; then
    export JAVA_HOME="/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
  else
    echo "JDK 17 не найден. Установите: brew install openjdk@17"
    exit 1
  fi
fi
export PATH="$JAVA_HOME/bin:$PATH"

echo "Using JAVA_HOME=$JAVA_HOME"
java -version

if [[ ! -f "$ROOT/.env.production.local" ]]; then
  echo "Создайте $ROOT/.env.production.local с VITE_API_URL (см. .env.android.example)"
  exit 1
fi

echo "API URL для сборки: $(grep -v '^#' "$ROOT/.env.production.local" | grep VITE_API_URL || true)"

bash "$ROOT/scripts/apply-android-icon.sh" 2>/dev/null || true

npm run cap:sync
cd android

# Повреждённый кэш Gradle (bcprov-jdk18on) — частая причина Failed to create Jar file
if [[ -d "$HOME/.gradle/caches/jars-9" ]]; then
  find "$HOME/.gradle/caches/jars-9" -name "bcprov-jdk18on*.jar*" -delete 2>/dev/null || true
fi

./gradlew assembleDebug --no-daemon

APK="app/build/outputs/apk/debug/app-debug.apk"
OUT="$ROOT/android/app/build/outputs/apk/debug/checkly-alfa.apk"
if [[ -f "$APK" ]]; then
  cp "$APK" "$OUT"
  echo ""
  echo "✅ APK: $OUT"
  echo "   API: $(grep VITE_API_URL "$ROOT/.env.production.local" 2>/dev/null || echo 'задайте VITE_API_URL в .env.production.local')"
else
  echo "Сборка завершилась, но APK не найден по пути $APK"
  exit 1
fi
