import random



pieceScores = {'K': 0, 'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
CHECKMATE = 1000
STALEMATE = 0



def findRandomMove(validMoves):
    return validMoves[random.randint(0, len(validMoves)-1)]


def findGreedyMove(gs, validMoves):
    turnMultiplier = 1 if gs.whiteToMove else -1
    bestPlayerMove = None
    opponentMinMaxScore = CHECKMATE

    random.shuffle(validMoves)
    for playerMove in validMoves:
        gs.makeMove(playerMove)
        opponentsMoves = gs.getValidMoves()
        opponentMaxScore = -CHECKMATE
        for opponentsMove in opponentsMoves:
            gs.makeMove(opponentsMove)
            if gs.checkmate:
                score =  -turnMultiplier * CHECKMATE
            elif gs.stalemate:
                score = STALEMATE
            else:
                score = -turnMultiplier * scoreMaterial(gs.board)
            if score > opponentMaxScore:
                opponentMaxScore = score
            gs.undoMove()
        if opponentMaxScore < opponentMinMaxScore:
            opponentMinMaxScore = opponentMaxScore
            bestPlayerMove = playerMove
        gs.undoMove()
    return bestPlayerMove


def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScores[square[1]]
            elif square[0] == 'b':
                score -= pieceScores[square[1]]

    return score