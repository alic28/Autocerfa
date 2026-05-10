@echo off
chcp 65001 >nul
title SIV CERFA - Serveur local v2.1

echo ==========================================
echo   SIV vers CERFA - Serveur local v2.1
echo   Dreux Carte Grise
echo ==========================================
echo.

cd /d "%~dp0"

:: ── Trouver Python ──────────────────────────────────────────────────────

set PYTHON=

:: 1. Python directement dans le PATH ?
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :python_found
)

:: 2. py launcher (installé avec la plupart des Python Windows)
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py
    goto :python_found
)

:: 3. Chemins classiques d'installation Python sur Windows
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Python39\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%P
        goto :python_found
    )
)

:: 4. Pas trouvé
echo.
echo  ERREUR : Python n'est pas installe ou pas dans le PATH.
echo.
echo  Solutions :
echo   A) Telechargez Python sur https://www.python.org/downloads/
echo      IMPORTANT : cocher "Add python.exe to PATH" pendant l'installation
echo      puis fermez et relancez ce fichier .bat
echo.
echo   B) Si Python est deja installe, lancez ce .bat depuis
echo      le dossier Python : C:\Python312\python.exe server\server.py
echo.
pause
exit /b 1

:python_found
echo [1/3] Python trouve : %PYTHON%
%PYTHON% --version

echo.
echo [2/3] Installation des dependances (flask + pypdf + reportlab)...
%PYTHON% -m pip install flask pypdf reportlab --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  ERREUR lors de l'installation des dependances.
    echo  Essayez : %PYTHON% -m pip install flask pypdf reportlab
    pause
    exit /b 1
)
echo     OK

echo.
echo [3/3] Demarrage du serveur...
echo.
echo     URL    : http://localhost:5000
echo     Output : %~dp0output\
echo.
echo     Laisser cette fenetre ouverte pendant l'utilisation.
echo     Ctrl+C pour arreter.
echo.
echo ==========================================
echo.

%PYTHON% server\server.py

echo.
echo Le serveur s'est arrete.
pause
