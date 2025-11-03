#!/usr/bin/env python3
import pygame, socket, threading, json, sys, os

WIDTH, HEIGHT = 900, 600
GRID_SIZE = 480
MARGIN = 30
ENC = "utf-8"
BUFSIZE = 4096
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5051

ASSETS_DIR = "assets"
FONT_PATH = os.path.join(ASSETS_DIR, "font.ttf")
CLICK_WAV = os.path.join(ASSETS_DIR, "click.wav")

# ---------- UI Helpers ----------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TicTacToe Online")
clock = pygame.time.Clock()

def load_font(size):
    try:
        return pygame.font.Font(FONT_PATH, size)
    except:
        return pygame.font.SysFont("arial", size)

FONT_L = load_font(48)
FONT_M = load_font(28)
FONT_S = load_font(20)

def draw_button(rect, text, enabled=True):
    color = (40,160,255) if enabled else (120,120,120)
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, (255,255,255), rect, width=2, border_radius=12)
    label = FONT_M.render(text, True, (0,0,0))
    screen.blit(label, label.get_rect(center=rect.center))

def play_click():
    try:
        snd = pygame.mixer.Sound(CLICK_WAV)
        snd.play()
    except: pass

# ---------- Networking ----------
class Client:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()
        self.state = {
            "board":" "*9, "turn":"X", "winner":None, "players":[]
        }
        self.chat = []
        self.mark = "S"
        self.name = "Player"
        self.buffer = ""

    def send(self, obj):
        try:
            self.sock.sendall((json.dumps(obj)+"\n").encode(ENC))
        except: pass

    def join(self, name):
        self.name = name
        self.send({"type":"JOIN","name":name})

    def move(self, cell):
        self.send({"type":"MOVE","cell":cell})

    def chat_send(self, msg):
        self.send({"type":"CHAT","msg":msg})

    def reset(self):
        self.send({"type":"RESET"})

    def _recv_loop(self):
        try:
            while True:
                data = self.sock.recv(BUFSIZE)
                if not data: break
                self.buffer += data.decode(ENC, errors="ignore")
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n",1)
                    if not line.strip(): continue
                    try:
                        msg = json.loads(line)
                    except:
                        continue
                    self._handle(msg)
        except:
            pass

    def _handle(self, msg):
        t = msg.get("type")
        if t == "STATE":
            self.state = msg
        elif t == "ROLE":
            self.mark = msg.get("mark","S")
        elif t == "CHAT":
            self.chat.append(f"{msg.get('from')}: {msg.get('msg')}")
            self.chat = self.chat[-10:]
        elif t in ("INFO","ERROR"):
            self.chat.append(f"[{t}] {msg.get('msg')}")
            self.chat = self.chat[-10:]

# ---------- UI State ----------
client_a = None
client_b = None
input_name1 = "Player1"
input_name2 = "Player2"
input_chat = ""
editing_name1 = True
editing_name2 = False
editing_chat = False
active_player = 'A'  # 'A' or 'B' - which local client controls moves/chat

def active_client():
    return client_a if active_player == 'A' else client_b

# Sidebar buttons (placed lower to avoid overlapping chat & inputs)
btn_quit  = pygame.Rect(650, 560, 200, 40)
btn_reset = pygame.Rect(650, 610, 200, 40)

grid_rect = pygame.Rect(MARGIN, MARGIN+50, GRID_SIZE, GRID_SIZE)

def cell_from_pos(pos):
    if not grid_rect.collidepoint(pos): return None
    x = pos[0] - grid_rect.x
    y = pos[1] - grid_rect.y
    c = x // (GRID_SIZE//3)
    r = y // (GRID_SIZE//3)
    return int(r*3 + c)

def draw_board(state, last_hover=None):
    # frame
    pygame.draw.rect(screen, (30,40,60), grid_rect, border_radius=16)
    # grid lines
    for i in range(1,3):
        # vertical
        x = grid_rect.x + i*GRID_SIZE//3
        pygame.draw.line(screen, (200,200,200), (x, grid_rect.y), (x, grid_rect.bottom), 4)
        # horizontal
        y = grid_rect.y + i*GRID_SIZE//3
        pygame.draw.line(screen, (200,200,200), (grid_rect.x, y), (grid_rect.right, y), 4)

    # cells
    for idx, ch in enumerate(state["board"]):
        r, c = divmod(idx, 3)
        cx = grid_rect.x + c*GRID_SIZE//3 + GRID_SIZE//6
        cy = grid_rect.y + r*GRID_SIZE//3 + GRID_SIZE//6
        if ch in ("X","O"):
            col = (255,90,90) if ch == "X" else (90,220,120)
            label = FONT_L.render(ch, True, col)
            screen.blit(label, label.get_rect(center=(cx, cy)))
        elif last_hover == idx:
            ac = active_client()
            ghost = ac.mark if (ac and ac.mark in ("X","O")) else "."
            label = FONT_L.render(ghost, True, (120,120,120))
            screen.blit(label, label.get_rect(center=(cx, cy)))

