# #!/usr/bin/env python3
# import pygame, socket, threading, json, sys, os, time

# WIDTH, HEIGHT = 900, 600
# GRID_SIZE = 480
# BASE_GRID_SIZE = GRID_SIZE
# PADDING = 12
# RADIUS = 12

# MARGIN = 30

# # Theme colors (WCAG-friendly palette)
# BG_COLOR = (15,23,42)        # #0F172A
# ACCENT = (59,130,246)        # #3B82F6
# TILE_BG = (46,58,79)         # #2E3A4F
# TEXT_COLOR = (226,232,240)   # #E2E8F0

# # Responsive sidebar (60% board, 40% sidebar)
# SIDEBAR_WIDTH = int(WIDTH * 0.4) - MARGIN
# SIDEBAR_X = WIDTH - SIDEBAR_WIDTH - MARGIN
# BASE_GRID_SIZE = GRID_SIZE
# split_screen = False
# zoom = 1.0
# MIN_ZOOM = 0.6
# MAX_ZOOM = 1.6
# ZOOM_STEP = 0.2
# ENC = "utf-8"
# BUFSIZE = 4096
# SERVER_HOST = "127.0.0.1"
# SERVER_PORT = 5051

# # Collect recent connection errors to show in the UI (so user sees them in-game)
# connection_errors = []

# def add_connection_error(msg):
#     try:
#         connection_errors.append(str(msg))
#         # keep list short
#         if len(connection_errors) > 6:
#             del connection_errors[0]
#     except: pass

# ASSETS_DIR = "assets"
# FONT_PATH = os.path.join(ASSETS_DIR, "font.ttf")
# CLICK_WAV = os.path.join(ASSETS_DIR, "click.wav")

# # ---------- UI Helpers ----------
# pygame.init()
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
# pygame.display.set_caption("TicTacToe Online")
# clock = pygame.time.Clock()

# def load_font(size):
#     try:
#         return pygame.font.Font(FONT_PATH, size)
#     except:
#         return pygame.font.SysFont("arial", size)

# # Base font sizes (will be scaled by `zoom` when zoom changes)
# BASE_FONT_SIZES = (44, 22, 16)
# FONT_L = load_font(BASE_FONT_SIZES[0])
# FONT_M = load_font(BASE_FONT_SIZES[1])
# FONT_S = load_font(BASE_FONT_SIZES[2])

# def update_fonts_for_zoom():
#     """Recreate fonts scaled by current `zoom` so UI text scales with zoom."""
#     global FONT_L, FONT_M, FONT_S
#     try:
#         FONT_L = load_font(max(8, int(BASE_FONT_SIZES[0] * zoom)))
#         FONT_M = load_font(max(8, int(BASE_FONT_SIZES[1] * zoom)))
#         FONT_S = load_font(max(8, int(BASE_FONT_SIZES[2] * zoom)))
#     except Exception:
#         # fallback to defaults
#         FONT_L = load_font(BASE_FONT_SIZES[0])
#         FONT_M = load_font(BASE_FONT_SIZES[1])
#         FONT_S = load_font(BASE_FONT_SIZES[2])

# # ensure fonts reflect initial zoom
# update_fonts_for_zoom()

# def render_clipped(text, font, color, box_x, box_y, box_w, pad=6):
#     """Render text clipped to fit into width box_w at (box_x, box_y).
#     Pads by `pad` pixels from left. If text too long, truncate with ellipsis.
#     """
#     s = str(text)
#     surf = font.render(s, True, color)
#     maxw = box_w - (pad * 2)
#     if surf.get_width() <= maxw:
#         screen.blit(surf, (box_x + pad, box_y + pad//2))
#         return
#     # truncate
#     while surf.get_width() > maxw and len(s) > 0:
#         s = s[:-1]
#         surf = font.render(s + '…', True, color)
#     screen.blit(surf, (box_x + pad, box_y + pad//2))

# def draw_button(rect, text, enabled=True):
#     # Brighter, modern button with subtle shadow and readable text
#     # allow color customization via text prefix like "#RRGGBB" or tuple via enabled param
#     base_color = (70,180,255) if enabled is True else (100,100,100)
#     if isinstance(enabled, tuple):
#         base_color = enabled
#     shadow_color = (20,20,20)
#     text_color = (255,255,255)
#     border_color = (255,255,255)

#     # shadow (simple darker rect offset)
#     sh = rect.move(2,2)
#     pygame.draw.rect(screen, shadow_color, sh, border_radius=10)
#     pygame.draw.rect(screen, base_color, rect, border_radius=10)
#     pygame.draw.rect(screen, border_color, rect, width=2, border_radius=10)
    
#     label = FONT_M.render(text, True, text_color)
#     screen.blit(label, label.get_rect(center=rect.center))

# def play_click():
#     try:
#         snd = pygame.mixer.Sound(CLICK_WAV)
#         snd.play()
#     except: pass

# # ---------- Networking ----------
# class Client:
#     def __init__(self, host, port):
#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.sock.connect((host, port))
#         self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
#         self.recv_thread.start()
#         self.state = {
#             "board":" "*9, "turn":"X", "winner":None, "players":[]
#         }
#         self.chat = []
#         self.mark = "S"
#         self.name = "Player"
#         self.buffer = ""
#         # animations: idx -> start_time
#         self.animations = {}

#     def send(self, obj):
#         try:
#             self.sock.sendall((json.dumps(obj)+"\n").encode(ENC))
#         except: pass

