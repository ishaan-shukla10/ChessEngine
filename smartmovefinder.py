import random



pieceScores = {'K': 0, 'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
CHECKMATE = 1000
STALEMATE = 0



def findRandomMove(validMoves):
    return validMoves[random.randint(0, len(validMoves)-1)]


def findBestMove(gs, validMoves):
    turnMultiplier = 1 if gs.whiteToMove else -1
    bestMove = None
    maxScore = -CHECKMATE

    for playerMove in validMoves:
        gs.makemove(playerMove)
        if gs.checkmate:
            score = CHECKMATE
        elif gs.stalemate:
            score = STALEMATE
        score = turnMultiplier * scoreMaterial(gs.board)
        if score > maxScore:
            score = maxScore
            bestMove = playerMove
        
        return bestMove


def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScores[square[1]]
            elif square[0] == 'b':
                score -= pieceScores[square[1]]

    return score