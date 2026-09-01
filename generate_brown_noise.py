#!/usr/bin/env python3
"""Generate the default 60-second deep brown noise WAV file.

The default is the low-rumble setting used by the Streamlit UI.
"""

from __future__ import annotations

from pathlib import Path

from noise_engine import PRESETS, generate_noise, write_wav


def main() -> None:
    preset = PRESETS["brown_deep"]
    output_file = Path(__file__).with_name("brown_noise_60s_deeper.wav")
    samples = generate_noise(
        kind="brown_deep",
        duration=int(preset["duration"]),
        amplitude=float(preset["amplitude"]),
        step=float(preset["step"]),
        damping=float(preset["damping"]),
        smooth=float(preset["smooth"]),
        bass=float(preset["bass"]),
    )
    write_wav(output_file, samples)
    print(f"Generated {output_file}")


if __name__ == "__main__":
    main()
