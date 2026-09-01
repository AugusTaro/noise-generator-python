"""Noise generation helpers for scripts and the Streamlit UI."""

from __future__ import annotations

import math
import random
import struct
import wave
from io import BytesIO
from pathlib import Path


SAMPLE_RATE = 44_100
MAX_DURATION_SECONDS = 600


PRESETS = {
    "brown_deep": {
        "label": "Brown - deep",
        "duration": 60,
        "amplitude": 0.85,
        "step": 0.35,
        "damping": 0.999,
        "smooth": 0.04,
        "bass": 1.12,
    },
    "brown_soft": {
        "label": "Brown - soft",
        "duration": 60,
        "amplitude": 0.80,
        "step": 0.28,
        "damping": 0.9985,
        "smooth": 0.06,
        "bass": 1.04,
    },
    "pink": {
        "label": "Pink",
        "duration": 60,
        "amplitude": 0.70,
        "step": 0.55,
        "damping": 0.997,
        "smooth": 0.16,
        "bass": 0.58,
    },
    "white": {
        "label": "White",
        "duration": 60,
        "amplitude": 0.45,
        "step": 1.0,
        "damping": 0.0,
        "smooth": 1.0,
        "bass": 0.0,
    },
}


def preset_defaults(preset: str) -> dict[str, float | int | str]:
    return dict(PRESETS[preset])


def generate_noise(
    kind: str,
    duration: int,
    amplitude: float,
    step: float,
    damping: float,
    smooth: float,
    bass: float,
    seed: int | None = None,
) -> list[float]:
    """Generate normalized samples for the selected noise kind."""
    duration = max(1, min(MAX_DURATION_SECONDS, int(duration)))
    sample_count = duration * SAMPLE_RATE
    rng = random.Random(seed)

    if kind == "white":
        samples = [rng.uniform(-1.0, 1.0) for _ in range(sample_count)]
    elif kind == "pink":
        samples = _pink_noise(sample_count, rng)
    else:
        samples = _brown_noise(sample_count, rng, step, damping, smooth)

    if kind != "white" and bass > 0:
        samples = _bass_shape(samples, bass)

    return _normalize(samples, amplitude)


def make_wav_bytes(samples: list[float]) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(_pcm16(samples))
    return buffer.getvalue()


def write_wav(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(_pcm16(samples))


def _brown_noise(
    sample_count: int,
    rng: random.Random,
    step: float,
    damping: float,
    smooth: float,
) -> list[float]:
    samples: list[float] = []
    value = 0.0
    smoothed = 0.0
    smooth = max(0.001, min(1.0, smooth))
    damping = max(0.0, min(0.9999, damping))

    for _ in range(sample_count):
        value += rng.uniform(-step, step)
        value *= damping
        smoothed += (value - smoothed) * smooth
        samples.append(smoothed)

    return samples


def _pink_noise(sample_count: int, rng: random.Random) -> list[float]:
    rows = [0.0] * 16
    running_sum = 0.0
    counter = 0
    samples: list[float] = []

    for _ in range(sample_count):
        counter += 1
        zeros = _trailing_zeros(counter)
        if zeros < len(rows):
            running_sum -= rows[zeros]
            rows[zeros] = rng.uniform(-1.0, 1.0)
            running_sum += rows[zeros]
        white = rng.uniform(-1.0, 1.0)
        samples.append((running_sum + white) / (len(rows) + 1))

    return samples


def _trailing_zeros(value: int) -> int:
    if value == 0:
        return 0
    return int(math.log2(value & -value))


def _bass_shape(samples: list[float], amount: float) -> list[float]:
    amount = max(0.0, min(1.5, amount))
    low = 0.0
    shaped: list[float] = []
    low_mix = min(0.92, 0.35 + amount * 0.38)
    cutoff = max(0.005, min(0.15, 0.08 / max(0.2, amount)))

    for sample in samples:
        low += (sample - low) * cutoff
        shaped.append((sample * (1.0 - low_mix)) + (low * low_mix))

    return shaped


def _normalize(samples: list[float], amplitude: float) -> list[float]:
    peak = max(abs(sample) for sample in samples) or 1.0
    amplitude = max(0.0, min(1.0, amplitude))
    return [(sample / peak) * amplitude for sample in samples]


def _pcm16(samples: list[float]) -> bytes:
    frames = bytearray()
    for sample in samples:
        clipped = max(-1.0, min(1.0, sample))
        frames.extend(struct.pack("<h", int(clipped * 32767)))
    return bytes(frames)
