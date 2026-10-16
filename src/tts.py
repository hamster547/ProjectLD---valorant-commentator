import io
import os
import subprocess
from kokoro_onnx import Kokoro
import numpy as np
import sounddevice as sd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # the folder this .py file is in

MODEL_PATH = BASE_DIR / "resources/voices/kokoro-v1.0.onnx"
VOICES_PATH = BASE_DIR / "resources/voices/voices-v1.0.bin"

if not MODEL_PATH.exists():
    print("Voice model not found. Please run install.bat first.")
    sys.exit(1)

kokoro = Kokoro(MODEL_PATH, VOICES_PATH)

def speak_comment(text: str, voice_name: str = "am_adam"):
	if not text:
		return

	# Generate audio samples via Kokoro ONNX
	samples, sample_rate = kokoro.create(text, voice=voice_name, speed=1.1, lang="en-us")
	return samples, sample_rate
	# Scale volume directly on the numpy array and play via sounddevice
	# scaled_samples = samples * volume
	# sd.play(scaled_samples, sample_rate)
	# sd.wait()  # Blocks until playback finishes, matching your original flow