import sys
import ctypes
import random
import threading
import numpy as np
import sounddevice as sd
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QKeyEvent
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

# Global state flag shared between your background TTS thread and the UI avatar loop
is_talking = False

audio_lock = threading.Lock()

def play_audio_stream(samples: np.ndarray, sample_rate: int, volume: float = 0.2):
    with audio_lock:
        global is_talking
        scaled_samples = (samples * volume).astype(np.float32)
        cursor = 0
        total_frames = len(scaled_samples)
        block_size = 1024
        threshold = 0.01

        # --- HANGOVER BUFFERS ---
        # Number of consecutive silent chunks to wait before actually declaring "not talking"
        silence_counter = 0
        silence_grace_limit = 6  # 6 chunks * ~43ms = ~250ms smooth grace window

        def callback(outdata, frames, time_info, status):
            nonlocal cursor, silence_counter
            global is_talking
            if cursor >= total_frames:
                outdata[:] = 0
                raise sd.CallbackStop()

            chunk_end = min(cursor + block_size, total_frames)
            current_chunk = scaled_samples[cursor:chunk_end]
        
            if len(current_chunk) < frames:
                current_chunk = np.pad(current_chunk, (0, frames - len(current_chunk)))

            outdata[:len(current_chunk), 0] = current_chunk

            # Real-time RMS volume check
            rms = np.sqrt(np.mean(current_chunk**2))
            is_speaking_now = rms > threshold

            if is_speaking_now:
                # Reset silence counter the second we hear sound
                silence_counter = 0
                is_talking = True
            else:
                # We hit a quiet chunk. Instead of dropping immediately, increment counter.
                silence_counter += 1
                if silence_counter > silence_grace_limit:
                    is_talking = False  # Only go idle after grace period expires

            cursor = chunk_end

        try:
            with sd.OutputStream(samplerate=sample_rate, channels=1, callback=callback, blocksize=block_size) as stream:
                while stream.active:
                    sd.sleep(20)
        except Exception as e:
            print(f"Audio stream error: {e}")
        finally:
            is_talking = False


class AvatarOverlay(QWidget):
    """Pure UI Widget living on the main PyQt thread. Handles rendering, sprites, and jitter."""
    def __init__(self, idle_path="idle.png", talking_path="talking.png"):
        super().__init__()

        # Window configuration & Click-through setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

	
        self.idle_path = idle_path
        self.talking_path = talking_path
        self.padding = 25
        self.avatar_size = 250
        total_size = self.avatar_size + (self.padding * 2)
        self.resize(total_size, total_size)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        # Assets
        self.idle_pixmap = self._load_pixmap(idle_path)
        self.talking_pixmap = self._load_pixmap(talking_path)
        self.image_label.setPixmap(self.idle_pixmap)
        self.current_display_state = "idle"
        self.reload_sprites()

        # Main UI Loop Timer (~25 FPS) automatically polls the global is_talking flag
        self.loop_timer = QTimer(self)
        self.loop_timer.setInterval(40)
        self.loop_timer.timeout.connect(self._update_loop)
        self.loop_timer.start()

    def reload_sprites(self):
        """Loads/reloads pixmaps using current avatar_size and stored paths."""
        self.idle_pixmap = self._load_pixmap(self.idle_path)
        self.talking_pixmap = self._load_pixmap(self.talking_path)

        # Refresh current visible pixmap based on display state
        if self.current_display_state == "talking":
            self.image_label.setPixmap(self.talking_pixmap)
        else:
            self.image_label.setPixmap(self.idle_pixmap)

    def set_avatar_size(self, new_size: int):
        """Updates size, resizes transparent window, and rescales sprites."""
        self.avatar_size = new_size
        total_size = self.avatar_size + (self.padding * 2)

        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX

        # 2. Reload sprites first so internal labels adjust size hints
        self.reload_sprites()

        # 3. Resize window first to force layout recalculation
        self.resize(total_size, total_size)

        # 4. Now snap position to bottom left cleanly in a single pass!
        screen_height = 1440  # or QApplication.primaryScreen().geometry().height()
        self.move(0, screen_height - total_size)

        self.reload_sprites()

    def set_idle_path(self, path: str):
        """Updates idle path and reloads pixmaps."""
        if path:
            self.idle_path = path
            self.reload_sprites()

    def set_talking_path(self, path: str):
        """Updates talking path and reloads pixmaps."""
        if path:
            self.talking_path = path
            self.reload_sprites()

    def reset_to_defaults(self):
        """Resets avatar size and paths back to KAY/O default settings."""
        self.idle_path = "idle.png"
        self.talking_path = "talking.png"
        self.set_avatar_size(250)

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex_style | 0x00000020 | 0x00080000)
            except Exception as e:
                print(f"Failed to set win32 click-through: {e}")

    def _load_pixmap(self, path) -> QPixmap:
        pixmap = QPixmap(path)
        if pixmap.isNull():
            fallback = QPixmap(self.avatar_size, self.avatar_size)
            fallback.fill(Qt.GlobalColor.transparent)
            return fallback
        return pixmap.scaled(
            self.avatar_size, self.avatar_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _update_loop(self):
        """Runs autonomously via QTimer: checks global `is_talking` and handles animations/jitter safely."""
        global is_talking
        if is_talking:
            if self.current_display_state != "talking":
                self.current_display_state = "talking"
                self.image_label.setPixmap(self.talking_pixmap)
            
            # Apply micro-jitter within the padding buffer
            shake = 3
            dx = random.randint(-shake, shake)
            dy = random.randint(-shake, shake)
            self.layout().setContentsMargins(
                self.padding + dx, self.padding + dy,
                self.padding - dx, self.padding - dy
            )
        else:
            if self.current_display_state != "idle":
                self.current_display_state = "idle"
                self.image_label.setPixmap(self.idle_pixmap)
                # Reset margins
                self.layout().setContentsMargins(self.padding, self.padding, self.padding, self.padding)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()
        else:
            super().keyPressEvent(event)