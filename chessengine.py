from helper_functions import initMvvLva


pieceScores = {'K': 0, 'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}

class GameState():
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'Q': self.getQueenMoves, 
                             'N': self.getKnightMoves, 'B': self.getBishopMoves, 'K': self.getKingMoves}
        self.whiteToMove = True
        self.moveLog = []

        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        #self.inCheck = False
        self.checkmate = False
        self.stalemate = False
        self.pins = []
        self.checks = []
        self.enPassantPossible = ()
        self.enPassantPossibleLog = [self.enPassantPossible]

        self.currentCastlingRights = CastlingRights(True, True, True, True)
        self.castlingRightsLog = [
            CastlingRights(
                self.currentCastlingRights.wks,
                self.currentCastlingRights.bks,
                self.currentCastlingRights.wqs,
                self.currentCastlingRights.bqs,
            )
        ]

        self.white_attacks = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.black_attacks = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.white_defends = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.black_defends = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}

        self.mvv_lva = initMvvLva()


    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove

        self.countAttacksAndDefends()

        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        if move.isPawnPromotion:
            # promotedPiece = input("Promote to Q, R, B or N: ")
            promotedPiece = move.promotionChoice
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + promotedPiece

        if move.isEnPassantMove:
            self.board[move.startRow][move.endCol] = '--'

        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.startRow + move.endRow)//2, move.startCol)
        else:
            self.enPassantPossible = ()

        
        
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:
                self.board[move.endRow][move.endCol-1] = self.board[move.endRow][move.endCol+1]
                self.board[move.endRow][move.endCol+1] = "--"
            else:
                self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-2]
                self.board[move.endRow][move.endCol-2] = '--'

        self.enPassantPossibleLog.append(self.enPassantPossible)

        self.updateCastlingRights(move)
        self.castlingRightsLog.append(CastlingRights(self.currentCastlingRights.wks,self.currentCastlingRights.bks,
                self.currentCastlingRights.wqs, self.currentCastlingRights.bqs,))
        



    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove

            self.countAttacksAndDefends()

            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)

            if move.isEnPassantMove:
                self.board[move.endRow][move.endCol] = '--'
                self.board[move.startRow][move.endCol] = move.pieceCaptured
                
            self.enPassantPossibleLog.pop()
            self.enPassantPossible = self.enPassantPossibleLog[-1]
            
            self.castlingRightsLog.pop()
            newRights = self.castlingRightsLog[-1]
            self.currentCastlingRights = CastlingRights(newRights.wks, newRights.bks, newRights.wqs, newRights.bqs)
            if move.isCastleMove:
                if move.endCol - move.startCol == 2:
                    self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-1]
                    self.board[move.endRow][move.endCol-1] = '--'
                else:
                    self.board[move.endRow][move.endCol-2] = self.board[move.endRow][move.endCol+1]
                    self.board[move.endRow][move.endCol+1] = '--'
            
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
                            (i==1 and type == 'p' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
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

    
    def updateCastlingRights(self, move):
        if move.pieceMoved == "wK":
            self.currentCastlingRights.wks = False
            self.currentCastlingRights.wqs = False
        elif move.pieceMoved == "bK":
            self.currentCastlingRights.bks = False
            self.currentCastlingRights.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0:
                    self.currentCastlingRights.wqs = False
                elif move.startCol == 7:
                    self.currentCastlingRights.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0:
                    self.currentCastlingRights.bqs = False
                elif move.startCol == 7:
                    self.currentCastlingRights.bks = False
        
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRights.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRights.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRights.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRights.bks = False


    
        
    def getValidMoves(self):
        tempEnpassantPossible = self.enPassantPossible
        tempCastleRights = CastlingRights(
            self.currentCastlingRights.wks,
            self.currentCastlingRights.bks,
            self.currentCastlingRights.wqs,
            self.currentCastlingRights.bqs,
        )
        
        moves = self.getAllPossibleMoves()
        
        for i in range(len(moves) - 1, -1, -1):
            self.makeMove(moves[i])
            self.whiteToMove = not self.whiteToMove
            if self.inCheck():
                
                moves.remove(moves[i])
            
            self.whiteToMove = not self.whiteToMove
            self.undoMove()
        
        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False
       
        if self.whiteToMove:
            self.getCastleMoves(
                self.whiteKingLocation[0], self.whiteKingLocation[1], moves
            )
        else:
            self.getCastleMoves(
                self.blackKingLocation[0], self.blackKingLocation[1], moves
            )
        self.enPassantPossible = tempEnpassantPossible
        self.currentCastlingRights = tempCastleRights
        return moves
    

    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])


    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove
        oppoMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for move in oppoMoves:
            if move.endRow == r and move.endCol == c:
                return True
        


    def detectAllPins(self):
        pins = []

        kingPins = self.detectPinsToRoyalPiece(isKing=True)
        pins.extend(kingPins)

        queenPins = self.detectPinsToRoyalPiece(isKing=False)
        pins.extend(queenPins)

        return pins
    

    def detectPinsToRoyalPiece(self, isKing=True):
        pins = []

        if self.whiteToMove:
            allyColor = 'w'
            enemyColor = 'b'
        else:
            allyColor = 'b'
            enemyColor = 'w'

        pieceLocation = None
        if isKing:
            pieceLocation = self.whiteKingLocation if self.whiteToMove else self.blackKingLocation
        else:
            for r in range(8):
                for c in range(8):
                    if self.board[r][c] == allyColor + 'Q':
                        pieceLocation = (r, c)
                        break
                if pieceLocation:
                    break
            
        if not pieceLocation:
            return pins
        
        startRow, startCol = pieceLocation

        directions = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1))
        for d in directions:
            possiblePin = ()
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
            
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                
                    if endPiece[0] == allyColor and (endPiece[1] != 'K' and endPiece[1] != 'Q'):
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:
                            break  
                        
                    elif endPiece[0] == enemyColor:
                        piece_type = endPiece[1]
                    
                        valid_pin = False
                    
                    
                        if 0 <= directions.index(d) <= 3:
                            if piece_type == 'R' or piece_type == 'Q':
                                valid_pin = True
                    
                        elif 4 <= directions.index(d) <= 7:
                            if piece_type == 'B' or piece_type == 'Q':
                                valid_pin = True
                    
                        if valid_pin and possiblePin != ():
                            pins.append((possiblePin[0], possiblePin[1], possiblePin[2], possiblePin[3], isKing))
                        break
                    else:
                        break
                else:
                    break
    
        return pins
    

    def scoreMove(self, move):
        score = 0

        self.makeMove(move)

        self.whiteToMove = not self.whiteToMove
        if self.inCheck():
            score += 10000
        self.whiteToMove = not self.whiteToMove

        self.undoMove()

        if move.isCapture:
            attacker_piece = move.pieceMoved[1]
            victim_piece = move.pieceCaptured[1]
        
            if attacker_piece in self.mvv_lva and victim_piece in self.mvv_lva[attacker_piece]:
            # Use MVV-LVA table to score the capture
                score += 1000 + self.mvv_lva[attacker_piece][victim_piece]
            else:
            # Fallback for any capture not in table
                score += 1000

        enemy_color = 'b' if self.whiteToMove else 'w'
        r, c = move.endRow, move.endCol

        piece_threatens = 0
        attack_squares = self.getPieceAttackSquares(r, c)
        if attack_squares:
            for square in attack_squares:
                target_r, target_c = square
                if 0 <= target_r < 8 and 0 <= target_c < 8:
                    target_piece = self.board[target_r][target_c]
                    if target_piece != '--' and target_piece[0] == enemy_color:
                    # Threaten score based on piece value
                        piece_threatens += pieceScores.get(target_piece[1], 0) * 10
    
        score += piece_threatens

        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        if (move.endRow, move.endCol) in center_squares:
            score += 50  # Small bonus for controlling center

        if move.pieceMoved[1] == 'p':
        # Calculate how far the pawn has advanced
            if self.whiteToMove:  # White pawns move up the board (decreasing row)
                pawn_advance = 7 - move.endRow  # 7 is the starting row for white pawns
            else:  # Black pawns move down the board (increasing row)
                pawn_advance = move.endRow  # 0 is the starting row for black pawns
        
        # Higher bonus for pawns closer to promotion
            score += pawn_advance * 10
    
    # 6. Bonus for castling
        if move.isCastleMove:
            score += 500  # Good bonus for castling
    
        return score
    

    def orderMoves(self, moves):
        moveScores = []

        for move in moves:
            moveScores.append((move, self.scoreMove(move)))

        moveScores.sort(key=lambda x: x[1], reverse=True)

        return [move[0] for move in moveScores]


    def countAttacksAndDefends(self):

        self.white_attacks = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.white_defends = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.black_attacks = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.black_defends = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}

        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                piece = self.board[r][c]
                if piece != '--':
                    color = piece[0]
                    piece_type = piece[1]

                    attack_squares = self.getPieceAttackSquares(r, c)
                    if attack_squares is not None:

                        for square in attack_squares:
                            target_r, target_c = square
                            target_piece = self.board[target_r][target_c]

                            if target_piece != '--':
                                target_color = target_piece[0]

                                if color != target_color:
                                    if color == 'w':
                                        self.white_attacks[piece_type] += 1
                                        self.white_attacks["total"] += 1
                                    else:
                                        self.black_attacks[piece_type] += 1
                                        self.black_attacks["total"] += 1
                                else:
                                    if color == 'w':
                                        self.white_defends[piece_type] += 1
                                        self.white_defends['total'] += 1
                                    else:
                                        self.black_defends[piece_type] += 1
                                        self.black_defends['total'] += 1
        
        return (self.white_attacks, self.white_defends, self.black_attacks, self.black_defends)



    def getPieceAttackSquares(self, r, c):
        piece = self.board[r][c]
        if piece == '--':
            return []
        
        color = piece[0]
        piece_type = piece[1]
        attack_squares = []

        if piece_type == 'p':
            if color == 'w':  
                if c-1 >= 0 and r-1 >= 0:  
                    attack_squares.append((r-1, c-1))
                if c+1 < 8 and r-1 >= 0:  
                    attack_squares.append((r-1, c+1))
            else:  
                if c-1 >= 0 and r+1 < 8:  
                    attack_squares.append((r+1, c-1))
                if c+1 < 8 and r+1 < 8: 
                    attack_squares.append((r+1, c+1))
        
        elif piece_type == 'N':
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
            for move in knight_moves:
                end_row = r + move[0]
                end_col = c + move[1]
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    attack_squares.append((end_row, end_col))

        elif piece_type in ['B', 'R', 'Q', 'K']:
            directions = []
            if piece_type in ['B', 'Q']:  
                directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
            if piece_type in ['R', 'Q']: 
                directions.extend([(-1, 0), (0, -1), (1, 0), (0, 1)])
            if piece_type == 'K': 
                directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

            for d in directions:
                for i in range(1, 8):
                    end_row = r + d[0] * i
                    end_col = c + d[1] * i
                    if 0 <= end_row < 8 and 0 <= end_col < 8:
                        attack_squares.append((end_row, end_col))
                        if self.board[end_row][end_col] != '--' or piece_type == 'K':
                            break
                    else:
                        break

        return attack_squares
    




    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)
        
        return moves



    def getPawnMoves(self, r, c, moves):

        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            backRow = 0
            enemyColor = 'b'
        
        else:
            moveAmount = 1
            startRow = 1
            backRow = 7
            enemyColor = 'w'
        
        isPawnPromotion = False

        if self.board[r+moveAmount][c] == "--":  
            if not piecePinned or pinDirection == (moveAmount, 0):
                if r+moveAmount == backRow:
                    isPawnPromotion = True
                moves.append(Move((r, c), (r+moveAmount, c), self.board, isPawnPromotion=isPawnPromotion))
                if r == startRow and self.board[r+2*moveAmount][c] == "--": 
                    moves.append(Move((r, c), (r+2*moveAmount, c), self.board))

        if c - 1 >= 0:
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[r+moveAmount][c-1][0] == enemyColor:
                    if r + moveAmount == backRow: 
                        isPawnPromotion = True
                    moves.append(Move((r, c), (r+moveAmount, c-1), self.board, isPawnPromotion=isPawnPromotion))
                elif (r + moveAmount, c - 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r+moveAmount, c-1), self.board, isEnPassantMove=True))

        if c + 1 <= 7:
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[r+moveAmount][c+1][0] == enemyColor:
                    if r + moveAmount == backRow: 
                        isPawnPromotion = True
                    moves.append(Move((r, c), (r+moveAmount, c+1), self.board, isPawnPromotion=isPawnPromotion))
                elif (r + moveAmount, c + 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r+moveAmount, c+1), self.board, isEnPassantMove=True))
            



    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemyColor = 'b' if self.whiteToMove else 'w'
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break



    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = 'w' if self.whiteToMove else 'b'
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))


    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))
        enemyColor = 'b' if self.whiteToMove else 'w'
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break


    def getKingMoves(self, r, c, moves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = 'w' if self.whiteToMove else 'b'
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    if allyColor == 'w':
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    if allyColor == 'w':
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c) 

    

    def getCastleMoves(self, r, c, moves):
        if self.squareUnderAttack(r, c):
            return 
        if (self.whiteToMove and self.currentCastlingRights.wks) or (not self.whiteToMove and self.currentCastlingRights.bks):
            self.getKingSideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRights.wqs) or (not self.whiteToMove and self.currentCastlingRights.bqs):
            self.getQueenSideCastleMoves(r, c, moves)
        
    

    def getKingSideCastleMoves(self, r, c, moves):
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
            if not self.squareUnderAttack(r, c+1) and not self.squareUnderAttack(r, c+2):
                moves.append(Move((r, c), (r, c+2), self.board, isCastleMove=True))



    
    def getQueenSideCastleMoves(self, r, c, moves):
        if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--':
            if not self.squareUnderAttack(r, c-1) and not self.squareUnderAttack(r, c-2):
                moves.append(Move((r, c), (r, c-2), self.board, isCastleMove=True))



    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)
        

class CastlingRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs



class Move():

    ranksToRows = {'1':7, '2':6, '3':5, '4':4, '5':3, '6':2, '7':1, '8':0}
    rowsToRanks = {v:k for k,v in ranksToRows.items()}
    filesToCols = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7}
    colsToFiles = {v:k for k,v in filesToCols.items()}


    def __init__(self, startSq, endSq, board, isPawnPromotion = False, isEnPassantMove = False, isCastleMove = False, promotionChoice='Q'):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.isCapture = (self.pieceCaptured != "--")
        self.isPawnPromotion = isPawnPromotion
        self.promotionChoice = promotionChoice


        if (self.pieceMoved == 'wp' and self.endRow == 0) or (self.pieceMoved == 'bp' and self.endRow == 7):
            self.isPawnPromotion = True
        
        self.isEnPassantMove = isEnPassantMove
        if self.isEnPassantMove:
            self.pieceCaptured = 'wp' if self.pieceMoved == 'bp' else 'bp'
        
        self.isCastleMove = isCastleMove

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol 

    
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False
    
    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)
    
    
    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]
    
    def __str__(self):
        if self.isCastleMove:
            return "O-O" if self.endCol == 6 else "O-O-O"
        
        endSquare = self.getRankFile(self.endRow, self.endCol)
        if self.pieceMoved[1] == 'p':
            if self.isCapture:
                return self.colsToFiles[self.startCol] + 'x' + endSquare
            else:
                return endSquare
        
        moveString = self.pieceMoved[1]

        if self.isCapture:
            moveString += 'x'
        
        return moveString + endSquare
