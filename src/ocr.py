import cv2
import easyocr
import numpy as np
from weapon_matcher import identify_weapon


class OCR:
	def __init__(self):
		self.reader = easyocr.Reader(["en"], gpu=True)
		self._warmup()

	def _warmup(self):
		dummy = np.zeros((30, 50), dtype=np.uint8)
		self.reader.readtext(dummy, detail=0, allowlist="0123456789")

	def read(self, frame):
		if frame is None:
			return None, None, None, None
		hp, shield = self.read_hp(frame)
		ammo = self.read_ammo(frame)
		teamr, enemyr = self.read_rounds(frame)

		return hp, shield, ammo, teamr, enemyr

	def read_weapon(self, frame):
		x, y = 1062, 388
		width, height = 200, 230
		crop = frame[y:y+height, x:x+width]

		gun_text = self.reader.readtext(crop, detail=0)

		return identify_weapon(gun_text)

	def read_hp(self, frame):
		x, y = 355, 667
		width, height = 30, 35
		shield_crop = frame[y:y+height, x:x+width]
		shield_crop = shield_crop[9:9+15, 8:8+15]
		shield_crop = cv2.resize(shield_crop, (30, 30))
		x += width
		width = 50
		hp_crop = frame[y:y+height, x:x+width]
		hp_crop = cv2.resize(hp_crop, (100, 70))

		hp_text = self.reader.readtext(hp_crop, detail=0, allowlist="0123456789")
		shield_text = self.reader.readtext(shield_crop, detail=0, allowlist="0123456789")

		if not hp_text:
			if not shield_text or shield_text[0] == '':
				return None, None
			return None, int(shield_text[0])
		elif not shield_text:
			if hp_text[0] == '':
				return None, None
			return int(hp_text[0]), None
		if shield_text[0] == '':
			if hp_text[0] == '':
				return None, None
			return int(hp_text[0]), None
		elif hp_text[0] == '':
			return None, int(shield_text[0])
		return int(hp_text[0]), int(shield_text[0])

	def read_ammo(self, frame):
		x = 850
		y = 666
		width = 37
		height = 35
		ammo_crop = frame[y:y+height, x:x+width]
		b, g, r = cv2.split(ammo_crop)
		mask = (
			(b > 230) &
			(g > 230) &
			(r > 230)
		)
		ammo_crop = (mask * 255).astype("uint8")
		
		ammo_text = self.reader.readtext(ammo_crop, detail=0, allowlist="0123456789")
		if not ammo_text or ammo_text[0] == '':
			return None

		return int(ammo_text[0])

	def read_rounds(self, frame):
		x, y = 537, 24
		width, height = 24, 20

		team_rounds = frame[y:y+height, x:x+width]
		team_rounds = cv2.resize(team_rounds, (72, 60))

		x = 721
		enemy_rounds = frame[y:y+height, x:x+width]
		enemy_rounds = cv2.resize(enemy_rounds, (72, 60))

		team_text = self.reader.readtext(team_rounds, detail=0, allowlist="0123456789")
		enemy_text = self.reader.readtext(enemy_rounds, detail=0, allowlist="0123456789")

		if not team_text:
			if not enemy_text or enemy_text[0] == '':
				return None, None
			return None, int(enemy_text[0])
		elif not enemy_text:
			if team_text[0] == '':
				return None, None
			return int(team_text[0]), None
		if team_text[0] == '':
			if enemy_text[0] == '':
				return None, None
			return None, int(enemy_text[0])
		if enemy_text[0] == '':
			return int(team_text[0]), None
		return int(team_text[0]), int(enemy_text[0])