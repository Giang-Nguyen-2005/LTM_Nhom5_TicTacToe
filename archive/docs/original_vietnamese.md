# Đồ án (Original Vietnamese Project Description)

Đồ án Giữa kỳ môn Lập trình mạng: Game Tic-Tac-Toe (X-O 3x3)

Dự án này xây dựng một game X-O 3x3 đa người chơi (multi-client) sử dụng Socket (TCP) và Đa luồng (Threading) trong Python.

---

## 🎯 Mô tả sơ bộ

* **Mô hình:** Multi Client-Server.
* **Mục tiêu:** Server phải có khả năng xử lý *nhiều ván đấu 3x3* diễn ra *đồng thời*.
* **Công nghệ:**
    * `socket`: Để xử lý kết nối mạng.
    * `threading`: Để Server xử lý nhiều Client cùng lúc.
    * `tkinter`: Để làm giao diện (GUI) cho Client.

---

## 🚀 Hướng dẫn cho Thành viên Nhóm

Dưới đây là vai trò của từng file để mọi người nắm rõ:

### 1. `server.py` (File Máy chủ 🖥️)

* **Đây là "Trọng tài" và "Sảnh chờ".**
* **Nhiệm vụ:**
    * Luôn chạy và lắng nghe kết nối từ Client.
    * Ghép 2 Client vào một "Phòng chơi".
    * **Quan trọng:** Dùng **Threading** để tạo một luồng riêng cho *mỗi phòng chơi* (giúp nhiều ván đấu diễn ra song song).
    * Nhận nước đi, kiểm tra thắng/thua (bằng cách dùng `game.py`), và báo kết quả lại cho 2 Client.

### 2. `client.py` (File Người chơi 🧑‍💻)

* **Đây là "Giao diện (GUI)" mà người chơi sẽ thấy.**
* **Nhiệm vụ:**
    * Dùng **Tkinter** để vẽ bàn cờ 3x3 (9 cái nút).
    * Kết nối đến Server (nhập IP/Port).
    * Khi người chơi click vào nút, nó sẽ gửi tọa độ (ví dụ: "MOVE 1 2") cho Server.
    * Phải có một luồng (`threading`) riêng để *luôn lắng nghe* tin nhắn từ Server (như nước đi của đối thủ, thông báo thắng/thua) mà không làm đơ giao diện.

### 3. `game.py` (File Logic game 🧠)

* **Đây là "Bộ não" xử lý luật chơi.**
* **Nhiệm vụ:**
    * Chứa một lớp (class) `TicTacToeGame` (hoặc các hàm) để quản lý trạng thái bàn cờ (mảng 3x3).
    * Cung cấp các hàm chính: `make_move()` (thực hiện nước đi), `check_win()` (kiểm tra 8 trường hợp thắng), `check_draw()` (kiểm tra hòa).
    * **`server.py` sẽ gọi các hàm trong file này** để xử lý logic, giúp cho file `server.py` gọn gàng hơn.

---

## 🏃‍♂️ Cách chạy thử

1.  **Chạy Server trước:**
    ```bash
    python server.py
    ```
2.  **Chạy Client 1:** Mở terminal mới, chạy:
    ```bash
    python client.py
    ```
3.  **Chạy Client 2:** Mở terminal mới nữa, chạy:
    ```bash
    python client.py
    ```
    (Lúc này 2 Client sẽ được ghép cặp và bắt đầu chơi)
