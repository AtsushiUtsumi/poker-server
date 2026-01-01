package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	"github.com/gorilla/websocket"
)

type Client struct {
	ServerURL string
	TableID   string
	PlayerID  string
	ws        *websocket.Conn
	OnMessage func(interface{})
}

type TableState struct {
	TableID         string   `json:"table_id"`
	Pot             int      `json:"pot"`
	CurrentBet      int      `json:"current_bet"`
	CommunityCards  []string `json:"community_cards"`
	Phase           string   `json:"phase"`
	SmallBlind      int      `json:"small_blind"`
	BigBlind        int      `json:"big_blind"`
	CurrentPlayerID string   `json:"current_player_id"`
	Players         []Player `json:"players"`
	LastAction      *Action  `json:"last_action,omitempty"`
}

type Player struct {
	ID         string   `json:"id"`
	Name       string   `json:"name"`
	Chips      int      `json:"chips"`
	CurrentBet int      `json:"current_bet"`
	Cards      []string `json:"cards"`
	Folded     bool     `json:"folded"`
	IsBot      bool     `json:"is_bot"`
	AllIn      bool     `json:"all_in"`
}

type Action struct {
	PlayerID   string `json:"player_id"`
	PlayerName string `json:"player_name"`
	Action     string `json:"action"`
	Amount     int    `json:"amount"`
}

type TableInfo struct {
	TableID    string `json:"table_id"`
	Players    int    `json:"players"`
	MaxPlayers int    `json:"max_players"`
	Phase      string `json:"phase"`
	SmallBlind int    `json:"small_blind"`
}

func NewClient(serverURL string) *Client {
	return &Client{
		ServerURL: serverURL,
	}
}

func (c *Client) ListTables() ([]TableInfo, error) {
	resp, err := http.Get(c.ServerURL + "/api/tables")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Tables []TableInfo `json:"tables"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return result.Tables, nil
}

func (c *Client) CreateTable(maxPlayers, smallBlind int) (string, error) {
	u := fmt.Sprintf("%s/api/tables?max_players=%d&small_blind=%d",
		c.ServerURL, maxPlayers, smallBlind)

	resp, err := http.Post(u, "application/json", nil)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	var result struct {
		TableID string `json:"table_id"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}

	return result.TableID, nil
}

func (c *Client) JoinTable(tableID, playerName string, isBot bool) (*TableState, error) {
	u := fmt.Sprintf("%s/api/tables/%s/join?player_name=%s&is_bot=%t",
		c.ServerURL, tableID, url.QueryEscape(playerName), isBot)

	resp, err := http.Post(u, "application/json", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to join table: %s", string(body))
	}

	var result struct {
		PlayerID   string      `json:"player_id"`
		TableState *TableState `json:"table_state"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	c.TableID = tableID
	c.PlayerID = result.PlayerID

	return result.TableState, nil
}

func (c *Client) GetTableState() (*TableState, error) {
	u := fmt.Sprintf("%s/api/tables/%s?player_id=%s",
		c.ServerURL, c.TableID, c.PlayerID)

	resp, err := http.Get(u)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var state TableState
	if err := json.NewDecoder(resp.Body).Decode(&state); err != nil {
		return nil, err
	}

	return &state, nil
}

func (c *Client) PerformAction(action string, amount int) (*TableState, error) {
	payload := map[string]interface{}{
		"player_id": c.PlayerID,
		"action":    action,
		"amount":    amount,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	u := fmt.Sprintf("%s/api/tables/%s/action", c.ServerURL, c.TableID)
	resp, err := http.Post(u, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		var errResp struct {
			Detail string `json:"detail"`
		}
		json.Unmarshal(body, &errResp)
		if errResp.Detail != "" {
			return nil, fmt.Errorf("%s", errResp.Detail)
		}
		return nil, fmt.Errorf("action failed: %s", string(body))
	}

	var result struct {
		Success    bool        `json:"success"`
		TableState *TableState `json:"table_state"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return result.TableState, nil
}

func (c *Client) ConnectWebSocket() error {
	wsURL := c.ServerURL
	wsURL = "ws" + wsURL[4:] // Replace http with ws
	wsURL = fmt.Sprintf("%s/ws/%s/%s", wsURL, c.TableID, c.PlayerID)

	var err error
	c.ws, _, err = websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		return err
	}

	// Start heartbeat
	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()
		for range ticker.C {
			if c.ws != nil {
				c.ws.WriteMessage(websocket.TextMessage, []byte("ping"))
			}
		}
	}()

	// Start reading messages
	go func() {
		for {
			_, message, err := c.ws.ReadMessage()
			if err != nil {
				return
			}

			var msg interface{}
			if err := json.Unmarshal(message, &msg); err == nil {
				if c.OnMessage != nil {
					c.OnMessage(msg)
				}
			}
		}
	}()

	return nil
}

func (c *Client) Close() {
	if c.ws != nil {
		c.ws.Close()
	}
}
