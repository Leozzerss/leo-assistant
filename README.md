# LEO — Personal AI Assistant

macOS masaüstü sesli asistan + tarayıcıdan erişilebilir web sürümü.

**Telif:** Tüm haklar sahibine aittir. Bkz. [COPYRIGHT](COPYRIGHT).

**Varsayılan konum:** Lezhë, Albania (Europe/Tirane)

---

## İki kullanım modu

| Mod | Nerede çalışır | Özellikler |
|-----|----------------|------------|
| **Masaüstü (Mac)** | Sadece macOS | Sesli komut, takvim, WhatsApp, ekran analizi, uygulama açma — **tam özellik** |
| **Web (Online)** | Herhangi bir tarayıcı | Sohbet, hava durumu, genel AI görevleri |

> Web sürümü macOS'a özel araçları (takvim, WhatsApp, uygulama açma vb.) çalıştıramaz. Tam özellik için Mac uygulamasını kullanın.

---

## 1) Mac masaüstü kurulumu

```bash
cd jarvis
bash setup.sh
bash start.sh
```

Mac kurulumu `requirements-desktop.txt` kullanır (mikrofon dahil):

```bash
pip install -r requirements-desktop.txt
```

---

## 2) Web sürümü — yerel test

```bash
cd jarvis
source venv/bin/activate
export GEMINI_API_KEY="your-key-here"
bash start-web.sh
```

Tarayıcıda: http://localhost:8000

---

## 3) GitHub'a yükleme

```bash
cd jarvis
git init
git add .
git commit -m "Initial commit: LEO assistant"
```

GitHub'da yeni repo oluşturun (ör. `leo-assistant`), sonra:

```bash
git remote add origin https://github.com/KULLANICI_ADINIZ/leo-assistant.git
git branch -M main
git push -u origin main
```

**Önemli:** `config/api_keys.json` ve `venv/` asla commit edilmemeli (.gitignore'da).

---

## 4) Online yayınlama (Render — ücretsiz)

> **Dikkat:** Render'da **Static Site değil**, **Web Service** seçin. Static Site `pyaudio` hatası verir.

### Yöntem A — Docker (önerilen)

1. https://render.com → GitHub ile giriş
2. **New → Blueprint** → repo: `leo-assistant`
3. Ortam değişkeni: `GEMINI_API_KEY` = API anahtarınız
4. Deploy → URL: `https://leo-assistant-xxxx.onrender.com`

`render.yaml` ve `Dockerfile` web için `requirements-web.txt` kullanır (pyaudio yok).

### Yöntem B — Python Web Service (Docker olmadan)

- **Build Command:** `pip install -r requirements-web.txt`
- **Start Command:** `python -m web.server`
- **Environment:** `GEMINI_API_KEY`, `LEO_WEATHER_LOCATION=Lezhë, Albania`

### Docker yerel test

```bash
docker build -t leo-web .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key leo-web
```

---

## Yapılandırma

`config/api_keys.example.json` dosyasını `config/api_keys.json` olarak kopyalayın:

```json
{
  "gemini_api_key": "",
  "voice": "Charon",
  "location": "Lezhë",
  "country": "Albania",
  "timezone": "Europe/Tirane"
}
```

Web/cloud ortamında API anahtarı `GEMINI_API_KEY` ortam değişkeni ile de verilebilir.

---

## Kullanım

**Masaüstü:** Yazı kutusuna yazın veya sesli komut verin · F4/⌘M sustur · F5 duraklat

**Web:** Mesaj yazıp Gönder · Hava durumu paneli otomatik yüklenir

---

## Gereksinimler

- macOS (masaüstü için)
- Python 3.13+ (önerilir)
- Homebrew, PortAudio (mikrofon)
- Gemini API anahtarı