def render_sidebar():
    # Header
    title = FONT_L.render("TicTacToe Online", True, (255,255,255))
    screen.blit(title, (MARGIN, 5))
    # Status panel
    status_rect = pygame.Rect(620, 20, 260, 120)
    pygame.draw.rect(screen, (20,80,120), status_rect, border_radius=12)
    pygame.draw.rect(screen, (255,255,255), status_rect, 2, border_radius=12)

    # Player A/B status
    a_name = client_a.name if client_a else "-"
    a_mark = client_a.mark if client_a else "-"
    b_name = client_b.name if client_b else "-"
    b_mark = client_b.mark if client_b else "-"
    mark_text = f"P1: {a_name} [{a_mark}]  P2: {b_name} [{b_mark}]"
    # show turn from whichever client has state, prefer A then B
    state = client_a.state if client_a and client_a.state else (client_b.state if client_b and client_b.state else {"turn":"-","winner":None})
    turn_text = f"Turn: {state.get('turn','-')}"
    winner = state.get("winner")
    win_text = "Winner: " + ("-" if not winner else ("Draw" if winner=="D" else winner))
    screen.blit(FONT_S.render(mark_text, True, (255,255,255)), (630, 35))
    screen.blit(FONT_S.render(turn_text, True, (255,255,255)), (630, 65))
    screen.blit(FONT_S.render(win_text,  True, (255,255,255)), (630, 95))

    # Players
    p_rect = pygame.Rect(620, 150, 260, 100)
    pygame.draw.rect(screen, (25,25,50), p_rect, border_radius=12)
    pygame.draw.rect(screen, (255,255,255), p_rect, 2, border_radius=12)
    screen.blit(FONT_M.render("Players", True, (255,255,255)), (630, 155))
    y = 185
    for p in state.get("players", []):
        s = f"{p['name']} [{p['mark']}]"
        screen.blit(FONT_S.render(s, True, (220,220,220)), (630, y))
        y += 22

    # Chat
    chat_rect = pygame.Rect(620, 260, 260, 140)
    pygame.draw.rect(screen, (15,15,25), chat_rect, border_radius=12)
    pygame.draw.rect(screen, (255,255,255), chat_rect, 2, border_radius=12)
    y = chat_rect.y + 10
    ac = active_client()
    chats = ac.chat if ac else []
    line_h = 20
    max_lines = max(1, (chat_rect.height - 16) // line_h)
    for line in chats[-max_lines:]:
        screen.blit(FONT_S.render(line, True, (230,230,230)), (630, y))
        y += line_h

    # Inputs (placed below chat)
    name1_label = FONT_S.render("P1 Name:", True, (255,255,255))
    name2_label = FONT_S.render("P2 Name:", True, (255,255,255))
    chat_label = FONT_S.render("Chat (active):", True, (255,255,255))
    screen.blit(name1_label, (620, 410))
    screen.blit(name2_label, (620, 445))
    screen.blit(chat_label, (620, 485))

    name1_box = pygame.Rect(675, 410, 140, 28)
    join1_box = pygame.Rect(820, 410, 60, 28)
    name2_box = pygame.Rect(675, 445, 140, 28)
    join2_box = pygame.Rect(820, 445, 60, 28)
    chat_box = pygame.Rect(675, 485, 205, 28)

    pygame.draw.rect(screen, (255,255,255), name1_box, 2, border_radius=8)
    pygame.draw.rect(screen, (255,255,255), join1_box, 2, border_radius=8)
    pygame.draw.rect(screen, (255,255,255), name2_box, 2, border_radius=8)
    pygame.draw.rect(screen, (255,255,255), join2_box, 2, border_radius=8)
    pygame.draw.rect(screen, (255,255,255), chat_box, 2, border_radius=8)

    name1_color = (255,255,0) if editing_name1 else (220,220,220)
    name2_color = (255,255,0) if editing_name2 else (220,220,220)
    chat_color = (255,255,0) if editing_chat else (220,220,220)

    screen.blit(FONT_S.render(input_name1, True, name1_color), (name1_box.x+6, name1_box.y+4))
    screen.blit(FONT_S.render("Join", True, (0,0,0)), (join1_box.x+18, join1_box.y+4))
    screen.blit(FONT_S.render(input_name2, True, name2_color), (name2_box.x+6, name2_box.y+4))
    screen.blit(FONT_S.render("Join", True, (0,0,0)), (join2_box.x+18, join2_box.y+4))
    screen.blit(FONT_S.render(input_chat, True, chat_color), (chat_box.x+6, chat_box.y+4))

    # Switch buttons (above the main action buttons)
    switch1 = pygame.Rect(620, 520, 90, 28)
    switch2 = pygame.Rect(715, 520, 90, 28)
    draw_button(switch1, "Control P1", enabled=(active_player=='A'))
    draw_button(switch2, "Control P2", enabled=(active_player=='B'))

    # Buttons
    draw_button(btn_quit, "Quit")
    draw_button(btn_reset, "Reset", enabled=True)

    # return the interactive rects we need for events
    return {
        'name1_box': name1_box, 'join1_box': join1_box,
        'name2_box': name2_box, 'join2_box': join2_box,
        'chat_box': chat_box, 'switch1': switch1, 'switch2': switch2
    }

# ---------- Main Loop ----------
hover_cell = None

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    hover_cell = cell_from_pos(mouse_pos)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if grid_rect.collidepoint(mouse_pos):
                ac = active_client()
                if ac and ac.state.get("winner") is None and ac.mark in ("X","O"):
                    cell = cell_from_pos(mouse_pos)
                    if cell is not None:
                        play_click()
                        ac.move(cell)
            elif btn_reset.collidepoint(mouse_pos):
                play_click()
                # send reset from both clients if present
                try:
                    if client_a: client_a.reset()
                except: pass
                try:
                    if client_b: client_b.reset()
                except: pass
            elif btn_quit.collidepoint(mouse_pos):
                running = False
            else:
                # focus inputs
                rects = render_sidebar()
                ny1 = rects['name1_box']
                j1 = rects['join1_box']
                ny2 = rects['name2_box']
                j2 = rects['join2_box']
                cy = rects['chat_box']
                sw1 = rects['switch1']
                sw2 = rects['switch2']
                editing_name1 = ny1.collidepoint(mouse_pos)
                editing_name2 = ny2.collidepoint(mouse_pos)
                editing_chat = cy.collidepoint(mouse_pos)
                if j1.collidepoint(mouse_pos):
                    # create/join client A
                    try:
                        globals()['client_a'] = Client(SERVER_HOST, SERVER_PORT)
                        client_a.join(input_name1 if input_name1.strip() else 'Player1')
                    except Exception as e:
                        print('join1 failed', e)
                if j2.collidepoint(mouse_pos):
                    try:
                        globals()['client_b'] = Client(SERVER_HOST, SERVER_PORT)
                        client_b.join(input_name2 if input_name2.strip() else 'Player2')
                    except Exception as e:
                        print('join2 failed', e)
                if sw1.collidepoint(mouse_pos):
                    active_player = 'A'
                if sw2.collidepoint(mouse_pos):
                    active_player = 'B'

        elif event.type == pygame.KEYDOWN:
            if editing_name1 or editing_name2:
                target = '1' if editing_name1 else '2'
                if event.key == pygame.K_RETURN:
                    if editing_name1:
                        try:
                            globals()['client_a'] = Client(SERVER_HOST, SERVER_PORT)
                            client_a.join(input_name1 if input_name1.strip() else "Player1")
                        except Exception as e:
                            print('join1 failed', e)
                        editing_name1 = False
                    else:
                        try:
                            globals()['client_b'] = Client(SERVER_HOST, SERVER_PORT)
                            client_b.join(input_name2 if input_name2.strip() else "Player2")
                        except Exception as e:
                            print('join2 failed', e)
                        editing_name2 = False
                elif event.key == pygame.K_BACKSPACE:
                    if editing_name1:
                        input_name1 = input_name1[:-1]
                    else:
                        input_name2 = input_name2[:-1]
                else:
                    if event.unicode.isprintable():
                        if editing_name1 and len(input_name1) < 20:
                            input_name1 += event.unicode
                        if editing_name2 and len(input_name2) < 20:
                            input_name2 += event.unicode
            elif editing_chat:
                if event.key == pygame.K_RETURN:
                    if input_chat.strip():
                        ac = active_client()
                        if ac: ac.chat_send(input_chat.strip())
                    input_chat = ""
                    editing_chat = False
                elif event.key == pygame.K_BACKSPACE:
                    input_chat = input_chat[:-1]
                else:
                    if len(input_chat) < 80 and event.unicode.isprintable():
                        input_chat += event.unicode
            else:
                # quick hotkeys
                if event.key == pygame.K_r:
                    try:
                        if client_a: client_a.reset()
                    except: pass
                    try:
                        if client_b: client_b.reset()
                    except: pass
                if event.key == pygame.K_1:
                    active_player = 'A'
                if event.key == pygame.K_2:
                    active_player = 'B'

    # Render
    screen.fill((10,12,20))
    draw_board((active_client().state if active_client() else {"board":"         "}), last_hover=hover_cell)
    rects = render_sidebar()

    # Winner overlay
    state = (active_client().state if active_client() else {"winner": None})
    w = state.get("winner")
    if w is not None:
        msg = "Draw!" if w == "D" else f"{w} Wins!"
        overlay = FONT_L.render(msg, True, (255,220,80))
        screen.blit(overlay, overlay.get_rect(center=(grid_rect.centerx, grid_rect.y-20)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
try:
    if client_a: client_a.sock.close()
except: pass
try:
    if client_b: client_b.sock.close()
except: pass
