# TicTacToeSocket

Midterm project: networked Tic-Tac-Toe (3x3) using a simple line-based text protocol.

This repository contains the server (`server.py`), the pygame GUI client (`client_ttt.py`), the game logic (`game.py`) and the `assets/` used by the GUI.

Quick start

1. Install dependencies (GUI client requires pygame):

```powershell
python -m pip install pygame
```

2. Start the server on the default port 5000:

```powershell
python server.py
```

3. Start one or more GUI clients:

```powershell
python client_ttt.py
```

ASCII playthrough (readable preview)

The project uses a simple text protocol. Below is an ASCII simulation of a short game so you can picture how the board and messages look in a console-based view.

Board coordinate indices: rows and columns are 0..2

Empty board (cells shown as numbers for coordinates):

```text
   0   1   2
0  . | . | .
  ---+---+---
1  . | . | .
  ---+---+---
2  . | . | .
```

Legend: X (player X), O (player O), . empty

Sample session (server -> client lines and client -> server moves):

```text
SERVER: START X
SERVER: MESSAGE Waiting for opponent...
SERVER: YOUR_TURN
CLIENT -> SERVER: MOVE 0 0    # Player X places at row 0, col 0
SERVER: VALID_MOVE
SERVER -> O: OPPONENT_MOVE 0 0
```

Board after X's first move:

```text
   0   1   2
0  X | . | .
  ---+---+---
1  . | . | .
  ---+---+---
2  . | . | .
```

Next moves (condensed):

```text
1) X -> MOVE 0 0  (valid)
2) O -> MOVE 1 1  (valid)
3) X -> MOVE 0 1  (valid)
4) O -> MOVE 2 2  (valid)
5) X -> MOVE 0 2  (valid)  <-- X completes top row and wins
```

Final board (X wins):

```text
   0   1   2
0  X | X | X   <- X wins
  ---+---+---
1  . | O | .
  ---+---+---
2  . | . | O
```

Server final messages for winner:

```text
SERVER: WIN
SERVER -> opponent: LOSE
```

How to read this in the GUI

- The GUI client sends moves as (row, col) to the server.
- The server validates moves and broadcasts opponent moves.
- The GUI shows the same final board as the ASCII art above.

Notes

- This README provides a console-friendly preview of gameplay so reviewers can understand game flow without launching the GUI.
- For more details about the message protocol see `server.py` and `game.py`.
