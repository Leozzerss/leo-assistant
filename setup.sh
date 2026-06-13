#!/bin/bash
# LEO macOS — Kurulum & Başlatma Scripti
# Çalıştır: bash setup.sh

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     L.E.O  macOS Kurulum            ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Xcode Command Line Tools kontrolü (PyAudio için zorunlu)
if ! xcode-select -p &>/dev/null; then
    echo "🔧 Xcode Command Line Tools kuruluyor (bu birkaç dakika sürebilir)..."
    xcode-select --install
    echo ""
    echo "⚠️  Açılan pencereden 'Install' butonuna tıklayın."
    echo "   Kurulum bitince bu scripti tekrar çalıştırın: bash setup.sh"
    exit 0
else
    echo "✅ Xcode Command Line Tools kurulu"
fi

# Python: macOS 26 (Tahoe) icin Homebrew 3.13+ gerekli (sistem 3.9 Tk ile coker)
if command -v brew &>/dev/null; then
    brew list expat &>/dev/null 2>&1 || brew install expat
    if ! command -v python3.13 &>/dev/null; then
        echo "📦 Python 3.13 kuruluyor (macOS 26 uyumlulugu)..."
        brew install python@3.13 python-tk@3.13
    fi
fi
if command -v python3.13 &>/dev/null; then
    PYTHON=$(command -v python3.13)
else
    PYTHON=$(which python3)
fi
VERSION=$($PYTHON --version 2>&1)
echo "✅ Python: $VERSION"

if [ -d "/opt/homebrew/opt/expat/lib" ]; then
    export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi

# PortAudio kurulumu (PyAudio için gerekli)
if ! command -v brew &>/dev/null; then
    echo ""
    echo "⚠️  Homebrew bulunamadı. Homebrew, macOS için paket yöneticisidir."
    echo "   Kurmak için terminale şunu yapıştırın:"
    echo ""
    echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo ""
    echo "   Kurulum bitince bu scripti tekrar çalıştırın: bash setup.sh"
    exit 1
fi

if ! brew list portaudio &>/dev/null 2>&1; then
    echo "📦 PortAudio kuruluyor..."
    brew install portaudio
else
    echo "✅ PortAudio zaten kurulu"
fi

# PyAudio'nun portaudio header'larını bulabilmesi için
PORTAUDIO_PREFIX=$(brew --prefix portaudio 2>/dev/null || echo "")
if [ -n "$PORTAUDIO_PREFIX" ]; then
    export CFLAGS="-I$PORTAUDIO_PREFIX/include ${CFLAGS:-}"
    export LDFLAGS="-L$PORTAUDIO_PREFIX/lib ${LDFLAGS:-}"
fi

# Grift fontlarını kur
FONT_DIR="$(dirname "$0")/Fonts"
USER_FONTS="$HOME/Library/Fonts"
if [ -d "$FONT_DIR" ]; then
    echo "🔤 Grift fontları kuruluyor..."
    cp "$FONT_DIR"/*.ttf "$USER_FONTS/"
    echo "✅ Fontlar kuruldu"
fi

# Virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment oluşturuluyor..."
    $PYTHON -m venv venv
fi

source venv/bin/activate

# API key dosyası yoksa örnek dosyadan oluştur
if [ ! -f "config/api_keys.json" ]; then
    cp config/api_keys.example.json config/api_keys.json
    echo "📝 config/api_keys.json oluşturuldu — Gemini API anahtarını buraya gir"
fi

echo "📦 Paketler yükleniyor..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "╔══════════════════════════════════════╗"
echo "║         Kurulum Tamamlandı!          ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "🚀 LEO'yu başlatmak için:"
echo "   bash start.sh"
echo "   bash start-web.sh   # web sürümü"
echo ""
echo "🎙️  Kullanım:"
echo "   • Yazı kutusuna yazıp Enter'a basın"
echo "   • F4 veya ⌘M ile mikrofonu susturun"
echo ""

# İstenirse hemen başlat
read -p "Şimdi başlatılsın mı? (e/h): " choice
if [[ "$choice" == "e" || "$choice" == "E" ]]; then
    bash start.sh
fi
