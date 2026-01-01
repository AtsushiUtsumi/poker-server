package ui

import (
	"fmt"
	"poker-cli/client"
	"strings"

	"github.com/fatih/color"
)

var (
	green  = color.New(color.FgGreen).SprintFunc()
	yellow = color.New(color.FgYellow).SprintFunc()
	red    = color.New(color.FgRed).SprintFunc()
	cyan   = color.New(color.FgCyan).SprintFunc()
	bold   = color.New(color.Bold).SprintFunc()
)

func PrintBanner() {
	fmt.Println(cyan("╔════════════════════════════════════════╗"))
	fmt.Println(cyan("║") + bold("     🎲 POKER CLI CLIENT 🎲          ") + cyan("║"))
	fmt.Println(cyan("╔════════════════════════════════════════╗"))
	fmt.Println()
}

func PrintTables(tables []client.TableInfo) {
	if len(tables) == 0 {
		fmt.Println(yellow("No tables available."))
		return
	}

	fmt.Println(bold("\n📋 Available Tables:"))
	fmt.Println(strings.Repeat("─", 80))
	fmt.Printf("%-12s %-10s %-15s %-10s\n", "Table ID", "Players", "Phase", "Blinds")
	fmt.Println(strings.Repeat("─", 80))

	for _, table := range tables {
		tableID := table.TableID[:8] + "..."
		players := fmt.Sprintf("%d/%d", table.Players, table.MaxPlayers)
		blinds := fmt.Sprintf("¥%d/¥%d", table.SmallBlind, table.SmallBlind*2)
		fmt.Printf("%-12s %-10s %-15s %-10s\n",
			tableID, players, table.Phase, blinds)
	}
	fmt.Println(strings.Repeat("─", 80))
}

func PrintTableState(state *client.TableState, playerID string) {
	fmt.Print("\033[H\033[2J") // Clear screen

	PrintBanner()

	// Table info
	fmt.Println(bold("🎲 TABLE STATE"))
	fmt.Println(strings.Repeat("═", 80))
	fmt.Printf("%s Phase: %s\n", yellow("📊"), green(state.Phase))
	fmt.Printf("%s Pot: %s | Current Bet: %s\n",
		yellow("💰"),
		green(fmt.Sprintf("¥%d", state.Pot)),
		yellow(fmt.Sprintf("¥%d", state.CurrentBet)))
	fmt.Println(strings.Repeat("═", 80))

	// Community cards
	if len(state.CommunityCards) > 0 {
		fmt.Printf("\n%s Community Cards: ", yellow("🃏"))
		for _, card := range state.CommunityCards {
			fmt.Print(formatCard(card) + " ")
		}
		fmt.Println()
	}

	// Players
	fmt.Println(bold("\n👥 PLAYERS:"))
	fmt.Println(strings.Repeat("─", 80))

	for _, player := range state.Players {
		isMe := player.ID == playerID
		isCurrent := player.ID == state.CurrentPlayerID

		prefix := "  "
		if isCurrent {
			prefix = green("→ ")
		}

		status := ""
		if player.Folded {
			status = red("[FOLDED]")
		} else if player.AllIn {
			status = yellow("[ALL IN]")
		}

		name := player.Name
		if isMe {
			name = bold(cyan(name + " (YOU)"))
		}
		if player.IsBot {
			name += " 🤖"
		}

		fmt.Printf("%s%-25s 💵 ¥%-6d Bet: ¥%-4d %s ",
			prefix, name, player.Chips, player.CurrentBet, status)

		// Show cards
		if len(player.Cards) > 0 {
			fmt.Print(" | Cards: ")
			for _, card := range player.Cards {
				if card == "hidden" {
					fmt.Print("🂠 ")
				} else {
					fmt.Print(formatCard(card) + " ")
				}
			}
		}

		fmt.Println()
	}
	fmt.Println(strings.Repeat("─", 80))

	// Current player indicator
	if state.CurrentPlayerID == playerID {
		fmt.Println(green(bold("\n⏰ YOUR TURN! Enter your action.")))
	} else {
		currentPlayer := findPlayer(state.Players, state.CurrentPlayerID)
		if currentPlayer != nil {
			fmt.Printf("\n⏰ Waiting for %s...\n", currentPlayer.Name)
		}
	}

	// Last action
	if state.LastAction != nil {
		action := state.LastAction
		actionStr := fmt.Sprintf("%s %s", action.PlayerName, action.Action)
		if action.Amount > 0 {
			actionStr += fmt.Sprintf(" ¥%d", action.Amount)
		}
		fmt.Printf("\n%s Last action: %s\n", yellow("📝"), actionStr)
	}
}

func formatCard(card string) string {
	if strings.Contains(card, "♥") || strings.Contains(card, "♦") {
		return red("[" + card + "]")
	}
	return "[" + card + "]"
}

func findPlayer(players []client.Player, playerID string) *client.Player {
	for _, p := range players {
		if p.ID == playerID {
			return &p
		}
	}
	return nil
}

func PrintHelp() {
	fmt.Println(bold("\n📖 AVAILABLE COMMANDS:"))
	fmt.Println(strings.Repeat("─", 60))
	fmt.Println("  fold, f           - Fold your hand")
	fmt.Println("  check, k          - Check")
	fmt.Println("  call, c           - Call the current bet")
	fmt.Println("  bet <amount>, b   - Bet an amount")
	fmt.Println("  raise <amount>, r - Raise to an amount")
	fmt.Println("  allin, a          - Go all in")
	fmt.Println("  state, s          - Show current table state")
	fmt.Println("  help, h, ?        - Show this help")
	fmt.Println("  quit, exit, q     - Quit the game")
	fmt.Println(strings.Repeat("─", 60))
}

func PrintError(err error) {
	fmt.Println(red("❌ Error: " + err.Error()))
}

func PrintSuccess(message string) {
	fmt.Println(green("✅ " + message))
}

func PrintInfo(message string) {
	fmt.Println(yellow("ℹ️  " + message))
}
