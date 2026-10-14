@echo off
title picasso-dev-tunnel
REM Picasso Dev SSH tunnel with AUTO-RECONNECT (heals itself 5s after any drop)
:loop
ssh -N -L 3082:127.0.0.1:3082 -o ServerAliveInterval=30 -o ServerAliveCountMax=4 -o ConnectTimeout=10 root@47.243.79.144
timeout /t 5 /nobreak >nul
goto loop
