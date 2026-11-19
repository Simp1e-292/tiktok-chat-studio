@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================================
echo   KHOI DONG TIKTOK CHAT STUDIO PRO (LOCAL SERVER + CAPCUT + EDGE-TTS)
echo ========================================================================

echo [1/3] Don sach file desktop.ini do Google Drive tao ra (neu co)...
for /r %%f in (desktop.ini) do (
    if exist "%%f" (
        attrib -r -h -s "%%f" > nul 2>&1
        del /f /q "%%f" > nul 2>&1
    )
)

set "PY_CMD="
if exist ".venv\Scripts\python.exe" set "PY_CMD=.venv\Scripts\python.exe"
if not defined PY_CMD if exist "venv\Scripts\python.exe" set "PY_CMD=venv\Scripts\python.exe"
if not defined PY_CMD if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
if not defined PY_CMD (
    where python > nul 2>&1 && set "PY_CMD=python"
)
if not defined PY_CMD (
    where py > nul 2>&1 && set "PY_CMD=py -3"
)

if not defined PY_CMD (
    echo [LOI] Khong tim thay Python 3! Hay cai Python 3 tu Microsoft Store hoac python.org.
    pause
    exit /b 1
)

echo [2/3] Kiem tra thu vien Python ^& Node.js...
%PY_CMD% -c "import PIL, pyJianYingDraft, gtts, edge_tts" > nul 2>&1
if errorlevel 1 (
    echo Dang cai dat cac thu vien trong requirements.txt...
    %PY_CMD% -m pip install -r requirements.txt
)

if not exist "node_modules\puppeteer-core" (
    where npm > nul 2>&1
    if not errorlevel 1 (
        echo Dang cai dat puppeteer-core cho tinh nang Render Khung Hinh CapCut/MP4...
        call npm install --no-audit --no-fund
    ) else (
        echo [CANH BAO] Chua co Node.js. Web Studio va TTS van chay binh thuong; cai Node.js de xuat CapCut/MP4 dong.
    )
)

echo [3/3] Dang bat TikTok Chat Studio tai http://localhost:8000 ...
%PY_CMD% studio_server.py
pause
