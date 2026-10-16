# [var name] refers to the captured value
# l_[var name] refers to the value in the last game state
# stl_[var name] refers to the value in the second to last game state (STL => Second To Last)
# there is a seperation between functions that need self and functions that dont
# this is sacaficing a bit of readability for less bloat in the game state object

WEAPONS_FULL_MAG = {
	"MELEE": 1, # they are used to identify them apart from None
	"CLASSIC": 12,
	"SHORTY": 2,
	"FRENZY": 15,
	"GHOST": 13,
	"BANDIT": 8,
	"SHERIFF": 6,
	"STINGER": 20,
	"SPECTRE": 30,
	"BUCKY": 5,
	"JUDGE": 5,
	"BULLDOG": 24,
	"GUARDIAN": 12,
	"PHANTOM": 30,
	"VANDAL": 25,
	"MARSHAL": 5,
	"OUTLAW": 2,
	"OPERATOR": 5,
	"ARES": 50,
	"ODIN": 100
}

def resolve_hp(hp, l_hp):
	if hp is None:
		return l_hp
	if hp >= 1 and hp <= 100:
		return hp
	return l_hp

def resolve_shield(shield, l_shield):
	if shield is None:
		return l_shield
	if shield >= 0 and shield <= 50:
		return shield
	return l_shield

def resolve_rounds(c_rounds_won, c_rounds_lost, rounds_won, rounds_lost, l_rounds_won, l_rounds_lost, swiftplay):
	if rounds_won is None:
		rounds_won = l_rounds_won
	if rounds_lost is None:
		rounds_lost = l_rounds_lost
	
	global max_rounds
	max_rounds = 13
	if swiftplay:
		max_rounds = 5

	if not(rounds_won >= 0 and rounds_won <= max_rounds) or rounds_won is None:
		rounds_won = l_rounds_won
	if not(rounds_lost >= 0 and rounds_lost <= max_rounds) or rounds_lost is None:
		rounds_lost = l_rounds_lost

	won_state = (rounds_won == l_rounds_won or rounds_won == l_rounds_won + 1)
	lost_state = (rounds_lost == l_rounds_lost or rounds_lost == l_rounds_lost + 1)
	both_state = (rounds_won + rounds_lost == l_rounds_won + l_rounds_lost or rounds_won + rounds_lost == l_rounds_won + l_rounds_lost + 1)

	if won_state and lost_state and both_state:
		if c_rounds_won is None or c_rounds_lost is None:
			return l_rounds_won, l_rounds_lost
		if rounds_won != l_rounds_won or rounds_lost != l_rounds_lost:
			if c_rounds_won == rounds_won and c_rounds_lost == rounds_lost:
				return rounds_won, rounds_lost
	return l_rounds_won, l_rounds_lost

def resolve_weapon(weapon, l_weapon):
	if weapon is None:
		weapon = l_weapon
	return weapon

def resolve_ammo(ammo, max_ammo, l_ammo):
	if max_ammo == 999 or max_ammo == 888:
		return max_ammo
	if ammo is None:
		return l_ammo
	if ammo >= 0 and ammo <= max_ammo:
		return ammo
	return l_ammo

def resolve_kill_reset(l_current_round, stl_current_round):
	if l_current_round > stl_current_round:
		return True
	return False

def resolve_top_bar_difference(top_bar_enemies, l_top_bar_enemies):
	if len(top_bar_enemies) < len(l_top_bar_enemies):
		difference = list(set(l_top_bar_enemies) - set(top_bar_enemies))
		return difference
	return []

class GameState:
	def __init__(self):
		self.hp = 100
		self.shield = 0
		self.rounds_won = 0
		self.rounds_lost = 0
		self.current_round = 1
		self.equipped_weapon = "CLASSIC"
		self.max_ammo = 12
		self.ammo = 12
		self.visible_enemies = 0
		self.is_dead = False
		self.total_deaths = 0
		self.round_kills = 0
		self.total_kills = 0
		self.top_bar_enemies = []

	def resolve_is_dead(self, l_is_dead, l_total_deaths, team_top_bar, my_agent):
		if my_agent in team_top_bar:
			self.total_deaths = l_total_deaths
			return False
		if not l_is_dead:
			self.total_deaths = l_total_deaths + 1
			return True
		self.total_deaths = l_total_deaths
		return True

	def resolve_kills(self, top_bar_enemies, my_kill_feed_enemies ,l_top_bar_enemies, stl_top_bar_enemies,l_current_round, stl_current_round, l_total_kills, l_round_kills):
		if resolve_kill_reset(l_current_round, stl_current_round):
			self.round_kills = 0
			self.total_kills = l_total_kills
			return top_bar_enemies

		top_bar_difference = resolve_top_bar_difference(l_top_bar_enemies, stl_top_bar_enemies)
		# top_bar_difference = resolve_top_bar_difference(top_bar_enemies, l_top_bar_enemies)
		enemies_killed_since_last = list(set(top_bar_difference) & set(my_kill_feed_enemies))
		capture_kill_count = len(enemies_killed_since_last)

		self.round_kills = l_round_kills + capture_kill_count
		self.total_kills = l_total_kills + capture_kill_count
		return top_bar_enemies

	def resolve_from_capture(self, results, last_game_state: "GameState", stl_top_bar_enemies,stl_current_round, stl_won, stl_lost, locr_won, locr_lost, my_agent, swiftplay=False):
		self.hp = resolve_hp(results["hp"], last_game_state.hp)
		self.shield = resolve_shield(results["shield"], last_game_state.shield)
		self.rounds_won, self.rounds_lost = resolve_rounds(
			results["team_rounds"], results["enemy_rounds"],
			locr_won, locr_lost,
			stl_won, stl_lost, swiftplay)
		self.current_round = self.rounds_won + self.rounds_lost + 1
		self.equipped_weapon = resolve_weapon(results["weapon_switch"], last_game_state.equipped_weapon)
		self.max_ammo = WEAPONS_FULL_MAG[self.equipped_weapon]
		self.ammo = resolve_ammo(results["ammo"], self.max_ammo, last_game_state.ammo)
		self.is_dead = self.resolve_is_dead(
			last_game_state.is_dead, last_game_state.total_deaths,
			results["team_top_bar_names"], my_agent)
		self.top_bar_enemies = self.resolve_kills(
			results["enemy_top_bar_names"], results["my_kill_feed_names"],
			last_game_state.top_bar_enemies, stl_top_bar_enemies,
			last_game_state.current_round,
			stl_current_round, last_game_state.total_kills,
			last_game_state.round_kills)