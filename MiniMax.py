import math
import time
from Heuristic import heuristic
from TreeNode import TreeNode

def Minimax_Search(current_board, max_depth=5):
    start_time = time.time()
    nodes_expanded = [0]  # Use list to allow modification in nested functions
    
    root = TreeNode(col=None, depth=0, node_type="max")
    value, move = Max_Value(current_board, max_depth, root, nodes_expanded)
    
    elapsed_time = time.time() - start_time
    
    return move, root, nodes_expanded[0], elapsed_time


def Max_Value(current_board, max_depth, node, nodes_expanded):
    nodes_expanded[0] += 1  # Count this node
    
    if max_depth == 0:
        v = heuristic(current_board)
        node.set_value(v)
        return v, None
    
    value = float('-inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        
        if row != -1:
            new_board = copy_board(current_board)
            new_board[row][col] = 2

            child = TreeNode(col=col, depth=node.depth + 1, node_type="min")
            node.add_child(child)

            v2, _ = Min_Value(new_board, max_depth - 1, child, nodes_expanded)

            if v2 > value:
                value = v2
                best_move = col

    node.set_value(value)
    return value, best_move


def Min_Value(current_board, max_depth, node, nodes_expanded):
    nodes_expanded[0] += 1  # Count this node
    
    if max_depth == 0:
        v = heuristic(current_board)
        node.set_value(v)
        return v, None
    
    value = float('inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        
        if row != -1:
            new_board = copy_board(current_board)
            new_board[row][col] = 1

            child = TreeNode(col=col, depth=node.depth + 1, node_type="max")
            node.add_child(child)

            v2, _ = Max_Value(new_board, max_depth - 1, child, nodes_expanded)

            if v2 < value:
                value = v2
                best_move = col

    node.set_value(value)
    return value, best_move

def find_lowest_empty_row(board, col):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1

def copy_board(board):
    return [row[:] for row in board]