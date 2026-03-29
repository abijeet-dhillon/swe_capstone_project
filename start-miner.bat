@echo off
setlocal
TITLE Digital Work Artifact Miner
color 0A

echo === Starting Digital Work Artifact Miner ===
echo.
echo Please keep this terminal window open to keep the processes running.
echo.

echo [1/3] Starting Python Backend via Docker...
REM Start docker desktop containers in the background
docker compose up --build -d backend

echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul
echo Backend is ready!
echo.

echo [2/3] Launching Portfolio Template Service...
cd portfolio-template

REM Check if node_modules exists, install if missing
IF NOT EXIST "node_modules\" (
    echo First time setup detected: Installing portfolio-template dependencies...
    cmd /c npm install
)

REM Start the portfolio template in a new background window
start "Portfolio-Service" cmd /c "title Portfolio-Service && npm run dev"
cd ..
echo.

echo [3/3] Launching Electron Frontend...
cd frontend

IF NOT EXIST "node_modules\" (
    echo First time setup detected: Installing frontend dependencies...
    cmd /c npm install
)

REM Run the electron app and block terminal
cmd /c npm run start

echo.
echo App closed. Shutting down the services...
cd ..
echo Stopping Docker backend...
docker compose down

echo Stopping Portfolio Template Service...
REM Kill the portfolio window
taskkill /FI "WINDOWTITLE eq Portfolio-Service*" /T /F >nul 2>&1

echo Shutdown complete. Goodbye!
REM Pause so you can see the terminal close cleanly
timeout /t 3 >nul
