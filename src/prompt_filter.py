from game_state import GameState
from event_detector import EVENTS
from dataclasses import dataclass
import random

@dataclass
class Fight:
	hp_start: int = 0
	hp_end: int = 0
	damage: int = 0
	shots: int = 0
	kills: int = 0
	died: bool = False
	round_won: bool = False
	round_lost: bool = False
	instant_death: bool = False


def build_fight(states, events, last_states_buffer, last_events_buffer):
	f = Fight()
	f.hp_start = states[0].hp + states[0].shield
	f.hp_end = states[-1].hp + states[-1].shield

	for state, event in zip(states, events):
		if event[EVENTS.HP_DOWN] <= 150:
			f.damage += event[EVENTS.HP_DOWN]
		if event[EVENTS.SHOTS_FIRED] <= state.max_ammo:
			f.shots += event[EVENTS.SHOTS_FIRED]
		f.kills += event[EVENTS.GOT_KILLS]
		if event[EVENTS.DIED]:
			f.died = True
			f.instant_death = (f.damage == 0)
			f.hp_end = 0
		if event[EVENTS.ROUND_WON]:
			f.round_won = True
		if event[EVENTS.ROUND_LOST]:
			f.round_lost = True
	# pass through the buffer backwards, add or break
	for state_win, event_win in reversed(list(zip(last_states_buffer, last_events_buffer))):
		for state, event in reversed(list(zip(state_win, event_win))):
			if event[EVENTS.GOT_KILLS] or event[EVENTS.DIED] or event[EVENTS.ROUND_WON] or event[EVENTS.ROUND_LOST]:
				return f
			if event[EVENTS.HP_DOWN] <= 150:
				f.damage += event[EVENTS.HP_DOWN]
			if event[EVENTS.SHOTS_FIRED] <= state.max_ammo:
				f.shots += event[EVENTS.SHOTS_FIRED]
			f.start_hp = state.hp + state.shield

	return f


def _kw(n):
	return "kill" if n == 1 else "kills"

def tag(f: Fight) -> list[tuple[int, str]]:
	"""Returns (priority, fact). Highest priority wins."""
	out = []

	# --- died ---
	if f.died:
		if f.instant_death and f.hp_start >= 100:
			out.append((85, "Went from full health to dead before firing a shot." if f.shots == 0
					else "Went from full health to dead in a blink."))
		if f.kills:
			out.append((95, f"Got {f.kills} {_kw(f.kills)} but died right after."))
		elif f.shots == 0:
			out.append((75, "Died without firing a single shot."))
		elif f.shots >= 15:
			out.append((70, f"Died after firing {f.shots} shots without getting a kill."))
		else:
			out.append((50, "Died in the fight."))
		return out

	# --- survived with kills ---
	if f.kills:
		# base fact: always present
		if f.kills >= 3:
			out.append((100, f"Got {f.kills} kills in one fight."))
		elif f.kills == 2:
			out.append((65, "Got 2 kills in one fight."))
		else:
			out.append((45, "Got a kill."))

		# upgrades: optional, only add more specific facts
		if f.hp_end <= 20:
			if f.round_won:
				out.append((90, f"Won the round with only {f.hp_end} HP left."))
			else:
				out.append((80, f"Got {f.kills} {_kw(f.kills)} but survived with only {f.hp_end} HP."))
		if f.damage == 0:
			out.append((70, f"Got {f.kills} {_kw(f.kills)} without taking a single hit."))
		if f.round_won:
			out.append((58, f"Got {f.kills} {_kw(f.kills)} and won the round."))
		if f.round_lost:
			out.append((62, f"Got {f.kills} {_kw(f.kills)} but still lost the round."))
		if f.kills == 1 and f.shots >= 10:
			out.append((60, f"Needed {f.shots} shots to get one kill."))
		if f.shots <= 3:
			out.append((55, f"Got {f.kills} {_kw(f.kills)} with only {f.shots} shots."))
		return out

	# --- no kill, no death ---
	if f.damage >= 60:
		out.append((40, f"Lost {f.damage} HP and got no kill."))
	return out  # empty = round-only or boring window, skipped on purpose

last_fact = None

def pick_fact(f):
	global last_fact
	tags = sorted(tag(f), reverse=True)
	if not tags:
		return None
	pool = [t for t in tags[:3] if t[1] != last_fact] or tags[:1]
	last_fact = random.choices(pool, weights=[t[0] for t in pool])[0][1]
	return last_fact