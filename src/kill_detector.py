import cv2
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # the folder this .py file is in

def match_template(enemy_crop, agent_temp):
	template_bgr = agent_temp[:, :, :3]
	alpha = agent_temp[:, :, 3]

	mask = alpha > 180

	difference = cv2.absdiff(template_bgr, enemy_crop)

	difference = difference[mask]

	score = difference.mean()

	return score

class KillDetector:
	def __init__(self):
		self.agent_names = [
			"astra", "breach", "brimstone", "chamber",
			"clove", "cypher", "deadlock", "fade",
			"gekko", "harbor", "iso", "jett", "kayo",
			"killjoy", "miks", "neon", "omen",
			"phoenix", "raze", "reyna", "sage", "skye",
			"sova", "tejo", "veto", "viper", "vyse",
			"waylay", "yoru"
		]

		self.top_bar_temps = []
		self.kill_feed_temps = []

		self.load_templates()

	def load_templates(self):
		for name in self.agent_names:
			path = BASE_DIR / str("resources/top_bar_portrait_templates/" + name + ".png")
			self.top_bar_temps.append(cv2.imread(path, cv2.IMREAD_UNCHANGED))
			path = BASE_DIR / str("resources/kill_feed_portrait_templates/" + name + ".png")
			self.kill_feed_temps.append(cv2.imread(path, cv2.IMREAD_UNCHANGED))

	def identify_agent_top(self, agent, flip=False):
		best_match = None
		best_score = 255

		for i in range(0, len(self.agent_names)):
			temp = self.top_bar_temps[i]
			if flip:
				temp = cv2.flip(temp, 1)
			score = match_template(agent, temp)

			if score > 28:
				continue
			if score < best_score:
				best_match = self.agent_names[i]
				best_score = score

		return best_match

	def identify_agent_kfeed(self, agent):
		best_match = None
		best_score = 255
	
		for i in range(0, len(self.agent_names)):
			score = match_template(agent, self.kill_feed_temps[i])
	
			if score < best_score:
				best_match = self.agent_names[i]
				best_score = score
	
		return best_match

	def detect_team_top_bar(self, frame):
		288, 20, 220, 27
		10, 1
		if frame is None:
			return None
		x, y = 288, 20
		width, height = 220, 27
		size = 25
		team_top_bar = frame[y:y+height, x:x+width]

		x, y = 10, 1
		names = []
		for i in range(0, 5):
			name = self.identify_agent_top(team_top_bar[y:y+size, x:x+size], True)
			if name is not None:
				names.append(name)
			x += 44

		return names

	def detect_enemy_top_bar(self, frame):
		if frame is None:
			return None
		x, y = 771, 20
		width, height = 220, 27
		size = 25
		enemy_top_bar = frame[y:y+height, x:x+width]

		x, y = 11, 1
		names = []
		for i in range(0, 5):
			name = self.identify_agent_top(enemy_top_bar[y:y+size, x:x+size])
			if name is not None:
				names.append(name)
			x += 44

		return names

	def is_my_kill(self, frame):
		x,y = 868, 82# 74
		width, height = 350, 5

		slots = [False, False, False, False, False]

		for i in range(0, 5):
			crop = frame[y:y+height, x:x+width]
			lower = np.array([135, 220, 200])
			upper = np.array([175, 245, 245])
			# lower = np.array([90, 220, 220])
			# upper = np.array([135, 245, 245])
			mask = cv2.inRange(crop, lower, upper)

			if np.any(mask):
				slots[i] = True

			y += 26

		return slots

	def detect_my_kill_feed(self, frame):
		if frame is None:
			return None
		x, y = 1222, 65 # 65, 91, 117, 143; +26
		width, height = 44, 21

		my_slots = self.is_my_kill(frame)
		names = []

		for i in range(0, 5):
			if my_slots[i]:
				name = self.identify_agent_kfeed(frame[y:y+height, x:x+width])
				names.append(name)

			y += 26

		return names