#     def join(self, name):
#         self.name = name
#         self.send({"type":"JOIN","name":name})

#     def move(self, cell):
#         self.send({"type":"MOVE","cell":cell})

#     def chat_send(self, msg):
#         self.send({"type":"CHAT","msg":msg})

#     def reset(self):
#         self.send({"type":"RESET"})

#     def _recv_loop(self):
#         try:
#             while True:
#                 data = self.sock.recv(BUFSIZE)
#                 if not data: break
#                 self.buffer += data.decode(ENC, errors="ignore")
#                 while "\n" in self.buffer:
#                     line, self.buffer = self.buffer.split("\n",1)
#                     if not line.strip(): continue
#                     try:
#                         msg = json.loads(line)
#                     except:
#                         continue
#                     self._handle(msg)
#         except:
#             pass

#     def _handle(self, msg):
#         t = msg.get("type")
#         if t == "STATE":
#             # detect newly placed marks for animation
#             prev = self.state.get("board", " "*9)
#             newb = msg.get("board", " "*9)
#             for i, (pa, nb) in enumerate(zip(prev, newb)):
#                 if pa == " " and nb in ("X","O"):
#                     # start animation
#                     self.animations[i] = time.time()
#             self.state = msg
#         elif t == "ROLE":
#             self.mark = msg.get("mark","S")
#         elif t == "CHAT":
#             self.chat.append(f"{msg.get('from')}: {msg.get('msg')}")
#             self.chat = self.chat[-10:]
#         elif t in ("INFO","ERROR"):
#             self.chat.append(f"[{t}] {msg.get('msg')}")
#             self.chat = self.chat[-10:]

# # ---------- UI State ----------
# client_a = None
# client_b = None
# input_name1 = "Player1"
# input_name2 = "Player2"
# input_chat = ""
# editing_name1 = True
# editing_name2 = False
# editing_chat = False
# active_player = 'A'  # 'A' or 'B' - which local client controls moves/chat

# # NEW: Constants for easier layout management
# SIDEBAR_X = 620
# SIDEBAR_WIDTH = 260
# PANEL_MARGIN = 10 # Space between panels

# # ---------- Board rendering & input helpers ----------
# def get_grid_rects():
#     """Return a list of 1 or 2 pygame.Rect for the game boards depending on split_screen and zoom."""
#     # available area to the left of the sidebar
#     avail_w = SIDEBAR_X - MARGIN
#     # spacing between two boards when split
#     gap = 16
#     if split_screen:
#         # two boards side-by-side
#         max_side = int((avail_w - gap) / 2)
#         side = int(min(GRID_SIZE, max_side) * zoom)
#         y = (HEIGHT - side) // 2
#         left = pygame.Rect(MARGIN, y, side, side)
#         right = pygame.Rect(MARGIN + side + gap, y, side, side)
#         return [left, right]
#     else:
#         side = int(min(GRID_SIZE, avail_w) * zoom)
#         x = MARGIN + max(0, (avail_w - side) // 2)
#         y = (HEIGHT - side) // 2
#         return [pygame.Rect(x, y, side, side)]


# def cell_from_pos(pos):
#     """Map mouse pos -> (grid_index, cell_index) or (None, None) if outside boards."""
#     if pos is None:
#         return None, None
#     grs = get_grid_rects()
#     for gi, gr in enumerate(grs):
#         if gr.collidepoint(pos):
#             cx = pos[0] - gr.x
#             cy = pos[1] - gr.y
#             cell_w = gr.width / 3.0
#             col = int(cx // cell_w)
#             row = int(cy // cell_w)
#             if 0 <= col < 3 and 0 <= row < 3:
#                 return gi, row * 3 + col
#     return None, None


# def draw_board(state, grid_rect, last_hover=None):
#     """Draw a single 3x3 board in grid_rect using state dict with key 'board'."""
#     board = state.get('board', ' ' * 9)
#     # background panel
#     pygame.draw.rect(screen, TILE_BG, grid_rect, border_radius=8)
#     # cell size
#     cell_w = grid_rect.width // 3
#     # draw cell backgrounds and marks
#     for i in range(9):
#         r = i // 3
#         c = i % 3
#         cell_rect = pygame.Rect(grid_rect.x + c * cell_w, grid_rect.y + r * cell_w, cell_w, cell_w)
#         # inner padding for nicer look
#         inner = cell_rect.inflate(-6, -6)
#         pygame.draw.rect(screen, (28,34,50), inner, border_radius=6)
#         mark = board[i] if i < len(board) else ' '
#         if mark and mark != ' ':
#             if mark == 'X':
#                 # draw X
#                 off = int(cell_w * 0.18)
#                 pygame.draw.line(screen, (240,180,80), (inner.x + off, inner.y + off), (inner.right - off, inner.bottom - off), max(2, cell_w//12))
#                 pygame.draw.line(screen, (240,180,80), (inner.right - off, inner.y + off), (inner.x + off, inner.bottom - off), max(2, cell_w//12))
#             else:
#                 # draw O
#                 center = inner.center
#                 radius = int(min(inner.width, inner.height) * 0.36)
#                 pygame.draw.circle(screen, (160,210,255), center, radius, max(2, cell_w//12))
#     # grid lines (subtle)
#     for i in range(1, 3):
#         # vertical
#         x = grid_rect.x + i * cell_w
#         pygame.draw.line(screen, (60,70,90), (x, grid_rect.y + 6), (x, grid_rect.bottom - 6), 3)
#         # horizontal
#         y = grid_rect.y + i * cell_w
#         pygame.draw.line(screen, (60,70,90), (grid_rect.x + 6, y), (grid_rect.right - 6, y), 3)

