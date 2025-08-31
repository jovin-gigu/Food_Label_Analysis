@echo off
echo Starting Nutrition Risk Predictor Application...
echo.

echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d "%~dp0backend" && .\venv\Scripts\activate && python venv\app.py"

echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers are starting...
echo Backend: http://127.0.0.1:5000
echo Frontend: http://localhost:5173
echo.
echo Press any key to exit this window (servers will continue running)
pause > nul
