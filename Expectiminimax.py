from TreeNode import TreeNode
from Heuristic import heuristic

def Expectiminimax(current_board, max_depth=5):
    """AI is player 2 (maximizing player)"""
    root = TreeNode(col=None, depth=0, node_type="max")
    value, move = Max_Value(current_board, max_depth, root)
    return move, root  # return root to inspect tree


def Max_Value(current_board, max_depth, node):
    """Player 2 (AI) maximizes"""
    if is_full(current_board) or max_depth <= 0:
        v = heuristic(current_board)
        node.set_value(v)
        return v, None
    
    value = float('-inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        if row != -1:
            child = TreeNode(col=col, depth=node.depth + 1, node_type="expect")
            node.add_child(child)

            v2 = Expected_Value(current_board, max_depth - 1, 2, col, child)
            
            if v2 > value:
                value = v2
                best_move = col
    
    node.set_value(value)
    return value, best_move


def Min_Value(current_board, max_depth, node):
    """Player 1 (opponent) minimizes"""
    if is_full(current_board) or max_depth <= 0:
        v = heuristic(current_board)
        node.set_value(v)
        return v, None
    
    value = float('inf')
    best_move = None
    
    for col in range(7):
        row = find_lowest_empty_row(current_board, col)
        if row != -1:
            child = TreeNode(col=col, depth=node.depth + 1, node_type="expect")
            node.add_child(child)

            v2 = Expected_Value(current_board, max_depth - 1, 1, col, child)
            
            if v2 < value:
                value = v2
                best_move = col
    
    node.set_value(value)
    return value, best_move


def Expected_Value(current_board, max_depth, player, col, node):
    """Calculate expected value after a stochastic move, constructing 'expect' nodes"""
    row = find_lowest_empty_row(current_board, col)
    if row == -1:
        v = float('-inf') if player == 2 else float('inf')
        node.set_value(v)
        return v
    
    # Determine probabilities for center / left / right
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
    children_values = []

    # Center
    new_board = copy_board(current_board)
    new_board[row][col] = player
    center_child = TreeNode(col=col, depth=node.depth + 1,
                            node_type="max" if player == 2 else "min")
    node.add_child(center_child)
    if player == 2:
        child_val, _ = Min_Value(new_board, max_depth - 1, center_child)
    else:
        child_val, _ = Max_Value(new_board, max_depth - 1, center_child)
    value += prob_center * child_val
    children_values.append(child_val)

    # Left
    if can_go_left:
        row_left = find_lowest_empty_row(current_board, col - 1)
        new_board_left = copy_board(current_board)
        new_board_left[row_left][col - 1] = player
        left_child = TreeNode(col=col-1, depth=node.depth + 1,
                              node_type="max" if player == 2 else "min")
        node.add_child(left_child)
        if player == 2:
            child_val, _ = Min_Value(new_board_left, max_depth - 1, left_child)
        else:
            child_val, _ = Max_Value(new_board_left, max_depth - 1, left_child)
        value += prob_left * child_val
        children_values.append(child_val)

    # Right
    if can_go_right:
        row_right = find_lowest_empty_row(current_board, col + 1)
        new_board_right = copy_board(current_board)
        new_board_right[row_right][col + 1] = player
        right_child = TreeNode(col=col+1, depth=node.depth + 1,
                               node_type="max" if player == 2 else "min")
        node.add_child(right_child)
        if player == 2:
            child_val, _ = Min_Value(new_board_right, max_depth - 1, right_child)
        else:
            child_val, _ = Max_Value(new_board_right, max_depth - 1, right_child)
        value += prob_right * child_val
        children_values.append(child_val)

    node.set_value(value)
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