#     # hover highlight
#     if last_hover is not None:
#         # last_hover is a cell index
#         r = last_hover // 3
#         c = last_hover % 3
#         hrect = pygame.Rect(grid_rect.x + c * cell_w + 4, grid_rect.y + r * cell_w + 4, cell_w - 8, cell_w - 8)
#         s = pygame.Surface((hrect.width, hrect.height), pygame.SRCALPHA)
#         s.fill((255,255,255,30))
#         screen.blit(s, (hrect.x, hrect.y))

# def active_client():
#     return client_a if active_player == 'A' else client_b

# # (Global definitions for buttons are moved inside render_sidebar
# #  and updated globally so the event loop can see them)
# btn_quit = pygame.Rect(0,0,0,0)
# btn_reset = pygame.Rect(0,0,0,0)

# # grid_rect will be computed dynamically to support split-screen and zoom

# def render_sidebar():
#     global btn_quit, btn_reset

#     # Header (clipped so it never overlaps the board area)
#     title_avail_w = SIDEBAR_X - (MARGIN * 1)
#     render_clipped("TicTacToe Online", FONT_L, (255,255,255), MARGIN, 5, title_avail_w)

#     # --- Sidebar Panels (Dynamic Stacking Layout) ---
#     current_y = 20

#     # 1. Status panel
#     status_rect = pygame.Rect(SIDEBAR_X, current_y, SIDEBAR_WIDTH, 120)
#     pygame.draw.rect(screen, (40,100,150), status_rect, border_radius=12)
#     pygame.draw.rect(screen, (255,255,255), status_rect, 2, border_radius=12)

#     a_name = client_a.name if client_a else "-"
#     a_mark = client_a.mark if client_a else "-"
#     b_name = client_b.name if client_b else "-"
#     b_mark = client_b.mark if client_b else "-"
#     mark_text = f"P1: {a_name} [{a_mark}]  P2: {b_name} [{b_mark}]"
#     state = client_a.state if client_a and client_a.state else (client_b.state if client_b and client_b.state else {"turn":"-","winner":None})
#     turn_text = f"Turn: {state.get('turn','-')}"
#     winner = state.get("winner")
#     win_text = "Winner: " + ("-" if not winner else ("Draw" if winner=="D" else winner))

#     render_clipped(mark_text, FONT_S, (255,255,255), status_rect.x, status_rect.y + 8, status_rect.width)
#     render_clipped(turn_text, FONT_S, (255,255,255), status_rect.x, status_rect.y + 34, status_rect.width)
#     render_clipped(win_text, FONT_S, (255,255,255), status_rect.x, status_rect.y + 60, status_rect.width)

#     # show recent connection errors (if any) inside the status card
#     err_y = status_rect.y + 86
#     if connection_errors:
#         for line in connection_errors[-3:]:
#             render_clipped(line, FONT_S, (255,120,120), status_rect.x, err_y, status_rect.width)
#             err_y += 18

#     current_y += status_rect.height + PANEL_MARGIN

#     # 2. Players Box
#     card_h = 90
#     p_rect = pygame.Rect(SIDEBAR_X, current_y, SIDEBAR_WIDTH, card_h)
#     pygame.draw.rect(screen, (40,40,70), p_rect, border_radius=12)
#     pygame.draw.rect(screen, (255,255,255), p_rect, 2, border_radius=12)
#     players_label = FONT_M.render("Players", True, TEXT_COLOR)
#     screen.blit(players_label, (p_rect.x + 10, p_rect.y + 8))

#     card_w = SIDEBAR_WIDTH - 20
#     card_x = SIDEBAR_X + 10
#     card_y = p_rect.y + 34
#     players = state.get("players", [])
#     p1 = players[0] if len(players) > 0 else {"name":"-","mark":"S"}
#     p2 = players[1] if len(players) > 1 else {"name":"-","mark":"S"}

#     def draw_player_card(x, y, info, is_active):
#         card = pygame.Rect(x, y, card_w, 28)
#         bg = (50,60,90) if not is_active else (70,90,140)
#         pygame.draw.rect(screen, bg, card, border_radius=8)
#         pygame.draw.rect(screen, (255,255,255), card, 1, border_radius=8)
#         avc = (card.x + 14, card.y + 14)
#         pygame.draw.circle(screen, (200,200,200), avc, 10)
#         mark = info.get('mark','S')
#         mark_col = (255,90,90) if mark == 'X' else ((90,220,120) if mark == 'O' else (180,180,180))
#         pygame.draw.circle(screen, mark_col, (card.x + 36, card.y + 14), 8)
#         name = info.get('name','-')
#         render_clipped(name, FONT_S, TEXT_COLOR, card.x + 52, card.y + 2, card.width - 56)
#         score = info.get('score', 0)
#         screen.blit(FONT_S.render(str(score), True, TEXT_COLOR), (card.right - 20, card.y + 6))

#     draw_player_card(card_x, card_y, p1, (state.get('turn') == 'X'))
#     draw_player_card(card_x, card_y + 34, p2, (state.get('turn') == 'O'))

#     current_y += p_rect.height + PANEL_MARGIN

