from ai_comment import Commentator
import time


window_prompt = """
CURRENT GAME WINDOW:
BASELINE: Started with 100 HP 50 Shield and a ares (50 magazine size)
TIMELINE OF EVENTS:
-fired 3 shots
-Took 22 damage, fired 6 shots
-got 1 kill, fired 3 shots
-fired 1 shots"""

commentator = Commentator()
while True:
	print(commentator.comment(window_prompt))
	time.sleep(1)