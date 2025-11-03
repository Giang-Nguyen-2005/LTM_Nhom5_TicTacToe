import socket, json, time

HOST='127.0.0.1'
PORT=5051
ENC='utf-8'
BUFSIZE=4096

def recv_all(sock, timeout=0.2):
    sock.settimeout(timeout)
    out=''
    try:
        while True:
            d=sock.recv(BUFSIZE).decode(ENC, errors='ignore')
            if not d: break
            out+=d
    except Exception:
        pass
    return out

s=socket.socket()
s.connect((HOST,PORT))
print('CONNECTED')
# initial banner
print('INITIAL RECV->', recv_all(s))
# JOIN
s.sendall((json.dumps({'type':'JOIN','name':'AutoTester'})+'\n').encode(ENC))
time.sleep(0.2)
print('AFTER JOIN RECV->', recv_all(s))
# Send a chat
s.sendall((json.dumps({'type':'CHAT','msg':'Hello from test client'})+'\n').encode(ENC))
time.sleep(0.2)
print('AFTER CHAT RECV->', recv_all(s))
# Attempt a move (cell 0)
s.sendall((json.dumps({'type':'MOVE','cell':0})+'\n').encode(ENC))
time.sleep(0.2)
print('AFTER MOVE RECV->', recv_all(s))
# Reset game
s.sendall((json.dumps({'type':'RESET'})+'\n').encode(ENC))
time.sleep(0.2)
print('AFTER RESET RECV->', recv_all(s))

s.close()
print('DONE')
