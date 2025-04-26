


def isValidEnPassant(self, move):
    if len(self.moveLog) == 0:
        return False
        
    last_move = self.moveLog[-1]
    # Check if the last move was a two-square pawn advance
    return (last_move.pieceMoved[1] == 'p' and 
            abs(last_move.startRow - last_move.endRow) == 2 and
            last_move.endCol == move.endCol and
            abs(last_move.endRow - move.startRow) == 0)