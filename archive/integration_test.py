# Integration test that starts server.accept_loop in-thread and runs a test client
import threading, socket, time, json
import server

HOST='127.0.0.1'
PORT=5051
ENC='utf-8'
BUFSIZE=4096

# start server.main in a background daemon thread (server.main binds and listens)
t = threading.Thread(target=server.main, daemon=True)
t.start()
print('[Integration] Server.main started in background')

# small test client
c = socket.socket()
c.connect((HOST, PORT))
print('[Client] connected')
# read initial
c.settimeout(0.5)
try:
    print('[Client] initial ->', c.recv(4096).decode(ENC))
except Exception as e:
    print('[Client] initial read err', e)
# send JOIN
c.sendall((json.dumps({'type':'JOIN','name':'Integration'}) + '\n').encode(ENC))

# receive a few messages
time.sleep(0.2)
try:
    print('[Client] after join ->', c.recv(8192).decode(ENC))
except Exception as e:
    print('[Client] recv err', e)

# send MOVE
c.sendall((json.dumps({'type':'MOVE','cell':0}) + '\n').encode(ENC))
time.sleep(0.2)
try:
    print('[Client] after move ->', c.recv(8192).decode(ENC))
except Exception as e:
    print('[Client] recv err', e)

# chat
c.sendall((json.dumps({'type':'CHAT','msg':'hi from integration'}) + '\n').encode(ENC))
time.sleep(0.2)
try:
    print('[Client] after chat ->', c.recv(8192).decode(ENC))
except Exception as e:
    print('[Client] recv err', e)

# reset
c.sendall((json.dumps({'type':'RESET'}) + '\n').encode(ENC))
time.sleep(0.2)
try:
    print('[Client] after reset ->', c.recv(8192).decode(ENC))
except Exception as e:
    print('[Client] recv err', e)

c.close()
print('[Client] closed')

# give server thread a moment then exit
time.sleep(0.5)
print('Integration test finished')
