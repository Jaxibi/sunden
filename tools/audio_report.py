"""Contrôle des fichiers audio générés : durée, crête, attaque et enveloppe (aucune modification).

Usage : <python ComfyUI> tools/audio_report.py [motif]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r"C:\Users\cleme\.claude\skills\game-sound-designer\scripts")
import comfy_audio_gen as gen  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
pattern = sys.argv[1] if len(sys.argv) > 1 else "*"
bars = " ▁▂▃▄▅▆▇█"

for p in sorted((ROOT / "assets" / "audio").rglob(f"{pattern}.*")):
    if p.suffix not in (".wav", ".ogg", ".mp3"):
        continue
    wave, sr = gen.decode_audio_bytes(p.read_bytes())
    x = wave.mean(axis=0)
    dur = len(x) / sr
    peak = 20 * np.log10(np.max(np.abs(x)) + 1e-9)
    win = max(1, int(sr * (0.025 if dur < 5 else dur / 40)))
    env = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x), win)])
    env_db = 20 * np.log10(env + 1e-9)
    attack_ms = 1000 * np.argmax(env) * win / sr
    norm = np.clip((env_db + 48) / 48, 0, 1)
    curve = "".join(bars[int(v * (len(bars) - 1))] for v in norm[:40])
    ch = "stéréo" if wave.shape[0] > 1 else "mono"
    print(f"{p.relative_to(ROOT)!s:44} {dur:6.2f}s {ch:6} crête {peak:5.1f} dB  max à {attack_ms:5.0f} ms  {curve}")
