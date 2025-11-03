# TicTacToeSocket

Midterm project for the Network Programming course: Tic-Tac-Toe (X-O 3x3)

This repository implements a networked Tic-Tac-Toe game with a JSON-based TCP server and a pygame-based GUI client. The server supports two active players (X and O) and any number of spectators. The protocol is text/JSON-based and easy to inspect.

Repository layout

- server.py
- client_ttt.py
- client.py
- game.py
- assets/
- README.md
- submission_checklist.json
- docs/

Quick start

1. Install dependencies:

```powershell
python -m pip install pygame
```

2. Start the server:

```powershell
python server.py
```

3. Start one or more GUI clients:

```powershell
python client_ttt.py
```

Or run the automated non-GUI integration test:

```powershell
python integration_test.py
```

For the original Vietnamese project brief see `docs/original_vietnamese.md`.
