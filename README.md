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

İlk açılışta Gemini API anahtarını girin: https://aistudio.google.com

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

1. https://render.com hesabı açın
2. **New → Blueprint** veya **Web Service**
3. GitHub reposunu bağlayın
4. Ortam değişkeni ekleyin:
   - `GEMINI_API_KEY` = Gemini API anahtarınız
   - `LEO_WEATHER_LOCATION` = `Lezhë, Albania` (isteğe bağlı)
5. Deploy tamamlanınca URL: `https://leo-web-xxxx.onrender.com`

`render.yaml` dosyası bu akış için hazırdır.

### Docker ile deploy

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
