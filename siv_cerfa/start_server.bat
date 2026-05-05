@echo off
title SIV CERFA - Service local

echo ============================================
echo   SIV CERFA  -  Dreux Carte Grise
echo   Generateur de formulaires CERFA
echo ============================================
echo.

cd /d "%~dp0"

python --version 2>nul
if %errorlevel% neq 0 (
    echo ERREUR : Python non trouve.
    echo Installez Python sur https://www.python.org/downloads/
    echo Cochez "Add Python to PATH" lors de l installation.
    pause
    exit /b 1
)

echo.
echo Installation des dependances...
pip install flask pillow reportlab --quiet --no-warn-script-location
echo Dependances OK.
echo.
echo Demarrage du service sur http://localhost:5000
echo Laissez cette fenetre ouverte pendant l utilisation du SIV.
echo Appuyez sur Ctrl+C pour arreter.
echo ============================================
echo.

python server\server.py

echo.
echo Service arrete.
pause
