from __future__ import annotations

import argparse
import array
import base64
import json
import math
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import unicodedata
import urllib.parse
import urllib.request
import wave
from collections import deque
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SERVER_URL = "http://127.0.0.1:8787"
DEFAULT_WAKE_WORD = "zeus"

ORB_SIZE = 96
WINDOW_SIZE = 176
POLL_MS = 200
ANIMATION_MS = 33
FOLLOW_UP_WINDOW_SECS = 8
MIN_CONFIDENCE = 0.45
TRANSPARENT_BG = "#010203"
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_BLOCK_SIZE = 1600
AUDIO_MIN_DURATION_SECS = 0.65
AUDIO_MAX_DURATION_SECS = 8.0
AUDIO_SILENCE_SECS = 1.05
AUDIO_PREROLL_BLOCKS = 4
DEFAULT_GROQ_STT_MODEL = "whisper-large-v3-turbo"

STATE_STYLES = {
    "starting": {
        "fill": "#bfdbfe",
        "ring": "#60a5fa",
        "text": "iniciando",
        "motion": 0.10,
        "speed": 1.05,
        "droplet": 0.08,
    },
    "listening": {
        "fill": "#2dd4bf",
        "ring": "#0f766e",
        "text": "on",
        "motion": 0.11,
        "speed": 1.20,
        "droplet": 0.10,
    },
    "awaiting": {
        "fill": "#fbbf24",
        "ring": "#d97706",
        "text": "ouvindo",
        "motion": 0.20,
        "speed": 1.85,
        "droplet": 0.20,
    },
    "thinking": {
        "fill": "#fb7185",
        "ring": "#be185d",
        "text": "pensando",
        "motion": 0.18,
        "speed": 1.45,
        "droplet": 0.12,
    },
    "speaking": {
        "fill": "#60a5fa",
        "ring": "#1d4ed8",
        "text": "falando",
        "motion": 0.29,
        "speed": 2.60,
        "droplet": 0.26,
    },
    "error": {
        "fill": "#f87171",
        "ring": "#b91c1c",
        "text": "erro",
        "motion": 0.18,
        "speed": 3.10,
        "droplet": 0.10,
    },
}


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _windows_creation_flags() -> int:
    if os.name != "nt":
        return 0
    return subprocess.CREATE_NO_WINDOW


def _http_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return without_marks.casefold().strip()


def _extract_prompt_from_wake_phrase(text: str, wake_word: str) -> str:
    pattern = re.compile(rf"\b{re.escape(wake_word)}\b[\s,:-]*(.*)$", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip()


def _powershell_command(script: str) -> list[str]:
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-EncodedCommand",
        encoded,
    ]


def _check_system_speech() -> tuple[bool, str]:
    script = """
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$rec = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  if ($null -eq $rec.RecognizerInfo) {
    throw 'Windows sem reconhecedor de fala instalado. Abra Configuracoes > Hora e idioma > Fala e instale/configure o reconhecimento de voz.'
  }
  $grammar = New-Object System.Speech.Recognition.DictationGrammar
  $rec.LoadGrammar($grammar)
  $rec.SetInputToDefaultAudioDevice()
  Write-Output ('ok|' + $rec.RecognizerInfo.Culture.Name)
} finally {
  $rec.Dispose()
  $synth.Dispose()
}
""".strip()
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_windows_creation_flags(),
        )
    except Exception as exc:  # pragma: no cover - defensive
        return False, str(exc)

    output = (result.stdout or "").strip()
    if result.returncode == 0 and output.startswith("ok|"):
        culture = output.split("|", 1)[1].strip()
        return True, f"Reconhecimento e fala prontos ({culture})"
    detail = (result.stderr or output or "falha ao carregar System.Speech").strip()
    return False, _friendly_listener_error(detail)