#     # Layout planning (bottom-up)
#     bar_h = 40
#     ctrl_h = 40
#     input_area_h = 30 + 5 + 30 + 10 + 30
#     action_y = HEIGHT - PANEL_MARGIN - bar_h
#     control_y = action_y - PANEL_MARGIN - ctrl_h
#     inputs_y = control_y - PANEL_MARGIN - input_area_h

#     min_chat_h = 60
#     chat_top = current_y
#     split_h = 36
#     split_y = inputs_y - split_h - PANEL_MARGIN
#     chat_bottom = max(chat_top + min_chat_h, split_y - PANEL_MARGIN)
#     max_chat_bottom = action_y - (ctrl_h + PANEL_MARGIN)
#     if chat_bottom > max_chat_bottom:
#         chat_bottom = max_chat_bottom
#     chat_h = max(min_chat_h, chat_bottom - chat_top)
#     chat_rect = pygame.Rect(SIDEBAR_X, chat_top, SIDEBAR_WIDTH, chat_h)
#     pygame.draw.rect(screen, (30,30,45), chat_rect, border_radius=12)
#     pygame.draw.rect(screen, (255,255,255), chat_rect, 2, border_radius=12)

#     y = chat_rect.y + 10
#     ac = active_client()
#     chats = ac.chat if ac else []
#     line_h = 20
#     max_lines = max(1, (chat_rect.height - 16) // line_h)
#     for line in chats[-max_lines:]:
#         render_clipped(line, FONT_S, (230,230,230), chat_rect.x, y - 4, chat_rect.width)
#         y += line_h

#     # Split / Zoom controls
#     split_label = "Split: ON" if split_screen else "Split: OFF"
#     small_btn_w = 36
#     spacing = 6
#     split_w = SIDEBAR_WIDTH - (small_btn_w * 2 + spacing * 3)
#     if split_w < 80:
#         split_w = SIDEBAR_WIDTH - (small_btn_w + spacing * 2)
#     split_x = SIDEBAR_X
#     split_rect = pygame.Rect(split_x, split_y, split_w, split_h)
#     zoom_minus = pygame.Rect(split_x + split_w + spacing, split_y, small_btn_w, split_h)
#     zoom_plus = pygame.Rect(zoom_minus.right + spacing, split_y, small_btn_w, split_h)
#     draw_button(split_rect, split_label, enabled=split_screen)
#     draw_button(zoom_minus, "-", enabled=True)
#     draw_button(zoom_plus, "+", enabled=True)

#     # Inputs (positioned using inputs_y)
#     p1_y = inputs_y
#     screen.blit(FONT_S.render("P1 Name:", True, (240,240,240)), (SIDEBAR_X, p1_y + 4))
#     name1_box = pygame.Rect(SIDEBAR_X + 70, p1_y, 120, 30)
#     join1_box = pygame.Rect(name1_box.right + 5, p1_y, 65, 30)

#     p2_y = p1_y + 30 + 5
#     screen.blit(FONT_S.render("P2 Name:", True, (240,240,240)), (SIDEBAR_X, p2_y + 4))
#     name2_box = pygame.Rect(SIDEBAR_X + 70, p2_y, 120, 30)
#     join2_box = pygame.Rect(name2_box.right + 5, p2_y, 65, 30)

#     chat_y = p2_y + 30 + 10
#     screen.blit(FONT_S.render("Chat:", True, (240,240,240)), (SIDEBAR_X, chat_y + 4))
#     chat_box = pygame.Rect(SIDEBAR_X + 70, chat_y, SIDEBAR_WIDTH - 70, 30)

#     pygame.draw.rect(screen, (230,230,230), name1_box, 2, border_radius=6)
#     pygame.draw.rect(screen, (230,230,230), name2_box, 2, border_radius=6)
#     pygame.draw.rect(screen, (230,230,230), chat_box, 2, border_radius=6)

#     draw_button(join1_box, "Join", enabled=(client_a is None))
#     draw_button(join2_box, "Join", enabled=(client_b is None))

#     name1_color = (255,230,120) if editing_name1 else (220,220,220)
#     name2_color = (255,230,120) if editing_name2 else (220,220,220)
#     chat_color = (255,230,120) if editing_chat else (220,220,220)

#     render_clipped(input_name1, FONT_S, name1_color, name1_box.x, name1_box.y, name1_box.width)
#     render_clipped(input_name2, FONT_S, name2_color, name2_box.x, name2_box.y, name2_box.width)
#     if input_chat.strip() == "" and not editing_chat:
#         render_clipped("Type your message...", FONT_S, (180,180,180), chat_box.x, chat_box.y, chat_box.width)
#     else:
#         render_clipped(input_chat, FONT_S, chat_color, chat_box.x, chat_box.y, chat_box.width)

#     # Action bar
#     bar_y = HEIGHT - bar_h - PANEL_MARGIN
#     action_x = SIDEBAR_X
#     bw = (SIDEBAR_WIDTH - (PANEL_MARGIN*3)) // 4
#     btn_join1 = pygame.Rect(action_x, bar_y, bw, bar_h)
#     btn_join2 = pygame.Rect(action_x + (bw + PANEL_MARGIN), bar_y, bw, bar_h)
#     btn_reset = pygame.Rect(action_x + 2*(bw + PANEL_MARGIN), bar_y, bw, bar_h)
#     btn_quit = pygame.Rect(action_x + 3*(bw + PANEL_MARGIN), bar_y, bw, bar_h)

