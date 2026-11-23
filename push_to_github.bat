@echo off
title Push Project to GitHub - Vikas
color 0b
echo ==============================================================================
echo   Pushing Assignment 19 Project to GitHub Repository:
echo   https://github.com/patilvikas7892-coder/public-website-with-restriceted-Admin-portal
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [*] Current Git Remote:
git remote -v
echo.

echo [*] Attempting standard push to main branch...
git push -u origin main

if errorlevel 1 (
    echo.
    echo ==============================================================================
    echo [!] Standard push rejected (Remote contains existing README or commits).
    echo [*] Attempting automated sync (pull with rebase and allow unrelated histories)...
    echo ==============================================================================
    git pull origin main --allow-unrelated-histories --no-rebase -m "Merge remote repository initial files"
    echo.
    echo [*] Retrying push to GitHub...
    git push -u origin main
)

if errorlevel 1 (
    echo.
    echo ==============================================================================
    echo [!] Remote still rejected push.
    echo     Would you like to FORCE push to overwrite the remote empty placeholder?
    echo ==============================================================================
    set /p choice="Force push to main? [Y/N] (Default is Y): "
    if "%choice%"=="" set choice=Y
    if /i "%choice%"=="Y" (
        echo [*] Force pushing to origin main...
        git push -u origin main --force
    )
)

if errorlevel 1 (
    echo.
    echo [!] Push failed. If authentication failed:
    echo     1. Use Username: patilvikas7892-coder
    echo     2. For password, use a GitHub Personal Access Token (classic) with 'repo' scope.
    echo        Generate at: https://github.com/settings/tokens
) else (
    echo.
    echo ==============================================================================
    echo [✓] Project Successfully Uploaded to GitHub!
    echo     Repository URL: https://github.com/patilvikas7892-coder/public-website-with-restriceted-Admin-portal
    echo ==============================================================================
)

echo.
pause