def _friendly_listener_error(detail: str) -> str:
    normalized = _normalize_text(detail)
    if "reconhecedor de fala instalado" in normalized:
        return (
            "Windows sem reconhecimento de voz configurado. "
            "Abra Configuracoes > Hora e idioma > Fala e instale um idioma de fala."
        )
    if "referencia de objeto" in normalized or "nao e possivel encontrar o item de dados solicitado" in normalized:
        return (
            "O reconhecedor de voz do Windows nao esta configurado. "
            "Abra Configuracoes > Hora e idioma > Fala e ative um idioma de fala."
        )
    if "acesso negado" in normalized:
        return (
            "Microfone bloqueado pelo Windows. "
            "Abra Configuracoes > Privacidade e seguranca > Microfone e libere acesso para apps desktop."
        )
    if "no module named 'sounddevice'" in normalized or "no module named sounddevice" in normalized:
        return "Captura de microfone nao instalada no Zeus."
    if "no module named 'openai'" in normalized or "no module named openai" in normalized:
        return "Cliente de transcricao do Zeus nao esta instalado."
    if "default input device" in normalized or "error querying device" in normalized:
        return "Nenhum microfone padrao disponivel para o Zeus."
    if "api key" in normalized or "authentication" in normalized or "401" in normalized:
        return "Falha de autenticacao no provedor de transcricao do Zeus."
    return detail.strip() or "Falha desconhecida no reconhecimento de voz."


def _write_wav_file(path: Path, pcm_frames: bytes) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(AUDIO_CHANNELS)
        wav_file.setsampwidth(2)
        wav_file.setframerate(AUDIO_SAMPLE_RATE)
        wav_file.writeframes(pcm_frames)


def _pcm_rms(chunk_bytes: bytes) -> float:
    samples = array.array("h")
    samples.frombytes(chunk_bytes)
    if not samples:
        return 0.0
    if sys.byteorder != "little":
        samples.byteswap()
    total = sum(sample * sample for sample in samples)
    return math.sqrt(total / len(samples))


def _check_groq_listener_stack() -> tuple[bool, str]:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return False, "GROQ_API_KEY ausente para fallback de escuta."
    try:
        from openai import OpenAI  # type: ignore  # noqa: F401
    except Exception as exc:
        return False, _friendly_listener_error(str(exc))
    try:
        import sounddevice as sd  # type: ignore
    except Exception as exc:
        return False, _friendly_listener_error(str(exc))

    try:
        device_info = sd.query_devices(kind="input")
    except Exception as exc:
        return False, _friendly_listener_error(str(exc))

    device_name = str(device_info.get("name") or "microfone padrao")
    return True, f"Fallback Groq pronto ({device_name})"


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _mix_color(color_a: str, color_b: str, amount: float) -> str:
    amount = _clamp(amount, 0.0, 1.0)
    rgb_a = _hex_to_rgb(color_a)
    rgb_b = _hex_to_rgb(color_b)
    mixed = tuple(
        int(round(channel_a + (channel_b - channel_a) * amount))
        for channel_a, channel_b in zip(rgb_a, rgb_b)
    )
    return _rgb_to_hex(mixed)


def _lighten(color: str, amount: float) -> str:
    return _mix_color(color, "#ffffff", amount)


def _darken(color: str, amount: float) -> str:
    return _mix_color(color, "#020617", amount)


