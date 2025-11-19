def heuristic(current_board):
    ai = 2
    human = 1

    score = 0 

    for row in current_board :
        for col in range(len(row)-3):
            window = row[col : col+4]
            score += evaluate(window , ai , human)

    for col in range(len(current_board[0])):
        col_array = [current_board[row][col] for row in range(len(current_board))]
        for row in range(len(current_board)-3):
            window = col_array[row : row +4]
            score += evaluate(window , ai , human)
    
    for row in range(len(current_board)-3):
        for col in range(len(current_board[0])-3):
            window = [current_board[row+i][col+i] for i in range(4)]
            score += evaluate(window , ai , human)

    for row in range(len(current_board)-3):
        for col in range(len(current_board[0])-3):
            window = [current_board[row-i][col+i] for i in range(4)]
            score += evaluate(window , ai , human)
    return score
def evaluate(window , ai , human):
    if ai in window and human in window :
        return 0
     
    score = 0
    if window.count(ai) == 4:
        score += 10000
    elif window.count(ai) == 3 and window.count(0) == 1:
        score += 100
    elif window.count(ai) == 2 and window.count(0) == 2:
        score += 10

    if window.count(human) == 4:
        score -= 10000
    elif window.count(human) == 3 and window.count(0) == 1:
        score -= 100
    elif window.count(human) == 2 and window.count(0) == 2:
        score -= 10

    return score

board = [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 2, 2, 2, 0, 0], 
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]

ans = heuristic(board)
print(ans)