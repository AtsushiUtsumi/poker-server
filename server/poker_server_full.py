"""
Poker Game Server - FastAPI implementation
Texas Hold'em Poker with WebSocket support
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from enum import Enum
import uuid
import random
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Poker Game Server")

# ===== Data Models =====

class GamePhase(str, Enum):
    WAITING = "waiting"
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"

class Player:
    def __init__(self, player_id: str, name: str, is_bot: bool = False):
        self.id = player_id
        self.name = name
        self.chips = 1000  # Starting chips
        self.current_bet = 0
        self.cards = []
        self.folded = False
        self.is_bot = is_bot
        self.last_action_time = datetime.now()
        self.all_in = False

    def to_dict(self, show_cards: bool = False):
        return {
            "id": self.id,
            "name": self.name,
            "chips": self.chips,
            "current_bet": self.current_bet,
            "cards": self.cards if show_cards else ["hidden", "hidden"] if len(self.cards) == 2 else [],
            "folded": self.folded,
            "is_bot": self.is_bot,
            "all_in": self.all_in
        }

class PokerTable:
    def __init__(self, table_id: str, max_players: int = 6, small_blind: int = 5):
        self.id = table_id
        self.players: Dict[str, Player] = {}
        self.player_order: List[str] = []
        self.max_players = max_players
        self.small_blind = small_blind
        self.big_blind = small_blind * 2
        self.pot = 0
        self.current_bet = 0
        self.community_cards = []
        self.phase = GamePhase.WAITING
        self.dealer_position = 0
        self.current_player_index = 0
        self.created_at = datetime.now()
        self.deck = []
        self.last_action = None

    def add_player(self, player: Player) -> bool:
        if len(self.players) >= self.max_players:
            return False
        self.players[player.id] = player
        self.player_order.append(player.id)

        # Start game if we have at least 2 players
        if len(self.players) >= 2 and self.phase == GamePhase.WAITING:
            self.start_new_hand()

        return True

    def create_deck(self):
        """Create a standard 52-card deck"""
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
        random.shuffle(self.deck)

    def deal_card(self) -> str:
        """Deal one card from the deck"""
        if not self.deck:
            self.create_deck()
        return self.deck.pop()

    def start_new_hand(self):
        """Start a new hand"""
        if len(self.players) < 2:
            return

        # Reset table
        self.pot = 0
        self.current_bet = 0
        self.community_cards = []
        self.phase = GamePhase.PRE_FLOP

        # Reset players
        for player in self.players.values():
            player.current_bet = 0
            player.folded = False
            player.cards = []
            player.all_in = False

        # Create and shuffle deck
        self.create_deck()

        # Deal cards to players
        for _ in range(2):
            for player_id in self.player_order:
                if not self.players[player_id].folded:
                    self.players[player_id].cards.append(self.deal_card())

        # Post blinds
        active_players = [pid for pid in self.player_order if not self.players[pid].folded]
        if len(active_players) >= 2:
            # Small blind
            sb_player_id = active_players[(self.dealer_position + 1) % len(active_players)]
            sb_amount = min(self.small_blind, self.players[sb_player_id].chips)
            self.players[sb_player_id].chips -= sb_amount
            self.players[sb_player_id].current_bet = sb_amount
            self.pot += sb_amount

            # Big blind
            bb_player_id = active_players[(self.dealer_position + 2) % len(active_players)]
            bb_amount = min(self.big_blind, self.players[bb_player_id].chips)
            self.players[bb_player_id].chips -= bb_amount
            self.players[bb_player_id].current_bet = bb_amount
            self.pot += bb_amount
            self.current_bet = bb_amount

            # Set first player (after big blind)
            self.current_player_index = (self.dealer_position + 3) % len(active_players)

    def get_current_player_id(self) -> Optional[str]:
        """Get the current player's ID"""
        active_players = [pid for pid in self.player_order if not self.players[pid].folded]
        if not active_players or self.phase == GamePhase.WAITING:
            return None
        return active_players[self.current_player_index % len(active_players)]

    def advance_to_next_player(self):
        """Move to the next active player"""
        active_players = [pid for pid in self.player_order if not self.players[pid].folded]
        if not active_players:
            return

        self.current_player_index = (self.current_player_index + 1) % len(active_players)

        # Check if betting round is complete
        if self.is_betting_round_complete():
            self.advance_phase()

    def is_betting_round_complete(self) -> bool:
        """Check if all active players have matched the current bet"""
        active_players = [p for p in self.players.values() if not p.folded and not p.all_in]
        if len(active_players) <= 1:
            return True

        # All active players must have matched current_bet
        for player in active_players:
            if player.current_bet < self.current_bet:
                return False
        return True

    def advance_phase(self):
        """Advance to the next game phase"""
        # Reset bets for next round
        for player in self.players.values():
            player.current_bet = 0
        self.current_bet = 0
        self.current_player_index = (self.dealer_position + 1) % len(self.player_order)

        if self.phase == GamePhase.PRE_FLOP:
            # Deal flop (3 cards)
            self.community_cards = [self.deal_card() for _ in range(3)]
            self.phase = GamePhase.FLOP
        elif self.phase == GamePhase.FLOP:
            # Deal turn (1 card)
            self.community_cards.append(self.deal_card())
            self.phase = GamePhase.TURN
        elif self.phase == GamePhase.TURN:
            # Deal river (1 card)
            self.community_cards.append(self.deal_card())
            self.phase = GamePhase.RIVER
        elif self.phase == GamePhase.RIVER:
            # Go to showdown
            self.phase = GamePhase.SHOWDOWN
            self.handle_showdown()

    def handle_showdown(self):
        """Handle showdown - simplified version"""
        active_players = [p for p in self.players.values() if not p.folded]

        if len(active_players) == 1:
            # Only one player left - they win
            winner = active_players[0]
            winner.chips += self.pot
            logger.info(f"Player {winner.name} wins {self.pot} chips (others folded)")
        else:
            # TODO: Implement hand evaluation
            # For now, randomly pick a winner
            winner = random.choice(active_players)
            winner.chips += self.pot
            logger.info(f"Player {winner.name} wins {self.pot} chips (showdown)")

        # Start new hand after a delay
        self.dealer_position = (self.dealer_position + 1) % len(self.player_order)
        self.start_new_hand()

    def perform_action(self, player_id: str, action: ActionType, amount: int = 0) -> bool:
        """Perform a player action"""
        if player_id != self.get_current_player_id():
            return False

        player = self.players[player_id]

        if action == ActionType.FOLD:
            player.folded = True
            # Check if only one player left
            active_players = [p for p in self.players.values() if not p.folded]
            if len(active_players) == 1:
                self.phase = GamePhase.SHOWDOWN
                self.handle_showdown()
                return True

        elif action == ActionType.CHECK:
            if player.current_bet < self.current_bet:
                return False  # Cannot check, must call or fold

        elif action == ActionType.CALL:
            call_amount = min(self.current_bet - player.current_bet, player.chips)
            player.chips -= call_amount
            player.current_bet += call_amount
            self.pot += call_amount
            if player.chips == 0:
                player.all_in = True

        elif action == ActionType.BET:
            if self.current_bet > 0:
                return False  # Cannot bet, must raise
            bet_amount = min(amount, player.chips)
            player.chips -= bet_amount
            player.current_bet += bet_amount
            self.pot += bet_amount
            self.current_bet = player.current_bet
            if player.chips == 0:
                player.all_in = True

        elif action == ActionType.RAISE:
            total_amount = min(amount, player.chips)
            actual_raise = total_amount - player.current_bet
            player.chips -= actual_raise
            player.current_bet = total_amount
            self.pot += actual_raise
            self.current_bet = max(self.current_bet, player.current_bet)
            if player.chips == 0:
                player.all_in = True

        elif action == ActionType.ALL_IN:
            all_in_amount = player.chips
            player.chips = 0
            player.current_bet += all_in_amount
            self.pot += all_in_amount
            self.current_bet = max(self.current_bet, player.current_bet)
            player.all_in = True

        self.last_action = {
            "player_id": player_id,
            "player_name": player.name,
            "action": action,
            "amount": amount
        }

        self.advance_to_next_player()
        return True

    def to_dict(self, viewing_player_id: Optional[str] = None):
        """Convert table to dictionary"""
        return {
            "table_id": self.id,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "community_cards": self.community_cards,
            "phase": self.phase,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "current_player_id": self.get_current_player_id(),
            "players": [
                self.players[pid].to_dict(show_cards=(pid == viewing_player_id))
                for pid in self.player_order
            ],
            "last_action": self.last_action
        }

