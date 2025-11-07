"""Tic-Tac-Toe multi-room server using TCP sockets and threading.

Protocol (line-based, UTF-8, \n terminated):
 - Client -> Server:
	 MOVE r c    -- attempt to place on row r (0-2) and col c (0-2)
 - Server -> Client:
	 START X|O   -- assigned symbol and game starts
	 YOUR_TURN   -- it's your turn to send MOVE
	 VALID_MOVE  -- last move accepted
	 INVALID     -- last move invalid (out of turn or occupied)
	 OPPONENT_MOVE r c -- opponent moved
	 WIN / LOSE / DRAW  -- game result
	 MESSAGE text -- informational

This server pairs clients in the order they connect (first-come, first-paired)
and spawns a thread per game (room). Designed to be simple and easy to extend.
"""

import socket
import threading
import logging
import sys
from game import TicTacToeGame

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

import socket
import threading
import json
import time
import random

HOST, PORT = "0.0.0.0", 5051
ENC = "utf-8"
BUFSIZE = 4096

# ---- Game Model ----
class TTTGame:
	def __init__(self):
		self.lock = threading.Lock()
		# mapping sock -> {name, mark}
		self.players = {}
		self.reset()

	def reset(self):
		with self.lock:
			# Reset board and game state but preserve connected players mapping.
			# Previously we wiped `self.players` which caused connected clients
			# to lose their roles and be treated as spectators after a reset.
			# Keep existing players so clients remain players and can continue.
			self.board = [" "] * 9
			# do NOT clear self.players or self.order here; keep connections
			# reset turn/winner/last_move to start a fresh game
			self.turn = "X"
			self.winner = None
			self.last_move = None

	def assign_role(self, sock, name):
		with self.lock:
			self.players[sock] = {"name": name, "mark": "S"}  # spectator default
			# Upgrade to X or O if slots empty
			marks = [p["mark"] for p in self.players.values()]
			if "X" not in marks:
				self.players[sock]["mark"] = "X"
			elif "O" not in marks:
				self.players[sock]["mark"] = "O"
			return self.players[sock]["mark"]

	def move(self, sock, idx):
		with self.lock:
			if self.winner is not None:
				return False, "Game over. Press Reset."
			if idx < 0 or idx > 8:
				return False, "Invalid cell."
			mark = self.players.get(sock, {"mark":"S"})["mark"]
			if mark not in ("X","O"):
				return False, "Spectator cannot move."
			if mark != self.turn:
				return False, f"Not your turn. ({self.turn})"
			if self.board[idx] != " ":
				return False, "Cell already taken."
			self.board[idx] = mark
			self.last_move = idx
			self.turn = "O" if self.turn == "X" else "X"
			self.winner = self.check_winner()
			return True, "OK"

	def check_winner(self):
		b = self.board
		wins = [(0,1,2),(3,4,5),(6,7,8),
				(0,3,6),(1,4,7),(2,5,8),
				(0,4,8),(2,4,6)]
		for a,b1,c in wins:
			line = self.board[a]+self.board[b1]+self.board[c]
			if line == "XXX": return "X"
			if line == "OOO": return "O"
		if all(c != " " for c in self.board):
			return "D"  # draw
		return None

	def snapshot(self):
		with self.lock:
			return {
				"type":"STATE",
				"board":"".join(self.board),
				"turn": self.turn,
				"winner": self.winner,
				"players": [ {"name":info["name"], "mark":info["mark"]}
							 for info in self.players.values() ]
			}

game = TTTGame()
clients = set()
srv_lock = threading.Lock()

def send(sock, obj):
	try:
		data = (json.dumps(obj) + "\n").encode(ENC)
		sock.sendall(data)
	except Exception:
		pass

def broadcast(obj):
	dead = []
	for s in list(clients):
		try:
			s.sendall((json.dumps(obj)+"\n").encode(ENC))
		except Exception:
			dead.append(s)
	for d in dead:
		drop_client(d)

def drop_client(sock):
	with srv_lock:
		if sock in clients:
			clients.remove(sock)
	# ensure we always have a name to report even if game.players missing
	name = "?"
	try:
		if hasattr(game, 'players') and sock in game.players:
			name = game.players.get(sock, {}).get("name","?")
			try:
				del game.players[sock]
			except Exception:
				# ignore deletion errors
				pass
	except Exception:
		# fallback - keep name as '?'
		pass
	try: sock.close()
	except: pass
	broadcast({"type":"INFO","msg":f"{name} left."})
	# Rebalance X/O if a player left
	with game.lock:
		marks_present = [p["mark"] for p in game.players.values()]
		# ensure X then O assigned to earliest spectators
		need = []
		if "X" not in marks_present: need.append("X")
		if "O" not in marks_present: need.append("O")
		for need_mark in need:
			for s,info in game.players.items():
				if info["mark"] == "S":
					info["mark"] = need_mark
					break
	broadcast(game.snapshot())

def handle(sock, addr):
	clients.add(sock)
	name = f"Player@{addr[0]}:{addr[1]}"
	send(sock, {"type":"INFO","msg":"Connected. Send: {\"type\":\"JOIN\",\"name\":\"Alice\"}"})
	try:
		buf = ""
		while True:
			data = sock.recv(BUFSIZE)
			if not data: break
			buf += data.decode(ENC, errors="ignore")
			while "\n" in buf:
				line, buf = buf.split("\n",1)
				if not line.strip(): continue
				try:
					msg = json.loads(line)
				except Exception:
					send(sock, {"type":"ERROR","msg":"Invalid JSON"})
					continue

				t = msg.get("type")
				if t == "JOIN":
					name = msg.get("name","Player")
					role = game.assign_role(sock, name)
					broadcast({"type":"INFO","msg":f"{name} joined as {role}."})
					send(sock, {"type":"ROLE","mark":role})
					send(sock, game.snapshot())
				elif t == "MOVE":
					idx = int(msg.get("cell",-1))
					ok, reason = game.move(sock, idx)
					if not ok:
						send(sock, {"type":"ERROR","msg":reason})
					broadcast(game.snapshot())
				elif t == "CHAT":
					txt = str(msg.get("msg","")).strip()[:200]
					if txt:
						broadcast({"type":"CHAT","from":name,"msg":txt})
				elif t == "RESET":
					game.reset()
					broadcast({"type":"INFO","msg":"Game reset."})
					broadcast(game.snapshot())
				else:
					send(sock, {"type":"ERROR","msg":"Unknown type"})
	except Exception as e:
		pass
	finally:
		drop_client(sock)

def main():
	print(f"[Server] TicTacToe on {HOST}:{PORT}")
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((HOST, PORT))
		s.listen(16)
		while True:
			conn, addr = s.accept()
			threading.Thread(target=handle, args=(conn,addr), daemon=True).start()

if __name__ == "__main__":
	main()
