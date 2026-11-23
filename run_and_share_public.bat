@echo off
title Start Application & Share to Public Internet - Vikas
color 0e
echo ==============================================================================
echo   ASSIGNMENT 19: PUBLIC WEBSITE WITH RESTRICTED ADMIN PORTAL
echo   Engineers: Vikas & Vijit | Cloud Computing Lab
echo   Starting Web Server & Establishing Public HTTPS Tunnel
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [*] Step 1: Starting Flask Cloud Web Server on Port 5000...
start "Assignment 19 - Web Server (Port 5000)" cmd /k "python app.py"

echo [*] Waiting for server to initialize...
timeout /t 3 /nobreak >nul

echo [*] Step 2: Opening Local Browser...
start "" http://localhost:5000

echo.
echo ==============================================================================
echo [*] Step 3: Generating Instant Worldwide Public HTTPS URL via SSH Tunnel...
echo [*] Copy the https://xxxxxx.a.pinggy.link URL below to share with anyone!
echo ==============================================================================
echo.

ssh -o StrictHostKeyChecking=no -p 443 -R0:localhost:5000 a.pinggy.io
pause
