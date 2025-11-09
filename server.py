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
    
    def handle_game(self, client1, client2):
        """
        Xử lý một ván chơi giữa 2 người chơi
        
        Args:
            client1: Socket của người chơi X
            client2: Socket của người chơi O
        """
        game = TicTacToeGame()
        players = {
            client1: {'symbol': 'X', 'socket': client1},
            client2: {'symbol': 'O', 'socket': client2}
        }
        
        # Thông báo cho cả 2 người chơi về ký hiệu của họ
        self.send_message(client1, {
            'type': 'START',
            'symbol': 'X',
            'message': 'Trận đấu bắt đầu! Bạn là X và đi trước.'
        })
        
        self.send_message(client2, {
            'type': 'START',
            'symbol': 'O',
            'message': 'Trận đấu bắt đầu! Bạn là O và đi sau.'
        })
        
        # Vòng lặp game
        try:
            while not game.is_game_over():
                # Xác định người chơi hiện tại
                current_socket = client1 if game.current_player == 'X' else client2
                
                # Nhận nước đi từ người chơi
                data = self.receive_message(current_socket)
                
                if not data or data['type'] == 'DISCONNECT':
                    # Người chơi ngắt kết nối
                    other_socket = client2 if current_socket == client1 else client1
                    self.send_message(other_socket, {
                        'type': 'OPPONENT_DISCONNECTED',
                        'message': 'Đối thủ đã ngắt kết nối. Bạn thắng!'
                    })
                    break
                
                if data['type'] == 'MOVE':
                    row, col = data['row'], data['col']
                    player_symbol = players[current_socket]['symbol']
                    
                    # Thực hiện nước đi
                    if game.make_move(row, col, player_symbol):
                        # Gửi cập nhật cho cả 2 người chơi
                        move_data = {
                            'type': 'MOVE_UPDATE',
                            'row': row,
                            'col': col,
                            'symbol': player_symbol,
                            'board': game.get_board_state()
                        }
                        
                        self.send_message(client1, move_data)
                        self.send_message(client2, move_data)
                        
                        # Kiểm tra game kết thúc
                        if game.is_game_over():
                            winner = game.get_winner()
                            
                            if winner == 'DRAW':
                                result_data = {
                                    'type': 'GAME_OVER',
                                    'result': 'DRAW',
                                    'message': 'Hòa!'
                                }
                                self.send_message(client1, result_data)
                                self.send_message(client2, result_data)
                            else:
                                message = f'Người chơi {winner} thắng!'
                                result_client1 = {
                                    'type': 'GAME_OVER',
                                    'result': 'WIN' if winner == players[client1]['symbol'] else 'LOSE',
                                    'message': message
                                }
                                # Gửi kết quả cho client 1
                                self.send_message(client1, result_client1)
                                result_client2 = {
                                    'type': 'GAME_OVER',
                                    'result': 'WIN' if winner == players[client2]['symbol'] else 'LOSE',
                                    'message': message
                                }
                                # Gửi kết quả cho client 2
                                self.send_message(client2, result_client2)
                            
                            break
                    else:
                        # Nước đi không hợp lệ
                        self.send_message(current_socket, {
                            'type': 'INVALID_MOVE',
                            'message': 'Nước đi không hợp lệ!'
                        })
        
        except Exception as e:
            print(f"❌ Lỗi trong phòng chơi: {e}")
        
        finally:
            # Đóng kết nối
            try:
                client1.close()
                client2.close()
            except:
                pass
            print("🏁 Một phòng chơi đã kết thúc")
    

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
