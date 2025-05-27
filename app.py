
import streamlit as st
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment, effects
import noisereduce as nr
import numpy as np
import scipy.io.wavfile as wav
import os
import tempfile

def reduce_noise(audio_path):
    rate, data = wav.read(audio_path)
    reduced = nr.reduce_noise(y=data, sr=rate)
    clean_path = audio_path.replace(".wav", "_clean.wav")
    wav.write(clean_path, rate, reduced.astype(np.int16))
    return clean_path

def apply_techno_eq(audio_path, intensity='normal'):
    sound = AudioSegment.from_wav(audio_path)
    sound = effects.normalize(sound)

    # Gain values based on intensity
    levels = {
        'soft': {'bass': 3, 'low_mids': -1, 'high_mids': 1.5, 'highs': 2},
        'normal': {'bass': 6, 'low_mids': -2, 'high_mids': 3, 'highs': 4},
        'intense': {'bass': 9, 'low_mids': -3, 'high_mids': 5, 'highs': 6}
    }

    gains = levels[intensity]

    bass = sound.low_pass_filter(120).apply_gain(gains['bass'])
    low_mids = sound.high_pass_filter(120).low_pass_filter(300).apply_gain(gains['low_mids'])
    high_mids = sound.high_pass_filter(3000).low_pass_filter(5000).apply_gain(gains['high_mids'])
    highs = sound.high_pass_filter(5000).apply_gain(gains['highs'])

    enhanced = bass.overlay(low_mids).overlay(high_mids).overlay(highs)

    enhanced_path = audio_path.replace(".wav", "_eq.wav")
    enhanced.export(enhanced_path, format="wav")
    return enhanced_path

def convert_to_vertical(clip):
    w, h = clip.size
    if w > h:
        new_h = w * 16 // 9
        y_center = h // 2
        top = max(0, y_center - new_h // 2)
        return clip.crop(y1=top, y2=top + new_h).resize(height=720)
    return clip

def process_video(video_file, intensity, preview_audio=False, convert_vertical=False):
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "input.mp4")
        with open(video_path, "wb") as f:
            f.write(video_file.read())

        video = VideoFileClip(video_path)
        audio_path = os.path.join(tmpdir, "audio.wav")
        video.audio.write_audiofile(audio_path, logger=None)

        clean_path = reduce_noise(audio_path)
        eq_path = apply_techno_eq(clean_path, intensity)

        if preview_audio:
            return eq_path, None

        if convert_vertical:
            video = convert_to_vertical(video)

        new_audio = AudioFileClip(eq_path)
        final = video.set_audio(new_audio)

        output_path = os.path.join(tmpdir, "output.mp4")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True, logger=None)

        return output_path, eq_path

# Streamlit UI
st.set_page_config(page_title="Techno Audio Enhancer", layout="centered")
st.title("Techno Audio Enhancer para TikTok")
st.write("Mejora el audio de tus videos techno con reducción de ruido, ecualización y formato vertical.")

video_file = st.file_uploader("Sube tu video (MP4)", type=["mp4"])

intensity = st.selectbox("Intensidad del Ecualizador", options=["soft", "normal", "intense"], index=1)
convert = st.checkbox("Convertir a formato vertical (9:16)")
preview_audio = st.checkbox("Previsualizar solo el audio mejorado")

if video_file is not None:
    if st.button("Procesar"):
        with st.spinner("Procesando..."):
            output_video, processed_audio = process_video(
                video_file, intensity=intensity, preview_audio=preview_audio, convert_vertical=convert
            )

            if preview_audio and processed_audio:
                st.audio(processed_audio)
            elif output_video:
                with open(output_video, "rb") as f:
                    st.success("¡Listo! Descarga tu video mejorado.")
                    st.download_button("Descargar Video", f, file_name="techno_mejorado.mp4")
    