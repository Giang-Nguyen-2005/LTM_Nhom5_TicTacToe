"""Console client for the Tic-Tac-Toe server.

Usage:
  python client.py [host] [port]

After connecting you will receive messages from the server and be prompted when it's
your turn. Type row and column separated by space (e.g. "1 2") where rows and cols
are 0-based (0..2).
"""

import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 5000


def recv_loop(sock):
    """Receive loop that prints server lines and signals prompts."""
    buffer = b""
    my_symbol = None
    your_turn = threading.Event()

    def input_thread():
        # separate thread waits for YOUR_TURN event then reads stdin
        while True:
            your_turn.wait()
            try:
                line = input('Enter move (r c): ').strip()
            except EOFError:
                return
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                print('Type two numbers: row col (0..2)')
                continue
            try:
                r = int(parts[0]); c = int(parts[1])
            except ValueError:
                print('Invalid numbers')
                continue
            msg = f"MOVE {r} {c}\n"
            try:
                sock.sendall(msg.encode('utf-8'))
            except Exception as e:
                print('Failed to send:', e)
                return
            your_turn.clear()

    threading.Thread(target=input_thread, daemon=True).start()

    while True:
        ch = sock.recv(1)
        if not ch:
            print('\nDisconnected from server')
            return
        if ch == b'\n':
            line = buffer.decode('utf-8').strip()
            buffer = b""
            if not line:
                continue
            parts = line.split(maxsplit=1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else ''
            if cmd == 'START':
                my_symbol = arg.strip()
                print(f'Game started. You are: {my_symbol}')
            elif cmd == 'YOUR_TURN':
                print('Your turn')
                your_turn.set()
            elif cmd == 'VALID_MOVE':
                print('Move accepted')
            elif cmd == 'INVALID':
                print('Invalid move, try again')
                your_turn.set()
            elif cmd == 'OPPONENT_MOVE':
                print('Opponent moved:', arg)
            elif cmd in ('WIN','LOSE','DRAW'):
                print('Game result:', cmd)
            elif cmd == 'MESSAGE':
                print('MSG:', arg)
            else:
                print('SERVER:', line)
        else:
            buffer += ch


def main():
    global HOST, PORT
    if len(sys.argv) >= 2:
        HOST = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            PORT = int(sys.argv[2])
        except ValueError:
            pass

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f'Connected to {HOST}:{PORT}. Waiting for pairing...')
        recv_loop(s)


if __name__ == '__main__':
    main()
