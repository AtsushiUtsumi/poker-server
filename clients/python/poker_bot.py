#!/usr/bin/env python3
"""
Poker Bot - Automated poker player
Simple AI that makes decisions based on basic strategy
"""

import requests
import time
import random
import sys
from typing import Optional, Dict, Any

class PokerBot:
    def __init__(self, server_url: str, bot_name: str):
        self.server_url = server_url
        self.bot_name = bot_name
        self.table_id: Optional[str] = None
        self.player_id: Optional[str] = None
        self.api_token: Optional[str] = None

    def list_tables(self):
        """List all available tables"""
        try:
            response = requests.get(f"{self.server_url}/api/tables")
            response.raise_for_status()
            return response.json()["tables"]
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []

    def create_table(self, max_players: int = 6, small_blind: int = 5) -> Optional[str]:
        """Create a new table"""
        try:
            response = requests.post(
                f"{self.server_url}/api/tables",
                params={"max_players": max_players, "small_blind": small_blind}
            )
            response.raise_for_status()
            data = response.json()
            return data["table_id"]
        except Exception as e:
            print(f"Error creating table: {e}")
            return None

    def join_table(self, table_id: str) -> bool:
        """Join a table"""
        try:
            response = requests.post(
                f"{self.server_url}/api/tables/{table_id}/join",
                params={"player_name": self.bot_name, "is_bot": True}
            )
            response.raise_for_status()
            data = response.json()
            self.table_id = table_id
            self.player_id = data["player_id"]
            self.api_token = data.get("api_token")
            print(f"✅ Bot {self.bot_name} joined table {table_id[:8]}...")
            return True
        except Exception as e:
            print(f"Error joining table: {e}")
            return False

    def get_table_state(self) -> Optional[Dict[str, Any]]:
        """Get current table state"""
        try:
            response = requests.get(
                f"{self.server_url}/api/tables/{self.table_id}",
                params={"player_id": self.player_id}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting table state: {e}")
            return None

    def perform_action(self, action: str, amount: int = 0) -> bool:
        """Perform a game action"""
        try:
            response = requests.post(
                f"{self.server_url}/api/tables/{self.table_id}/action",
                json={
                    "player_id": self.player_id,
                    "action": action,
                    "amount": amount
                }
            )
            response.raise_for_status()
            print(f"🤖 Bot {self.bot_name}: {action}" + (f" ¥{amount}" if amount > 0 else ""))
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_detail = e.response.json().get("detail", "Unknown error")
                # Not our turn or invalid action - this is normal
                return False
            print(f"Error performing action: {e}")
            return False
        except Exception as e:
            print(f"Error performing action: {e}")
            return False

    def decide_action(self, state: Dict[str, Any]) -> tuple[str, int]:
        """
        Decide what action to take based on simple AI strategy
        Returns (action, amount)
        """
        # Find our player
        our_player = None
        for player in state["players"]:
            if player["id"] == self.player_id:
                our_player = player
                break

        if not our_player:
            return "fold", 0

        current_bet = state["current_bet"]
        our_bet = our_player["current_bet"]
        our_chips = our_player["chips"]
        pot = state["pot"]
        need_to_call = current_bet - our_bet

        # Simple strategy
        # 1. If we can check (no bet to call), sometimes bet, sometimes check
        if need_to_call == 0:
            if random.random() < 0.3:  # 30% of the time, make a small bet
                bet_amount = min(state["small_blind"] * 2, our_chips)
                return "bet", bet_amount
            else:
                return "check", 0

        # 2. If we need to call, decide based on pot odds and randomness
        # Simple heuristic: if call amount is more than 20% of our chips, fold more often
        call_ratio = need_to_call / our_chips if our_chips > 0 else 1.0

        if call_ratio > 0.5:
            # Large bet relative to our stack - fold 70% of the time
            if random.random() < 0.7:
                return "fold", 0
            else:
                return "call", 0
        elif call_ratio > 0.2:
            # Medium bet - fold 40% of the time
            if random.random() < 0.4:
                return "fold", 0
            else:
                return "call", 0
        else:
            # Small bet - mostly call, sometimes raise
            if random.random() < 0.8:
                return "call", 0
            else:
                # Small raise
                raise_amount = current_bet + min(state["small_blind"] * 2, our_chips - need_to_call)
                return "raise", raise_amount

    def play_game(self):
        """Main game loop"""
        print(f"🤖 Bot {self.bot_name} is playing...")

        consecutive_errors = 0
        max_consecutive_errors = 10

        while consecutive_errors < max_consecutive_errors:
            try:
                # Get current state
                state = self.get_table_state()
                if not state:
                    consecutive_errors += 1
                    time.sleep(2)
                    continue

                # Check if it's our turn
                if state.get("current_player_id") != self.player_id:
                    # Not our turn, wait
                    consecutive_errors = 0  # Reset error counter
                    time.sleep(1)
                    continue

                # It's our turn - decide action
                action, amount = self.decide_action(state)

                # Perform action
                success = self.perform_action(action, amount)
                if success:
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1

                # Wait a bit before next check
                time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n🤖 Bot {self.bot_name} is leaving...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                consecutive_errors += 1
                time.sleep(2)

        if consecutive_errors >= max_consecutive_errors:
            print(f"❌ Bot {self.bot_name} encountered too many errors, stopping...")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Poker Bot")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--name", default=f"Bot{random.randint(1, 999)}", help="Bot name")
    parser.add_argument("--table", help="Table ID to join (if not specified, will join first available or create)")
    args = parser.parse_args()

    bot = PokerBot(args.server, args.name)

    # Determine which table to join
    table_id = args.table
    if not table_id:
        # List tables and join first available
        tables = bot.list_tables()
        if tables:
            # Join first table with space
            for table in tables:
                if table["players"] < table["max_players"]:
                    table_id = table["table_id"]
                    print(f"Found available table: {table_id[:8]}...")
                    break

        if not table_id:
            # No available tables, create one
            print("No available tables, creating new one...")
            table_id = bot.create_table()
            if not table_id:
                print("Failed to create table")
                sys.exit(1)

    # Join table
    if not bot.join_table(table_id):
        print("Failed to join table")
        sys.exit(1)

    # Play game
    try:
        bot.play_game()
    except KeyboardInterrupt:
        print(f"\n🤖 Bot {args.name} stopped by user")

if __name__ == "__main__":
    main()
