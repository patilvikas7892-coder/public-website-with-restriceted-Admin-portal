@echo off
title Assignment 19: Public Website with Restricted Admin Portal - Vikas
color 0b
echo ==============================================================================
echo   ASSIGNMENT 19: PUBLIC WEBSITE WITH RESTRICTED ADMIN PORTAL
echo   Engineers: Vikas & Vijit | Domain: Web Hosting & Cloud Security
echo   Stack: Cloud Linux VM + AWS S3 Object Storage + Security Groups (IP Filter)
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [*] Checking Python runtime...
python --version
if errorlevel 1 (
    echo [!] Python was not found in PATH. Please install Python 3.
    pause
    exit /b
)

echo [*] Verifying test suite...
python test_security.py
if errorlevel 1 (
    echo [!] Warning: Some tests failed.
) else (
    echo [✓] All 10 Automated Security Tests Passed!
)
echo.

echo ==============================================================================
echo [*] Starting Cloud Web Portal on http://127.0.0.1:5000
echo [*] Public Website: Accessible from 0.0.0.0/0
echo [*] Admin Portal: Restricted to College IP (203.0.113.195/32)
echo [*] Evaluation Credentials: username='vikas'  password='AdminPassword123!'
echo ==============================================================================
echo.

REM Open browser after 2 seconds
start "" http://127.0.0.1:5000

python app.py
pause
