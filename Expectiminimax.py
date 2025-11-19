import math

def Expectimimimax(current_board, max_depth=5):
    value, move = Max_Value(current_board, max_depth)
    return move

def Max_Value(current_board, max_depth):
    if is_full(current_board) or max_depth == 0:
        return heuristic(current_board), None
    
    value = float('-inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        
        if row != -1:  
            new_board = copy_board(current_board)
            new_board[row][col] = 2     
            v2, _ = Expected_Value(new_board, max_depth - 1, 1)
            
            if v2 > value:
                value = v2
                best_move = col
    
    return value, best_move

def Min_Value(current_board, max_depth):
    if is_full(current_board) or max_depth == 0:
        return heuristic(current_board), None
    
    value = float('inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        
        if row != -1: 
            new_board = copy_board(current_board)
            new_board[row][col] = 1
            v2, _ = Expected_Value(new_board, max_depth - 1, 2)
            if v2 < value:
                value = v2
                best_move = col
    
    return value, best_move

def Expected_Value(current_board, max_depth, player):
    if is_full(current_board) or max_depth == 0 :
        return heuristic(current_board), None

    value = 0
    best_move = None

    for col in range(7):
         row = find_lowest_empty_row(current_board, col)
         if row != -1:
            new_boar_boardd = copy(curren
            new_board[row][col] = t_board)player
            new_false_left_board = copy_board(current_board)
            new_false_right_board = copy_board(current_board)
            if col != 0:
                new_false_left_board[row][col - 1] = player
            if col != 6:
                new_false_right_board[row][col + 1] = player
            if col == 0 and player == 2:
                value = (0.6*Max_Value(new_board,max_depth-1)+0.4*Max_Value(new_false_right_board,max_depth-1))
            elif col == 6 and player == 2:
                value = (0.6*Max_Value(new_board,max_depth-1)+0.4*Max_Value(new_false_left_board,max_depth-1))
            elif player == 2:
                value = (0.6*Max_Value(new_board,max_depth-1)+0.2*Max_Value(new_false_left_board,max_depth-1)
                +0.2*Max_Value(new_false_right_board,max_depth-1))
            elif col == 0 and player == 1:
                value = (0.6*Min_Value(new_board,max_depth-1)+0.4*Min_Value(new_false_right_board,max_depth-1))
            elif col == 6 and player == 1:
                value = (0.6*Min_Value(new_board,max_depth-1)+0.4*Min_Value(new_false_left_board,max_depth-1))
            else:
                value = (0.6*Min_Value(new_board,max_depth-1)+0.2*Min_Value(new_false_left_board,max_depth-1)
                +0.2*Min_Value(new_false_right_board,max_depth-1))

        return value, None

               

def find_lowest_empty_row(board,r col):
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
         
def heuristic(currnet_board):           
    pass 
    
