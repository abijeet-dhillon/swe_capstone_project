@echo off
setlocal
TITLE Digital Work Artifact Miner
color 0A

echo === Starting Digital Work Artifact Miner ===
echo.
echo Please keep this terminal window open to keep the processes running.
echo.

IF NOT EXIST ".env" (
    echo Notice: No .env file found. Copying env.template to .env...
    copy env.template .env >nul
)

FINDSTR /C:"OPENAI_API_KEY=sk-" ".env" >nul
IF ERRORLEVEL 1 (
    echo.
    echo Notice: No active OpenAI API key detected in .env.
    echo IMPORTANT: If you want to test the optional LLM features, paste your OpenAI API key below.
    set /p OPENAI_KEY="API Key (leave blank to skip): "
    
    setlocal EnableDelayedExpansion
    IF NOT "!OPENAI_KEY!"=="" (
        powershell -Command "$c = Get-Content .env; if ($c -match '^OPENAI_API_KEY=') { $c -replace '^OPENAI_API_KEY=.*', 'OPENAI_API_KEY=!OPENAI_KEY!' | Set-Content .env } else { Add-Content .env 'OPENAI_API_KEY=!OPENAI_KEY!' }"
        echo API Key successfully saved to .env!
    ) ELSE (
        echo Starting without OpenAI key. The app will use local fallbacks.
    )
    endlocal
    echo.
)

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
