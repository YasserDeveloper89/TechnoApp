import streamlit as st
import subprocess
import tempfile
import os
from pydub import AudioSegment, effects
import scipy.io.wavfile as wav
import numpy as np
import noisereduce as nr

def extract_audio(video_path, output_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def apply_noise_reduction(wav_path):
    rate, data = wav.read(wav_path)
    reduced = nr.reduce_noise(y=data, sr=rate)
    output_path = wav_path.replace(".wav", "_clean.wav")
    wav.write(output_path, rate, reduced.astype(np.int16))
    return output_path

def apply_techno_eq(wav_path, level='normal'):
    audio = AudioSegment.from_wav(wav_path)
    audio = effects.normalize(audio)

    eq = {
        "soft": {"bass": 3, "mid": 0, "high": 2},
        "normal": {"bass": 6, "mid": 1, "high": 3},
        "intense": {"bass": 9, "mid": 2, "high": 6},
    }[level]

    bass = audio.low_pass_filter(150).apply_gain(eq["bass"])
    mid = audio.high_pass_filter(150).low_pass_filter(4000).apply_gain(eq["mid"])
    high = audio.high_pass_filter(4000).apply_gain(eq["high"])

    final = bass.overlay(mid).overlay(high)
    output_path = wav_path.replace(".wav", "_eq.wav")
    final.export(output_path, format="wav")
    return output_path

# Streamlit UI
st.set_page_config(page_title="Audio Techno Enhancer", layout="centered")
st.title("Mejora el audio de tus videos Techno")
st.write("Reduce ruido y ecualiza audio de videos para TikTok, sin errores.")

video_file = st.file_uploader("Sube un video (mp4)", type=["mp4"])
intensity = st.selectbox("Nivel del ecualizador", ["soft", "normal", "intense"], index=1)

if video_file:
    with st.spinner("Procesando..."):
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input.mp4")
            with open(video_path, "wb") as f:
                f.write(video_file.read())

            audio_path = os.path.join(tmpdir, "audio.wav")
            extract_audio(video_path, audio_path)

            cleaned = apply_noise_reduction(audio_path)
            final_audio = apply_techno_eq(cleaned, level=intensity)

            st.audio(final_audio)
            with open(final_audio, "rb") as f:
                st.download_button("Descargar audio mejorado", f, file_name="techno_audio_mejorado.wav")
