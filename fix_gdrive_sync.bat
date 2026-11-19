@echo off
chcp 65001 > nul
echo ===================================================================
echo   FIX LOI GOOGLE DRIVE (desktop.ini) & DONG BO CAPCUT / GITHUB
echo ===================================================================
cd /d "%~dp0"

echo [1/4] Dang xoa cac file an desktop.ini do Google Drive tao ra...
for /r %%f in (desktop.ini) do (
    if exist "%%f" (
        attrib -r -h -s "%%f" > nul 2>&1
        del /f /q "%%f" > nul 2>&1
    )
)
if exist ".git" (
    for /r ".git" %%f in (desktop.ini) do (
        if exist "%%f" (
            attrib -r -h -s "%%f" > nul 2>&1
            del /f /q "%%f" > nul 2>&1
        )
    )
)

set "PY_CMD="
if exist ".venv\Scripts\python.exe" set "PY_CMD=.venv\Scripts\python.exe"
if not defined PY_CMD if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
if not defined PY_CMD where python > nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD where py > nul 2>&1 && set "PY_CMD=py -3"

echo [2/4] Kiem tra node_modules va thu vien Python...
if not exist "node_modules\puppeteer-core" (
    where npm > nul 2>&1 && call npm install --no-audit --no-fund
)
if defined PY_CMD (
    %PY_CMD% -c "import PIL, pyJianYingDraft, gtts, edge_tts" > nul 2>&1 || %PY_CMD% -m pip install -r requirements.txt
)

echo [3/4] Dang chay capcut_draft_generator.py de dong bo lai CapCut Desktop...
if defined PY_CMD (
    %PY_CMD% capcut_draft_generator.py
) else (
    echo [CANH BAO] Khong tim thay Python de chay capcut_draft_generator.py
)

echo [4/4] Kiem tra trang thai Git...
git status -s
echo ===================================================================
echo   HOAN TAT! Chay CHAY_STUDIO.bat de mo Web Studio hoac mo CapCut!
echo ===================================================================
pause
