@echo off
REM Adam Prism — launcher for Windows
REM Use this if you can't run `python bin\adam.py` directly.
REM
REM Usage:
REM   adam                REM Start server
REM   adam --port 8080    REM Custom port
REM   adam --doctor       REM Health check
REM   adam --install      REM Install dependencies
REM   adam --help         REM All options

setlocal
cd /d "%~dp0\.."
python bin\adam.py %*
endlocal
