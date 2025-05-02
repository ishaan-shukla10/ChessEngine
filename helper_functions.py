
def isValidEnPassant(self, move):
    # Can't do en passant if no moves have been made yet
    if len(self.moveLog) == 0:
        return False
        
    last_move = self.moveLog[-1]
    
    # For en passant to be valid:
    # 1. Last move must be a pawn move (piece type 'p')
    # 2. Last move must be a two-square advance (moved 2 rows)
    # 3. The capturing pawn must be on the same column as where the enemy pawn landed
    # 4. The capturing pawn must be on the same row as where the enemy pawn started
    return (last_move.pieceMoved[1] == 'p' and 
            abs(last_move.startRow - last_move.endRow) == 2 and
            last_move.endCol == move.endCol and
            abs(last_move.endRow - move.startRow) == 0)