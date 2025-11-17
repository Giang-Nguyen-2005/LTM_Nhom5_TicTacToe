# TicTacToeSocket

Midterm project: networked Tic-Tac-Toe (3x3) using a simple line-based text protocol.

This repository contains the server (`server.py`), the pygame GUI client (`client_ttt.py`), the game logic (`game.py`) and the `assets/` used by the GUI.
## Game run:


## Quick start

# ![Demo screenshot](assets/Screenshot%202025-11-18%20000042.png)

# Tic-Tac-Toe (Networked)

Phiên bản ngắn: Trò Tic-Tac-Toe (3x3) nhiều người chơi qua TCP sockets. Repository chứa:

- `server.py` — server ghép đôi và điều phối các phòng chơi (mặc định lắng nghe `0.0.0.0:5555`).
- `client_ttt.py` — client GUI (Tkinter) để kết nối và chơi.
- `game.py` — logic game (kiểm tra nước đi, thắng/hòa).
- `assets/` — tài nguyên giao diện (nếu có).

---

**Mục lục**

- Overview
- Yêu cầu
- Cài đặt
- Chạy server
- Chạy client (GUI)
- Hướng dẫn chơi (chi tiết)
- Thông tin giao thức ngắn
- Khắc phục sự cố (Troubleshooting)
- Ghi chú

---

**Overview:**

Trò chơi ghép 2 người chơi trên server. Server ghép cặp theo thứ tự kết nối và tạo một phòng (thread) cho mỗi ván. Client là GUI đơn giản dùng `tkinter` (không cần pygame).

**Yêu cầu:**

- Python 3.8+ (đã kiểm tra với Python 3.12 trên máy phát triển).
- Thư viện chuẩn (`socket`, `threading`, `json`, `tkinter`) — `tkinter` thường có sẵn với Python trên Windows; nếu không có, cài thông qua bộ cài Python.

Không cần `pygame` cho client này (ghi chú: README cũ nhắc tới `pygame` nhưng client hiện dùng `tkinter`).

---

**Cài đặt nhanh (Windows, PowerShell):**

1. (Tùy chọn) Tạo virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Cài dependencies (không có thư viện bên ngoài bắt buộc). Nếu bạn muốn cài thêm thứ gì, dùng pip:

```powershell
python -m pip install --upgrade pip
# (không có phụ thuộc bắt buộc cho client/server hiện tại)
```

---

**Chạy server:**

Mặc định server lắng nghe port `5555` (xem `server.py`). Để chạy server:

```powershell
python server.py
```

Bạn sẽ thấy dòng: `Server đang chạy tại 0.0.0.0:5555` và `Đang chờ người chơi kết nối...`.

Để sử dụng cổng khác, chỉnh tham số trong mã (khởi tạo `TicTacToeServer(host, port)`) hoặc sửa file trước khi chạy.

**Chạy client (GUI):**

```powershell
python client_ttt.py
```

Client sẽ mở cửa sổ GUI. Khi bấm `Kết nối Server`, hộp thoại sẽ yêu cầu `IP` và `Port` (mặc định `127.0.0.1` và `5555`).

Lưu ý: client không yêu cầu tên người chơi qua tham số dòng lệnh; việc đặt P1/P2/Join được thực hiện qua GUI.

---

**Hướng dẫn chơi (ngắn gọn):**

- Mục tiêu: 3 dấu cùng loại (X hoặc O) thẳng hàng (hàng ngang, dọc hoặc chéo).
- Thứ tự: X đi trước.
- Luật mạng: client gửi JSON dạng `{"type": "MOVE", "row": r, "col": c}` (dòng kết thúc `\n`). Server kiểm tra hợp lệ, cập nhật, rồi gửi `MOVE_UPDATE` cho cả hai.

Chi tiết thao tác trong GUI:

1. Chạy `server.py` trước.
2. Chạy 2 client (có thể chạy 2 cửa sổ `client_ttt.py` hoặc chạy 1 cửa sổ và dùng chức năng để tạo cả P1/P2 nếu GUI hỗ trợ Split Screen).
3. Mỗi client bấm `Kết nối Server` và nhập `IP` + `Port` (ví dụ `127.0.0.1:5555`).
4. Khi server ghép cặp xong, client nhận `START` và GUI sẽ cho phép click vào ô trống để đánh khi đến lượt.
5. Nếu nước đi hợp lệ server gửi `MOVE_UPDATE` cho cả hai; nếu không hợp lệ client sẽ không thay đổi ô và có thể nhận `INVALID_MOVE`.
6. Khi ván kết thúc, server gửi `GAME_OVER` với `result` là `WIN` / `LOSE` / `DRAW`.

---

**Thông tin giao thức ngắn (để phát triển):**

- Client -> Server JSON messages (line-delimited):
  - `{"type":"MOVE","row":<0-2>,"col":<0-2>}`
  - `{"type":"DISCONNECT"}` (khi client đóng kết nối)
- Server -> Client JSON messages (line-delimited):
  - `{"type":"WAITING","message":"..."}` — đang chờ đối thủ
  - `{"type":"START","symbol":"X"|"O","message":"..."}` — bắt đầu ván
  - `{"type":"MOVE_UPDATE","row":r,"col":c,"symbol":"X"|"O","board": <board_state>}`
  - `{"type":"INVALID_MOVE","message":"..."}`
  - `{"type":"GAME_OVER","result":"WIN"|"LOSE"|"DRAW","message":"..."}`
  - `{"type":"OPPONENT_DISCONNECTED","message":"..."}`

`board_state` là danh sách 3x3 như trong `game.py` (None cho ô trống, 'X' hoặc 'O').

---

**Khắc phục sự cố (Troubleshooting):**

- Nếu client không kết nối: kiểm tra server đang chạy, ip/port đúng, firewall không chặn port `5555`.
- Nếu GUI không hiện (`tkinter` lỗi): đảm bảo Python được cài kèm `tkinter` (trên Windows thường mặc định có). Nếu không, cài lại Python với tùy chọn `tcl/tk and IDLE`.
- Nếu thấy thông báo `Address already in use`: có thể port đang được dùng; đổi port trong `server.py` hoặc tắt tiến trình đang dùng port đó.

---

**Ghi chú cho người phát triển:**

- File `game.py` chứa logic độc lập, dễ dùng để viết client console hoặc bot.
- `server.py` hiện ghép cặp theo thứ tự kết nối; có thể mở rộng để hỗ trợ lobby, tên người chơi, hoặc rooms có nhiều người.

---

**Tóm tắt lệnh (PowerShell):**

```powershell
# Chạy server
python server.py

# Chạy client GUI
python client_ttt.py
```

---


© Nhóm LTM_Nhom5_TicTacToe
