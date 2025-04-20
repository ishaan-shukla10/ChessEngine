def getValidMoves(self):
        moves = []

        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]

        if self.inCheck:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()

                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol]
                validSquares = []
                if pieceChecking[1] == "N":
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2]*i, kingCol + check[3]*i)
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:
                            break
                
                for i in range(len(moves)-1, -1, -1):
                    if moves[i].pieceMoved[1] != 'K':
                        if not (moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else:
                self.getKingMoves(kingRow, kingCol, moves)
        else:
            moves = self.getAllPossibleMoves()



        # for i in range(len(moves) - 1, -1, -1):
        #     self.makeMove(moves[i])

        #     self.whiteToMove = not self.whiteToMove
            
        #     if self.inCheck():
        #         moves.remove(moves[i])

        #     self.whiteToMove = not self.whiteToMove
        #     self.undoMove()
        
        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

def checkForPinsAndChecks(self):
    pins = []
    checks = []
    inCheck = False
    if self.whiteToMove:
        enemyColor = 'b'
        allyColor = 'w'
        startRow = self.whiteKingLocation[0]
        startCol = self.whiteKingLocation[1]
    else:
        enemyColor = 'w'
        allyColor = 'b'
        startRow = self.blackKingLocation[0]
        startCol = self.blackKingLocation[1]

    directions = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1))
    for j in range(len(directions)):
        d = directions[j]
        possiblePin = ()
        for i in range(1, 8):
            endRow = startRow + d[0] * i
            endCol = startCol + d[1] * i
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == allyColor and endPiece[1] != 'K':
                    if possiblePin == ():
                        possiblePin = (endRow, endCol, d[0], d[1])
                    else:
                        break
                elif endPiece[0] == enemyColor:
                    type = endPiece[1]

                    if (0 <= j <= 3 and type == 'R') or (4 <= j <= 7 and type == 'B') or \
                        (i==1 and type == 'p' and ((enemyColor == 'w' and 6 <= i <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                        (type == 'Q') or (i == 1 and type == 'K'):

                        if possiblePin == ():
                            inCheck = True
                            checks.append((endRow, endCol, d[0], d[1]))
                            break
                        else:
                            pins.append(possiblePin)
                            break
                    else:
                        break
        
            else:
                break

    knightMoves = knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
    for m in knightMoves:
        endRow = startRow + m[0]
        endCol = startCol + m[1]
        if 0 <= endRow < 8 and 0 <= endCol < 8:
            endPiece = self.board[endRow][endCol]
            if endPiece[0] == enemyColor and endPiece[1] == 'N':
                inCheck = True
                checks.append((endRow, endCol, m[0], m[1]))
    
    return inCheck, pins, checks