# server.py
import socket
import threading
import json
from game import TicTacToeGame

class TicTacToeServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.waiting_client = None
        self.lock = threading.Lock()
        self.active_clients = set()
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"Server đang chạy tại {self.host}:{self.port}")
        print("Đang chờ người chơi kết nối...\n")
        
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"Người chơi mới kết nối từ {address}")
                
                with self.lock:
                    if self.waiting_client is None:
                        self.waiting_client = client_socket
                        self.send_message(client_socket, {
                            'type': 'WAITING',
                            'message': 'Đang chờ đối thủ...'
                        })
                    else:
                        # Check whether the waiting client is still alive without consuming data
                        dead = False
                        try:
                            import select
                            r, _, _ = select.select([self.waiting_client], [], [], 0)
                            if r:
                                try:
                                    # Peek to see if socket closed; MSG_PEEK avoids consuming data
                                    data = self.waiting_client.recv(1, socket.MSG_PEEK)
                                    if not data:
                                        dead = True
                                except Exception:
                                    dead = True
                        except Exception:
                            # if select or peek not supported, assume alive
                            dead = False

                        if dead:
                            # previous waiting client disconnected; replace with new
                            try:
                                self.waiting_client.close()
                            except: pass
                            self.waiting_client = client_socket
                            self.send_message(client_socket, {
                                'type': 'WAITING',
                                'message': 'Đang chờ đối thủ...'
                            })
                        else:
                            client1 = self.waiting_client
                            client2 = client_socket
                            self.waiting_client = None
                            game_thread = threading.Thread(
                                target=self.handle_game,
                                args=(client1, client2),
                                daemon=True
                            )
                            game_thread.start()
                        
        except KeyboardInterrupt:
            print("\nServer đang tắt...")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_game(self, client1, client2):
        game = TicTacToeGame()
        players = {
            client1: {'symbol': 'X', 'socket': client1},
            client2: {'symbol': 'O', 'socket': client2}
        }
        # mark clients as active in a game
        with self.lock:
            try:
                self.active_clients.add(client1)
                self.active_clients.add(client2)
            except: pass
        
        self.send_message(client1, {'type': 'START', 'symbol': 'X'})
        self.send_message(client2, {'type': 'START', 'symbol': 'O'})
        
        try:
            while True:
                # Main game loop for moves
                while not game.is_game_over():
                    current_socket = client1 if game.current_player == 'X' else client2
                    data = self.receive_message(current_socket)

                    if not data or data.get('type') == 'DISCONNECT':
                        other = client2 if current_socket == client1 else client1
                        self.send_message(other, {
                            'type': 'OPPONENT_DISCONNECTED',
                            'message': 'Đối thủ đã thoát. Bạn thắng!'
                        })
                        return

                    if data['type'] == 'MOVE':
                        row, col = data['row'], data['col']
                        symbol = players[current_socket]['symbol']

                        if game.make_move(row, col, symbol):
                            move_data = {
                                'type': 'MOVE_UPDATE',
                                'row': row, 'col': col, 'symbol': symbol
                            }
                            self.send_message(client1, move_data)
                            self.send_message(client2, move_data)

                            if game.is_game_over():
                                winner = game.get_winner()
                                win_line = game.get_winning_line()
                                if winner == 'DRAW':
                                    result = {'type': 'GAME_OVER', 'result': 'DRAW'}
                                    self.send_message(client1, result)
                                    self.send_message(client2, result)
                                else:
                                    win_data = {'type': 'GAME_OVER', 'result': 'WIN', 'win_line': win_line}
                                    lose_data = {'type': 'GAME_OVER', 'result': 'LOSE', 'win_line': win_line}
                                    if winner == 'X':
                                        self.send_message(client1, win_data)
                                        self.send_message(client2, lose_data)
                                    else:
                                        self.send_message(client1, lose_data)
                                        self.send_message(client2, win_data)
                        else:
                            self.send_message(current_socket, {
                                'type': 'INVALID_MOVE',
                                'message': 'Nước đi không hợp lệ!'
                            })

                # After game over, offer replay
                self.send_message(client1, {'type': 'REPLAY_REQUEST', 'message': 'Chơi lại không?'})
                self.send_message(client2, {'type': 'REPLAY_REQUEST', 'message': 'Chơi lại không?'})

                def recv_with_timeout(sock, timeout=30):
                    sock.settimeout(timeout)
                    try:
                        buffer = ""
                        while '\n' not in buffer:
                            chunk = sock.recv(1024).decode('utf-8')
                            if not chunk:
                                return None
                            buffer += chunk
                        message, _ = buffer.split('\n', 1)
                        return json.loads(message)
                    except Exception:
                        return None
                    finally:
                        try:
                            sock.settimeout(None)
                        except: pass

                votes = {client1: None, client2: None}
                # wait for both players to respond (or timeout)
                # CRITICAL: Must wait for BOTH votes before allowing disconnect/reconnect
                vote_received = {client1: False, client2: False}
                start_time = __import__('time').time()
                timeout = 30
                
                while not (vote_received[client1] and vote_received[client2]):
                    if __import__('time').time() - start_time > timeout:
                        # timeout: set unresponded votes to False
                        if not vote_received[client1]:
                            votes[client1] = False
                        if not vote_received[client2]:
                            votes[client2] = False
                        break
                    
                    for sock in (client1, client2):
                        if not vote_received[sock]:
                            # use non-blocking check to see if data is available
                            try:
                                import select
                                r, _, _ = select.select([sock], [], [], 0.1)
                                if r:
                                    data = recv_with_timeout(sock, timeout=2)
                                    if data and data.get('type') == 'REPLAY':
                                        votes[sock] = bool(data.get('accept'))
                                        vote_received[sock] = True
                                        print(f"[REPLAY] {sock.getpeername()} voted: {votes[sock]}")
                            except Exception as e:
                                print(f"[REPLAY] Error waiting for vote from {sock.getpeername()}: {e}")
                                votes[sock] = False
                                vote_received[sock] = True
                
                # Log votes for debugging
                try:
                    print(f"Replay votes final: client1={votes.get(client1)}, client2={votes.get(client2)}")
                except: pass

                # if both accepted, reset game and continue; otherwise end
                if votes.get(client1) and votes.get(client2):
                    game.reset()
                    # inform clients that new match starts
                    self.send_message(client1, {'type': 'START', 'symbol': 'X'})
                    self.send_message(client2, {'type': 'START', 'symbol': 'O'})
                    continue
                else:
                    # notify only those who requested a rematch but whose opponent declined
                    for sock in (client1, client2):
                        try:
                            if votes.get(sock):
                                # this player wanted to rematch but opponent didn't
                                sock.sendall((json.dumps({'type': 'OPPONENT_DECLINED', 'message': 'Đối thủ đã từ chối ghép lại.'}) + '\n').encode('utf-8'))
                        except: pass
                    return
        
        except Exception as e:
            print(f"Lỗi trong phòng chơi: {e}")
        finally:
            # cleanup active clients
            with self.lock:
                try: self.active_clients.discard(client1)
                except: pass
                try: self.active_clients.discard(client2)
                except: pass
            try: client1.close()
            except: pass
            try: client2.close()
            except: pass
            print("Một phòng chơi đã kết thúc\n")
    
    def monitor_waiting_player(self, client_socket):
        """(removed) Monitoring waiting player via background recv caused issues
        with a non-blocking select+peek check implemented in the accept loop,
        a separate monitor thread is no longer required.
        """
        return
    
    def send_message(self, client_socket, data):
        try:
            message = json.dumps(data) + '\n'
            client_socket.sendall(message.encode('utf-8'))
        except: pass
    
    def receive_message(self, client_socket):
        try:
            buffer = ""
            while '\n' not in buffer:
                chunk = client_socket.recv(1024).decode('utf-8')
                if not chunk: return None
                buffer += chunk
            message, _ = buffer.split('\n', 1)
            return json.loads(message)
        except: return None


if __name__ == "__main__":
    server = TicTacToeServer()
    server.start()