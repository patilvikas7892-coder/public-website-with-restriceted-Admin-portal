@echo off
title Push Project to GitHub - Vikas
color 0b
echo ==============================================================================
echo   Pushing Assignment 19 Project to GitHub Repository:
echo   https://github.com/patilvikas7892-coder/public-website-with-restriceted-Admin-portal
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [*] Current Git Status:
git status
echo.

echo [*] Pushing branch 'main' to GitHub origin...
git push -u origin main

if errorlevel 1 (
    echo.
    echo [!] Push failed or authentication was cancelled.
    echo     If you are prompted for credentials:
    echo     - Username: patilvikas7892-coder
    echo     - Password: Use a GitHub Personal Access Token (classic) with 'repo' scope.
    echo     Generate token at: https://github.com/settings/tokens
) else (
    echo.
    echo ==============================================================================
    echo [✓] Project Successfully Uploaded to GitHub!
    echo     Repository URL: https://github.com/patilvikas7892-coder/public-website-with-restriceted-Admin-portal
    echo ==============================================================================
)

echo.
pause
