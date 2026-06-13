const sessionId = `web-${Math.random().toString(36).slice(2, 10)}`;
const messagesEl = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const statusEl = document.getElementById("status");
const weatherEl = document.getElementById("weather");
const locationEl = document.getElementById("location");
const refreshWeatherBtn = document.getElementById("refreshWeather");

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

window.leoAddMessage = addMessage;

async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    locationEl.textContent = data.location || "Lezhë, Albania";
    if (data.api_ready) {
      statusEl.textContent = data.voice_ready ? "● Online · Ses hazır" : "● Online";
      addMessage(
        data.voice_ready
          ? "LEO hazır. Yazın veya 🎙️ Sesi Aç ile konuşun."
          : "LEO hazır (API key eksik).",
        "sys"
      );
    } else {
      statusEl.textContent = "● API key eksik";
      addMessage("Sunucuda GEMINI_API_KEY ayarlanmamış.", "sys");
    }
  } catch {
    statusEl.textContent = "● Offline";
    addMessage("Sunucuya bağlanılamadı.", "sys");
  }
}

async function loadWeather() {
  weatherEl.textContent = "Yükleniyor...";
  try {
    const res = await fetch("/api/weather");
    const data = await res.json();
    weatherEl.textContent = data.summary || "Hava durumu alınamadı.";
  } catch {
    weatherEl.textContent = "Hava durumu alınamadı.";
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  addMessage(message, "user");
  const submitBtn = form.querySelector("button[type='submit']");
  submitBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "İstek başarısız");
    addMessage(data.reply, "leo");
  } catch (err) {
    addMessage(`Hata: ${err.message}`, "sys");
  } finally {
    submitBtn.disabled = false;
    input.focus();
  }
});

refreshWeatherBtn.addEventListener("click", loadWeather);
loadHealth();
loadWeather();
