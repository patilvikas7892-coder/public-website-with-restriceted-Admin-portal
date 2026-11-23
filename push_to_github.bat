@echo off
title Upload Assignment 19 to GitHub - Vikas
color 0b
echo ==============================================================================
echo   Pushing Assignment 19 Project to GitHub Repository:
echo   patilvikas7892-coder/public-website-with-restriceted-Admin-portal
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [*] Target Remote:
git remote -v
echo.

echo [*] Starting push to GitHub (main branch)...
echo [*] If a browser window pops up, click "Sign in with your browser" as:
echo     patilvikas7892-coder
echo.

git push -u origin main --force

if errorlevel 1 (
    echo.
    echo ==============================================================================
    echo [!] Direct push failed or browser sign-in was not completed.
    echo [*] Alternative: Push using a GitHub Personal Access Token (PAT).
    echo ==============================================================================
    echo.
    echo If you have a GitHub Personal Access Token:
    echo 1. Generate one at: https://github.com/settings/tokens (check 'repo' scope)
    echo 2. Paste your token below:
    echo.
    set /p token="Enter GitHub Personal Access Token (or press ENTER to exit): "
    if not "%token%"=="" (
        echo [*] Pushing with your token...
        git push https://%token%@github.com/patilvikas7892-coder/public-website-with-restriceted-Admin-portal.git main --force
    )
)

if errorlevel 1 (
    echo.
    echo [!] Push failed. Please verify your token or internet connection.
) else (
    echo.
    echo ==============================================================================
    echo [✓] Project Successfully Uploaded to GitHub!
    echo     Repository URL: https://github.com/patilvikas7892-coder/public-website-with-restriceted-Admin-portal
    echo ==============================================================================
)

echo.
pause
