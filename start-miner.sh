#!/bin/bash

# Define colors for better terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Starting Digital Work Artifact Miner ===${NC}"
echo -e "${YELLOW}Please keep this terminal window open to keep the processes running.${NC}"

# Cleanup function to run when the app closes
cleanup() {
    echo -e "\n${YELLOW}App closed. Shutting down the services...${NC}"
    
    if [ -n "$PORTFOLIO_PID" ]; then
        echo "Stopping Portfolio Template..."
        kill $PORTFOLIO_PID 2>/dev/null
    fi
    
    echo "Stopping Docker backend..."
    docker compose down
    
    echo -e "${GREEN}Shutdown complete. Goodbye!${NC}"
    exit 0
}

# Trap exit signals to ensure cleanup always happens
trap 'cleanup' SIGINT SIGTERM EXIT

# --- STEP 1: START BACKEND ---
echo -e "\n${GREEN}[1/3] Starting Python Backend via Docker...${NC}"
docker compose up -d backend

# Wait a few seconds to ensure FastAPI is fully booted
echo "Waiting for backend to be ready on port 8000..."
while ! curl -s http://localhost:8000/docs > /dev/null; do
  sleep 1
done
echo -e "${GREEN}Backend is ready!${NC}"

# --- STEP 2: START PORTFOLIO TEMPLATE ---
echo -e "\n${GREEN}[2/3] Launching Portfolio Template Service...${NC}"
cd portfolio-template || exit

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}First time setup detected: Installing portfolio-template dependencies...${NC}"
    npm install
fi

# Run the portfolio dev server in the background and capture its PID
npm run dev > /dev/null 2>&1 &
PORTFOLIO_PID=$!
cd ..

# --- STEP 3: START FRONTEND ---
echo -e "\n${GREEN}[3/3] Launching Electron Frontend...${NC}"
cd frontend || exit

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}First time setup detected: Installing frontend dependencies...${NC}"
    npm install
fi

# This will block the terminal while the Electron app is open
npm run start
