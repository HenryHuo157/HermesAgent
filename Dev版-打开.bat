@echo off
REM Picasso Dev one-click OPEN: start server dev env + tunnel + browser
REM First time: register an account in the page (Dev has its own account DB)

echo.
echo [1/3] Starting Dev environment on server (skips if already running)...
ssh root@47.243.79.144 "picasso-dev start"
if errorlevel 1 (
  echo [X] SSH failed - check network and retry
  pause
  exit /b 1
)

echo.
echo [2/3] Waiting for Dev LibreChat ready (first boot ~40s)...
ssh root@47.243.79.144 "for i in $(seq 1 36); do curl -s -o /dev/null -m 4 -w '%%{http_code}' http://127.0.0.1:3081 | grep -q 200 && exit 0; sleep 5; done; exit 1"
if errorlevel 1 (
  echo [!] Timeout after 3 min - page will open anyway, refresh later
) else (
  echo [OK] Dev is ready
)

echo.
echo [3/3] Opening tunnel + browser...
start "picasso-dev-tunnel" ssh -N -L 3081:127.0.0.1:3081 root@47.243.79.144
timeout /t 2 /nobreak >nul
start http://localhost:3081

echo.
echo ============================================================
echo   Dev Picasso:   http://localhost:3081
echo   When done: double-click Dev-GCLOSE bat to free server RAM
echo   (keep the picasso-dev-tunnel window open, minimize is fine)
echo ============================================================
echo Press any key to close this window (Dev keeps running)
pause >nul
