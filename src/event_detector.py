from enum import Enum
from game_state import GameState

class EVENTS(Enum):
	GOT_KILLS = 1
	DIED = 2
	HP_UP = 3
	HP_DOWN = 4
	ROUND_WON = 5
	ROUND_LOST = 6
	SWAPPED_WEAPON = 7
	RELOAD = 8
	SHOTS_FIRED = 9

# gs - game state
# [number]_last_gs - the [number] to last game state

def reslove_kills(current_gs: GameState, last_gs: GameState):
	kills = current_gs.total_kills - last_gs.total_kills
	if kills > 0:
		print("KILL")
	return max(0, kills)

def resolve_death(current_gs: GameState, last_gs: GameState):
	died = current_gs.total_deaths - last_gs.total_deaths
	return max(0, died)

def resolve_hp(current_gs: GameState, last_gs: GameState):
	current_shield = current_gs.shield
	last_shield = last_gs.shield
	if current_gs.hp is None:
		return 0, 0
	if current_gs.shield is None:
		current_shield = 0
	if last_gs.hp is None:
		return 0, 0
	if last_gs.shield is None:
		last_shield = 0

	hp_diff = current_gs.hp + current_shield - last_gs.hp - last_shield
	if hp_diff < 0:
		return abs(hp_diff), 0
	elif hp_diff > 0:
		return 0, hp_diff
	return 0, 0

def resolve_rounds(current_gs: GameState, last_gs: GameState):
	if current_gs.rounds_won == last_gs.rounds_won + 1:
		return 1, 0
	if current_gs.rounds_lost == last_gs.rounds_lost + 1:
		return 0, 1
	return 0, 0

def resolve_weapon_swapping(current_gs: GameState, last_gs: GameState):
	if current_gs.equipped_weapon != last_gs.equipped_weapon:
		return 1
	return 0

def resolve_reload(current_gs: GameState, last_gs: GameState):
	if current_gs.ammo == current_gs.max_ammo and last_gs.ammo != last_gs.max_ammo:
		if resolve_weapon_swapping(current_gs, last_gs) == 0:
			return 1
	return 0

def resolve_enemies_appear(current_gs: GameState, last_gs: GameState):
	vis_diff = current_gs.visible_enemies - last_gs.visible_enemies
	if vis_diff > 0:
		return vis_diff
	return 0

def resolve_shots_fired(current_gs: GameState, last_gs: GameState):
	if current_gs.ammo is None or last_gs.ammo is None:
		return 0
	if resolve_weapon_swapping(current_gs, last_gs) == 1:
		return 0

	ammo_diff = current_gs.ammo - last_gs.ammo
	if ammo_diff < 0:
		return min(abs(ammo_diff), current_gs.max_ammo)
	return 0


class EventDetector:
	def __init__(self):
		self.events = {
			flag: 0
			for flag in EVENTS
		}

	def detect_events(self, current_gs: GameState, last_gs: GameState):
		self.events = {
			flag: 0
			for flag in EVENTS
		}

		self.events[EVENTS.GOT_KILLS] = reslove_kills(current_gs, last_gs)
		self.events[EVENTS.DIED] = resolve_death(current_gs, last_gs)
		self.events[EVENTS.HP_DOWN], self.events[EVENTS.HP_UP] = resolve_hp(current_gs, last_gs)		
		self.events[EVENTS.ROUND_WON], self.events[EVENTS.ROUND_LOST] = resolve_rounds(current_gs, last_gs)
		self.events[EVENTS.SWAPPED_WEAPON] = resolve_weapon_swapping(current_gs, last_gs)
		self.events[EVENTS.RELOAD] = resolve_reload(current_gs, last_gs)
		self.events[EVENTS.SHOTS_FIRED] = resolve_shots_fired(current_gs, last_gs)

		return self.events
