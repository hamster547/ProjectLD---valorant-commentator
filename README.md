This project watches your screen as you play valorant on your primary monitor.

When something interesting enough happens, it will react to it.



\## Why it's called projectLD

LD stand for little devil, which is a nickname i had for my best friend.

He used to keep me company when i played games, so i made this project to show my appreciation to him

Love you, little devil. Im really glad i met you.



\## What it does

\- Reads your screen (health, shield, ammo, kills, deaths) about 3 times a second

\- Spots events like kills, deaths and round results

\- Picks the most interesting moment and has a local AI model react to it

\- Speaks the reaction out loud

\- Personalities: Roast, Hype, and a Kymasu roaster



Everything runs on your own computer. No accounts, no API keys, nothing is sent anywhere.



\## What you need

\- Windows 10 or 11

\- An NVIDIA graphics card is recommended (it works without one, but slower)

\- About 15GB of free disk space (the AI model and voice files are large)

\- Python 3.14: https://www.python.org/ftp/python/pymanager/python-manager-26.4.msix

\- Ollama: https://ollama.com/download/OllamaSetup.exe



\## Install

1\. Install Python 3.14 first install the Python install manager from the link above, then, open the terminal (win+r, type cmd, press enter) and type `py install 3.14`

2\. Install Ollama from ollama.com (when asked to log in, choose run locally)

3\. Download this project (green "Code" button, then "Download ZIP"), unzip it somewhere

&#x20;  like Documents (not Program Files)

4\. Double-click `install.bat` and wait. The first time takes a while,

&#x20;  because it downloads several GB of models.



\## Run

Double-click `start.bat`. \[Mention the test voice button and where the settings are.]



\## Tips

\- Use Valorant in windowed fullscreen for the best readings. make sure the res is a 16:9 ration! (eg. 1280x720, 1920x1080, 2560x1440)

\- This app will run badly with a low-end machine. Running a language model locally with Valorant takes resources.



\## Known limitations

\- A 7B model sometimes says silly things (this is part of the charm)

\- The model may be slow and inaccurate. This is a solo project where I did the best of my abilities to optimize, yet it still might run slow.

\- Screen reading was tested at a 16:9 ratio. Other setups may be less accurate.



\## Credits

\- Kokoro (voices), EasyOCR, Ollama, Qwen2.5