def _build_blob_points(
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    wobble: float,
    droplet: float,
    phase: float,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> list[float]:
    points: list[float] = []
    segments = 16
    for index in range(segments):
        angle = (index / segments) * math.tau
        wave_a = math.sin((angle * 3.0) - (phase * 1.8))
        wave_b = math.cos((angle * 2.0) + (phase * 1.2))
        wave_c = math.sin((angle * 5.0) + (phase * 2.4))
        local_scale = 1.0 + wobble * ((0.11 * wave_a) + (0.07 * wave_b) + (0.03 * wave_c))
        sin_angle = math.sin(angle)
        cos_angle = math.cos(angle)
        top_pull = max(0.0, -sin_angle)
        bottom_pull = max(0.0, sin_angle)
        x = center_x + offset_x + (cos_angle * radius_x * local_scale)
        y = center_y + offset_y + (sin_angle * radius_y * local_scale)
        x += math.sin(phase + angle * 2.0) * wobble * 5.5
        y -= (top_pull**2) * droplet * 10.0
        y += (bottom_pull**2.6) * droplet * 18.0
        x += cos_angle * bottom_pull * droplet * 4.0
        points.extend((x, y))
    points.extend(points[:4])
    return points


class ZeusCompanion:
    def __init__(
        self,
        server_url: str,
        wake_word: str = DEFAULT_WAKE_WORD,
        auto_start_server: bool = True,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.wake_word = _normalize_text(wake_word) or "zeus"
        self.auto_start_server = auto_start_server

        self.event_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.listener_process: subprocess.Popen[str] | None = None
        self.server_process: subprocess.Popen[str] | None = None
        self.speaker_process: subprocess.Popen[str] | None = None
        self.session_id: str | None = None
        self.awaiting_follow_up_until = 0.0
        self.running_request = False
        self.listener_backend = "starting"
        self.started_server = False
        self.current_state = "starting"
        self.last_detail = "preparando companion"
        self.drag_origin: tuple[int, int] | None = None
        self.is_shutting_down = False
        self.frame_started_at = time.perf_counter()
        self.last_frame_at = self.frame_started_at
        self.reaction_energy = 0.16
        self.ripple_energy = 0.0
        self.groq_stt_model = os.environ.get("ZEUS_STT_MODEL", DEFAULT_GROQ_STT_MODEL).strip() or DEFAULT_GROQ_STT_MODEL

        self.root = tk.Tk()
        self.root.title("Zeus")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT_BG)
        self.root.wm_attributes("-alpha", 0.94)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_BG)
        except tk.TclError:
            pass

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        pos_x = screen_width - WINDOW_SIZE - 28
        pos_y = int(screen_height * 0.34)
        self.root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}+{pos_x}+{pos_y}")

        self.card = tk.Frame(self.root, bg=TRANSPARENT_BG, bd=0, highlightthickness=0)
        self.card.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.card,
            width=WINDOW_SIZE,
            height=WINDOW_SIZE,
            bg=TRANSPARENT_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.blob_center_x = WINDOW_SIZE // 2
        self.blob_center_y = 70

        self.shadow = self.canvas.create_oval(0, 0, 0, 0, fill="#020617", outline="")
        self.ripple_outer = self.canvas.create_oval(0, 0, 0, 0, outline="", width=2)
        self.ripple_inner = self.canvas.create_oval(0, 0, 0, 0, outline="", width=2)
        self.glow_ring = self.canvas.create_oval(0, 0, 0, 0, outline="", width=4)
        placeholder_points = [0, 0, 1, 0, 1, 1, 0, 1]
        self.blob_shell = self.canvas.create_polygon(
            placeholder_points,
            smooth=True,
            splinesteps=36,
            fill="#0f766e",
            outline="",
        )
        self.blob_body = self.canvas.create_polygon(
            placeholder_points,
            smooth=True,
            splinesteps=36,
            fill="#2dd4bf",
            outline="",
        )
        self.blob_core = self.canvas.create_polygon(
            placeholder_points,
            smooth=True,
            splinesteps=36,
            fill="#99f6e4",
            outline="",
        )
        self.orb_text = self.canvas.create_text(
            self.blob_center_x,
            self.blob_center_y,
            text="Z",
            fill="white",
            font=("Segoe UI", 26, "bold"),
        )
        self.shine = self.canvas.create_oval(0, 0, 0, 0, fill="#ffffff", outline="")
        self.spark = self.canvas.create_oval(0, 0, 0, 0, fill="#ffffff", outline="")
        self.status_label = self.canvas.create_text(
            WINDOW_SIZE // 2,
            138,
            text="iniciando",
            fill="#f8fafc",
            font=("Segoe UI", 11, "bold"),
        )
        self.last_label = self.canvas.create_text(
            WINDOW_SIZE // 2,
            156,
            text="escutando wake word",
            width=WINDOW_SIZE - 28,
            fill="#cbd5e1",
            font=("Segoe UI", 8),
        )

        self.root.bind("<ButtonPress-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._on_drag)
        self.root.bind("<Button-3>", lambda _e: self.shutdown())
        self.root.bind(
            "<Double-Button-1>",
            lambda _e: self.event_queue.put(("manual_chat", "Zeus")),
        )

        self.set_state("starting", "preparando companion")
        self._render_blob()

    def _start_drag(self, event: tk.Event[Any]) -> None:
        self.drag_origin = (event.x_root, event.y_root)

    def _on_drag(self, event: tk.Event[Any]) -> None:
        if self.drag_origin is None:
            return
        delta_x = event.x_root - self.drag_origin[0]
        delta_y = event.y_root - self.drag_origin[1]
        current_x = self.root.winfo_x()
        current_y = self.root.winfo_y()
        self.root.geometry(f"+{current_x + delta_x}+{current_y + delta_y}")
        self.drag_origin = (event.x_root, event.y_root)

    def _excite_blob(self, amount: float) -> None:
        boosted = _clamp(amount, 0.0, 1.0)
        self.reaction_energy = max(self.reaction_energy, boosted)
        self.ripple_energy = max(self.ripple_energy, min(1.0, boosted * 0.95))

    def set_state(self, state: str, detail: str = "") -> None:
        previous_state = self.current_state
        style = STATE_STYLES.get(state, STATE_STYLES["error"])
        self.current_state = state
        self.canvas.itemconfig(self.status_label, text=style["text"])
        if detail:
            self.last_detail = detail[:90]
            self.canvas.itemconfig(self.last_label, text=self.last_detail)
        if state != previous_state:
            self._excite_blob(style["motion"] + 0.14)

    def _render_blob(self) -> None:
        style = STATE_STYLES.get(self.current_state, STATE_STYLES["error"])
        elapsed = time.perf_counter() - self.frame_started_at
        phase = elapsed * style["speed"] * 2.1
        base_motion = float(style["motion"])
        wobble = _clamp(base_motion + (self.reaction_energy * 0.42), 0.05, 0.55)
        droplet = float(style["droplet"]) + (self.reaction_energy * 0.10)
        breath = 1.0 + math.sin(phase * 0.8) * 0.03 + self.reaction_energy * 0.03
        jitter_x = math.sin(phase * 1.6) * self.reaction_energy * 1.4
        jitter_y = math.cos(phase * 1.3) * self.reaction_energy * 1.0

        if self.current_state == "error":
            jitter_x += math.sin(phase * 5.4) * 1.6

        radius_x = (ORB_SIZE * 0.50) * breath * (1.0 + math.sin(phase * 1.1) * wobble * 0.08)
        radius_y = (ORB_SIZE * 0.47) * breath * (1.0 + math.cos(phase * 1.25) * wobble * 0.11)
        shell_points = _build_blob_points(
            self.blob_center_x,
            self.blob_center_y,
            radius_x + 6,
            radius_y + 6,
            wobble * 1.12,
            droplet * 1.05,
            phase,
            jitter_x * 0.7,
            jitter_y * 0.7,
        )
        body_points = _build_blob_points(
            self.blob_center_x,
            self.blob_center_y,
            radius_x,
            radius_y,
            wobble,
            droplet,
            phase + 0.18,
            jitter_x,
            jitter_y,
        )
        core_points = _build_blob_points(
            self.blob_center_x,
            self.blob_center_y - 4,
            radius_x * 0.72,
            radius_y * 0.70,
            wobble * 0.58,
            droplet * 0.52,
            phase + 0.48,
            jitter_x * 0.35,
            jitter_y * 0.20,
        )

        fill = str(style["fill"])
        ring = str(style["ring"])
        shell_color = _darken(ring, 0.06)
        core_color = _lighten(fill, 0.38)
        glow_color = _lighten(fill, 0.28 + min(0.18, self.reaction_energy * 0.22))
        shadow_color = _mix_color("#020617", ring, 0.22)

        shadow_width = radius_x * 1.38
        shadow_height = 14 + (self.reaction_energy * 10)
        shadow_y = self.blob_center_y + radius_y + 10
        self.canvas.coords(
            self.shadow,
            self.blob_center_x - shadow_width * 0.5,
            shadow_y,
            self.blob_center_x + shadow_width * 0.5,
            shadow_y + shadow_height,
        )
        self.canvas.itemconfig(self.shadow, fill=shadow_color)

        glow_radius = max(radius_x, radius_y) + 12 + (self.reaction_energy * 8)
        self.canvas.coords(
            self.glow_ring,
            self.blob_center_x - glow_radius + jitter_x * 0.4,
            self.blob_center_y - glow_radius + jitter_y * 0.4,
            self.blob_center_x + glow_radius + jitter_x * 0.4,
            self.blob_center_y + glow_radius + jitter_y * 0.4,
        )
        self.canvas.itemconfig(
            self.glow_ring,
            outline=glow_color,
            width=max(3, int(round(4 + self.reaction_energy * 2))),
        )

        ripple_inner_radius = max(radius_x, radius_y) + 10 + (self.ripple_energy * 12)
        ripple_outer_radius = max(radius_x, radius_y) + 20 + (self.ripple_energy * 18)
        if self.ripple_energy > 0.03 or self.current_state in {"awaiting", "speaking"}:
            self.canvas.coords(
                self.ripple_inner,
                self.blob_center_x - ripple_inner_radius,
                self.blob_center_y - ripple_inner_radius,
                self.blob_center_x + ripple_inner_radius,
                self.blob_center_y + ripple_inner_radius,
            )
            self.canvas.coords(
                self.ripple_outer,
                self.blob_center_x - ripple_outer_radius,
                self.blob_center_y - ripple_outer_radius,
                self.blob_center_x + ripple_outer_radius,
                self.blob_center_y + ripple_outer_radius,
            )
            self.canvas.itemconfig(
                self.ripple_inner,
                outline=_lighten(fill, 0.48),
                width=max(1, int(round(2 + self.ripple_energy * 2))),
            )
            self.canvas.itemconfig(
                self.ripple_outer,
                outline=_lighten(ring, 0.32),
                width=max(1, int(round(1 + self.ripple_energy * 2))),
            )
        else:
            self.canvas.itemconfig(self.ripple_inner, outline="")
            self.canvas.itemconfig(self.ripple_outer, outline="")

        self.canvas.coords(self.blob_shell, *shell_points)
        self.canvas.coords(self.blob_body, *body_points)
        self.canvas.coords(self.blob_core, *core_points)
        self.canvas.itemconfig(self.blob_shell, fill=shell_color)
        self.canvas.itemconfig(self.blob_body, fill=fill)
        self.canvas.itemconfig(self.blob_core, fill=core_color)

        self.canvas.coords(
            self.shine,
            self.blob_center_x - radius_x * 0.48 + jitter_x * 0.25,
            self.blob_center_y - radius_y * 0.72 + jitter_y * 0.2,
            self.blob_center_x - radius_x * 0.02 + jitter_x * 0.18,
            self.blob_center_y - radius_y * 0.14 + jitter_y * 0.15,
        )
        self.canvas.itemconfig(self.shine, fill=_mix_color("#ffffff", fill, 0.16))

        spark_size = 8 + (self.reaction_energy * 4)
        spark_x = self.blob_center_x + radius_x * 0.16 + math.cos(phase * 1.1) * 2.0
        spark_y = self.blob_center_y - radius_y * 0.12 + math.sin(phase * 1.3) * 2.0
        self.canvas.coords(
            self.spark,
            spark_x - spark_size,
            spark_y - spark_size,
            spark_x,
            spark_y,
        )
        self.canvas.itemconfig(self.spark, fill=_mix_color("#ffffff", fill, 0.10))

        self.canvas.coords(
            self.orb_text,
            self.blob_center_x + jitter_x * 0.18,
            self.blob_center_y + jitter_y * 0.10 + 2,
        )
        self.canvas.tag_raise(self.orb_text)
        self.canvas.tag_raise(self.status_label)
        self.canvas.tag_raise(self.last_label)

    def _animate(self) -> None:
        if self.is_shutting_down or not self.root.winfo_exists():
            return
        now = time.perf_counter()
        dt = _clamp(now - self.last_frame_at, 0.008, 0.060)
        self.last_frame_at = now
        self.reaction_energy *= max(0.0, 1.0 - (dt * 2.4))
        self.ripple_energy *= max(0.0, 1.0 - (dt * 3.0))
        self._render_blob()
        self.root.after(ANIMATION_MS, self._animate)

    def _transcribe_with_groq(self, pcm_frames: bytes) -> tuple[str, float]:
        from openai import OpenAI  # type: ignore

        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GROQ_API_KEY ausente para transcricao.")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        try:
            _write_wav_file(temp_path, pcm_frames)
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            with temp_path.open("rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.groq_stt_model,
                    language="pt",
                    response_format="verbose_json",
                    temperature=0.0,
                )
            text = str(getattr(transcription, "text", "") or "").strip()
            confidence = 0.86 if text else 0.0
            return text, confidence
        finally:
            temp_path.unlink(missing_ok=True)

    def _process_groq_segment(self, pcm_frames: bytes) -> None:
        try:
            text, confidence = self._transcribe_with_groq(pcm_frames)
            if text:
                self.event_queue.put(("heard", {"text": text, "confidence": confidence}))
        except Exception as exc:
            self.event_queue.put(("error", _friendly_listener_error(str(exc))))

    def _groq_listener_loop(self) -> None:
        try:
            import sounddevice as sd  # type: ignore
        except Exception as exc:
            self.event_queue.put(("error", _friendly_listener_error(str(exc))))
            return

        noise_floor = 110.0
        silence_deadline = 0.0
        speech_chunks: list[bytes] = []
        pre_roll: deque[bytes] = deque(maxlen=AUDIO_PREROLL_BLOCKS)
        speech_started_at = 0.0
        capturing = False

        try:
            with sd.RawInputStream(
                samplerate=AUDIO_SAMPLE_RATE,
                channels=AUDIO_CHANNELS,
                dtype="int16",
                blocksize=AUDIO_BLOCK_SIZE,
            ) as stream:
                self.event_queue.put(("status", {"state": "listening"}))
                while not self.is_shutting_down:
                    chunk, _overflowed = stream.read(AUDIO_BLOCK_SIZE)
                    chunk_bytes = bytes(chunk)
                    level = _pcm_rms(chunk_bytes)

                    if not capturing:
                        noise_floor = (noise_floor * 0.94) + (level * 0.06)
                    threshold = max(230.0, noise_floor * 2.9)

                    now = time.time()
                    if not capturing:
                        pre_roll.append(chunk_bytes)
                        if level >= threshold:
                            capturing = True
                            speech_started_at = now
                            silence_deadline = now + AUDIO_SILENCE_SECS
                            speech_chunks = list(pre_roll)
                            pre_roll.clear()
                            speech_chunks.append(chunk_bytes)
                    else:
                        speech_chunks.append(chunk_bytes)
                        if level >= (threshold * 0.7):
                            silence_deadline = now + AUDIO_SILENCE_SECS

                        duration = now - speech_started_at
                        if now >= silence_deadline or duration >= AUDIO_MAX_DURATION_SECS:
                            capturing = False
                            pcm_frames = b"".join(speech_chunks)
                            speech_chunks = []
                            pre_roll.clear()
                            if duration >= AUDIO_MIN_DURATION_SECS:
                                self.event_queue.put(("detail", "transcrevendo audio"))
                                self._process_groq_segment(pcm_frames)
        except Exception as exc:
            self.event_queue.put(("error", _friendly_listener_error(str(exc))))

    def ensure_server(self) -> None:
        try:
            status = _http_json(f"{self.server_url}/api/status", timeout=4)
            detail = "servidor pronto"
            if status.get("provider_ready") is False and status.get("message"):
                detail = str(status["message"])
            self.event_queue.put(("server_ready", detail))
            return
        except Exception:
            if not self.auto_start_server:
                self.event_queue.put(("error", "Servidor do Zeus offline"))
                return

        parsed_url = urllib.parse.urlparse(self.server_url)
        port = str(parsed_url.port or 8787)
        script = ROOT / "automation" / "obsidian_memory_ai.py"
        self.started_server = True
        self.server_process = subprocess.Popen(
            [sys.executable, str(script), "--port", port],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_windows_creation_flags(),
        )

        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                status = _http_json(f"{self.server_url}/api/status", timeout=3)
                detail = "servidor iniciado"
                if status.get("provider_ready") is False and status.get("message"):
                    detail = str(status["message"])
                self.event_queue.put(("server_ready", detail))
                return
            except Exception:
                time.sleep(1)

        self.event_queue.put(("error", "Nao consegui iniciar o servidor do Zeus"))

    def ensure_session(self) -> str:
        if self.session_id:
            return self.session_id
        payload = _http_json(f"{self.server_url}/api/session", method="POST", payload={})
        self.session_id = str(payload.get("session_id") or "")
        if not self.session_id:
            raise RuntimeError("Falha ao criar sessao do Zeus")
        return self.session_id

    def _start_native_listener(self) -> None:
        script = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$engine = $null
try {
  $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
  if ($null -eq $engine.RecognizerInfo) {
    throw 'Windows sem reconhecedor de fala instalado ou idioma de fala configurado.'
  }
  $grammar = New-Object System.Speech.Recognition.DictationGrammar
  $engine.LoadGrammar($grammar)
  $engine.SetInputToDefaultAudioDevice()
  [Console]::Out.WriteLine('{"type":"status","state":"listening"}')
  [Console]::Out.Flush()
} catch {
  $payload = @{
    type = "error"
    error = $_.Exception.Message
  } | ConvertTo-Json -Compress
  [Console]::Out.WriteLine($payload)
  [Console]::Out.Flush()
  if ($null -ne $engine) {
    $engine.Dispose()
  }
  exit 1
}
while ($true) {
  try {
    $result = $engine.Recognize()
    if ($null -ne $result -and -not [string]::IsNullOrWhiteSpace($result.Text)) {
      $payload = @{
        type = "heard"
        text = $result.Text
        confidence = [math]::Round($result.Confidence, 2)
      } | ConvertTo-Json -Compress
      [Console]::Out.WriteLine($payload)
      [Console]::Out.Flush()
    }
  } catch {
    $payload = @{
      type = "error"
      error = $_.Exception.Message
    } | ConvertTo-Json -Compress
    [Console]::Out.WriteLine($payload)
    [Console]::Out.Flush()
    Start-Sleep -Milliseconds 500
  }
}
""".strip()
        self.listener_process = subprocess.Popen(
            _powershell_command(script),
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=_windows_creation_flags(),
        )
        threading.Thread(target=self._read_listener_stdout, daemon=True).start()
        threading.Thread(target=self._read_listener_stderr, daemon=True).start()

    def start_listener(self) -> None:
        native_ok, native_detail = _check_system_speech()
        if native_ok:
            self.listener_backend = "windows"
            self.event_queue.put(("detail", f"escuta windows ativa: {native_detail}"))
            self._start_native_listener()
            return

        groq_ok, groq_detail = _check_groq_listener_stack()
        if groq_ok:
            self.listener_backend = "groq"
            self.event_queue.put(("detail", f"escuta groq ativa: {groq_detail}"))
            threading.Thread(target=self._groq_listener_loop, daemon=True).start()
            return

        self.listener_backend = "error"
        self.event_queue.put(("error", native_detail or groq_detail))

    def _read_listener_stdout(self) -> None:
        if not self.listener_process or not self.listener_process.stdout:
            return
        for raw_line in self.listener_process.stdout:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                self.event_queue.put(("heard", {"text": line, "confidence": 1.0}))
                continue
            self.event_queue.put((payload.get("type", "status"), payload))

    def _read_listener_stderr(self) -> None:
        if not self.listener_process or not self.listener_process.stderr:
            return
        for raw_line in self.listener_process.stderr:
            line = raw_line.strip()
            if line:
                self.event_queue.put(("error", _friendly_listener_error(line)))

    def stop_speaking(self) -> None:
        if self.speaker_process and self.speaker_process.poll() is None:
            self.speaker_process.kill()
        self.speaker_process = None

    def speak(self, text: str) -> None:
        cleaned = re.sub(r"\s+", " ", re.sub(r"```[\s\S]*?```", " ", text)).strip()
        if not cleaned:
            return
        cleaned = cleaned[:900]
        self._excite_blob(0.64)
        self.stop_speaking()
        script = """
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  $speaker.Speak($env:ZEUS_SPEAK_TEXT)
} finally {
  $speaker.Dispose()
}
""".strip()
        speaker_env = os.environ.copy()
        speaker_env["ZEUS_SPEAK_TEXT"] = cleaned
        self.speaker_process = subprocess.Popen(
            _powershell_command(script),
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=speaker_env,
            creationflags=_windows_creation_flags(),
        )
        threading.Thread(target=self._watch_speaker, daemon=True).start()

    def _watch_speaker(self) -> None:
        process = self.speaker_process
        if not process:
            return
        process.wait()
        self.event_queue.put(("speech_done", None))

    def submit_prompt(self, prompt: str) -> None:
        if self.running_request:
            self.event_queue.put(("detail", "aguarde a resposta atual"))
            return
        self.running_request = True
        self._excite_blob(0.52)
        self.set_state("thinking", prompt[:80])
        threading.Thread(target=self._request_worker, args=(prompt,), daemon=True).start()

    def _request_worker(self, prompt: str) -> None:
        try:
            session_id = self.ensure_session()
            payload = _http_json(
                f"{self.server_url}/api/chat",
                method="POST",
                payload={"message": prompt, "session_id": session_id},
                timeout=120,
            )
            answer = str(payload.get("answer") or "").strip()
            if not answer:
                raise RuntimeError("Zeus nao retornou resposta")
            self.event_queue.put(("assistant", {"prompt": prompt, "answer": answer}))
        except Exception as exc:
            self.event_queue.put(("error", f"Falha ao responder: {exc}"))
        finally:
            self.running_request = False

    def handle_heard_text(self, text: str, confidence: float) -> None:
        normalized = _normalize_text(text)
        if confidence < MIN_CONFIDENCE:
            return

        now = time.time()
        if self.wake_word in normalized:
            prompt = _extract_prompt_from_wake_phrase(text, self.wake_word)
            self._excite_blob(0.48 + confidence * 0.26)
            if prompt:
                self.submit_prompt(prompt)
                return
            self.awaiting_follow_up_until = now + FOLLOW_UP_WINDOW_SECS
            self.set_state("awaiting", "sim? pode falar")
            self.speak("Sim? Pode falar.")
            return

        if now <= self.awaiting_follow_up_until:
            self.awaiting_follow_up_until = 0.0
            self._excite_blob(0.44 + confidence * 0.22)
            self.submit_prompt(text.strip())

    def process_events(self) -> None:
        try:
            while True:
                event_type, payload = self.event_queue.get_nowait()
                if event_type == "status":
                    self._excite_blob(0.20)
                    self.set_state("listening", "wake word ativo")
                elif event_type == "server_ready":
                    self._excite_blob(0.22)
                    self.set_state("listening", str(payload))
                elif event_type == "heard":
                    text = str(payload.get("text") or "").strip()
                    confidence = float(payload.get("confidence") or 0.0)
                    if text:
                        self._excite_blob(0.24 + confidence * 0.36)
                        self.set_state("listening", f"ouvi: {text[:70]}")
                        self.handle_heard_text(text, confidence)
                elif event_type == "assistant":
                    answer = str(payload.get("answer") or "").strip()
                    prompt = str(payload.get("prompt") or "").strip()
                    self._excite_blob(0.66)
                    self.set_state("speaking", f"{prompt[:60]} -> resposta pronta")
                    self.speak(answer)
                elif event_type == "speech_done":
                    self._excite_blob(0.18)
                    if time.time() <= self.awaiting_follow_up_until:
                        self.set_state("awaiting", "sim? pode falar")
                    else:
                        self.set_state("listening", "wake word ativo")
                elif event_type == "detail":
                    self._excite_blob(0.18)
                    self.set_state("listening", str(payload))
                elif event_type == "manual_chat":
                    self._excite_blob(0.40)
                    self.handle_heard_text(str(payload), 1.0)
                elif event_type == "error":
                    self._excite_blob(0.56)
                    self.set_state("error", _friendly_listener_error(str(payload))[:90])
        except queue.Empty:
            pass

        if (
            self.current_state == "awaiting"
            and time.time() > self.awaiting_follow_up_until
            and not self.running_request
        ):
            self.set_state("listening", "wake word ativo")

        self.root.after(POLL_MS, self.process_events)

    def shutdown(self) -> None:
        if self.is_shutting_down:
            return
        self.is_shutting_down = True
        self.stop_speaking()
        if self.listener_process and self.listener_process.poll() is None:
            self.listener_process.kill()
        if self.started_server and self.server_process and self.server_process.poll() is None:
            self.server_process.kill()
        self.root.destroy()

    def run(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.root.after(50, self.process_events)
        self.root.after(50, self._animate)
        threading.Thread(target=self.ensure_server, daemon=True).start()
        self.start_listener()
        self.root.mainloop()


def self_test(server_url: str) -> int:
    native_ok, native_detail = _check_system_speech()
    groq_ok, groq_detail = _check_groq_listener_stack()
    listener_ok = native_ok or groq_ok
    print(f"speech_stack_native: {'ok' if native_ok else 'error'} - {native_detail}")
    print(f"speech_stack_groq: {'ok' if groq_ok else 'error'} - {groq_detail}")
    try:
        status = _http_json(f"{server_url.rstrip('/')}/api/status", timeout=4)
        print(
            "server_status: ok - "
            f"{status.get('assistant_name', 'Zeus')} / provider_ready={status.get('provider_ready')}"
        )
    except Exception as exc:
        print(f"server_status: error - {exc}")
    return 0 if listener_ok else 1


def main() -> None:
    _load_dotenv(ROOT / ".env")
    default_server_url = os.environ.get("ZEUS_SERVER_URL", DEFAULT_SERVER_URL)
    default_wake_word = os.environ.get("ZEUS_WAKE_WORD", DEFAULT_WAKE_WORD)

    parser = argparse.ArgumentParser(description="Companion flutuante do Zeus no Windows")
    parser.add_argument("--server-url", default=default_server_url)
    parser.add_argument("--wake-word", default=default_wake_word)
    parser.add_argument("--no-auto-start-server", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if sys.platform != "win32":
        raise SystemExit("O companion do Zeus foi feito para Windows.")

    if args.self_test:
        raise SystemExit(self_test(args.server_url))

    companion = ZeusCompanion(
        server_url=args.server_url,
        wake_word=args.wake_word,
        auto_start_server=not args.no_auto_start_server,
    )
    companion.run()


if __name__ == "__main__":
    main()
