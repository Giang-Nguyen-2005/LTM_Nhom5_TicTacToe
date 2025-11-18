# client.py
import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox

class TicTacToeClient:
    def __init__(self):
        self.socket = None
        self.my_symbol = None
        self.current_turn = 'X'
        self.game_started = False
        self.board_canvas = None
        self.win_line_id = None
        self.cell_size = 100
        self.margin = 8
        self._user_requested_new_match = False
        
        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe Game")
        self.root.geometry("450x650")
        self.root.resizable(False, False)
        self.root.configure(bg='#0a0e27')
        
        self.colors = {
            'bg': '#0a0e27',
            'primary': '#1e2749',
            'secondary': '#2a3663',
            'accent': '#ff2e63',
            'accent_hover': '#ff4d7d',
            'text': "#ffffff",
            'X': "#00ff7b",
            'O': "#ffbb00",
            'button_hover': '#3d4a7a',
            'win': "#61ff96",
            'lose': "#ff7272"
        }
        
        self.create_widgets()
        
    def create_widgets(self):
        # === KHỐI 1: TIÊU ĐỀ & KẾT NỐI ===
        conn_frame = tk.Frame(self.root, bg=self.colors['bg'])
        conn_frame.pack(pady=8)
        
        tk.Label(conn_frame, text="TIC-TAC-TOE", font=('Arial', 18, 'bold'),
                 bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=(0, 5))
        
        # Nhập IP & Port
        input_frame = tk.Frame(conn_frame, bg=self.colors['bg'])
        input_frame.pack(pady=5)
        
        tk.Label(input_frame, text="IP:", font=('Arial', 10), bg=self.colors['bg'], fg=self.colors['text']).grid(row=0, column=0, padx=3)
        self.ip_entry = tk.Entry(input_frame, font=('Arial', 10), width=12, justify='center')
        self.ip_entry.grid(row=0, column=1, padx=3)
        self.ip_entry.insert(0, "127.0.0.1")
        
        tk.Label(input_frame, text="Port:", font=('Arial', 10), bg=self.colors['bg'], fg=self.colors['text']).grid(row=0, column=2, padx=3)
        self.port_entry = tk.Entry(input_frame, font=('Arial', 10), width=6, justify='center')
        self.port_entry.grid(row=0, column=3, padx=3)
        self.port_entry.insert(0, "5555")
        
        self.connect_button = tk.Button(
            conn_frame, text="Kết nối", font=('Arial', 12, 'bold'),
            bg=self.colors['accent'], fg=self.colors['text'],
            activebackground=self.colors['accent_hover'], relief=tk.FLAT,
            cursor='hand2', command=self.connect_to_server, bd=0, padx=20, pady=6
        )
        self.connect_button.pack(pady=5)
        
        # === TRẠNG THÁI & KẾT QUẢ (GỘP CHUNG) ===
        status_frame = tk.Frame(self.root, bg=self.colors['primary'], padx=10, pady=6)
        status_frame.pack(pady=6, fill=tk.X)
        self.status_label = tk.Label(status_frame, text="Chưa kết nối", font=('Arial', 11, 'bold'),
                                     bg=self.colors['primary'], fg=self.colors['text'])
        self.status_label.pack()
        
        # Kết quả hiển thị ngay trong status_label, chỉ tạo result_label để update màu
        self.result_label = tk.Label(status_frame, text="", font=('Arial', 14, 'bold'),
                                     bg=self.colors['primary'], fg=self.colors['text'])
        self.result_label.pack()
        self.result_label.pack_forget()  # Ẩn ban đầu, chỉ hiện khi có kết quả
        
        # === THÔNG TIN NGƯỜI CHƠI (COMPACT) ===
        info_frame = tk.Frame(self.root, bg=self.colors['bg'])
        info_frame.pack(pady=6)
        
        pbox = tk.Frame(info_frame, bg=self.colors['primary'], padx=12, pady=6)
        pbox.pack(side=tk.LEFT, padx=5)
        self.player_label = tk.Label(pbox, text="Bạn: --", font=('Arial', 11, 'bold'),
                                     bg=self.colors['primary'], fg=self.colors['text'])
        self.player_label.pack()
        
        tbox = tk.Frame(info_frame, bg=self.colors['primary'], padx=12, pady=6)
        tbox.pack(side=tk.LEFT, padx=5)
        self.turn_label = tk.Label(tbox, text="Lượt: X", font=('Arial', 11, 'bold'),
                                   bg=self.colors['primary'], fg=self.colors['X'])
        self.turn_label.pack()
        
        # === KHUNG LỰA CHỌN SAU KHI KẾT THÚC (ĐẶT TRƯỚC BÀN CỜ) ===
        self.choice_frame = tk.Frame(self.root, bg=self.colors['primary'], padx=15, pady=8)
        self.choice_frame.pack(pady=6, fill=tk.X)
        self.choice_frame.pack_forget()  # Ẩn ban đầu
        
        choice_buttons_frame = tk.Frame(self.choice_frame, bg=self.colors['primary'])
        choice_buttons_frame.pack()
        
        self.replay_button = tk.Button(choice_buttons_frame, text="Ghép lại", font=('Arial', 11, 'bold'),
                                       bg=self.colors['accent'], fg=self.colors['text'],
                                       activebackground=self.colors['accent_hover'], relief=tk.FLAT,
                                       cursor='hand2', state=tk.DISABLED, bd=0, padx=18, pady=6,
                                       command=self.request_replay)
        self.replay_button.pack(side=tk.LEFT, padx=6)

        self.new_button = tk.Button(choice_buttons_frame, text="Chơi mới", font=('Arial', 11, 'bold'),
                                    bg=self.colors['secondary'], fg=self.colors['text'],
                                    activebackground=self.colors['button_hover'], relief=tk.FLAT,
                                    cursor='hand2', state=tk.DISABLED, bd=0, padx=18, pady=6,
                                    command=self.request_new_match)
        self.new_button.pack(side=tk.LEFT, padx=6)
        
        # === BÀN CỜ ===
        canvas_size = self.cell_size * 3 + self.margin * 2
        self.board_canvas = tk.Canvas(self.root, width=canvas_size, height=canvas_size,
                                      bg=self.colors['primary'], highlightthickness=0)
        self.board_canvas.pack(pady=8)

        # Draw grid and use canvas items for symbols so win-line can be on top
        self.cell_texts = [[None for _ in range(3)] for _ in range(3)]
        self.cell_values = [[None for _ in range(3)] for _ in range(3)]
        # draw background cells with tags for layering
        for i in range(3):
            for j in range(3):
                x0 = self.margin + j * self.cell_size
                y0 = self.margin + i * self.cell_size
                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size
                self.board_canvas.create_rectangle(x0, y0, x1, y1, fill=self.colors['secondary'], outline=self.colors['primary'], width=2, tags=('cell_bg', f'cell_{i}_{j}'))
        # draw grid lines (optional)
        for i in range(1, 3):
            pos = self.margin + i * self.cell_size
            self.board_canvas.create_line(self.margin, pos, self.margin + 3*self.cell_size, pos, fill=self.colors['primary'], width=3, tags=('cell_bg',))
            self.board_canvas.create_line(pos, self.margin, pos, self.margin + 3*self.cell_size, fill=self.colors['primary'], width=3, tags=('cell_bg',))

        # bind click on canvas
        self.board_canvas.bind('<Button-1>', self._on_canvas_click)
        
        # Note: exit button removed per user request (no separate quit control)
    
    def connect_to_server(self):
        host = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        
        if not host:
            messagebox.showerror("Lỗi", "Vui lòng nhập IP!")
            return
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                raise ValueError
        except:
            messagebox.showerror("Lỗi", "Port phải từ 1 đến 65535!")
            return
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.status_label.config(text=f"Đã kết nối {host}:{port}")
            self.connect_button.config(state=tk.DISABLED)
            self.ip_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)
            
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể kết nối:\n{e}")
    
    def receive_messages(self):
        buffer = ""
        try:
            while True:
                chunk = self.socket.recv(1024).decode('utf-8')
                if not chunk: break
                buffer += chunk
                while '\n' in buffer:
                    msg, buffer = buffer.split('\n', 1)
                    try:
                        data = json.loads(msg)
                        self.root.after(0, lambda d=data: self.handle_server_message(d))
                    except: pass
        except: pass
        finally:
            if self.socket:
                self.socket.close()
            self.root.after(0, lambda: self.status_label.config(text="Mất kết nối"))
    
    def handle_server_message(self, data):
        t = data.get('type')
        if t == 'WAITING':
            self.status_label.config(text="Đang chờ đối thủ...")
        elif t == 'START':
            self.my_symbol = data['symbol']
            self.game_started = True
            self.root.after(0, self.start_game)
            # Ẩn choice_frame khi bắt đầu game mới
            self.root.after(0, lambda: self.choice_frame.pack_forget())
        elif t == 'REPLAY_REQUEST':
            # Server asks whether to replay; show in-window options (Ghép lại / Chơi mới)
            self.root.after(0, lambda: self._show_replay_options())
        elif t == 'OPPONENT_DECLINED':
            # Only show opponent_declined if THIS player did NOT initiate new match
            if not self._user_requested_new_match:
                # Opponent declined rematch (or no rematch possible).
                # Show an in-window notification and allow the player to choose 'Chơi mới'.
                msg = data.get('message', 'Đối thủ đã từ chối chơi lại.')
                self.status_label.config(text=msg, fg=self.colors['lose'])
                # Show the choice frame so player can pick 'Chơi mới'
                self.choice_frame.pack(pady=6, fill=tk.X, before=self.board_canvas)
                # Disable rematch button, enable new-match button
                self.replay_button.config(state=tk.DISABLED)
                self.new_button.config(state=tk.NORMAL)
                # Also show a small result label to inform the user
                self.result_label.config(text=msg, fg=self.colors['lose'])
                self.result_label.pack()
            # If user initiated new match, ignore this message (they're already reconnecting)
            self._user_requested_new_match = False
        elif t == 'MOVE_UPDATE':
            self.root.after(0, lambda: self.update_board(data))
        elif t == 'GAME_OVER':
            self.root.after(0, lambda: self.show_game_over(data))
        elif t == 'INVALID_MOVE':
            messagebox.showwarning("Lỗi", data['message'])
        elif t == 'OPPONENT_DISCONNECTED':
            messagebox.showinfo("Thông báo", data['message'])
            self.root.after(0, self.reset_for_new_game)
    
    def start_game(self):
        self.status_label.config(text="Trận đấu bắt đầu!")
        self.player_label.config(text=f"Bạn: {self.my_symbol}", fg=self.colors[self.my_symbol])
        self.result_label.pack_forget()  # Ẩn result_label khi bắt đầu game mới
        self._user_requested_new_match = False
        # clear board visuals and enable buttons
        self.clear_win_line()
        for i in range(3):
            for j in range(3):
                # clear canvas cell values and texts
                self.cell_values[i][j] = None
                if self.cell_texts[i][j]:
                    try: self.board_canvas.delete(self.cell_texts[i][j])
                    except: pass
                    self.cell_texts[i][j] = None
                # visually reset cell background
                rect_tag = f'cell_{i}_{j}'
                try:
                    self.board_canvas.itemconfig(rect_tag, fill=self.colors['secondary'])
                except: pass
        # Reset layering after clearing
        self.board_canvas.tag_lower('cell_bg')
        if self.win_line_id:
            self.board_canvas.tag_raise('win_line')
        # Ẩn khung lựa chọn khi bắt đầu game mới
        self.choice_frame.pack_forget()
        self.replay_button.config(state=tk.DISABLED)
        self.new_button.config(state=tk.DISABLED)
        self.update_turn('X')
    
    def make_move(self, row, col):
        if not self.game_started or self.current_turn != self.my_symbol:
            return
        if self.cell_values[row][col] is not None:
            return
        self.send_message({'type': 'MOVE', 'row': row, 'col': col})
    
    def update_board(self, data):
        r, c, s = data['row'], data['col'], data['symbol']
        # draw symbol on canvas cell
        if self.cell_texts[r][c]:
            try: self.board_canvas.delete(self.cell_texts[r][c])
            except: pass
            self.cell_texts[r][c] = None
        x = self.margin + c * self.cell_size + self.cell_size / 2
        y = self.margin + r * self.cell_size + self.cell_size / 2
        txt = self.board_canvas.create_text(x, y, text=s, font=('Arial', 42, 'bold'), fill=self.colors[s], tags=('symbol',))
        self.cell_texts[r][c] = txt
        self.cell_values[r][c] = s
        # Ensure symbols are above background but below win line
        self.board_canvas.tag_raise('symbol')
        # If win line exists, ensure it stays on top
        if self.win_line_id:
            try:
                self.board_canvas.tag_raise('win_line')
            except: pass
        self.update_turn('O' if s == 'X' else 'X')
    
    def update_turn(self, turn):
        self.current_turn = turn
        self.turn_label.config(text=f"Lượt: {turn}", fg=self.colors[turn])
        self.status_label.config(text="Đến lượt bạn!" if turn == self.my_symbol else "Đang chờ đối thủ...")
    
    def show_game_over(self, data):
        result = data['result']
        # disable further clicks
        self.game_started = False
        # Draw win-line if provided
        win_line = data.get('win_line')
        if result == 'WIN':
            self.result_label.config(text="BẠN THẮNG!", fg=self.colors['win'])
            self.status_label.config(text="Chúc mừng!", fg=self.colors['win'])
            self.result_label.pack()
            if win_line:
                self.draw_win_line(win_line, color=self.colors['win'])
        elif result == 'LOSE':
            self.result_label.config(text="BẠN THUA!", fg=self.colors['lose'])
            self.status_label.config(text="Rất tiếc!", fg=self.colors['lose'])
            self.result_label.pack()
            if win_line:
                # show opponent's winning line in lose color
                self.draw_win_line(win_line, color=self.colors['lose'])
        else:
            self.result_label.config(text="HÒA!", fg=self.colors['O'])
            self.status_label.config(text="Trận đấu hòa!", fg=self.colors['O'])
            self.result_label.pack()
        # Hiển thị khung lựa chọn trong cửa sổ game (phía trên bàn cờ)
        self.choice_frame.pack(pady=6, fill=tk.X, before=self.board_canvas)
        self.replay_button.config(state=tk.NORMAL)
        self.new_button.config(state=tk.NORMAL)
    
    def request_replay(self):
        """Gửi yêu cầu ghép lại với cùng đối thủ"""
        if not self.socket:
            messagebox.showerror("Lỗi", "Chưa kết nối đến server!")
            return
        try:
            # Gửi yêu cầu chơi lại (accept=True)
            self.send_message({'type': 'REPLAY', 'accept': True})
            # Disable buttons để tránh click nhiều lần
            self.replay_button.config(state=tk.DISABLED)
            self.new_button.config(state=tk.DISABLED)
            self.status_label.config(text="Đã gửi yêu cầu ghép lại. Đang chờ đối thủ...", fg=self.colors['text'])
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể gửi yêu cầu chơi lại: {e}")

    def request_new_match(self):
        """Gửi yêu cầu chơi mới (không ghép lại với đối thủ cũ)"""
        # Mark that this player initiated new match (so don't show OPPONENT_DECLINED)
        self._user_requested_new_match = True
        
        # Disable buttons ngay lập tức
        self.replay_button.config(state=tk.DISABLED)
        self.new_button.config(state=tk.DISABLED)
        
        # Gửi thông báo từ chối chơi lại (nếu đang trong trạng thái replay)
        if self.socket:
            try:
                self.send_message({'type': 'REPLAY', 'accept': False})
            except: pass
        
        # Đóng kết nối hiện tại
        old_socket = self.socket
        self.socket = None
        
        # Reset UI
        self.reset_for_new_game()
        
        # Đóng socket cũ (sau khi reset UI)
        if old_socket:
            try:
                old_socket.close()
            except: pass
        
        # Tự động kết nối lại để tìm đối thủ mới
        self.status_label.config(text="Tìm đối thủ mới...", fg=self.colors['text'])
        # Kết nối lại với IP/Port hiện tại
        try:
            host = self.ip_entry.get().strip()
            port_str = self.port_entry.get().strip()
            if host and port_str:
                port = int(port_str)
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((host, port))
                self.status_label.config(text=f"Đã kết nối {host}:{port}")
                self.connect_button.config(state=tk.DISABLED)
                self.ip_entry.config(state=tk.DISABLED)
                self.port_entry.config(state=tk.DISABLED)
                threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            self.status_label.config(text="Không thể kết nối lại. Vui lòng kết nối thủ công.", fg=self.colors['lose'])
            self.connect_button.config(state=tk.NORMAL)
            self.ip_entry.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.NORMAL)
    
    def exit_game(self):
        if messagebox.askyesno("Thoát", "Thoát game?"):
            # Send DISCONNECT to server if connected
            if self.socket:
                try:
                    self.send_message({'type': 'DISCONNECT'})
                except: pass
            # Destroy the window
            try:
                self.root.destroy()
            except: pass
    
    def reset_for_new_game(self):
        self.game_started = False
        self.my_symbol = None
        self.current_turn = 'X'
        self._user_requested_new_match = False
        
        for i in range(3):
            for j in range(3):
                self.cell_values[i][j] = None
                if self.cell_texts[i][j]:
                    try: self.board_canvas.delete(self.cell_texts[i][j])
                    except: pass
                    self.cell_texts[i][j] = None
                rect_tag = f'cell_{i}_{j}'
                try:
                    self.board_canvas.itemconfig(rect_tag, fill=self.colors['secondary'])
                except: pass

        # clear win-line overlay
        self.clear_win_line()
        
        self.status_label.config(text="Chưa kết nối", fg=self.colors['text'])
        self.player_label.config(text="Bạn: --", fg=self.colors['text'])
        self.turn_label.config(text="Lượt: X", fg=self.colors['X'])
        self.result_label.config(text="")
        self.result_label.pack_forget()  # Ẩn result_label khi reset
        
        self.connect_button.config(state=tk.NORMAL)
        self.ip_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        self.choice_frame.pack_forget()  # Ẩn khung lựa chọn
        self.replay_button.config(state=tk.DISABLED)
        self.new_button.config(state=tk.DISABLED)
        
        if self.socket:
            try: self.socket.close()
            except: pass
        self.socket = None
    
    def send_message(self, data):
        try:
            self.socket.sendall((json.dumps(data) + '\n').encode('utf-8'))
        except: pass

    def _on_canvas_click(self, event):
        """Handle clicks on the canvas and translate to board cell coordinates."""
        if not self.game_started:
            return
        x, y = event.x, event.y
        # compute column and row
        col = int((x - self.margin) // self.cell_size)
        row = int((y - self.margin) // self.cell_size)
        if row < 0 or row > 2 or col < 0 or col > 2:
            return
        # attempt to make move (no need for extra bounds check)
        try:
            self.make_move(row, col)
        except: pass

    def _show_replay_options(self):
        """Enable in-window replay options for rematch or new match."""
        # Hiển thị khung lựa chọn phía trên bàn cờ
        self.choice_frame.pack(pady=6, fill=tk.X, before=self.board_canvas)
        self.replay_button.config(state=tk.NORMAL)
        self.new_button.config(state=tk.NORMAL)

    def draw_win_line(self, win_line, color=None):
        """Draw a line connecting the winning cells. `win_line` is a list of [row,col]."""
        if color is None:
            color = self.colors['win']
        if not win_line or not self.board_canvas:
            return
        # clear previous
        self.clear_win_line()
        first = win_line[0]
        last = win_line[-1]
        x1 = self.margin + first[1] * self.cell_size + self.cell_size / 2
        y1 = self.margin + first[0] * self.cell_size + self.cell_size / 2
        x2 = self.margin + last[1] * self.cell_size + self.cell_size / 2
        y2 = self.margin + last[0] * self.cell_size + self.cell_size / 2
        # Vẽ shadow line để tạo hiệu ứng nổi bật
        try:
            # Shadow line (màu đen mờ phía sau)
            shadow_id = self.board_canvas.create_line(x1+1, y1+1, x2+1, y2+1, fill='#000000', width=9, capstyle='round', tags=('win_line',))
            # Main line (màu chính, đẹp hơn)
            self.win_line_id = self.board_canvas.create_line(x1, y1, x2, y2, fill=color, width=8, capstyle='round', tags=('win_line',))
            # Đảm bảo win line luôn ở trên cùng
            self.board_canvas.tag_raise('win_line')
            # Raise win_line above all other tags
            for item in self.board_canvas.find_all():
                try:
                    tags = self.board_canvas.gettags(item)
                    if 'win_line' not in tags:
                        self.board_canvas.tag_lower(item, 'win_line')
                except: pass
        except Exception as e:
            self.win_line_id = None

    def clear_win_line(self):
        try:
            if getattr(self, 'board_canvas', None):
                # Xóa tất cả items có tag 'win_line'
                self.board_canvas.delete('win_line')
        except: pass
        self.win_line_id = None
    
    def run(self):
        self.root.mainloop()
        if self.socket:
            try: self.send_message({'type': 'DISCONNECT'})
            except: pass

if __name__ == "__main__":
    client = TicTacToeClient()
    client.run()