#     ctrl_y = control_y
#     ctrl_w = (SIDEBAR_WIDTH - PANEL_MARGIN) // 2
#     switch1 = pygame.Rect(SIDEBAR_X, ctrl_y, ctrl_w, bar_h)
#     switch2 = pygame.Rect(SIDEBAR_X + ctrl_w + PANEL_MARGIN, ctrl_y, ctrl_w, bar_h)

#     draw_button(btn_join1, "Join P1", enabled=ACCENT)
#     draw_button(btn_join2, "Join P2", enabled=ACCENT)
#     draw_button(btn_reset, "Reset", enabled=(255,200,60))
#     draw_button(btn_quit, "Quit", enabled=(220,60,60))
#     draw_button(switch1, "Control P1", enabled=(ACCENT if active_player=='A' else (100,100,100)))
#     draw_button(switch2, "Control P2", enabled=(ACCENT if active_player=='B' else (100,100,100)))

#     return {
#         'name1_box': name1_box, 'join1_box': join1_box,
#         'name2_box': name2_box, 'join2_box': join2_box,
#         'chat_box': chat_box, 'switch1': switch1, 'switch2': switch2,
#         'split': split_rect, 'zoom_minus': zoom_minus, 'zoom_plus': zoom_plus,
#         'btn_join1': btn_join1, 'btn_join2': btn_join2, 'btn_reset': btn_reset, 'btn_quit': btn_quit
#     }
# # =========================================================================
# # ===== END REFACTORED SIDEBAR FUNCTION =====
# # =========================================================================


# # ---------- Main Loop ----------
# hover_cell = None

# running = True
# while running:
#     mouse_pos = pygame.mouse.get_pos()
#     hover_grid, hover_cell = cell_from_pos(mouse_pos)

#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False

#         elif event.type == pygame.MOUSEBUTTONDOWN:
#             # Render sidebar once to update interactive rects (sets btn_quit/btn_reset)
#             rects = render_sidebar()
#             # grid click handling
#             gi, cell = cell_from_pos(mouse_pos)
#             if gi is not None and cell is not None:
#                 # choose target client depending on split or active selection
#                 if split_screen:
#                     target = client_a if gi == 0 else client_b
#                 else:
#                     target = active_client()
#                 if target and target.state.get("winner") is None and target.mark in ("X","O"):
#                     play_click()
#                     target.move(cell)
#             elif rects.get('btn_reset') and rects['btn_reset'].collidepoint(mouse_pos):
#                 play_click()
#                 # send reset from both clients if present
#                 try:
#                     if client_a: client_a.reset()
#                 except: pass
#                 try:
#                     if client_b: client_b.reset()
#                 except: pass
#             elif rects.get('btn_quit') and rects['btn_quit'].collidepoint(mouse_pos):
#                 running = False
#             else:
#                 ny1 = rects['name1_box']
#                 j1 = rects['join1_box']
#                 ny2 = rects['name2_box']
#                 j2 = rects['join2_box']
#                 cy = rects['chat_box']
#                 sw1 = rects['switch1']
#                 sw2 = rects['switch2']
#                 sp = rects.get('split')
#                 zm = rects.get('zoom_minus')
#                 zp = rects.get('zoom_plus')
#                 btn_join1 = rects.get('btn_join1')
#                 btn_join2 = rects.get('btn_join2')
#                 btn_reset = rects.get('btn_reset')
#                 btn_quit = rects.get('btn_quit')

#                 # Check for input box clicks
#                 editing_name1 = ny1.collidepoint(mouse_pos)
#                 editing_name2 = ny2.collidepoint(mouse_pos)
#                 editing_chat = cy.collidepoint(mouse_pos)

#                 # Check for button clicks
#                 if j1.collidepoint(mouse_pos) and client_a is None:
#                     play_click()
#                     try:
#                         globals()['client_a'] = Client(SERVER_HOST, SERVER_PORT)
#                         client_a.join(input_name1 if input_name1.strip() else 'Player1')
#                     except Exception as e:
#                         err = f"join1 failed: {e}. Ensure server is running (run: python server.py)"
#                         print(err)
#                         add_connection_error(err)
#                 if j2.collidepoint(mouse_pos) and client_b is None:
#                     play_click()
#                     try:
#                         globals()['client_b'] = Client(SERVER_HOST, SERVER_PORT)
#                         client_b.join(input_name2 if input_name2.strip() else 'Player2')
#                     except Exception as e:
#                         err = f"join2 failed: {e}. Ensure server is running (run: python server.py)"
#                         print(err)
#                         add_connection_error(err)
#                 if sw1.collidepoint(mouse_pos):
#                     play_click()
#                     active_player = 'A'
#                 if sw2.collidepoint(mouse_pos):
#                     play_click()
#                     active_player = 'B'
#                 # action bar clicks
#                 if btn_join1.collidepoint(mouse_pos) and client_a is None:
#                     play_click()
#                     try:
#                         globals()['client_a'] = Client(SERVER_HOST, SERVER_PORT)
#                         client_a.join(input_name1 if input_name1.strip() else 'Player1')
#                     except Exception as e:
#                         err = f"join1 failed: {e}. Ensure server is running (run: python server.py)"
#                         print(err)
#                         add_connection_error(err)
#                 if btn_join2.collidepoint(mouse_pos) and client_b is None:
#                     play_click()
#                     try:
#                         globals()['client_b'] = Client(SERVER_HOST, SERVER_PORT)
#                         client_b.join(input_name2 if input_name2.strip() else 'Player2')
#                     except Exception as e:
#                         err = f"join2 failed: {e}. Ensure server is running (run: python server.py)"
#                         print(err)
#                         add_connection_error(err)
#                 if btn_reset.collidepoint(mouse_pos):
#                     play_click()
#                     try:
#                         if client_a: client_a.reset()
#                     except: pass
#                     try:
#                         if client_b: client_b.reset()
#                     except: pass
#                 if btn_quit.collidepoint(mouse_pos):
#                     play_click()
#                     running = False
#                 if sp and sp.collidepoint(mouse_pos):
#                     play_click()
#                     split_screen = not split_screen
#                 if zm and zm.collidepoint(mouse_pos):
#                     play_click()
#                     zoom = max(MIN_ZOOM, zoom - ZOOM_STEP)
#                     update_fonts_for_zoom()
#                 if zp and zp.collidepoint(mouse_pos):
#                     play_click()
#                     zoom = min(MAX_ZOOM, zoom + ZOOM_STEP)
#                     update_fonts_for_zoom()

