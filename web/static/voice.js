const SEND_RATE = 16000;
const RECV_RATE = 24000;

let voiceWs = null;
let voiceActive = false;
let voiceMuted = false;
let micStream = null;
let micCtx = null;
let micProcessor = null;
let micSource = null;
let pcmPlayer = null;

function wsBaseUrl() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${location.host}/ws/voice`;
}

function downsample(buffer, inputRate, outputRate) {
  if (outputRate >= inputRate) return buffer;
  const ratio = inputRate / outputRate;
  const length = Math.round(buffer.length / ratio);
  const result = new Float32Array(length);
  for (let i = 0; i < length; i++) {
    result[i] = buffer[Math.floor(i * ratio)] || 0;
  }
  return result;
}

function floatTo16BitPCM(float32Array) {
  const buffer = new ArrayBuffer(float32Array.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

class PcmPlayer {
  constructor(sampleRate = RECV_RATE) {
    this.ctx = new AudioContext({ sampleRate });
    this.queue = [];
    this.playing = false;
  }

  async resume() {
    if (this.ctx.state === "suspended") await this.ctx.resume();
  }

  enqueue(arrayBuffer) {
    const int16 = new Int16Array(arrayBuffer);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;
    const audioBuffer = this.ctx.createBuffer(1, float32.length, RECV_RATE);
    audioBuffer.getChannelData(0).set(float32);
    this.queue.push(audioBuffer);
    if (!this.playing) this._playNext();
  }

  _playNext() {
    if (!this.queue.length) {
      this.playing = false;
      return;
    }
    this.playing = true;
    const buffer = this.queue.shift();
    const source = this.ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(this.ctx.destination);
    source.onended = () => this._playNext();
    source.start();
  }
}

async function startMicrophone() {
  micStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });

  micCtx = new AudioContext();
  micSource = micCtx.createMediaStreamSource(micStream);
  micProcessor = micCtx.createScriptProcessor(4096, 1, 1);
  const inputRate = micCtx.sampleRate;

  micProcessor.onaudioprocess = (event) => {
    if (!voiceActive || voiceMuted || !voiceWs || voiceWs.readyState !== WebSocket.OPEN) return;
    const input = event.inputBuffer.getChannelData(0);
    const down = downsample(input, inputRate, SEND_RATE);
    voiceWs.send(floatTo16BitPCM(down));
  };

  micSource.connect(micProcessor);
  micProcessor.connect(micCtx.destination);
}

function stopMicrophone() {
  if (micProcessor) {
    micProcessor.disconnect();
    micProcessor.onaudioprocess = null;
    micProcessor = null;
  }
  if (micSource) {
    micSource.disconnect();
    micSource = null;
  }
  if (micCtx) {
    micCtx.close();
    micCtx = null;
  }
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
}

function setVoiceState(text) {
  const el = document.getElementById("voiceState");
  if (el) el.textContent = text;
}

function handleVoiceMessage(data) {
  if (typeof data !== "string") return;
  let payload;
  try {
    payload = JSON.parse(data);
  } catch {
    return;
  }

  if (payload.type === "transcript" && window.leoAddMessage) {
    const role = payload.role === "user" ? "user" : payload.role === "leo" ? "leo" : "sys";
    window.leoAddMessage(payload.text, role);
  } else if (payload.type === "state") {
    const map = {
      connecting: "Bağlanıyor...",
      listening: "● Dinliyor",
      speaking: "● Konuşuyor",
      thinking: "● Düşünüyor",
      error: "● Hata",
    };
    setVoiceState(`Ses: ${map[payload.value] || payload.value}`);
  } else if (payload.type === "error" && window.leoAddMessage) {
    window.leoAddMessage(`Ses hatası: ${payload.message}`, "sys");
  }
}

async function connectVoice() {
  if (voiceWs && voiceWs.readyState === WebSocket.OPEN) return;

  if (!navigator.mediaDevices?.getUserMedia) {
    window.leoAddMessage?.("Tarayıcı mikrofonu desteklemiyor.", "sys");
    return;
  }

  pcmPlayer = pcmPlayer || new PcmPlayer(RECV_RATE);
  await pcmPlayer.resume();
  await startMicrophone();

  voiceWs = new WebSocket(wsBaseUrl());
  voiceWs.binaryType = "arraybuffer";

  voiceWs.onopen = () => {
    voiceActive = true;
    setVoiceState("Ses: bağlandı");
    document.getElementById("voiceToggle").textContent = "⏹ Sesi Kapat";
    document.getElementById("muteToggle").disabled = false;
  };

  voiceWs.onmessage = (event) => {
    if (event.data instanceof ArrayBuffer) {
      pcmPlayer?.enqueue(event.data);
      return;
    }
    handleVoiceMessage(event.data);
  };

  voiceWs.onclose = () => {
    voiceActive = false;
    setVoiceState("Ses: kapalı");
    document.getElementById("voiceToggle").textContent = "🎙️ Sesi Aç";
    document.getElementById("muteToggle").disabled = true;
  };

  voiceWs.onerror = () => {
    window.leoAddMessage?.("Ses bağlantısı kurulamadı.", "sys");
  };
}

function disconnectVoice() {
  voiceActive = false;
  if (voiceWs) {
    voiceWs.close();
    voiceWs = null;
  }
  stopMicrophone();
  setVoiceState("Ses: kapalı");
  document.getElementById("voiceToggle").textContent = "🎙️ Sesi Aç";
  document.getElementById("muteToggle").disabled = true;
}

function toggleMute() {
  voiceMuted = !voiceMuted;
  const btn = document.getElementById("muteToggle");
  btn.textContent = voiceMuted ? "Mikrofonu Aç" : "Mikrofonu Kapat";
  if (voiceWs?.readyState === WebSocket.OPEN) {
    voiceWs.send(JSON.stringify({ type: "mute", value: voiceMuted }));
  }
}

function initVoiceControls() {
  document.getElementById("voiceToggle")?.addEventListener("click", async () => {
    if (voiceActive) {
      disconnectVoice();
      return;
    }
    try {
      await connectVoice();
    } catch (err) {
      window.leoAddMessage?.(`Mikrofon izni gerekli: ${err.message}`, "sys");
    }
  });

  document.getElementById("muteToggle")?.addEventListener("click", toggleMute);
}

document.addEventListener("DOMContentLoaded", initVoiceControls);
