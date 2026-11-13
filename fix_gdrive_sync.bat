@echo off
chcp 65001 > nul
echo ===================================================================
echo   FIX LOI GOOGLE DRIVE (desktop.ini) & DONG BO CAPCUT / GITHUB
echo ===================================================================
cd /d "%~dp0"

echo [1/3] Dang xoa cac file an desktop.ini do Google Drive tao ra...
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

echo [2/3] Dang chay capcut_draft_generator.py de dong bo lai CapCut Desktop...
"%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" capcut_draft_generator.py
if errorlevel 1 (
    python capcut_draft_generator.py
)

echo [3/3] Kiem tra trang thai Git...
git status -s
echo ===================================================================
echo   HOAN TAT! Ban co the mo CapCut Desktop va Export video ngay.
echo ===================================================================
pause
