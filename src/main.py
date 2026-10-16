import time
import threading
import queue
import cv2
import random
from capture import ScreenCapture
from vision import Perception
from game_state import GameState
from event_detector import EventDetector
from interest_score import evaluate_interest_score
from prompt_filter import build_fight, pick_fact
from ai_comment import Commentator, clean
from tts import speak_comment
from config import Config
from avatar import play_audio_stream

time.sleep(3)
perception = Perception()
commentator = Commentator()
event_detector = EventDetector()

pipeline_config = Config()

pipeline_config.agent = "astra"
pipeline_config.voice = "am_adam"
pipeline_config.persona = "roast"
pipeline_config.volume = 0.5


prompt_queue = queue.Queue()
tts_queue = queue.Queue()

def mood(f):
	if f.died or (f.round_lost and not f.kills):
		return "bad"
	return "good"

GOOD_WORDS = ["unreal", "insane", "filthy", "cinematic", "historic", "disgusting", "clean", "ridiculous"]
BAD_BLAME = ["lag", "the servers", "anti-cheat", "the bullet spread", "the map", "a ghost bug", "Riot", "ping"]

def hype_hint(mood):
    if mood == "good":
        words = ", ".join(random.sample(GOOD_WORDS, 2))
        return f"MOOD: He did great. Go wild, like it is the best thing you have ever seen. You could use words like {words}."
    else:
        blame = ", ".join(random.sample(BAD_BLAME, 2))
        return f"MOOD: That went badly and you cannot believe it. Act shocked and blame something other than him, like {blame}."

hint = {
	"bad": "He messed up. Mock him for it.",
	"good": "He did well. Refuse to give him credit: blame luck, a sleeping enemy, or a bad opponent.",
}


def llm_worker():
	while True:
		window_data = prompt_queue.get()
		try:
			comment = commentator.comment(window_data)
			comment = clean(comment)
			if comment is None:
				comment = commentator.comment(window_data)
				if pipeline_config.persona != "advance kymasu roaster":
					comment = clean(comment)				
			print(comment + "\n")
			if comment:
				tts_queue.put(comment)
		except Exception as e:
			print(f"LLM Error: {e}")
		finally:
			prompt_queue.task_done()

def tts_worker():
	while True:
		comment = tts_queue.get()
		try:
			samples, sample_rate = speak_comment(comment, pipeline_config.voice)
			play_audio_stream(samples, sample_rate, pipeline_config.volume)
		except Exception as e:
			print(f"TTS Error: {e}")
		finally:
			tts_queue.task_done()

class Pipeline:
	def __init__(self):
		self.stl_current_round = 1
		self.stl_won = 0
		self.stl_lost = 0
		self.stl_top_bar_enemies = []
		self.locr_won = 0
		self.locr_lost = 0
		self.last_game_state = GameState()

		self.states_window = []
		self.events_window = []
		self.window_size = 10

		self.last_states_buffer = []
		self.last_events_buffer = []
		self.buffer_size = 2		

		self.INTEREST_THRESHOLD = 10
		
		commentator.change_persona(pipeline_config.persona)
		self.capture = ScreenCapture() # eventually mss

		threading.Thread(target=llm_worker, daemon=True).start()
		threading.Thread(target=tts_worker, daemon=True).start()

	def changePersona(self, persona):
		pipeline_config.persona = persona
		commentator.change_persona(pipeline_config.persona)

	def pipeline_thread(self):
		start = time.perf_counter()

		frame = self.capture.get_frame() # needs mss on windows
		
		results = perception.process_frame(frame)

		game_state = GameState()
		game_state.resolve_from_capture(
			results, self.last_game_state, self.stl_top_bar_enemies,
			self.stl_current_round, self.stl_won, self.stl_lost,
			self.locr_won, self.locr_lost,
			pipeline_config.agent)
		
		events = event_detector.detect_events(game_state, self.last_game_state)

		self.states_window.append(game_state)
		self.events_window.append(events)

		if len(self.states_window) == self.window_size and len(self.events_window) == self.window_size:
			score = evaluate_interest_score(self.states_window, self.events_window, self.window_size)
			if score == -1 or score >= self.INTEREST_THRESHOLD:
				f = build_fight(self.states_window, self.events_window, self.last_states_buffer, self.last_events_buffer)
				fact = pick_fact(f)
				print("\n")
				print(fact)
				print(f)
				if fact is not None:
					if pipeline_config.persona == "roast":
						prompt_queue.put("React to this fact in one short sentence.\nFACT: " + fact + "\n" + hint[mood(f)])
					elif pipeline_config.persona == "hype":
						prompt_queue.put("React to this fact in one short sentence.\nFACT: " + fact + "\n" + hype_hint(mood(f)))
					else:
						prompt_queue.put("React to this fact in one short sentence.\nFACT: " + fact)
			self.last_states_buffer.append(self.states_window)
			self.last_events_buffer.append(self.events_window)
			self.last_states_buffer[-self.buffer_size:]
			self.last_events_buffer[-self.buffer_size:]
			self.states_window.clear()
			self.events_window.clear()
			

		self.stl_current_round = self.last_game_state.current_round
		self.stl_won = self.last_game_state.rounds_won
		self.stl_lost = self.last_game_state.rounds_lost
		self.stl_top_bar_enemies = self.last_game_state.top_bar_enemies
		self.locr_won = results["team_rounds"]
		self.locr_lost = results["enemy_rounds"]
		self.last_game_state = game_state

		end = time.perf_counter() - start

		# print("hp:", game_state.hp)
		# print("shield:", game_state.shield)
		# print("rounds won:", game_state.rounds_won)
		# # print("ocr won:", results["team_rounds"])
		# print("rounds lost:", game_state.rounds_lost)
		# # print("ocr lost:", results["enemy_rounds"])
		# print("current round:", game_state.current_round)
		# print("equipped weapon:", game_state.equipped_weapon)
		# print(f"ammo: {game_state.ammo}/{game_state.max_ammo}")
		# print("visible enemies:", game_state.visible_enemies)
		# print("is dead:", game_state.is_dead)
		# print("total deaths:", game_state.total_deaths)
		# print("round kills:", game_state.round_kills)
		# print("total kills:", game_state.total_kills)
		# print("top bar enemies:", game_state.top_bar_enemies)
		# print(*events.items(), sep="\n")
		
		# print("hp:", results["hp"])
		# print("shield:", results["shield"])
		# print("ammo:", results["ammo"])
		# print("team rounds:", results["team_rounds"])
		# print("enemy rounds:", results["enemy_rounds"])
		# print("weapon switch:", results["weapon_switch"])
		# print("enemy top bar names:", results["enemy_top_bar_names"])
		# print("team top bar names:", results["team_top_bar_names"])
		# print("my kill feed names:", results["my_kill_feed_names"])
		# print("processing time:", results["processing_time"])
		
		# print("processing time:", end)
		time.sleep(max(1/3 - end, 0))