#         elif event.type == pygame.KEYDOWN:
#             if editing_name1 or editing_name2:
#                 target = '1' if editing_name1 else '2'
#                 if event.key == pygame.K_RETURN:
#                     if editing_name1 and client_a is None:
#                         try:
#                             globals()['client_a'] = Client(SERVER_HOST, SERVER_PORT)
#                             client_a.join(input_name1 if input_name1.strip() else "Player1")
#                         except Exception as e:
#                             err = f"join1 failed: {e}. Ensure server is running (run: python server.py)"
#                             print(err)
#                             add_connection_error(err)
#                         editing_name1 = False
#                     elif editing_name2 and client_b is None:
#                         try:
#                             globals()['client_b'] = Client(SERVER_HOST, SERVER_PORT)
#                             client_b.join(input_name2 if input_name2.strip() else "Player2")
#                         except Exception as e:
#                             err = f"join2 failed: {e}. Ensure server is running (run: python server.py)"
#                             print(err)
#                             add_connection_error(err)
#                         editing_name2 = False
#                 elif event.key == pygame.K_BACKSPACE:
#                     if editing_name1:
#                         input_name1 = input_name1[:-1]
#                     else:
#                         input_name2 = input_name2[:-1]
#                 else:
#                     if event.unicode.isprintable():
#                         if editing_name1 and len(input_name1) < 20:
#                             input_name1 += event.unicode
#                         if editing_name2 and len(input_name2) < 20:
#                             input_name2 += event.unicode
#             elif editing_chat:
#                 if event.key == pygame.K_RETURN:
#                     if input_chat.strip():
#                         ac = active_client()
#                         if ac: ac.chat_send(input_chat.strip())
#                     input_chat = ""
#                     editing_chat = False # Stop editing on Enter
#                 elif event.key == pygame.K_BACKSPACE:
#                     input_chat = input_chat[:-1]
#                 else:
#                     if len(input_chat) < 80 and event.unicode.isprintable():
#                         input_chat += event.unicode
#             else:
#                 # quick hotkeys
#                 if event.key == pygame.K_r:
#                     try:
#                         if client_a: client_a.reset()
#                     except: pass
#                     try:
#                         if client_b: client_b.reset()
#                     except: pass
#                 if event.key == pygame.K_1:
#                     active_player = 'A'
#                 if event.key == pygame.K_2:
#                     active_player = 'B'
#                 if event.key == pygame.K_s:
#                     split_screen = not split_screen
#                 if event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
#                     zoom = max(MIN_ZOOM, zoom - ZOOM_STEP)
#                     update_fonts_for_zoom()
#                 if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
#                     zoom = min(MAX_ZOOM, zoom + ZOOM_STEP)
#                     update_fonts_for_zoom()

#     # Render
#     screen.fill((10,12,20))
#     grid_rects = get_grid_rects()
#     # draw one or two boards
#     for gi, gr in enumerate(grid_rects):
#         # choose which client's state to show
#         if split_screen:
#             st = client_a.state if gi == 0 and client_a else (client_b.state if gi == 1 and client_b else {"board":"         "})
#         else:
#             ac = active_client()
#             st = ac.state if ac else {"board":"         "}
#         last_h = hover_cell if (hover_grid == gi) else None
#         draw_board(st, gr, last_hover=last_h)

#     rects = render_sidebar()

#     # Winner overlay (over first grid)
#     primary_state = client_a.state if client_a else (client_b.state if client_b else {"winner": None})
#     w = primary_state.get("winner")
#     if w is not None:
#         msg = "Draw!" if w == "D" else f"{w} Wins!"
#         main_rect = grid_rects[0]
#         # Draw a semi-opaque rounded banner above the board center to avoid overlapping UI
#         banner_w = int(main_rect.width * 0.9)
#         banner_h = int(FONT_L.get_height() * 1.6)
#         banner_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
#         # slightly dark translucent background
#         banner_surf.fill((10, 12, 20, 180))
#         # render text centered on the banner
#         text_surf = FONT_L.render(msg, True, (255,220,80))
#         tx = (banner_w - text_surf.get_width()) // 2
#         ty = (banner_h - text_surf.get_height()) // 2
#         banner_surf.blit(text_surf, (tx, ty))
#         bx = main_rect.centerx - banner_w // 2
#         # place banner slightly below top of board but not off-screen
#         by = max(10, main_rect.y + 8)
#         screen.blit(banner_surf, (bx, by))

