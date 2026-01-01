#!/bin/bash

# Poker Game Startup Script
# This script starts the server and optionally launches clients for testing

set -e

echo "🎲 Poker Game Startup Script"
echo "=============================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if server is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Server is already running on port 8000${NC}"
    read -p "Do you want to stop it and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing server..."
        kill $(lsof -t -i:8000) 2>/dev/null || true
        sleep 2
    else
        echo "Using existing server..."
    fi
fi

# Start server if not running
if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}Starting Poker Server...${NC}"
    cd server

    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt

    # Start server in background
    echo "Starting FastAPI server on http://localhost:8000"
    python poker_server_full.py > server.log 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > server.pid
    echo -e "${GREEN}✅ Server started (PID: $SERVER_PID)${NC}"

    cd ..

    # Wait for server to be ready
    echo "Waiting for server to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is ready!${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Server failed to start${NC}"
            cat server/server.log
            exit 1
        fi
        sleep 1
    done
else
    echo -e "${GREEN}✅ Server is already running${NC}"
fi

# Display menu
echo ""
echo "Server is running at: http://localhost:8000"
echo ""
echo "What would you like to do?"
echo "1. Open Web UI in browser"
echo "2. Start Go CLI client"
echo "3. Start Python bot"
echo "4. Start all clients for demo"
echo "5. Just keep server running"
echo "6. Stop server and exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo "Opening browser..."
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:8000
        elif command -v open > /dev/null; then
            open http://localhost:8000
        else
            echo "Please open http://localhost:8000 in your browser"
        fi
        ;;
    2)
        echo "Starting Go CLI client..."
        cd clients/go
        if [ ! -f "poker-cli" ]; then
            echo "Building Go client..."
            go mod download
            go build -o poker-cli .
        fi
        ./poker-cli -server http://localhost:8000 -name "GoPlayer"
        cd ../..
        ;;
    3)
        echo "Starting Python bot..."
        cd clients/python
        python3 poker_bot.py --server http://localhost:8000 --name "TestBot"
        cd ../..
        ;;
    4)
        echo -e "${YELLOW}Starting demo with multiple clients...${NC}"
        echo "This will open:"
        echo "  - Web browser (you can play as human)"
        echo "  - 2 Python bots"
        echo ""

        # Open browser
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:8000 &
        elif command -v open > /dev/null; then
            open http://localhost:8000 &
        fi

        sleep 3

        # Start bots
        echo "Starting Bot1..."
        cd clients/python
        python3 poker_bot.py --server http://localhost:8000 --name "Bot1" > bot1.log 2>&1 &
        BOT1_PID=$!
        echo $BOT1_PID > bot1.pid

        sleep 2

        echo "Starting Bot2..."
        python3 poker_bot.py --server http://localhost:8000 --name "Bot2" > bot2.log 2>&1 &
        BOT2_PID=$!
        echo $BOT2_PID > bot2.pid
        cd ../..

        echo -e "${GREEN}✅ Demo started!${NC}"
        echo "  - Open http://localhost:8000 in your browser to play"
        echo "  - Bot1 (PID: $BOT1_PID) and Bot2 (PID: $BOT2_PID) are playing"
        echo ""
        echo "Press Ctrl+C to stop all components"

        # Wait for interrupt
        trap "echo -e '\n${YELLOW}Stopping all components...${NC}'; kill $BOT1_PID $BOT2_PID 2>/dev/null; exit 0" INT
        wait
        ;;
    5)
        echo "Server is running. Press Ctrl+C to stop."
        trap "echo -e '\n${YELLOW}Stopping server...${NC}'; kill $(cat server/server.pid) 2>/dev/null; rm -f server/server.pid; exit 0" INT
        wait
        ;;
    6)
        if [ -f "server/server.pid" ]; then
            echo "Stopping server..."
            kill $(cat server/server.pid) 2>/dev/null || true
            rm -f server/server.pid
            echo -e "${GREEN}✅ Server stopped${NC}"
        fi
        exit 0
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
