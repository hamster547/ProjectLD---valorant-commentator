import cv2
import time
from ocr import OCR
from kill_detector import KillDetector


class Perception:
	def __init__(self):
		self.ocr = OCR()
		self.kill_detector = KillDetector()

	def process_frame(self, frame):
		start = time.perf_counter()
		high_res_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
		frame = cv2.resize(frame, (1280, 720))
		frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

		hp, shield, ammo, teamr, enemyr = self.ocr.read(frame)
		weapon_switch = self.ocr.read_weapon(frame)

		enemy_top_bar_names = self.kill_detector.detect_enemy_top_bar(frame)
		my_kill_feed_names = self.kill_detector.detect_my_kill_feed(frame)
		team_top_bar_names = self.kill_detector.detect_team_top_bar(frame)

		processing_time = time.perf_counter() - start

		return {
			"hp": hp,
			"shield": shield,
			"ammo": ammo,
			"team_rounds": teamr,
			"enemy_rounds": enemyr,
			"weapon_switch": weapon_switch,
			"enemy_top_bar_names": enemy_top_bar_names,
			"team_top_bar_names": team_top_bar_names,
			"my_kill_feed_names": my_kill_feed_names,
			"processing_time": processing_time
		}

