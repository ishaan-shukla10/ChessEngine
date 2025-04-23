
def initMvvLva():
    
    piece_values = {'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 10}
    mvv_lva = {}
    
    
    for attacker in piece_values:
        mvv_lva[attacker] = {}
        for victim in piece_values:
            mvv_lva[attacker][victim] = piece_values[victim] * 10 - piece_values[attacker]
    
    return mvv_lva


def isValidEnPassant(self, move):
    if len(self.moveLog) == 0:
        return False
        
    last_move = self.moveLog[-1]
    # Check if the last move was a two-square pawn advance
    return (last_move.pieceMoved[1] == 'p' and 
            abs(last_move.startRow - last_move.endRow) == 2 and
            last_move.endCol == move.endCol and
            abs(last_move.endRow - move.startRow) == 0)