# ===== Global State =====

tables: Dict[str, PokerTable] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}  # table_id -> list of websockets

# ===== WebSocket Connection Manager =====

async def broadcast_to_table(table_id: str, message: dict):
    """Broadcast message to all connected clients at a table"""
    if table_id in websocket_connections:
        disconnected = []
        for ws in websocket_connections[table_id]:
            try:
                await ws.send_json(message)
            except:
                disconnected.append(ws)

        # Remove disconnected websockets
        for ws in disconnected:
            websocket_connections[table_id].remove(ws)

# ===== API Endpoints =====

@app.get("/")
async def root():
    """Redirect to static HTML"""
    return HTMLResponse(content=open("static/index.html").read())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tables": len(tables),
        "active_connections": sum(len(conns) for conns in websocket_connections.values())
    }

@app.get("/api/tables")
async def list_tables():
    """List all tables"""
    return {
        "tables": [
            {
                "table_id": table.id,
                "players": len(table.players),
                "max_players": table.max_players,
                "phase": table.phase,
                "small_blind": table.small_blind
            }
            for table in tables.values()
        ]
    }

@app.post("/api/tables")
async def create_table(max_players: int = Query(6), small_blind: int = Query(5)):
    """Create a new table"""
    table_id = str(uuid.uuid4())
    table = PokerTable(table_id, max_players, small_blind)
    tables[table_id] = table

    logger.info(f"Created table {table_id}")

    return {
        "table_id": table_id,
        "max_players": max_players,
        "small_blind": small_blind,
        "big_blind": small_blind * 2
    }

