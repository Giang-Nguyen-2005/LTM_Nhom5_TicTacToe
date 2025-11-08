class TicTacToeGame:
    """
    Lớp quản lý logic game Tic-Tac-Toe 3x3
    """
    
    def __init__(self):
        # Khởi tạo bàn cờ 3x3 (None = ô trống)
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'  # X đi trước
        self.winner = None
        self.game_over = False
    
    def make_move(self, row, col, player):
        """
        Thực hiện nước đi
        
        Args:
            row (int): Hàng (0-2)
            col (int): Cột (0-2)
            player (str): 'X' hoặc 'O'
        
        Returns:
            bool: True nếu nước đi hợp lệ, False nếu không
        """
        # Kiểm tra nước đi hợp lệ
        if self.game_over:
            return False
        
        if row < 0 or row > 2 or col < 0 or col > 2:
            return False
        
        if self.board[row][col] is not None:
            return False
        
        if player != self.current_player:
            return False
        
        # Thực hiện nước đi
        self.board[row][col] = player
        
        # Kiểm tra thắng
        if self.check_win(player):
            self.winner = player
            self.game_over = True
            return True
        
        # Kiểm tra hòa
        if self.check_draw():
            self.winner = 'DRAW'
            self.game_over = True
            return True
        
        # Chuyển lượt
        self.current_player = 'O' if player == 'X' else 'X'
        return True
    
    def check_win(self, player):
        """
        Kiểm tra người chơi có thắng không
        
        Args:
            player (str): 'X' hoặc 'O'
        
        Returns:
            bool: True nếu thắng, False nếu không
        """
        # Kiểm tra 3 hàng ngang
        for row in range(3):
            if all(self.board[row][col] == player for col in range(3)):
                return True
        
        # Kiểm tra 3 cột dọc
        for col in range(3):
            if all(self.board[row][col] == player for row in range(3)):
                return True
        
        # Kiểm tra đường chéo chính (top-left to bottom-right)
        if all(self.board[i][i] == player for i in range(3)):
            return True
        
        # Kiểm tra đường chéo phụ (top-right to bottom-left)
        if all(self.board[i][2-i] == player for i in range(3)):
            return True
        
        return False
    
    def check_draw(self):
        """
        Kiểm tra ván đấu có hòa không (bàn cờ đầy mà không có ai thắng)
        
        Returns:
            bool: True nếu hòa, False nếu không
        """
        for row in range(3):
            for col in range(3):
                if self.board[row][col] is None:
                    return False
        return True
    
    def get_board_state(self):
        """
        Lấy trạng thái bàn cờ hiện tại
        
        Returns:
            list: Bàn cờ 3x3
        """
        return self.board
    
    def reset(self):
        """
        Reset game về trạng thái ban đầu
        """
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.winner = None
        self.game_over = False
    
    def is_game_over(self):
        """
        Kiểm tra game đã kết thúc chưa
        
        Returns:
            bool: True nếu game đã kết thúc
        """
        return self.game_over
    
    def get_winner(self):
        """
        Lấy người thắng cuộc
        
        Returns:
            str: 'X', 'O', 'DRAW', hoặc None nếu chưa kết thúc
        """
        return self.winner