#     pygame.display.flip()
#     clock.tick(60)

# pygame.quit()
# try:
#     if client_a: client_a.sock.close()
# except: pass
# try:
#     if client_b: client_b.sock.close()
# except: pass
import threading
import json
import tkinter as tk
from tkinter import messagebox, simpledialog

class TicTacToeClient:
    """
    Client game Tic-Tac-Toe với GUI đẹp
    """
    
    def __init__(self):
        # --- Các biến trạng thái của Client ---
        self.socket = None              # Đối tượng socket để kết nối với server
        self.my_symbol = None           # Ký hiệu của người chơi này ('X' hoặc 'O')
        self.current_turn = 'X'         # Lượt đi hiện tại của ván game, luôn bắt đầu bằng 'X'
        self.game_started = False       # Cờ hiệu (flag) để kiểm tra game đã bắt đầu chưa, ngăn click sớm
        
        # --- Cửa sổ chính (root window) ---
        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe Game 🎮")
        self.root.geometry("550x850")   # Kích thước cửa sổ [rộng x cao]
        self.root.resizable(False, False) # Không cho phép thay đổi kích thước
        self.root.configure(bg='#0a0e27')
        
        # --- Bảng màu (color palette) ---
        self.colors = {
            'bg': '#0a0e27',
            'primary': '#1e2749',
            'secondary': '#2a3663',
            'accent': '#ff2e63',
            'accent_hover': '#ff4d7d',
            'text': "#ffffff",
            'X': "#00ffc8",
            'O': "#ffbb00",
            'button_hover': '#3d4a7a',
            'win': '#00ff88',
            'lose': '#ff3864'
        }
        
        # --- Khởi tạo giao diện ---
        self.create_widgets()
        
    def create_widgets(self):
        """
        Tạo và sắp xếp tất cả các thành phần giao diện (widgets)
        """
        
        # === KHỐI 1: KẾT NỐI & TIÊU ĐỀ ===
        self.connection_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.connection_frame.pack(pady=15)
        
        # Tiêu đề
        title_label = tk.Label(
            self.connection_frame,
            text="⚡ TIC-TAC-TOE ⚡",
            font=('Arial', 22, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        title_label.pack(pady=7)
        
        # Nút kết nối
        self.connect_button = tk.Button(
            self.connection_frame,
            text="🔌 Kết nối Server",
            font=('Arial', 15, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['text'],
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['text'],
            padx=25,
            pady=10,
            relief=tk.FLAT, 
            cursor='hand2',
            command=self.connect_to_server,
            bd=0
        )
        self.connect_button.pack(pady=8)
        
        # === KHỐI 2: TRẠNG THÁI (STATUS) ===
        status_container = tk.Frame(self.root, bg=self.colors['primary'], padx=15, pady=8)
        status_container.pack(pady=10)
        
        self.status_label = tk.Label(
            status_container,
            text="⚪ Chưa kết nối",
            font=('Arial', 12, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['text']
        )
        self.status_label.pack()
        
        # === KHỐI 3: THÔNG TIN NGƯỜI CHƠI (Bạn là, Lượt) ===
        info_container = tk.Frame(self.root, bg=self.colors['bg'])
        info_container.pack(pady=10)
        
        # Box người chơi
        player_box = tk.Frame(info_container, bg=self.colors['primary'], padx=20, pady=10)
        player_box.pack(side=tk.LEFT, padx=10)
        
        self.player_label = tk.Label(
            player_box,
            text="Bạn là: --",
            font=('Arial', 15, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['text']
        )
        self.player_label.pack()
        
        # Box lượt chơi
        turn_box = tk.Frame(info_container, bg=self.colors['primary'], padx=20, pady=10)
        turn_box.pack(side=tk.LEFT, padx=10)
        
        self.turn_label = tk.Label(
            turn_box,
            text="Lượt: X",
            font=('Arial', 15, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['X']
        )
        self.turn_label.pack()
        
        # === KHỐI 4: BÀN CỜ ===
        board_container = tk.Frame(self.root, bg=self.colors['primary'], padx=15, pady=15)
        board_container.pack(pady=15)
    # Tạo bàn cờ 3x3
    self.buttons = []
    for i in range(3):
        row = []
        for j in range(3):
            button = tk.Button(
                board_container,
                text="",
                font=('Arial', 48, 'bold'),
                width=3,
                height=1,
                bg=self.colors['secondary'],
                fg=self.colors['text'],
                disabledforeground=self.colors['text'],
                activebackground=self.colors['button_hover'],
                relief=tk.FLAT,
                cursor='hand2',
                state=tk.DISABLED, # Ban đầu vô hiệu hóa
                bd=0,
                command=lambda r=i, c=j: self.make_move(r, c)
            )
            button.grid(row=i, column=j, padx=4, pady=4)
            
            button.bind('<Enter>', lambda e, b=button: b.config(bg=self.colors['button_hover']) if b['state'] == 'normal' else None)
            button.bind('<Leave>', lambda e, b=button: b.config(bg=self.colors['secondary']) if b['state'] == 'normal' else None)
            
            row.append(button)
        self.buttons.append(row)
    
    # === KHỐI 5: NÚT ĐIỀU KHIỂN (Chơi tiếp, Thoát) ===
    control_frame = tk.Frame(self.root, bg=self.colors['bg'])
    control_frame.pack(pady=15)
    
    # Nút Chơi tiếp
    self.replay_button = tk.Button(
        control_frame,
        text="🔄 Chơi tiếp", 
        font=('Arial', 14, 'bold'), 
        bg=self.colors['accent'],
        fg=self.colors['text'],
        activebackground=self.colors['accent_hover'],
        padx=20,
        pady=10,
        relief=tk.FLAT,
        cursor='hand2',
        state=tk.DISABLED,
        bd=0,
        command=self.request_replay
    )
    self.replay_button.pack(side=tk.LEFT, padx=5)
    
    # Nút Thoát
    self.exit_button = tk.Button(
        control_frame,
        text="❌ Thoát",
        font=('Arial', 14, 'bold'),
        bg=self.colors['secondary'], 
        fg=self.colors['text'],
        activebackground=self.colors['button_hover'],
        padx=20,
        pady=10,
        relief=tk.FLAT,
        cursor='hand2',
        state=tk.DISABLED, # Sẽ được bật khi game over
        bd=0,
        command=self.exit_game
    )
    self.exit_button.pack(side=tk.LEFT, padx=5)
    
def connect_to_server(self):
    """
    Hiển thị popup hỏi IP/Port và thực hiện kết nối.
    """
    # Hiển thị hộp thoại popup để hỏi IP
    host = simpledialog.askstring(
        "Kết nối Server",
        "Nhập địa chỉ IP Server:",
        initialvalue="127.0.0.1"
    )
    if not host: return # Người dùng bấm Cancel

    # Hiển thị hộp thoại popup để hỏi Port
    port = simpledialog.askinteger(
        "Kết nối Server",
        "Nhập Port:",
        initialvalue=5555,
        minvalue=1,
        maxvalue=65535
    )
    if not port: return # Người dùng bấm Cancel
    
    try:
        # Tạo socket và kết nối
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        
        # Cập nhật GUI
        self.status_label.config(text=f"✅ Đã kết nối đến {host}:{port}")
        self.connect_button.config(state=tk.DISABLED) # Vô hiệu hóa nút "Kết nối"
        
    
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        # daemon=True nghĩa là luồng này sẽ tự động tắt khi chương trình chính (GUI) tắt
        receive_thread.start()
        
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể kết nối đến server:\n{e}")

def receive_messages(self):
    """
    Chạy trong luồng riêng, liên tục lắng nghe tin nhắn từ server.
    """
    buffer = "" # Bộ đệm để xử lý các tin nhắn JSON có thể bị ngắt quãng
    try:
        while True:
            # Nhận dữ liệu
            chunk = self.socket.recv(1024).decode('utf-8')
            if not chunk:
                # Nếu chunk rỗng, server đã ngắt kết nối
                break
            
            buffer += chunk
            
            # Server gửi các tin nhắn JSON kết thúc bằng '\n'
            # Xử lý trường hợp nhận được nhiều tin nhắn cùng lúc
            while '\n' in buffer:
                # Tách tin nhắn đầu tiên ra khỏi buffer
                message, buffer = buffer.split('\n', 1)
                try:
                    data = json.loads(message)
                    # Gửi dữ liệu an toàn về luồng chính của GUI để xử lý
                    self.handle_server_message(data)
                except json.JSONDecodeError:
                    # Bỏ qua nếu nhận phải tin nhắn rác không phải JSON
                    print(f"Lỗi JSON: Bỏ qua tin nhắn '{message}'")
                    
    except Exception as e:
        # Xảy ra khi server sập hoặc mất mạng
        print(f"❌ Lỗi khi nhận tin nhắn: {e}")
    finally:
        # Dọn dẹp khi mất kết nối
        if self.socket:
            self.socket.close()
        # Cập nhật GUI từ luồng chính
        self.root.after(0, lambda: self.status_label.config(text="❌ Mất kết nối"))

def handle_server_message(self, data):
    """
    Phân loại và xử lý tin nhắn JSON từ server.
    Chạy trên LUỒNG CHÍNH (thông qua self.root.after).
    """
    # Dùng .get() để tránh lỗi nếu 'type' không tồn tại
    msg_type = data.get('type') 
    
    
    if msg_type == 'WAITING':
        # Server báo "đang chờ đối thủ"
        self.root.after(0, lambda: self.status_label.config(text="⏳ " + data['message']))
    
    elif msg_type == 'START':
        # Server báo "Game bắt đầu", gán ký hiệu (X/O)
        self.my_symbol = data['symbol']
        self.game_started = True
        self.root.after(0, self.start_game)
    
    elif msg_type == 'MOVE_UPDATE':
        # Server cập nhật một nước đi mới
        self.root.after(0, lambda: self.update_board(data))
    
    elif msg_type == 'GAME_OVER':
        # Server báo "Game kết thúc"
        self.root.after(0, lambda: self.show_game_over(data))
    
    elif msg_type == 'INVALID_MOVE':
        # Server báo "Nước đi không hợp lệ"
        self.root.after(0, lambda: messagebox.showwarning("Cảnh báo", data['message']))
    
    elif msg_type == 'OPPONENT_DISCONNECTED':
        # Server báo "Đối thủ thoát"
        self.root.after(0, lambda: messagebox.showinfo("Thông báo", data['message']))
        # Tự động reset game về sảnh chờ
        self.root.after(0, self.reset_for_new_game) 
    