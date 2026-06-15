@echo off
cd /d "%~dp0site"
echo Open in browser: http://localhost:8765/
python -m http.server 8765
