@echo off
chcp 65001 >nul
title SIV CERFA - Serveur local

echo ==========================================
echo   SIV vers CERFA - Serveur local v2.0
echo   Dreux Carte Grise
echo ==========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python n est pas installe ou absent du PATH.
    echo Telechargez Python sur https://python.org
    pause
    exit /b
)

echo Installation des dependances...
python -m pip install flask pdf2image pypdf pillow --quiet

echo.
echo Demarrage du serveur sur http://localhost:5000
echo Laisser cette fenetre ouverte pendant l utilisation.
echo Appuyer sur Ctrl+C pour arreter.
echo.

python server\server.py

pause
