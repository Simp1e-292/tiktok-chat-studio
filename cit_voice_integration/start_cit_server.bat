@echo off
chcp 65001 >nul
cd /d "%~dp0cit-voice-studio"
if "%PORT%"=="" set PORT=8001
echo Starting CIT Voice Studio server on http://127.0.0.1:%PORT% ...
uv run --no-sync vieneu-stream
