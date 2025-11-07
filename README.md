# TicTacToeSocket

Midterm project: networked Tic-Tac-Toe (3x3) using a simple line-based text protocol.

This repository contains the server (`server.py`), the pygame GUI client (`client_ttt.py`), the game logic (`game.py`) and the `assets/` used by the GUI.
## Game run:
<img width="1343" height="237" alt="image" src="https://github.com/user-attachments/assets/d696dba2-0026-4008-b30e-483df3a6804e" />
<img width="954" height="335" alt="image" src="https://github.com/user-attachments/assets/ba48787a-c421-48d6-891c-7421bc572f89" />
<img width="1123" height="786" alt="image" src="https://github.com/user-attachments/assets/ff938ebd-dc8e-4af9-b901-3ed3656c41ab" />
<img width="1116" height="788" alt="image" src="https://github.com/user-attachments/assets/74f89e5a-340b-409b-a99d-931a279cec20" />
<img width="1118" height="775" alt="image" src="https://github.com/user-attachments/assets/b1366f40-e2ae-4115-996b-39e5b5325f84" />
<img width="1118" height="781" alt="image" src="https://github.com/user-attachments/assets/ab347144-ad9a-4028-830c-2b7957bb57ff" />
<img width="1122" height="785" alt="image" src="https://github.com/user-attachments/assets/41c27f14-b0fe-416b-8959-e9c201f08d9b" />

## Quick start

1. Install dependencies (GUI client requires pygame):

```powershell
python -m pip install pygame
```

2. Start the server on the default port 5051:

```powershell
python server.py
```

3. Start one or more GUI clients:

```powershell
python client_ttt.py
```

ASCII playthrough (readable preview)

The project uses a simple text protocol. Below is an ASCII simulation of a short game so you can picture how the board and messages look in a console-based view.

Board coordinate indices: rows and columns are 0..2

Empty board (cells shown as numbers for coordinates):

```text
   0   1   2
0  . | . | .
  ---+---+---
1  . | . | .
  ---+---+---
2  . | . | .
```

Legend: X (player X), O (player O), . empty

Sample session (server -> client lines and client -> server moves):

```text
SERVER: START X
SERVER: MESSAGE Waiting for opponent...
SERVER: YOUR_TURN
CLIENT -> SERVER: MOVE 0 0    # Player X places at row 0, col 0
SERVER: VALID_MOVE
SERVER -> O: OPPONENT_MOVE 0 0
```

Board after X's first move:

```text
   0   1   2
0  X | . | .
  ---+---+---
1  . | . | .
  ---+---+---
2  . | . | .
```

Next moves (condensed):

```text
1) X -> MOVE 0 0  (valid)
2) O -> MOVE 1 1  (valid)
3) X -> MOVE 0 1  (valid)
4) O -> MOVE 2 2  (valid)
5) X -> MOVE 0 2  (valid)  <-- X completes top row and wins
```

Final board (X wins):

```text
   0   1   2
0  X | X | X   <- X wins
  ---+---+---
1  . | O | .
  ---+---+---
2  . | . | O
```

Server final messages for winner:

```text
SERVER: WIN
SERVER -> opponent: LOSE
```

How to read this in the GUI

- The GUI client sends moves as (row, col) to the server.
- The server validates moves and broadcasts opponent moves.
- The GUI shows the same final board as the ASCII art above.

Notes

- This README provides a console-friendly preview of gameplay so reviewers can understand game flow without launching the GUI.
- For more details about the message protocol see `server.py` and `game.py`.
---
## Cách chơi đúng (Hướng dẫn nhanh - tiếng Việt)

- Mục tiêu: 3 dấu cùng loại (X hoặc O) thẳng hàng — hàng ngang, hàng dọc hoặc đường chéo.
- Chuẩn bị: Mở `server.py` trước (mặc định lắng nghe cổng 5051), rồi mở 1 hoặc 2 client bằng `client_ttt.py`.
- Tạo người chơi: Dùng ô "P1 Name" / "P2 Name" và bấm "Join" để tạo kết nối cho Player 1 / Player 2. Có thể tạo cả hai trong cùng một cửa sổ.
- Lượt đi: X luôn đi trước. Chỉ được nhấp để đánh khi server thông báo đến lượt của bạn (GUI sẽ chỉ hiện ghost mark khi hợp lệ).
- Cách đánh: Nhấp vào ô trên bàn cờ để gửi MOVE tới server. Nếu đang ở chế độ Split Screen, nhấp vào bàn bên trái để điều khiển P1, bàn bên phải để điều khiển P2.
- Trường hợp không hợp lệ: Nếu ô đã có hoặc không phải lượt bạn, server sẽ không chấp nhận nước đi — GUI sẽ không thay đổi ô đó.
- Kết thúc ván: Khi có người thắng hoặc hòa, GUI sẽ hiển thị thông báo thắng/hòa. Dùng nút "Reset" để bắt đầu ván mới.
- Chat: Gõ vào ô Chat (sidebar) và nhấn Enter để gửi — tin nhắn sẽ được gửi từ client mà bạn đang điều khiển (Control P1 / Control P2).
- Tùy chọn giao diện: Dùng nút "Split Screen" để xem hai bàn song song (thuận tiện khi bạn chạy cả P1 và P2 trên cùng một máy). Dùng "Control P1" / "Control P2" để chuyển focus nhập liệu/chat.

Mẹo nhanh:
- Nếu gặp lỗi kết nối, kiểm tra rằng `server.py` đang chạy và cổng đúng (5051), hoặc thay đổi `SERVER_HOST`/`SERVER_PORT` trong `client_ttt.py` nếu cần.
- Để chơi nhanh trên cùng một máy: mở 1 cửa sổ GUI, bấm Join cả P1 và P2, bật Split Screen — bạn sẽ thấy hai bàn và có thể nhấp vào mỗi bàn để gửi nước đi.

---

For additional developer notes and protocol examples see `server.py` and `game.py`.
