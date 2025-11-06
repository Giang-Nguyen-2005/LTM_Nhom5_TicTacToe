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

FONT_L = load_font(44)
FONT_M = load_font(22)
FONT_S = load_font(16)

def draw_button(rect, text, enabled=True):
    # Brighter, modern button with subtle shadow and readable text
    base_color = (70,180,255) if enabled else (100,100,100)
    shadow_color = (20,20,20)
    text_color = (255,255,255) if enabled else (160,160,160)
    border_color = (255,255,255) if enabled else (130,130,130)

    # shadow (simple darker rect offset)
    sh = rect.move(2,2)
    pygame.draw.rect(screen, shadow_color, sh, border_radius=10)
    pygame.draw.rect(screen, base_color, rect, border_radius=10)
    pygame.draw.rect(screen, border_color, rect, width=2, border_radius=10)
    
    label = FONT_M.render(text, True, text_color)
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

# NEW: Constants for easier layout management
SIDEBAR_X = 620
SIDEBAR_WIDTH = 260
PANEL_MARGIN = 10 # Space between panels

def active_client():
    return client_a if active_player == 'A' else client_b

# (Global definitions for buttons are moved inside render_sidebar
#  and updated globally so the event loop can see them)
btn_quit = pygame.Rect(0,0,0,0)
btn_reset = pygame.Rect(0,0,0,0)

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


