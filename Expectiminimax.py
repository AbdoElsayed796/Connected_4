import math
from Heuristic import heuristic


def Expectiminimax(current_board, max_depth=5):
    """AI is player 2 (maximizing player)"""
    value, move = Max_Value(current_board, max_depth)
    return move


def Max_Value(current_board, max_depth):
    """Player 2 (AI) maximizes"""
    if is_full(current_board) or max_depth <= 0:
        return heuristic(current_board), None
    
    value = float('-inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        
        if row != -1:
            v2 = Expected_Value(current_board, max_depth - 1, 2, col)
            
            if v2 > value:
                value = v2
                best_move = col
    
    return value, best_move


def Min_Value(current_board, max_depth):
    """Player 1 (opponent) minimizes"""
    if is_full(current_board) or max_depth <= 0:
        return heuristic(current_board), None
    
    value = float('inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        
        if row != -1:
            v2 = Expected_Value(current_board, max_depth - 1, 1, col)
            
            if v2 < value:
                value = v2
                best_move = col
    
    return value, best_move


def Expected_Value(current_board, max_depth, player, col):
    """Calculate expected value after a stochastic move"""
    row = find_lowest_empty_row(current_board, col)
    
    if row == -1:
        return float('-inf') if player == 2 else float('inf')
    
    can_go_left = (col > 0) and (find_lowest_empty_row(current_board, col - 1) != -1)
    can_go_right = (col < 6) and (find_lowest_empty_row(current_board, col + 1) != -1)
    
    if can_go_left and can_go_right:
        prob_center, prob_left, prob_right = 0.6, 0.2, 0.2
    elif can_go_left:
        prob_center, prob_left, prob_right = 0.8, 0.2, 0.0
    elif can_go_right:
        prob_center, prob_left, prob_right = 0.8, 0.0, 0.2
    else:
        prob_center, prob_left, prob_right = 1.0, 0.0, 0.0
    
    value = 0.0
    
    new_board = copy_board(current_board)
    new_board[row][col] = player
    if player == 2:
        value += prob_center * Min_Value(new_board, max_depth - 1)[0]
    else:
        value += prob_center * Max_Value(new_board, max_depth - 1)[0]
    
    if can_go_left:
        row_left = find_lowest_empty_row(current_board, col - 1)
        new_board_left = copy_board(current_board)
        new_board_left[row_left][col - 1] = player
        if player == 2:
            value += prob_left * Min_Value(new_board_left, max_depth - 1)[0]
        else:
            value += prob_left * Max_Value(new_board_left, max_depth - 1)[0]
    
    if can_go_right:
        row_right = find_lowest_empty_row(current_board, col + 1)
        new_board_right = copy_board(current_board)
        new_board_right[row_right][col + 1] = player
        if player == 2:
            value += prob_right * Min_Value(new_board_right, max_depth - 1)[0]
        else:
            value += prob_right * Max_Value(new_board_right, max_depth - 1)[0]
    
    return value


def find_lowest_empty_row(board, col):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1


def copy_board(board):
    return [row[:] for row in board]


def is_full(board):
    for col in range(7):
        if board[0][col] == 0:
            return False
    return True