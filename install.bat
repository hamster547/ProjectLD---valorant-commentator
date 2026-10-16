@echo off
setlocal
cd /d "%~dp0"
echo ===== Valorant Commentator installer =====
echo.

rem ---------- 1. Python 3.14 ----------
set "PY="
py -3.14 -c "import sys" >nul 2>nul && set "PY=py -3.14"
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info[:2]==(3,14) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Python 3.14 was not found.
  echo Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" in the installer, then run this again.
  goto fail
)

rem ---------- 2. Ollama ----------
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama was not found.
  echo Install it from https://ollama.com/download, then CLOSE this window and run install.bat again.
  goto fail
)

rem ---------- 3. Private Python environment ----------
if not exist venv (
  echo Creating the environment...
  %PY% -m venv venv
  if errorlevel 1 goto fail
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

rem ---------- 4. PyTorch (GPU version if there is an NVIDIA card) ----------
nvidia-smi >nul 2>nul
if not errorlevel 1 (
  echo NVIDIA GPU found. Installing the GPU version of PyTorch...
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
  if errorlevel 1 echo GPU PyTorch failed, the normal CPU version will be used instead.
)

rem ---------- 5. The rest of the packages ----------
pip install -r requirements.txt
if errorlevel 1 goto fail

python -c "import torch; print('GPU available for OCR:', torch.cuda.is_available())"

rem ---------- 6. Language model ----------
echo Downloading the language model (a few GB, this takes a while the first time)...
ollama pull qwen2.5:7b
if errorlevel 1 (
  echo Could not download the model. Open the Ollama app from the Start menu,
  echo wait a few seconds, then run install.bat again.
  goto fail
)

rem ---------- 7. OCR models (so the first launch isn't slow) ----------
echo Downloading text-reading models...
python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"
if errorlevel 1 goto fail

rem ---------- 8. Voice files ----------
if not exist resources mkdir resources
call :download "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx" "resources\kokoro-v1.0.onnx" "the voice model, about 310 MB"
if errorlevel 1 goto fail
call :download "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin" "resources\voices-v1.0.bin" "the voice list, about 28 MB"
if errorlevel 1 goto fail

echo.
echo ===== All done! Use start.bat to launch. =====
pause
exit /b 0

:download
rem  %1 = web address, %2 = where to save it, %3 = description
if exist "%~2" exit /b 0
echo Downloading %~3, please wait...
curl.exe -L --fail -o "%~2.part" "%~1"
if errorlevel 1 (
  del "%~2.part" >nul 2>nul
  echo Download failed. Check your internet connection and run install.bat again.
  exit /b 1
)
move /y "%~2.part" "%~2" >nul
exit /b 0

:fail
echo.
echo ===== Installation stopped. Take a screenshot of the messages above and send it over. =====
pause
exit /b 1