# =========================================================================
# ===== 🚀 REFACTORED SIDEBAR FUNCTION 🚀 =====
# =========================================================================
def render_sidebar():
    global btn_quit, btn_reset # We need to update the global rects for clicking

    # Header
    title = FONT_L.render("TicTacToe Online", True, (255,255,255))
    screen.blit(title, (MARGIN, 5))
    
    # --- Sidebar Panels (Dynamic Stacking Layout) ---
    current_y = 20 # Y_pos to stack panels

    # 1. Status panel
    status_rect = pygame.Rect(SIDEBAR_X, current_y, SIDEBAR_WIDTH, 120)
    pygame.draw.rect(screen, (40,100,150), status_rect, border_radius=12)
    pygame.draw.rect(screen, (255,255,255), status_rect, 2, border_radius=12)

    a_name = client_a.name if client_a else "-"
    a_mark = client_a.mark if client_a else "-"
    b_name = client_b.name if client_b else "-"
    b_mark = client_b.mark if client_b else "-"
    mark_text = f"P1: {a_name} [{a_mark}]  P2: {b_name} [{b_mark}]"
    state = client_a.state if client_a and client_a.state else (client_b.state if client_b and client_b.state else {"turn":"-","winner":None})
    turn_text = f"Turn: {state.get('turn','-')}"
    winner = state.get("winner")
    win_text = "Winner: " + ("-" if not winner else ("Draw" if winner=="D" else winner))
    
    # Draw text inside Status panel with padding
    screen.blit(FONT_S.render(mark_text, True, (255,255,255)), (status_rect.x + 10, status_rect.y + 15))
    screen.blit(FONT_S.render(turn_text, True, (255,255,255)), (status_rect.x + 10, status_rect.y + 45))
    screen.blit(FONT_S.render(win_text,  True, (255,255,255)), (status_rect.x + 10, status_rect.y + 75))

    current_y += status_rect.height + PANEL_MARGIN # <-- Move Y down for next panel

    # 2. Players Box
    p_rect = pygame.Rect(SIDEBAR_X, current_y, SIDEBAR_WIDTH, 100)
    pygame.draw.rect(screen, (40,40,70), p_rect, border_radius=12)
    pygame.draw.rect(screen, (255,255,255), p_rect, 2, border_radius=12)
    
    # *** FIX: Center-align "Players" title to prevent overflow ***
    players_label = FONT_M.render("Players", True, (255,255,255))
    players_label_rect = players_label.get_rect(centerx=p_rect.centerx, y=p_rect.y + 8) # 8px top padding
    screen.blit(players_label, players_label_rect)

    # Draw player list below title
    y = p_rect.y + 35 
    for p in state.get("players", []):
        s = f"{p['name']} [{p['mark']}]"
        screen.blit(FONT_S.render(s, True, (220,220,220)), (p_rect.x + 10, y))
        y += 22

    current_y += p_rect.height + PANEL_MARGIN # <-- Move Y down

    # 3. Chat Box
    chat_rect = pygame.Rect(SIDEBAR_X, current_y, SIDEBAR_WIDTH, 140)
    pygame.draw.rect(screen, (30,30,45), chat_rect, border_radius=12)
    pygame.draw.rect(screen, (255,255,255), chat_rect, 2, border_radius=12)
    
    y = chat_rect.y + 10
    ac = active_client()
    chats = ac.chat if ac else []
    line_h = 20
    max_lines = max(1, (chat_rect.height - 16) // line_h)
    for line in chats[-max_lines:]:
        screen.blit(FONT_S.render(line, True, (230,230,230)), (chat_rect.x + 10, y))
        y += line_h

    current_y += chat_rect.height + PANEL_MARGIN # <-- Move Y down

    # --- 4. Inputs (P1, P2, Chat) ---
    # Rearranged for clarity
    name1_label = FONT_S.render("P1 Name:", True, (240,240,240))
    name2_label = FONT_S.render("P2 Name:", True, (240,240,240))
    chat_label = FONT_S.render("Chat:", True, (240,240,240))
    
    # P1
    screen.blit(name1_label, (SIDEBAR_X, current_y + 4))
    name1_box = pygame.Rect(SIDEBAR_X + 70, current_y, 120, 30)
    join1_box = pygame.Rect(name1_box.right + 5, current_y, 65, 30) # Join button
    current_y += 30 + 5 # height + small margin

    # P2
    screen.blit(name2_label, (SIDEBAR_X, current_y + 4))
    name2_box = pygame.Rect(SIDEBAR_X + 70, current_y, 120, 30)
    join2_box = pygame.Rect(name2_box.right + 5, current_y, 65, 30) # Join button
    current_y += 30 + 10 # height + larger margin

    # Chat
    screen.blit(chat_label, (SIDEBAR_X, current_y + 4))
    chat_box = pygame.Rect(SIDEBAR_X + 70, current_y, SIDEBAR_WIDTH - 70, 30)
    
    # Draw input boxes
    pygame.draw.rect(screen, (230,230,230), name1_box, 2, border_radius=6)
    pygame.draw.rect(screen, (230,230,230), name2_box, 2, border_radius=6)
    pygame.draw.rect(screen, (230,230,230), chat_box, 2, border_radius=6)
    
    # Use draw_button for Join buttons
    draw_button(join1_box, "Join", enabled=(client_a is None))
    draw_button(join2_box, "Join", enabled=(client_b is None))

    # Helper function (no changes, just moved inside)
    def render_clipped(text, font, color, box):
        s = text
        surf = font.render(s, True, color)
        maxw = box.width - 12 # More padding
        if surf.get_width() <= maxw:
            screen.blit(surf, (box.x+6, box.y+6)) # More padding
            return
        while surf.get_width() > maxw and len(s) > 0:
            s = s[:-1]
            surf = font.render(s + '…', True, color)
        screen.blit(surf, (box.x+6, box.y+6))

    # Input text colors
    name1_color = (255,230,120) if editing_name1 else (220,220,220)
    name2_color = (255,230,120) if editing_name2 else (220,220,220)
    chat_color = (255,230,120) if editing_chat else (220,220,220)

    render_clipped(input_name1, FONT_S, name1_color, name1_box)
    render_clipped(input_name2, FONT_S, name2_color, name2_box)
    render_clipped(input_chat, FONT_S, chat_color, chat_box)

    # --- 5. Bottom Control Buttons ---
    # Pinned to the bottom of the screen for a clean look
    
    # Row 1 (Quit/Reset)
    bottom_y = HEIGHT - PANEL_MARGIN - 36 # Start from very bottom
    btn_quit = pygame.Rect(SIDEBAR_X, bottom_y, (SIDEBAR_WIDTH // 2) - 5, 36)
    btn_reset = pygame.Rect(SIDEBAR_X + (SIDEBAR_WIDTH // 2) + 5, bottom_y, (SIDEBAR_WIDTH // 2) - 5, 36)
    
    # Row 2 (Control P1/P2)
    bottom_y -= (36 + PANEL_MARGIN) # Move Y up for the next row
    switch1 = pygame.Rect(SIDEBAR_X, bottom_y, (SIDEBAR_WIDTH // 2) - 5, 36)
    switch2 = pygame.Rect(SIDEBAR_X + (SIDEBAR_WIDTH // 2) + 5, bottom_y, (SIDEBAR_WIDTH // 2) - 5, 36)

    # Draw all buttons
    draw_button(switch1, "Control P1", enabled=(active_player=='A'))
    draw_button(switch2, "Control P2", enabled=(active_player=='B'))
    draw_button(btn_quit, "Quit")
    draw_button(btn_reset, "Reset", enabled=(client_a or client_b))
    
    # Return all interactive rects for the event loop
    return {
        'name1_box': name1_box, 'join1_box': join1_box,
        'name2_box': name2_box, 'join2_box': join2_box,
        'chat_box': chat_box, 'switch1': switch1, 'switch2': switch2
    }
# =========================================================================
# ===== END REFACTORED SIDEBAR FUNCTION =====
# =========================================================================


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
                rects = render_sidebar() # This call now also updates global btn_quit/btn_reset
                ny1 = rects['name1_box']
                j1 = rects['join1_box']
                ny2 = rects['name2_box']
                j2 = rects['join2_box']
                cy = rects['chat_box']
                sw1 = rects['switch1']
                sw2 = rects['switch2']
                
                # Check for input box clicks
                editing_name1 = ny1.collidepoint(mouse_pos)
                editing_name2 = ny2.collidepoint(mouse_pos)
                editing_chat = cy.collidepoint(mouse_pos)
                
                # Check for button clicks
                if j1.collidepoint(mouse_pos) and client_a is None:
                    play_click()
                    try:
                        globals()['client_a'] = Client(SERVER_HOST, SERVER_PORT)
                        client_a.join(input_name1 if input_name1.strip() else 'Player1')
                    except Exception as e:
                        print('join1 failed', e)
                if j2.collidepoint(mouse_pos) and client_b is None:
                    play_click()
                    try:
                        globals()['client_b'] = Client(SERVER_HOST, SERVER_PORT)
                        client_b.join(input_name2 if input_name2.strip() else 'Player2')
                    except Exception as e:
                        print('join2 failed', e)
                if sw1.collidepoint(mouse_pos):
                    play_click()
                    active_player = 'A'
                if sw2.collidepoint(mouse_pos):
                    play_click()
                    active_player = 'B'

        elif event.type == pygame.KEYDOWN:
            if editing_name1 or editing_name2:
                target = '1' if editing_name1 else '2'
                if event.key == pygame.K_RETURN:
                    if editing_name1 and client_a is None:
                        try:
                            globals()['client_a'] = Client(SERVER_HOST, SERVER_PORT)
                            client_a.join(input_name1 if input_name1.strip() else "Player1")
                        except Exception as e:
                            print('join1 failed', e)
                        editing_name1 = False
                    elif editing_name2 and client_b is None:
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
                    editing_chat = False # Stop editing on Enter
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
        # (Placed above the grid)
        screen.blit(overlay, overlay.get_rect(center=(grid_rect.centerx, grid_rect.y - 30))) 

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
try:
    if client_a: client_a.sock.close()
except: pass
try:
    if client_b: client_b.sock.close()
except: pass