import random
from openingbook import OpeningBook

pieceScores = {'K': 0, 'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}

knightScores = [[1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]]


bishopScores = [[4, 3, 2, 1, 1, 2, 3, 4],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [4, 3, 2, 1, 1, 2, 3, 4]]

queenScores = [[1, 1, 1, 3, 1, 1, 1, 1],
               [1, 2, 3, 3, 3, 1, 1, 1],
               [1, 4, 3, 3, 3, 4, 2, 1],
               [1, 2, 3, 3, 3, 2, 2, 1],
               [1, 2, 3, 3, 3, 2, 2, 1],
               [1, 4, 3, 3, 3, 4, 2, 1],
               [1, 2, 3, 3, 3, 1, 1, 1],
               [1, 1, 1, 3, 1, 1, 1, 1]]

rookScores = [[4, 3, 4, 4, 4, 4, 3, 4],
              [4, 4, 4, 4, 4, 4, 4, 4],
              [1, 1, 2, 3, 3, 2, 1, 1],
              [1, 2, 3, 4, 4, 3, 2, 1],
              [1, 2, 3, 4, 4, 3, 2, 1],
              [1, 1, 2, 3, 3, 2, 1, 1],
              [4, 4, 4, 4, 4, 4, 4, 4],
              [4, 3, 4, 4, 4, 4, 3, 4]]

whitePawnScores = [[8, 8, 8, 8, 8, 8, 8, 8],
                   [8, 8, 8, 8, 8, 8, 8, 8],
                   [5, 6, 6, 7, 7, 6, 6, 5],
                   [2, 3, 3, 5, 5, 3, 3, 2],
                   [1, 2, 3, 4, 4, 3, 2, 1],
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [1, 1, 1, 0, 0, 1, 1, 1],
                   [0, 0, 0, 0, 0, 0, 0, 0]]

blackPawnScores = [[0, 0, 0, 0, 0, 0, 0, 0],
                   [1, 1, 1, 0, 0, 1, 1, 1],
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [1, 2, 3, 4, 4, 3, 2, 1],
                   [2, 3, 3, 5, 5, 3, 3, 2],
                   [5, 6, 6, 7, 7, 6, 6, 5],
                   [8, 8, 8, 8, 8, 8, 8, 8],
                   [8, 8, 8, 8, 8, 8, 8, 8]]

piecePositionScores = {'N': knightScores, 'Q': queenScores, 'R': rookScores, 'B': bishopScores, 'bp': blackPawnScores, 
                       'wp': whitePawnScores}

CHECKMATE = 1000
STALEMATE = 0
DEPTH = 2



opening_book = OpeningBook("alekhine.json")
USE_OPENING_BOOK = True
MAX_BOOK_MOVE = 10  

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
        if gs.checkmate:
            opponentMaxScore = -CHECKMATE
        elif gs.stalemate:
            opponentMaxScore = STALEMATE
        else:
            opponentMaxScore = -CHECKMATE
            for opponentsMove in opponentsMoves:
                gs.makeMove(opponentsMove)
                gs.getValidMoves()
                if gs.checkmate:
                    score =  CHECKMATE
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


def findBestMove(gs, validMoves, returnQueue):
    global nextMove
    nextMove = None
    
    if USE_OPENING_BOOK and len(gs.moveLog) < 2 * MAX_BOOK_MOVE:
        book_move = opening_book.get_book_move(gs.board, gs.whiteToMove, gs.currentCastlingRights, 
                                            gs.enPassantPossible[1] if gs.enPassantPossible else -1, selection_mode = "mixed")
        if book_move:
            print("Using book move:", book_move.getChessNotation())
            returnQueue.put(book_move)
            return
    
    random.shuffle(validMoves)
    
    current_pins = gs.detectAllPins()
    ordered_moves = gs.orderMoves(validMoves)

    findMoveNegaMaxAlphaBeta(gs, ordered_moves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)

    returnQueue.put(nextMove) 


def moveTargetsPinnedPiece(gs, move, pins):
    pinned_squares = [(pin[0], pin[1]) for pin in pins]

    if (move.endRow, move.endCol) in pinned_squares:
        target_piece = gs.board[move.endRow][move.endCol]
        if target_piece[1] != 'p':
            return pieceScores[target_piece[1]]
    
    return 0


def findMoveMinMax(gs, validMoves, depth, whiteToMove):
    global nextMove
    if depth == 0:
        return scoreMaterial(gs.board)
    
    if whiteToMove:
        maxScore = -CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            nextMoves = gs.getValidMoves()
            score = findMoveMinMax(gs, nextMoves, depth-1, False)
            if score > maxScore:
                maxScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undoMove()
        return maxScore
    else:
        minScore = CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            nextMoves = gs.getValidMoves()
            score = findMoveMinMax(gs, nextMoves, depth-1, True)
            if score < minScore:
                minScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undoMove()
        return minScore


def findMoveNegaMax(gs, validMoves, depth, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)
    
    maxScore = -CHECKMATE
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMax(gs, nextMoves, depth-1, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undoMove()
    return maxScore

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    global nextMove

    if depth == 0:
        return turnMultiplier * scoreBoard(gs)
    
    if depth < DEPTH:
        validMoves = gs.orderMoves(validMoves)

    maxScore = -CHECKMATE
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth-1, -beta, -alpha, -turnMultiplier)
        gs.undoMove()

        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
                print(move, score)
                print("White attacks, ", gs.white_attacks)
                print("White defends, ", gs.white_defends)
                print("Black attacks, ", gs.black_attacks)
                print("Black defends, ", gs.black_defends)
        
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break

    return maxScore


def scoreBoard(gs):
    score = 0

    if gs.checkmate:
        if gs.whiteToMove:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif gs.stalemate:
        return STALEMATE
    
    white_pieces_under_attack = {}
    black_pieces_under_attack = {}
    
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece != '--':
                is_white = piece[0] == 'w'
                attacker_color = 'b' if is_white else 'w'
                
                if gs.isSquareAttacked(row, col, not is_white):
                    attackers = gs.getAttackersOfSquare(row, col, attacker_color)
                    lowest_attacker_value = float('inf')
                    
                    for att_row, att_col in attackers:
                        att_piece = gs.board[att_row][att_col]
                        if att_piece != '--' and att_piece[0] == attacker_color:
                            att_value = pieceScores.get(att_piece[1], 0)
                            lowest_attacker_value = min(lowest_attacker_value, att_value)
                    
                    defenders = gs.getAttackersOfSquare(row, col, piece[0])
                    lowest_defender_value = float('inf')
                    
                    for def_row, def_col in defenders:
                        def_piece = gs.board[def_row][def_col]
                        if def_piece != '--' and def_piece[0] == piece[0]:
                            def_value = pieceScores.get(def_piece[1], 0)
                            lowest_defender_value = min(lowest_defender_value, def_value)
                    
                    piece_value = pieceScores.get(piece[1], 0)
                    exchange_value = piece_value - lowest_attacker_value
                    
                    if is_white:
                        white_pieces_under_attack[(row, col)] = {
                            'piece': piece,
                            'value': piece_value,
                            'attackers': attackers,
                            'defenders': defenders,
                            'min_attacker_value': lowest_attacker_value,
                            'min_defender_value': lowest_defender_value,
                            'exchange_favorable': exchange_value <= 0 or len(defenders) > len(attackers)
                        }
                    else:
                        black_pieces_under_attack[(row, col)] = {
                            'piece': piece,
                            'value': piece_value,
                            'attackers': attackers,
                            'defenders': defenders,
                            'min_attacker_value': lowest_attacker_value,
                            'min_defender_value': lowest_defender_value,
                            'exchange_favorable': exchange_value <= 0 or len(defenders) > len(attackers)
                        }
    
    pieces_under_attack = white_pieces_under_attack if gs.whiteToMove else black_pieces_under_attack
    opponent_pieces_under_attack = black_pieces_under_attack if gs.whiteToMove else white_pieces_under_attack
    
    for coords, data in pieces_under_attack.items():
        if not data['defenders']:  
            score -= data['value'] * 0.5 if gs.whiteToMove else -data['value'] * 0.5
        elif not data['exchange_favorable']: 
            potential_loss = data['value'] - data['min_attacker_value']
            score -= potential_loss * 0.3 if gs.whiteToMove else -potential_loss * 0.3
    
    for coords, data in opponent_pieces_under_attack.items():
        if not data['defenders']:  
            score += data['value'] * 0.5 if gs.whiteToMove else -data['value'] * 0.5
        elif not data['exchange_favorable']:  
            potential_gain = data['value'] - data['min_attacker_value']
            score += potential_gain * 0.3 if gs.whiteToMove else -potential_gain * 0.3
    
    pins = gs.detectAllPins()
    pinned_pieces = [(pin[0], pin[1]) for pin in pins]

    pinned_pieces_info = {}
    for pin in pins:
        row, col = pin[0], pin[1]
        piece = gs.board[row][col]
        is_king_pin = pin[4]

        pinned_pieces_info[(row, col)] = {
            'piece': piece,
            'is_king_pin': is_king_pin,
            'direction': (pin[2], pin[3])
        }

    attacking_pinned_pieces = []
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece != '--':
                if (gs.whiteToMove and piece[0] == 'w') or (not gs.whiteToMove and piece[0] == 'b'):
                    attack_squares = gs.getPieceAttackSquares(r, c)
                    if attack_squares:
                        for square in attack_squares:
                            if square in pinned_pieces:
                                target_piece = gs.board[square[0]][square[1]]
                                if target_piece[1] != 'p':
                                    attacking_pinned_pieces.append({
                                        'attacker': (r, c),
                                        'target': square,
                                        'piece_value': pieceScores[target_piece[1]],
                                        'is_king_pin': pinned_pieces_info[square]['is_king_pin']
                                    })

    for attack in attacking_pinned_pieces:
        pin_bonus = attack['piece_value'] * 0.3  
        if attack['is_king_pin']:
            pin_bonus *= 1.5
        if gs.whiteToMove:
            score += pin_bonus
        else:
            score -= pin_bonus
    
    gs.whiteToMove = not gs.whiteToMove
    if gs.inCheck():
        score += 0.2 if gs.whiteToMove else -0.2
    gs.whiteToMove = not gs.whiteToMove

    white_pawns_by_file = [[] for _ in range(8)]
    black_pawns_by_file = [[] for _ in range(8)]
    
    white_king_pos = None
    black_king_pos = None
    
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece == 'wp':
                white_pawns_by_file[col].append(row)
            elif piece == 'bp':
                black_pawns_by_file[col].append(row)
            elif piece == 'wK':
                white_king_pos = (row, col)
            elif piece == 'bK':
                black_king_pos = (row, col)
    
    for col in range(8):
        if len(white_pawns_by_file[col]) > 1:
            doubled_penalty = 0.3 * (len(white_pawns_by_file[col]) - 1)
            
            if white_king_pos and white_king_pos[0] >= 6:
                king_file = white_king_pos[1]
                if abs(col - king_file) <= 1:  
                    doubled_penalty *= 1.5  
            
            score -= doubled_penalty
        
        if len(black_pawns_by_file[col]) > 1:
            doubled_penalty = 0.3 * (len(black_pawns_by_file[col]) - 1)
            
            if black_king_pos and black_king_pos[0] <= 1: 
                king_file = black_king_pos[1]
                if abs(col - king_file) <= 1:  
                    doubled_penalty *= 1.5 
            
            score += doubled_penalty
    
    for col in range(8):
        if white_pawns_by_file[col] and (col == 0 or not white_pawns_by_file[col-1]) and (col == 7 or not white_pawns_by_file[col+1]):
            isolated_penalty = 0.2 * len(white_pawns_by_file[col])
            
            if white_king_pos and white_king_pos[0] >= 6:  
                king_file = white_king_pos[1]
                if abs(col - king_file) <= 1: 
                    isolated_penalty *= 1.5 
            
            score -= isolated_penalty
        
        if black_pawns_by_file[col] and (col == 0 or not black_pawns_by_file[col-1]) and (col == 7 or not black_pawns_by_file[col+1]):
            isolated_penalty = 0.2 * len(black_pawns_by_file[col])
            
            if black_king_pos and black_king_pos[0] <= 1:  
                king_file = black_king_pos[1]
                if abs(col - king_file) <= 1:  
                    isolated_penalty *= 1.5 
            
            score += isolated_penalty
    
    white_passed_pawns = []
    black_passed_pawns = []
    
    for col in range(8):
        passed_rank = None
        for row in range(7, -1, -1):  
            if gs.board[row][col] == 'wp':
                passed_rank = row
                break
        
        if passed_rank is not None:
            is_passed = True
            for r in range(passed_rank-1, -1, -1):  
                for c in range(max(0, col-1), min(8, col+2)): 
                    if gs.board[r][c] == 'bp':
                        is_passed = False
                        break
                if not is_passed:
                    break
            
            if is_passed:
                white_passed_pawns.append((passed_rank, col))
        
        passed_rank = None
        for row in range(8):  
            if gs.board[row][col] == 'bp':
                passed_rank = row
                break
        
        if passed_rank is not None:
            is_passed = True
            for r in range(passed_rank+1, 8):  
                for c in range(max(0, col-1), min(8, col+2)): 
                    if gs.board[r][c] == 'wp':
                        is_passed = False
                        break
                if not is_passed:
                    break
            
            if is_passed:
                black_passed_pawns.append((passed_rank, col))
    
    for rank, file in white_passed_pawns:
        distance_to_promotion = rank
        promotion_value = (7 - distance_to_promotion) * 0.2
        score += 0.5 + promotion_value
        
        if rank <= 2: 
            score += (3 - rank) * 0.3
    
    for rank, file in black_passed_pawns:
        distance_to_promotion = 7 - rank
        promotion_value = (7 - distance_to_promotion) * 0.2
        score -= 0.5 + promotion_value
        
        if rank >= 5:  
            score -= (rank - 4) * 0.3
    
    totalAttacks = gs.white_attacks['total'] if gs.whiteToMove else gs.black_attacks['total']
    totalDefends = gs.white_defends['total'] if gs.whiteToMove else gs.black_defends['total']

    if gs.whiteToMove:
        score += totalAttacks * 0.15 + totalDefends * 0.1
    else:
        score -= totalAttacks * 0.15 + totalDefends * 0.1
    
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != '--':
                piecePositionScore = 0
                if square[1] != 'K':
                    if square[1] == 'p':
                        piecePositionScore = piecePositionScores[square][row][col]
                    else:
                        piecePositionScore = piecePositionScores[square[1]][row][col]
                
                pin_maintainer_bonus = 0
                if (row, col) in [attack['attacker'] for attack in attacking_pinned_pieces]:
                    pin_maintainer_bonus = 0.5  
                
                piece_value = pieceScores[square[1]]
                
                material_factor = 1.0 
                if square[0] == 'w':
                   
                    if gs.whiteToMove and len(black_pieces_under_attack) > 0:
                       
                        material_factor = 0.8
                    
                    
                    if len(white_passed_pawns) > 0 and any(rank <= 2 for rank, _ in white_passed_pawns):
                        
                        material_factor = 0.85
                        
                    score += piece_value * material_factor + piecePositionScore * 0.1 + pin_maintainer_bonus
                
                elif square[0] == 'b':
                    
                    if not gs.whiteToMove and len(white_pieces_under_attack) > 0:
                        
                        material_factor = 0.8
                    
                    
                    if len(black_passed_pawns) > 0 and any(rank >= 5 for rank, _ in black_passed_pawns):
                        
                        material_factor = 0.85
                        
                    score -= piece_value * material_factor + piecePositionScore * 0.1 + pin_maintainer_bonus
                
               
                if (row, col) in pinned_pieces:
                    pin_info = pinned_pieces_info[(row, col)]
                    
                    pin_penalty = piece_value * 0.15  
                    
                    if pin_info['is_king_pin']:
                        pin_penalty *= 1.3
                    
                    if square[0] == 'w':
                        score -= pin_penalty
                    else:
                        score += pin_penalty
    
    return score


def getAttackersOfSquare(self, row, col, color):
    attackers = []
    for r in range(8):
        for c in range(8):
            piece = self.board[r][c]
            if piece != '--' and piece[0] == color:
                attack_squares = self.getPieceAttackSquares(r, c)
                if (row, col) in attack_squares:
                    attackers.append((r, c))
    return attackers


def isSquareDefended(self, row, col, by_white):
    defenders = self.getAttackersOfSquare(row, col, 'w' if by_white else 'b')
    return len(defenders) > 0


def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScores[square[1]]
            elif square[0] == 'b':
                score -= pieceScores[square[1]]

    return score


def record_move_to_opening_book(gs, move, quality=1):
    if len(gs.moveLog) <= MAX_BOOK_MOVE:
        position_hash = opening_book.add_position(gs.board, move, quality)
        print(f"Added position {position_hash} to opening book")
        opening_book.save_book()