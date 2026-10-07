@echo off
REM Picasso Dev one-click CLOSE: stop server dev env (free ~1.1G RAM) + close local tunnel

echo.
echo [1/2] Stopping Dev environment on server...
ssh root@47.243.79.144 "picasso-dev stop"
if errorlevel 1 (
  echo [X] SSH failed
  pause
  exit /b 1
)

echo.
echo [2/2] Closing local tunnel window...
taskkill /FI "WINDOWTITLE eq picasso-dev-tunnel*" /F >nul 2>&1

echo.
echo [OK] Dev fully stopped (production untouched)
echo Press any key to close this window
pause >nul
