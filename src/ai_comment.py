import ollama
import subprocess
import time
import random
import re
from collections import deque
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # the folder this .py file is in

PROMPTS = {
	"roast": BASE_DIR / "resources/prompt_templates/roaster.txt",
	"high low": BASE_DIR / "resources/prompt_templates/supporter.txt",
	"advance kymasu roaster": BASE_DIR / "resources/prompt_templates/advance_kymasu_roaster.txt"
}


KYMASU_PROMPTS = [
	"Proceed to roast Kymasu.",
	"Roast Kymasu like a disappointed coach who has seen enough.",
	"Roast Kymasu like a sports commentator who has completely given up.",
	"Give Kymasu a backhanded compliment about his Valorant gameplay.",
	"Roast Kymasu with one dry, deadpan line."
]

def load_base_prompt(prompt_file):
	with open(prompt_file, "r", encoding="utf-8") as f:
		return f.read()

def clean(text, max_words=15):
	t = text.strip().strip('"')
	t = re.sub(r"^(oh man|oh|wow|man|well|seriously|oh really|did you really|huh)[,!.]?\s+", "", t, flags=re.I)
	m = re.match(r"(.+?[.!?])(\s|$)", t)      # first sentence only
	if not m:
		return None
	t = re.sub(r"\b[A-Z]{4,}\b", lambda w: w.group(0).capitalize(), t)
	return t if len(t.split()) <= max_words else None

BANNED = ["paint dry", "grass grow", "you must have been", "you must be", "chess"]
recent = deque(maxlen=8)

def _words(text):
	return re.sub(r"[^a-z0-9' ]", " ", text.lower()).split()


def _grams(text, n=4):
	w = _words(text)
	return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def too_similar(text, recent_texts):
	low = text.lower()
	if any(b in low for b in BANNED):
		return True
	mine = _grams(text)
	return any(mine & _grams(r) for r in recent_texts)


def fix_glued(text):
	# "Kymasu'sValorant" -> "Kymasu's Valorant"
	return re.sub(r"([a-z])([A-Z])", r"\1 \2", text)


def trim_incomplete(text):
	# cut back to the last finished sentence if num_predict chopped it
	text = text.strip()
	if text and text[-1] in ".!?":
		return text
	cut = max(text.rfind("."), text.rfind("!"), text.rfind("?"))
	return text[:cut + 1] if cut != -1 else text


class Commentator:
	def __init__(self, prompt_file="roast", model_name="qwen2.5:7b", temp=0.7):
		self.prompt_base = load_base_prompt(PROMPTS[prompt_file])
		self.model_name = model_name
		self.temp = temp

		self.ensure_ollama_running()
		self.warm_up()

	def change_persona(self, persona: str):
		self.prompt_base = load_base_prompt(PROMPTS[persona])

	def ensure_ollama_running(self):
		try:
			ollama.list()

		except Exception:
			subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
			time.sleep(2)

	def warm_up(self):
		try:
			ollama.generate(
				model=self.model_name,
				prompt="ping",
				options={"num_predict": 1}
			)
		except Exception as e:
			print(f"Error: {e}")


	def kymasu_comment(self, tries=3):
		text = None
		for _ in range(tries):
			raw = ollama.generate(
				model=self.model_name,
				system=self.prompt_base,
				prompt=random.choice(KYMASU_PROMPTS),
				options={
					"temperature": 1.0,
					"top_p": 0.95,
					"repeat_penalty": 1.05,
					"num_predict": 60,
					"stop": ["\n"]
				}
			)

			if not raw:
				continue
			text = trim_incomplete(fix_glued(raw.response.strip().strip('"')))
			if not too_similar(text, recent):
				break
		if text:
			recent.append(text)   # even the fallback gets remembered
		return text

	def comment(self, game_window_prompt: str) -> str:
		start = time.perf_counter()
		if "Kymasu" not in self.prompt_base:
			response = ollama.generate(
				model=self.model_name,
				system=self.prompt_base,
				prompt=game_window_prompt,
				options={
					"top_p": 0.9,
					"top_k": 40,
					"temperature": self.temp,
					"repeat_penalty": 1.1,
					"num_predict": 30,
					"stop": ["\n"]
				}
			)
		else:
			response = self.kymasu_comment()
			if response is None:
				response = ""
			return response

		end = time.perf_counter() - start
		clean_comment = response["response"].strip()

		return clean_comment