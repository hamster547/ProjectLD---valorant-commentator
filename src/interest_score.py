from event_detector import EVENTS
from game_state import GameState

def score_visible(vis):
	if vis == 1:
		return 0.05
	if vis == 2:
		return 0.5
	if vis == 3:
		return 1
	return 0

def score_appeared(appeared):
	if appeared == 1:
		return 0.05
	if appeared == 2:
		return 0.7
	if appeared == 3:
		return 1.5
	return 0

def evaluate_interest_score(states: list[GameState], events: list[dict[EVENTS, int]], window_size: int):
	
	deaths = 0
	for state, event in zip(states, events):
		if state.is_dead:
			deaths += 1
		if event[EVENTS.DIED] != 0:
			# print("\tdied: INFINITE")
			return -1
	if deaths > window_size // 2:
		# print("\tmostly deaths: 0")
		return 0
	
	for state, event in zip(states, events):
		if event[EVENTS.ROUND_WON] != 0:
			# print("\tround won: INFINITE")
			return -1
		if event[EVENTS.ROUND_LOST] != 0:
			# print("\tround lost: INFINITE")
			return -1
	
	kills = 0
	for event in events:
		kills += event[EVENTS.GOT_KILLS]
		if kills >= 2:
			# print("\t2+ kills: INFINITE")
			return -1
	for state in states:
		if state.visible_enemies >= 4:
			# print("\t4+ visible enemies: INFINITE")
			return -1

	total_score = 0
	i = 1
	for state, event in zip(states, events):
		# print(f"state {i}:")
		score = 0
		if event[EVENTS.HP_DOWN] > 0:
			# print("\thp down:", event[EVENTS.HP_DOWN] / 150)
			score += event[EVENTS.HP_DOWN] / 75
		
		if event[EVENTS.HP_UP] > 0:
			# print("\thp up:", event[EVENTS.HP_UP] / 150)
			score += event[EVENTS.HP_UP] / 75

		if event[EVENTS.SHOTS_FIRED] > 0:
			# print("\tshots fired:", event[EVENTS.SHOTS_FIRED]*2 / state.max_ammo)
			score += event[EVENTS.SHOTS_FIRED]*2 / state.max_ammo

		if event[EVENTS.RELOAD] > 0:
			# print("\treload:", 0.5)
			score += 0.5

		# if event[EVENTS.ENEMIES_APPEARED] > 0:
		# 	# print("\tenemies appeared:", event[EVENTS.ENEMIES_APPEARED] * score_appeared(event[EVENTS.ENEMIES_APPEARED]))
		# 	score += event[EVENTS.ENEMIES_APPEARED] * score_appeared(event[EVENTS.ENEMIES_APPEARED])

		if event[EVENTS.GOT_KILLS] > 0:
			print("\tgot kill:", 10)
			score += 10
		# print("    total:", score)
		total_score += score
		i += 1
	# print("TOTAL SCORE:", total_score)
	return total_score