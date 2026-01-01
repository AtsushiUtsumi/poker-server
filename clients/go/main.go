package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"poker-cli/client"
	"poker-cli/ui"
	"strconv"
	"strings"
)

func main() {
	serverURL := flag.String("server", "http://localhost:8000", "Poker server URL")
	playerName := flag.String("name", "GoPlayer", "Your player name")
	tableID := flag.String("table", "", "Table ID to join (empty to create new)")
	flag.Parse()

	ui.PrintBanner()

	c := client.NewClient(*serverURL)

	// Setup WebSocket message handler
	c.OnMessage = func(msg interface{}) {
		// Message will be displayed on next state update
	}

	// Join or create table
	var state *client.TableState
	var err error

	if *tableID == "" {
		// Create new table
		ui.PrintInfo("Creating new table...")
		*tableID, err = c.CreateTable(6, 5)
		if err != nil {
			ui.PrintError(err)
			return
		}
		ui.PrintSuccess(fmt.Sprintf("Created table: %s", *tableID))
	}

	// Join table
	ui.PrintInfo(fmt.Sprintf("Joining table %s as %s...", *tableID, *playerName))
	state, err = c.JoinTable(*tableID, *playerName, false)
	if err != nil {
		ui.PrintError(err)
		return
	}

	ui.PrintSuccess(fmt.Sprintf("Joined table! Your ID: %s", c.PlayerID))

	// Connect WebSocket
	err = c.ConnectWebSocket()
	if err != nil {
		ui.PrintError(fmt.Errorf("WebSocket connection failed: %v", err))
		ui.PrintInfo("Continuing without WebSocket (polling mode)")
	} else {
		ui.PrintSuccess("WebSocket connected")
	}

	defer c.Close()

	// Display initial state
	ui.PrintTableState(state, c.PlayerID)
	ui.PrintHelp()

	// Command loop
	scanner := bufio.NewScanner(os.Stdin)
	fmt.Print("\n> ")

	for scanner.Scan() {
		input := strings.TrimSpace(scanner.Text())
		if input == "" {
			fmt.Print("> ")
			continue
		}

		parts := strings.Fields(input)
		cmd := strings.ToLower(parts[0])

		switch cmd {
		case "quit", "exit", "q":
			ui.PrintInfo("Goodbye!")
			return

		case "help", "h", "?":
			ui.PrintHelp()

		case "state", "s":
			state, err = c.GetTableState()
			if err != nil {
				ui.PrintError(err)
			} else {
				ui.PrintTableState(state, c.PlayerID)
			}

		case "fold", "f":
			state, err = c.PerformAction("fold", 0)
			if err != nil {
				ui.PrintError(err)
			} else {
				ui.PrintTableState(state, c.PlayerID)
			}

		case "check", "k":
			state, err = c.PerformAction("check", 0)
			if err != nil {
				ui.PrintError(err)
			} else {
				ui.PrintTableState(state, c.PlayerID)
			}

		case "call", "c":
			state, err = c.PerformAction("call", 0)
			if err != nil {
				ui.PrintError(err)
			} else {
				ui.PrintTableState(state, c.PlayerID)
			}

		case "bet", "b":
			if len(parts) < 2 {
				ui.PrintError(fmt.Errorf("usage: bet <amount>"))
				break
			}
			amount, err := strconv.Atoi(parts[1])
			if err != nil {
				ui.PrintError(fmt.Errorf("invalid amount: %s", parts[1]))
				break
			}
			state, err = c.PerformAction("bet", amount)
			if err != nil {
				ui.PrintError(err)
			} else {
				ui.PrintTableState(state, c.PlayerID)
			}

		case "raise", "r":
			if len(parts) < 2 {
				ui.PrintError(fmt.Errorf("usage: raise <amount>"))
				break
			}
			amount, err := strconv.Atoi(parts[1])
			if err != nil {
				ui.PrintError(fmt.Errorf("invalid amount: %s", parts[1]))
				break
			}
			state, err = c.PerformAction("raise", amount)
			if err != nil {
				ui.PrintError(err)
			} else {
				ui.PrintTableState(state, c.PlayerID)
			}

		case "allin", "a":
			state, err = c.PerformAction("all_in", 0)
			if err != nil {
				ui.PrintError(err)
			} else {
				ui.PrintTableState(state, c.PlayerID)
			}

		default:
			ui.PrintError(fmt.Errorf("unknown command: %s (type 'help' for commands)", cmd))
		}

		fmt.Print("\n> ")
	}

	if err := scanner.Err(); err != nil {
		ui.PrintError(err)
	}
}
