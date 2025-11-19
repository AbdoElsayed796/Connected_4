import math
from Heuristic import heuristic

def Minimax_Search(current_board, max_depth=5):
    value, move = Max_Value(current_board, max_depth)
    return move

def Max_Value(current_board, max_depth):
    if max_depth == 0:
        return heuristic(current_board), None
    
    value = float('-inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        
        if row != -1:  
            new_board = copy_board(current_board)
            new_board[row][col] = 2     
            v2, _ = Min_Value(new_board, max_depth - 1)
            
            if v2 > value:
                value = v2
                best_move = col
    
    return value, best_move

def Min_Value(current_board, max_depth):
    if max_depth == 0:
        return heuristic(current_board), None
    
    value = float('inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        
        if row != -1: 
            new_board = copy_board(current_board)
            new_board[row][col] = 1
            v2, _ = Max_Value(new_board, max_depth - 1)
            if v2 < value:
                value = v2
                best_move = col
    
    return value, best_move

def find_lowest_empty_row(board, col):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1

def copy_board(board):
    return [row[:] for row in board]
         