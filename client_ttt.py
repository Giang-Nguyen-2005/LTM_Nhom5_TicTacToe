import threading
import socket
import json
import tkinter as tk
from tkinter import messagebox, simpledialog

class TicTacToeClient:
    """
    Client game Tic-Tac-Toe với GUI đẹp
    """
    
    def __init__(self):
        self.socket = None
        self.my_symbol = None
        self.current_turn = 'X'
        self.game_started = False

        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe Game 🎮")
        self.root.geometry("550x850")
        self.root.resizable(False, False)
        self.root.configure(bg='#0a0e27')
        
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

        self.create_widgets()
        
    def create_widgets(self):

        # === KHỐI 1: KẾT NỐI ===
        self.connection_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.connection_frame.pack(pady=15)

        title_label = tk.Label(
            self.connection_frame,
            text="⚡ TIC-TAC-TOE ⚡",
            font=('Arial', 22, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        title_label.pack(pady=7)

        self.connect_button = tk.Button(
            self.connection_frame,
            text="🔌 Kết nối Server",
            font=('Arial', 15, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['text'],
            activebackground=self.colors['accent_hover'],
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.connect_to_server
        )
        self.connect_button.pack(pady=8)

        # === KHỐI 2: TRẠNG THÁI ===
        status_container = tk.Frame(self.root, bg=self.colors['primary'], padx=15, pady=10)
        status_container.pack(pady=10)

        self.status_label = tk.Label(
            status_container,
            text="⚪ Chưa kết nối",
            font=('Arial', 12, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['text']
        )
        self.status_label.pack()

        # === KHỐI 3: THÔNG TIN NGƯỜI CHƠI ===
        info_container = tk.Frame(self.root, bg=self.colors['bg'])
        info_container.pack(pady=10)

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

        # === KHỐI 4: BÀN CỜ 3x3 ===
        board_container = tk.Frame(self.root, bg=self.colors['primary'], padx=15, pady=15)
        board_container.pack(pady=15)

        self.buttons = []
        for i in range(3):
            row = []
            for j in range(3):
                btn = tk.Button(
                    board_container,
                    text="",
                    font=('Arial', 48, 'bold'),
                    width=3, height=1,
                    bg=self.colors['secondary'],
                    fg=self.colors['text'],
                    disabledforeground=self.colors['text'],
                    relief=tk.FLAT,
                    state=tk.DISABLED,
                    cursor='hand2',
                    command=lambda r=i, c=j: self.make_move(r, c)
                )
                btn.grid(row=i, column=j, padx=4, pady=4)
                row.append(btn)
            self.buttons.append(row)

        # === KHỐI 5: NÚT ĐIỀU KHIỂN ===
        control_frame = tk.Frame(self.root, bg=self.colors['bg'])
        control_frame.pack(pady=15)

        self.replay_button = tk.Button(
            control_frame,
            text="🔄 Chơi tiếp",
            font=('Arial', 14, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['text'],
            padx=20, pady=10,
            relief=tk.FLAT,
            state=tk.DISABLED,
            command=self.request_replay
        )
        self.replay_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = tk.Button(
            control_frame,
            text="❌ Thoát",
            font=('Arial', 14, 'bold'),
            bg=self.colors['secondary'],
            fg=self.colors['text'],
            padx=20, pady=10,
            state=tk.DISABLED,
            relief=tk.FLAT,
            command=self.exit_game
        )
        self.exit_button.pack(side=tk.LEFT, padx=5)

    # ================== SOCKET & NETWORK ===================
    def connect_to_server(self):
        host = simpledialog.askstring("Kết nối Server", "Nhập IP:", initialvalue="127.0.0.1")
        if not host: return
        port = simpledialog.askinteger("Kết nối Server", "Nhập Port:", initialvalue=5555)
        if not port: return
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))

            self.status_label.config(text=f"✅ Đã kết nối {host}:{port}")
            self.connect_button.config(state=tk.DISABLED)

            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể kết nối:\n{e}")

    def receive_messages(self):
        buffer = ""
        try:
            while True:
                chunk = self.socket.recv(1024).decode()
                if not chunk:
                    break
                buffer += chunk

                while '\n' in buffer:
                    msg, buffer = buffer.split('\n', 1)
                    try:
                        data = json.loads(msg)
                        self.root.after(0, lambda d=data: self.handle_server_message(d))
                    except:
                        pass
        except:
            pass
        finally:
            if self.socket:
                self.socket.close()
            self.root.after(0, lambda: self.status_label.config(text="❌ Mất kết nối"))

    def send_message(self, data):
        try:
            self.socket.sendall((json.dumps(data) + "\n").encode())
        except:
            pass

    # ================== GAME LOGIC ===================
    def handle_server_message(self, data):
        t = data.get("type")

        if t == "WAITING":
            self.status_label.config(text="⏳ " + data["message"])

        elif t == "START":
            self.my_symbol = data["symbol"]
            self.game_started = True
            self.start_game()

        elif t == "MOVE_UPDATE":
            self.update_board(data)

        elif t == "GAME_OVER":
            self.show_game_over(data)

    def start_game(self):
        self.status_label.config(text="🎮 Trận đấu bắt đầu!")
        self.player_label.config(text=f"Bạn là: {self.my_symbol}", fg=self.colors[self.my_symbol])

        for i in range(3):
            for j in range(3):
                if self.buttons[i][j]["text"] == "":
                    self.buttons[i][j].config(state=tk.NORMAL)

        self.update_turn("X")

    def make_move(self, r, c):
        if not self.game_started: return
        if self.current_turn != self.my_symbol:
            messagebox.showwarning("Cảnh báo", "Chưa đến lượt bạn!")
            return
        if self.buttons[r][c]["text"] != "":
            return

        self.send_message({"type": "MOVE", "row": r, "col": c})

    def update_board(self, data):
        r = data["row"]
        c = data["col"]
        s = data["symbol"]

        self.buttons[r][c].config(text=s, fg=self.colors[s], state=tk.DISABLED)
        self.update_turn("O" if s == "X" else "X")

    def update_turn(self, turn):
        self.current_turn = turn
        self.turn_label.config(text=f"Lượt: {turn}", fg=self.colors[turn])

        if turn == self.my_symbol:
            self.status_label.config(text="🎯 Đến lượt bạn!")
        else:
            self.status_label.config(text="⏳ Đang chờ đối thủ...")

    def show_game_over(self, data):
        result = data["result"]

        for row in self.buttons:
            for b in row:
                b.config(state=tk.DISABLED)

        if result == "WIN":
            self.status_label.config(text="🎉 Bạn thắng!", fg=self.colors["win"])
            messagebox.showinfo("Kết quả", "Bạn thắng!")
        elif result == "LOSE":
            self.status_label.config(text="😢 Bạn thua!", fg=self.colors["lose"])
            messagebox.showinfo("Kết quả", "Bạn thua!")
        else:
            self.status_label.config(text="🤝 Hòa!", fg=self.colors["O"])
            messagebox.showinfo("Kết quả", "Hòa!")

        self.replay_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.NORMAL)

    # ================== CONTROL BUTTONS ===================
    def request_replay(self):
        if messagebox.askyesno("Chơi tiếp", "Tìm trận mới?"):
            self.reset_for_new_game()
            self.connect_to_server()

    def exit_game(self):
        if messagebox.askyesno("Thoát", "Bạn chắc chắn muốn thoát?"):
            self.root.destroy()

    def reset_for_new_game(self):
        self.game_started = False
        self.my_symbol = None
        self.current_turn = 'X'

        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(
                    text="",
                    state=tk.DISABLED,
                    bg=self.colors['secondary'],
                    fg=self.colors['text']
                )

        self.status_label.config(text="⚪ Chưa kết nối", fg=self.colors['text'])
        self.player_label.config(text="Bạn là: --", fg=self.colors['text'])
        self.turn_label.config(text="Lượt: X", fg=self.colors['X'])

        self.connect_button.config(state=tk.NORMAL)
        self.replay_button.config(state=tk.DISABLED)
        self.exit_button.config(state=tk.DISABLED)

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

    # ================== RUN ===================
    def run(self):
        self.root.mainloop()
        if self.socket:
            try:
                self.send_message({"type": "DISCONNECT"})
                self.socket.close()
            except:
                pass


if __name__ == "__main__":
    TicTacToeClient().run()