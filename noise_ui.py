#!/usr/bin/env python3
"""Streamlit UI for generating adjustable noise WAV files."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from noise_engine import PRESETS, generate_noise, make_wav_bytes


st.set_page_config(page_title="Noise Generator", layout="centered")


def apply_preset(name: str) -> None:
    preset = PRESETS[name]
    st.session_state.noise_kind = name
    st.session_state.duration = preset["duration"]
    st.session_state.preview_duration = min(5, preset["duration"])
    st.session_state.amplitude = preset["amplitude"]
    st.session_state.step = preset["step"]
    st.session_state.damping = preset["damping"]
    st.session_state.smooth = preset["smooth"]
    st.session_state.bass = preset["bass"]
    st.session_state.preview = None
    st.session_state.generated = None


def init_state() -> None:
    if "noise_kind" not in st.session_state:
        apply_preset("brown_deep")
    if "generated" not in st.session_state:
        st.session_state.generated = None
    if "preview" not in st.session_state:
        st.session_state.preview = None


init_state()

st.title("Noise Generator")

preset_cols = st.columns(4)
for index, (name, preset) in enumerate(PRESETS.items()):
    with preset_cols[index]:
        button_type = "primary" if st.session_state.noise_kind == name else "secondary"
        if st.button(preset["label"], key=f"preset_{name}", type=button_type, use_container_width=True):
            apply_preset(name)
            st.rerun()

st.divider()

left, right = st.columns(2)
with left:
    st.slider("Length", 1, 300, key="duration", format="%d sec")
    st.slider("Preview length", 1, 30, key="preview_duration", format="%d sec")
    st.slider("Volume", 0.05, 1.0, key="amplitude", step=0.01)
    st.slider("Bass weight", 0.0, 1.5, key="bass", step=0.01)

with right:
    st.slider("Random movement", 0.05, 1.5, key="step", step=0.01)
    st.slider("Brown persistence", 0.0, 0.9999, key="damping", step=0.0001, format="%.4f")
    st.slider("Smoothness", 0.001, 1.0, key="smooth", step=0.001, format="%.3f")

seed_enabled = st.checkbox("Use fixed seed")
seed = st.number_input("Seed", min_value=0, max_value=999_999, value=12345, disabled=not seed_enabled)

kind = st.session_state.noise_kind
if kind == "white":
    st.caption("White noise uses volume and length. Tone sliders are kept visible so presets can move as a group.")
elif kind == "pink":
    st.caption("Pink noise sits between white and brown, with a softer high end.")
else:
    st.caption("Default is the deeper brown setting from the latest generated WAV.")

preview_col, export_col = st.columns(2)

with preview_col:
    if st.button("Preview", use_container_width=True):
        samples = generate_noise(
            kind=kind,
            duration=st.session_state.preview_duration,
            amplitude=st.session_state.amplitude,
            step=st.session_state.step,
            damping=st.session_state.damping,
            smooth=st.session_state.smooth,
            bass=st.session_state.bass,
            seed=int(seed) if seed_enabled else None,
        )
        st.session_state.preview = make_wav_bytes(samples)

with export_col:
    generate_clicked = st.button("Generate WAV", type="primary", use_container_width=True)

if st.session_state.preview:
    st.audio(st.session_state.preview, format="audio/wav")

if generate_clicked:
    samples = generate_noise(
        kind=kind,
        duration=st.session_state.duration,
        amplitude=st.session_state.amplitude,
        step=st.session_state.step,
        damping=st.session_state.damping,
        smooth=st.session_state.smooth,
        bass=st.session_state.bass,
        seed=int(seed) if seed_enabled else None,
    )
    wav_bytes = make_wav_bytes(samples)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{kind}_{st.session_state.duration}s_{timestamp}.wav"
    st.session_state.generated = {"filename": filename, "wav": wav_bytes}

if st.session_state.generated:
    st.subheader("Export")
    st.audio(st.session_state.generated["wav"], format="audio/wav")
    st.download_button(
        "Download WAV",
        data=st.session_state.generated["wav"],
        file_name=st.session_state.generated["filename"],
        mime="audio/wav",
        use_container_width=True,
    )
