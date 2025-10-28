@echo off
REM Birthday Voucher Management System - Quick Start
REM This script starts all three Flask applications

echo ============================================================
echo  Birthday Voucher Management System
echo ============================================================
echo.
echo Starting all services...
echo.

cd prog

REM Start Main Application on port 5000
echo [1/3] Starting Main Application (port 5000)...
start "BDVoucher - Main App" python app.py

REM Wait for the first app to initialize
timeout /t 3 /nobreak >nul

REM Start Cafe Interface on port 5001
echo [2/3] Starting Cafe Interface (port 5001)...
start "BDVoucher - Cafe Interface" python cafe_interface.py

REM Wait for the second app to initialize
timeout /t 3 /nobreak >nul

REM Start Admin Interface on port 5002
echo [3/3] Starting Admin Interface (port 5002)...
start "BDVoucher - Admin Interface" python admin_interface.py

echo.
echo ============================================================
echo  All services are now running!
echo ============================================================
echo.
echo Access the applications at:
echo   Main App:      http://localhost:5000
echo   Cafe Interface: http://localhost:5001
echo   Admin Interface: http://localhost:5002
echo.
echo ============================================================
echo  Note: Close the Python windows to stop the services.
echo ============================================================
echo.
pause Compact

