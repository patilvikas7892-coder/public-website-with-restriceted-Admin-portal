@echo off
title Share Public Website & Restricted Admin Portal to Internet
color 0a
echo ==============================================================================
echo   ASSIGNMENT 19: EXPOSE TO PUBLIC INTERNET (HTTP/HTTPS TUNNEL)
echo   Students: Vikas & Vijit | Domain: Web Hosting & Cloud Security
echo ==============================================================================
echo.
echo Make sure your app is running on http://localhost:5000 (run.bat) first!
echo.
echo [LAN/Wi-Fi Local Access]:
echo   Any device on your Wi-Fi network can open: http://172.20.3.86:5000
echo.
echo [Worldwide Public Internet Tunnel]:
echo  [1] Pinggy (Fast HTTPS Tunnel, Zero install, uses built-in SSH) - RECOMMENDED
echo  [2] Cloudflare Quick Tunnel (Free, Highly Secure, trycloudflare.com)
echo  [3] Localtunnel (via Node.js npx)
echo.

set /p choice="Enter tunnel choice [1, 2, or 3] (Default is 1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo [*] Launching Pinggy SSH Public Tunnel on Port 5000...
    echo [*] Your Public URL will be displayed below (e.g. https://xxxxx.a.pinggy.link):
    echo ==============================================================================
    ssh -o StrictHostKeyChecking=no -p 443 -R0:localhost:5000 a.pinggy.io
    goto end
)

if "%choice%"=="2" (
    echo.
    echo [*] Launching Cloudflare Tunnel on Port 5000...
    echo [*] Your Public URL will appear below (e.g. https://xxxxx.trycloudflare.com):
    echo ==============================================================================
    npx --yes cloudflared tunnel --url http://localhost:5000
    goto end
)

if "%choice%"=="3" (
    echo.
    echo [*] Launching Localtunnel on Port 5000...
    echo ==============================================================================
    npx --yes localtunnel --port 5000
    goto end
)

:end
pause
