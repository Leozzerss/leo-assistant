#!/bin/bash
# LEO başlatıcı — macOS 26 + Homebrew Python için gerekli ortam değişkenleri
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "Önce kurulum: bash setup.sh"
  exit 1
fi

# Homebrew Python pyexpat uyumluluğu (pip/venv için)
if [ -d "/opt/homebrew/opt/expat/lib" ]; then
  export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi

source venv/bin/activate
exec python main.py
