from difflib import SequenceMatcher

WEAPONS = [
	"MELEE",
	"CLASSIC",
	"SHORTY",
	"FRENZY",
	"GHOST",
	"BANDIT",
	"SHERIFF",
	"STINGER",
	"SPECTRE",
	"BUCKY",
	"JUDGE",
	"BULLDOG",
	"GUARDIAN",
	"PHANTOM",
	"VANDAL",
	"MARSHAL",
	"OUTLAW",
	"OPERATOR",
	"ARES",
	"ODIN"
]

def identify_weapon(text):
	if not text:
		return None

	clean_text = text[0].upper().strip()

	best_weapon = None
	best_score = 0

	for weapon in WEAPONS:
		score = SequenceMatcher(None, clean_text, weapon).ratio()

		if score > best_score:
			best_score = score
			best_weapon = weapon

	if best_score < 0.6:
		return None

	return best_weapon