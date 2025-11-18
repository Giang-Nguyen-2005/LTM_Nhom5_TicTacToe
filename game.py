# game.py
class TicTacToeGame:
    """
    Lớp quản lý logic game Tic-Tac-Toe 3x3
    """
    
    def __init__(self):
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.winner = None
        self.game_over = False
        self.winning_line = None
    
    def make_move(self, row, col, player):
        if self.game_over or row < 0 or row > 2 or col < 0 or col > 2:
            return False
        if self.board[row][col] is not None or player != self.current_player:
            return False
        
        self.board[row][col] = player
        
        if self.check_win(player):
            self.winner = player
            self.game_over = True
            return True
        
        if self.check_draw():
            self.winner = 'DRAW'
            self.game_over = True
            return True
        
        self.current_player = 'O' if player == 'X' else 'X'
        return True
    
    def check_win(self, player):
        # Check rows
        for i in range(3):
            if all(self.board[i][j] == player for j in range(3)):
                self.winning_line = [[i, 0], [i, 1], [i, 2]]
                return True
        # Check columns
        for j in range(3):
            if all(self.board[i][j] == player for i in range(3)):
                self.winning_line = [[0, j], [1, j], [2, j]]
                return True
        # Diagonal TL-BR
        if all(self.board[i][i] == player for i in range(3)):
            self.winning_line = [[0, 0], [1, 1], [2, 2]]
            return True
        # Diagonal TR-BL
        if all(self.board[i][2-i] == player for i in range(3)):
            self.winning_line = [[0, 2], [1, 1], [2, 0]]
            return True
        self.winning_line = None
        return False
    
    def check_draw(self):
        return all(self.board[i][j] is not None for i in range(3) for j in range(3))
    
    def get_board_state(self):
        return [row[:] for row in self.board]
    
    def reset(self):
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.winner = None
        self.game_over = False
        self.winning_line = None
    
    def is_game_over(self):
        return self.game_over
    
    def get_winner(self):
        return self.winner

    def get_winning_line(self):
        return self.winning_line