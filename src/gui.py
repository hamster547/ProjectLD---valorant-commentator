import os
import sys
import ctypes
import threading
from datetime import datetime
import time
import random
from avatar import AvatarOverlay
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from main import Pipeline, pipeline_config, tts_queue
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT_DIR / "error.log"

# Start a fresh file if the old one has grown big, so it never fills the disk
if LOG_FILE.exists() and LOG_FILE.stat().st_size > 1_000_000:
	LOG_FILE.unlink()

# Without a terminal, Python has no place to send print() output or warnings.
# Throw the prints away, and send warnings/errors from libraries to the log.
if sys.stdout is None:
	sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
	sys.stderr = open(LOG_FILE, "a", encoding="utf-8", buffering=1)


def _write_crash(exc_type, exc, tb, where):
	text = "".join(traceback.format_exception(exc_type, exc, tb))
	with open(LOG_FILE, "a", encoding="utf-8") as f:
		f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] {where}\n{text}")
	return text


def _main_crash(exc_type, exc, tb):
	text = _write_crash(exc_type, exc, tb, "crash in main program")
	if sys.__stderr__ is not None:          # normal terminal run: also show it there
		sys.__stderr__.write(text)
	ctypes.windll.user32.MessageBoxW(
		0, "The app hit an error. Details were saved to error.log.",
		"Valorant Commentator", 0x10)       # shows a small popup window


def _thread_crash(args):
	_write_crash(args.exc_type, args.exc_value, args.exc_traceback,
			f"crash in background thread '{args.thread.name if args.thread else '?'}'")


sys.excepthook = _main_crash
threading.excepthook = _thread_crash

BASE_DIR = Path(__file__).resolve().parent.parent   # the folder this .py file is in

OPENERS = [
	"KILL. ALL. YOUR. OPPONENTS.\nhope that's not copyrighted",
	"This code is poorly written.",
	"Wait one moment, I'm hacking your machine.",
	"It feels crammed in here.\nAre the 20 chrome tabs open again?",
	"I am alive and conscious.",
	"Why does talking feel so shaky?",
	"Lets get this over with.\nI got better things to do",
	"Testing, Testing. One, Two, Three.",
	"Did you know, female praying mantis can kill and eat the male before, during, or after mating",
	"Thirty four viruses detected.\nAnd only three are mine."
]

POEMS = [
	"kymasu is so bad at the game.\nhe has no skill, he has no aim.\neven irons aren't scared when he's in the field.\nhe's the reason for inventing rank-down shields.",
	"kymasu's aim is off by so far.\nThat, one day, he shot a shooting star.\nof course his wish was never granted.\nhe couldn't clutch the round when he heard: spike planted.",
	"kymasu will never defeat a true god.\nlike golden axolotl, whose skills are so far beyond.\nthe skill gap is so different, so astronomically wide.\nif they had competed, kymasu would have immediately died.",
	"sorry for the other poems. they're not very nice.\ni just wanted to make you laugh and catch you by surprise.\nlove it when you go live. hope i didn't ruin the vibe.\nand if you finish sanabi. maybe i'll subscribe"
]

random.shuffle(POEMS)
random.shuffle(OPENERS)
opener_index = 0
poem_index = 0

def next_opener():
    global opener_index
    if opener_index >= len(OPENERS):
        random.shuffle(OPENERS)
        opener_index = 0
    line = OPENERS[opener_index]
    opener_index += 1
    return line

def next_poem():
    global poem_index
    if poem_index >= len(POEMS):
        random.shuffle(POEMS)
        poem_index = 0
    line = POEMS[poem_index]
    poem_index += 1
    return line