@app.get("/api/tables/{table_id}")
async def get_table(table_id: str, player_id: Optional[str] = Query(None)):
    """Get table state"""
    if table_id not in tables:
        raise HTTPException(status_code=404, detail="Table not found")

    table = tables[table_id]
    return table.to_dict(viewing_player_id=player_id)

@app.post("/api/tables/{table_id}/join")
async def join_table(
    table_id: str,
    player_name: str = Query(...),
    is_bot: bool = Query(False)
):
    """Join a table"""
    if table_id not in tables:
        raise HTTPException(status_code=404, detail="Table not found")

    table = tables[table_id]

    if len(table.players) >= table.max_players:
        raise HTTPException(status_code=400, detail="Table is full")

    player_id = str(uuid.uuid4())
    player = Player(player_id, player_name, is_bot)

    if not table.add_player(player):
        raise HTTPException(status_code=400, detail="Failed to join table")

    logger.info(f"Player {player_name} joined table {table_id}")

    # Broadcast player joined
    await broadcast_to_table(table_id, {
        "type": "player_joined",
        "player_id": player_id,
        "player_name": player_name,
        "table_state": table.to_dict()
    })

    response = {
        "player_id": player_id,
        "table_state": table.to_dict(viewing_player_id=player_id)
    }

    if is_bot:
        response["api_token"] = f"token_{player_id}"

    return response

class ActionRequest(BaseModel):
    player_id: str
    action: ActionType
    amount: Optional[int] = 0

@app.post("/api/tables/{table_id}/action")
async def perform_action(table_id: str, action_request: ActionRequest):
    """Perform a game action"""
    if table_id not in tables:
        raise HTTPException(status_code=404, detail="Table not found")

    table = tables[table_id]

    current_player_id = table.get_current_player_id()
    if action_request.player_id != current_player_id:
        current_player_name = table.players[current_player_id].name if current_player_id else "unknown"
        raise HTTPException(
            status_code=400,
            detail=f"Not your turn. Current player: {current_player_name}"
        )

    success = table.perform_action(
        action_request.player_id,
        action_request.action,
        action_request.amount or 0
    )

    if not success:
        raise HTTPException(status_code=400, detail="Invalid action")

    logger.info(f"Player {action_request.player_id} performed {action_request.action}")

    # Broadcast action
    await broadcast_to_table(table_id, {
        "type": "action_performed",
        "player_id": action_request.player_id,
        "player_name": table.players[action_request.player_id].name,
        "action": action_request.action,
        "amount": action_request.amount,
        "table_state": table.to_dict()
    })

    return {
        "success": True,
        "table_state": table.to_dict(viewing_player_id=action_request.player_id)
    }

@app.websocket("/ws/{table_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, table_id: str, player_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()

    # Add to connections
    if table_id not in websocket_connections:
        websocket_connections[table_id] = []
    websocket_connections[table_id].append(websocket)

    logger.info(f"WebSocket connected: {player_id} to table {table_id}")

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "player_id": player_id,
            "table_id": table_id
        })

        # Keep connection alive and handle ping/pong
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {player_id}")
        websocket_connections[table_id].remove(websocket)

        # Broadcast disconnection
        await broadcast_to_table(table_id, {
            "type": "player_disconnected",
            "player_id": player_id
        })

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ===== Main =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
