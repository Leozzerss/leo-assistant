#!/bin/bash
# LEO Web — çevrimiçi sürüm başlatıcı
cd "$(dirname "$0")"

if [ -d "/opt/homebrew/opt/expat/lib" ]; then
  export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi

if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

export PORT="${PORT:-8000}"
echo "LEO Web: http://localhost:${PORT}"
exec python -m web.server