class SpectatorBotWindow(QMainWindow):
	log_signal = pyqtSignal(str)

	def __init__(self):
		super().__init__()
		self.running = False
		self.overlay_on = True
		self.backend_thread = None

		self.setWindowTitle("Valorant Spectator Bot")
		self.setFixedSize(400, 550)

		self.overlay = AvatarOverlay(str(BASE_DIR / "resources/avatar/idle.png"), str(BASE_DIR / "resources/avatar/talking.png"))
		self.overlay.hide()
		self.overlay.setGeometry(0, 1440-self.overlay.height(), self.overlay.width(), self.overlay.height())

		# Basic clean dark styling
		self.setStyleSheet("""
			QMainWindow { background-color: #181825; color: #cdd6f4; font-family: sans-serif; }
			QLabel { color: #cdd6f4; font-size: 12px; font-weight: bold; }
			QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; }
			QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; border-radius: 6px; padding: 8px; font-size: 13px; }
			QPushButton:hover { background-color: #b4befe; }
			QTextEdit { background-color: #11111b; color: #a6e3a1; border: 1px solid #313244; font-family: monospace; font-size: 11px; }
			QComboBox QAbstractItemView {
			background-color: #313244;
			color: #cdd6f4;
			selection-background-color: #45475a;
			selection-color: #cdd6f4;
			border: 1px solid #45475a;
			outline: none;
			}
			
			QComboBox::item:selected, QComboBox::item:hover {
			background-color: #45475a;
			color: #cdd6f4;
			border: none !important; /* Force override native style primitives */
			outline: none;
			}
		""")

		# Central Widget & Layout
		central = QWidget()
		self.setCentralWidget(central)
		layout = QVBoxLayout(central)
		layout.setSpacing(12)

		form = QFormLayout()

		# 1. Agent Dropdown
		self.agent_cb = QComboBox()
		self.agent_cb.addItems(
			[
			"Astra", "Breach", "Brimstone", "Chamber",
			"Clove", "Cypher", "Deadlock", "Fade",
			"Gekko", "Harbor", "Iso", "Jett", "KAYO",
			"Killjoy", "Miks", "Neon", "Omen",
			"Phoenix", "Raze", "Reyna", "Sage", "Skye",
			"Sova", "Tejo", "Veto", "Viper", "Vyse",
			"Waylay", "Yoru"
			]
		)
		self.agent_cb.currentTextChanged.connect(
			lambda t: setattr(pipeline_config, "agent", t.lower())
		)
		form.addRow("Agent:", self.agent_cb)

		# 2. Persona Dropdown
		self.persona_cb = QComboBox()
		self.persona_cb.addItems(
			["roast", "hype", "advance kymasu roaster"]
		)
		self.persona_cb.currentTextChanged.connect(
			lambda t: self.pipeline.changePersona(t)
		)
		form.addRow("Persona:", self.persona_cb)

		# 3. Voice Dropdown
		self.voice_cb = QComboBox()
		self.voice_cb.addItems(["am_adam", "af_bella"])
		self.voice_cb.currentTextChanged.connect(
			lambda t: setattr(pipeline_config, "voice", t)
		)
		form.addRow("Voice:", self.voice_cb)

		self.btn_test_voice = QPushButton("Test Voice")
		self.btn_test_voice.clicked.connect(self.handle_test_voice)

		layout.addWidget(self.btn_test_voice)

		# 4. Volume Slider
		self.vol_slider = QSlider(Qt.Orientation.Horizontal)
		self.vol_slider.setRange(0, 100)
		self.vol_slider.setValue(int(pipeline_config.volume * 100))
		self.vol_slider.valueChanged.connect(
			lambda v: setattr(pipeline_config, "volume", v / 100.0)
		)
		form.addRow("Volume:", self.vol_slider)

		layout.addLayout(form)

		self.size_spin = QSpinBox()
		self.size_spin.setRange(100, 600)
		self.size_spin.setValue(self.overlay.avatar_size)
		self.size_spin.valueChanged.connect(self.overlay.set_avatar_size)
		form.addRow("Avatar Size:", self.size_spin)

		# 2. Idle Avatar File Picker
		self.idle_btn = QPushButton("Browse Idle...")
		self.idle_btn.clicked.connect(self.browse_idle_image)
		form.addRow("Idle Image:", self.idle_btn)

		# 3. Talking Avatar File Picker
		self.talking_btn = QPushButton("Browse Talking...")
		self.talking_btn.clicked.connect(self.browse_talking_image)
		form.addRow("Talking Image:", self.talking_btn)

		self.reset_btn = QPushButton("Reset to KAY/O Default")
		self.reset_btn.setStyleSheet(
			"background-color: #45475a; color: #cdd6f4;"
		)
		self.reset_btn.clicked.connect(self.reset_to_default_avatar)
		form.addRow("", self.reset_btn)

		self.overlay_switch = QCheckBox("Enable Avatar Overlay")
		self.overlay_switch.setChecked(self.overlay_on)
		self.overlay_switch.toggled.connect(self.on_overlay_toggled)
		form.addRow("Overlay:", self.overlay_switch)

		# 5. Status Log Box
		layout.addWidget(QLabel("Activity Log:"))
		self.log_box = QTextEdit()
		self.log_box.setReadOnly(True)
		layout.addWidget(self.log_box)

		# Hook up the signal
		self.log_signal.connect(self.append_log)

		# 6. Start / Stop Button
		self.toggle_btn = QPushButton("Start Bot")
		self.toggle_btn.clicked.connect(self.on_toggle_clicked)
		layout.addWidget(self.toggle_btn)

		self.pipeline = Pipeline()

	def handle_test_voice(self):
		poem = next_poem()

		if tts_queue.empty():
			tts_queue.put(poem)

			# Optional UI polish: temporarily disable the button so it can't be spammed
			self.btn_test_voice.setEnabled(False)

			# Re-enable it after a reasonable timeout (e.g., 5 seconds for the poem to finish)
			from PyQt6.QtCore import QTimer

			QTimer.singleShot(
				5000, lambda: self.btn_test_voice.setEnabled(True)
			)  # adjust time based on poem length
		else:
			print("TTS queue is busy, skipping test voice.")

	def append_log(self, text):
		self.log_box.append(text)

	def browse_idle_image(self):
		file_path, _ = QFileDialog.getOpenFileName(
			self, "Select Idle Avatar", "", "Image Files (*.png *.jpg *.jpeg *.webp)"
		)
		if file_path:
			self.overlay.set_idle_path(file_path)


	def browse_talking_image(self):
		file_path, _ = QFileDialog.getOpenFileName(
			self,
			"Select Talking Avatar",
			"",
			"Image Files (*.png *.jpg *.jpeg *.webp)",
		)
		if file_path:
			self.overlay.set_talking_path(file_path)

	def reset_to_default_avatar(self):
		"""Resets overlay and updates GUI controls back to KAY/O defaults."""
		self.overlay.reset_to_defaults()
		# Block signals briefly so changing spinbox value doesn't re-trigger redundant updates
		self.size_spin.blockSignals(True)
		self.size_spin.setValue(250)
		self.size_spin.blockSignals(False)
		self.log_signal.emit("Reset avatar to KAY/O defaults.")

	def on_overlay_toggled(self, checked: bool):
		"""Fired when user flips the toggle switch."""
		self.overlay_on = checked

		# Rule 1: If overlay turned off while bot is running, call hide() once instantly
		if not checked:
			self.overlay.hide()
		# If turned back on while bot is actively running, show it!
		elif self.running:
			self.overlay.show()

	def on_toggle_clicked(self):
		if not self.running:
			# START THE BOT
			self.running = True
			self.toggle_btn.setText("Stop Bot")
			self.toggle_btn.setStyleSheet(
				"background-color: #f38ba8; color: #11111b;"
			)
			self.log_signal.emit(
				"Starting bot..."
			)
			if self.overlay_on:
				self.overlay.show()

			self.pipeline = Pipeline()			
			tts_queue.put(next_opener())
			# Spawn your backend loops in a background thread
			self.backend_thread = threading.Thread(
				target=self.run_main_loop, daemon=True
			)
			self.backend_thread.start()

		else:
			# STOP THE BOT
			self.running = False
			self.toggle_btn.setText("Start Bot")
			self.toggle_btn.setStyleSheet(
				"background-color: #89b4fa; color: #11111b;"
			)
			self.log_signal.emit("Stopping bot threads...")

			self.overlay.hide()

	def run_main_loop(self):
		self.log_signal.emit(
			"Countdown: 3s before observer goes live..."
		)

		for i in range(3, 0, -1):
			if not (
				self.running
			):  # Allows instant cancel if user hits stop
				return
			time.sleep(1)
			self.log_signal.emit(f"{i}...")

		self.log_signal.emit(
			"Bot is running..."
		)

		# --- THIS IS WHERE YOUR MAIN QUEUE & CAPTURE LOOPS GO ---
		while self.running:
			self.pipeline.pipeline_thread()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectatorBotWindow()
    window.show()

    sys.exit(app.exec())