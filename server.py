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
import json
from game import TicTacToeGame

class TicTacToeServer:
    """
    Server game Tic-Tac-Toe đa người chơi
    """
    
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.waiting_client = None  # Client đang chờ ghép đôi
        self.games = []  # Danh sách các phòng chơi
        self.lock = threading.Lock()
        
    def start(self):
        """
        Khởi động server
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"🎮 Server đang chạy tại {self.host}:{self.port}")
        print("⏳ Đang chờ người chơi kết nối...")
        
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"✅ Người chơi mới kết nối từ {address}")
                
                # Ghép đôi người chơi
                if self.waiting_client is None:
                    # Client đầu tiên, đặt vào chế độ chờ
                    self.waiting_client = client_socket
                    self.send_message(client_socket, {
                        'type': 'WAITING',
                        'message': 'Đang chờ đối thủ...'
                    })
                else:
                    # Client thứ hai, tạo phòng chơi mới
                    client1 = self.waiting_client
                    client2 = client_socket
                    self.waiting_client = None
                    
                    # Tạo luồng mới cho phòng chơi
                    game_thread = threading.Thread(
                        target=self.handle_game,
                        args=(client1, client2)
                    )
                    game_thread.daemon = True
                    game_thread.start()
                    
                    print(f"Đã tạo phòng chơi mới! Tổng số phòng: {len(self.games) + 1}")
        
        except KeyboardInterrupt:
            print("\n🛑 Server đang tắt...")
        finally:
            self.server_socket.close()
    


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
