import mss
import numpy as np
import cv2
import time

class ScreenCapture:
	def __init__(self):
		self.sct = mss.MSS()
		self.monitor = self.sct.primary_monitor

	def get_frame(self):
		return np.array(self.sct.grab(self.monitor))