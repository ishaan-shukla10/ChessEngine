import random
from openingbook import OpeningBook

pieceScores = {'K': 0, 'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}

knightScores = [[0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 2, 2, 2, 2, 1, 0],
                [0, 1, 2, 3, 3, 2, 1, 0],
                [0, 1, 2, 3, 3, 2, 1, 0],
                [0, 1, 2, 2, 2, 2, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0]]


bishopScores = [[0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 2, 2, 2, 2, 1, 0],
                [0, 1, 2, 3, 3, 2, 1, 0],
                [0, 1, 2, 3, 3, 2, 1, 0],
                [0, 1, 2, 2, 2, 2, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0]]

queenScores = [[0 for _ in range(8)] for _ in range(8)]

rookScores = [[0 for _ in range(8)] for _ in range(8)]

whitePawnScores = [[8, 8, 8, 8, 8, 8, 8, 8], 
                   [5, 5, 5, 5, 5, 5, 5, 5],
                   [3, 3, 4, 4, 4, 4, 3, 3],
                   [2, 2, 3, 4, 4, 3, 2, 2],
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [1, 1, 1, 2, 2, 1, 1, 1],
                   [1, 1, 1, 0, 0, 1, 1, 1], 
                   [0, 0, 0, 0, 0, 0, 0, 0]]

blackPawnScores = [[0, 0, 0, 0, 0, 0, 0, 0],
                   [1, 1, 1, 0, 0, 1, 1, 1],
                   [1, 1, 1, 2, 2, 1, 1, 1], 
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [2, 2, 3, 4, 4, 3, 2, 2],
                   [3, 3, 4, 4, 4, 4, 3, 3],
                   [5, 5, 5, 5, 5, 5, 5, 5],
                   [8, 8, 8, 8, 8, 8, 8, 8]]

piecePositionScores = {'N': knightScores, 'Q': queenScores, 'R': rookScores, 'B': bishopScores, 'bp': blackPawnScores, 
                       'wp': whitePawnScores}

CHECKMATE = 1000
STALEMATE = 0
DEPTH = 3



opening_book = OpeningBook("opening_books/bogo.json")
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
                                            gs.enPassantPossible[1] if gs.enPassantPossible else -1)
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
    
    # Add development evaluation
    development_score = evaluateDevelopment(gs)
    score += development_score
    
    # Add rook positioning evaluation
    rook_positioning_score = evaluateRookPositioning(gs)
    score += rook_positioning_score
    
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

    totalAttacks = gs.white_attacks['total'] if gs.whiteToMove else gs.black_attacks['total']
    totalDefends = gs.white_defends['total'] if gs.whiteToMove else gs.black_defends['total']

    if gs.whiteToMove:
        score += totalAttacks * 0.08 + totalDefends * 0.05
    else:
        score -= totalAttacks * 0.08 + totalDefends * 0.05

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
                    pin_maintainer_bonus = 0.4  
                
                piece_value = pieceScores[square[1]]
                if square[0] == 'w':
                    score += piece_value + piecePositionScore * 0.05 + pin_maintainer_bonus
                elif square[0] == 'b':
                    score -= piece_value + piecePositionScore * 0.05 + pin_maintainer_bonus
                
                if (row, col) in pinned_pieces:
                    pin_info = pinned_pieces_info[(row, col)]
                    
                    pin_penalty = piece_value * 0.1  
                    
                    if pin_info['is_king_pin']:
                        pin_penalty *= 1.2
                    
                    if square[0] == 'w':
                        score -= pin_penalty
                    else:
                        score += pin_penalty

    if gs.num_moves > 15:
        if not gs.blackHasCastled:
            score += 2 ** (gs.num_moves - 15)
        if not gs.whiteHasCastled:
            score -= 2 ** (gs.num_moves - 15)
    
    return score

def evaluateDevelopment(gs):
    """
    Evaluates piece development in the opening.
    Penalizes undeveloped minor pieces in the opening phase and rewards proper development.
    """
    if gs.num_moves > 20:  # Only apply in opening/early middlegame phase
        return 0
    
    development_score = 0
    
    # Scale development weight based on game phase
    if gs.num_moves <= 10:  # Early opening
        development_weight = 4.0 - gs.num_moves * 0.2  # Starts very high and decreases
    else:
        development_weight = max(1.0, 3.0 - gs.num_moves * 0.1)
    
    # Check white minor pieces
    # Knights starting at b1 and g1, Bishops at c1 and f1
    white_minor_starting_positions = [(7, 1), (7, 6), (7, 2), (7, 5)]
    white_undeveloped = 0
    
    for pos in white_minor_starting_positions:
        piece = gs.board[pos[0]][pos[1]]
        if (piece == 'wN' and pos in [(7, 1), (7, 6)]) or (piece == 'wB' and pos in [(7, 2), (7, 5)]):
            white_undeveloped += 1
    
    # Check black minor pieces
    # Knights starting at b8 and g8, Bishops at c8 and f8
    black_minor_starting_positions = [(0, 1), (0, 6), (0, 2), (0, 5)]
    black_undeveloped = 0
    
    for pos in black_minor_starting_positions:
        piece = gs.board[pos[0]][pos[1]]
        if (piece == 'bN' and pos in [(0, 1), (0, 6)]) or (piece == 'bB' and pos in [(0, 2), (0, 5)]):
            black_undeveloped += 1
    
    # Apply penalties for undeveloped pieces
    development_penalty = 0.5 * development_weight  # 0.5 points per undeveloped piece, scaled by game phase
    development_score = (black_undeveloped - white_undeveloped) * development_penalty
    
    # Check if knights and bishops are developed to good squares
    good_development_bonus = 0.2 * development_weight
    
    # Good knight development squares
    white_good_knight_squares = [(5, 2), (5, 5), (4, 3), (4, 4), (5, 3), (5, 4)]
    black_good_knight_squares = [(2, 2), (2, 5), (3, 3), (3, 4), (2, 3), (2, 4)]
    
    # Good bishop development squares
    white_good_bishop_squares = [(6, 2), (6, 5), (5, 1), (5, 6), (4, 2), (4, 5)]
    black_good_bishop_squares = [(1, 2), (1, 5), (2, 1), (2, 6), (3, 2), (3, 5)]
    
    # Count well-developed pieces
    white_well_developed = 0
    black_well_developed = 0
    
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece == 'wN' and (row, col) in white_good_knight_squares:
                white_well_developed += 1
            elif piece == 'wB' and (row, col) in white_good_bishop_squares:
                white_well_developed += 1
            elif piece == 'bN' and (row, col) in black_good_knight_squares:
                black_well_developed += 1
            elif piece == 'bB' and (row, col) in black_good_bishop_squares:
                black_well_developed += 1
    
    development_score += (white_well_developed - black_well_developed) * good_development_bonus
    
    # Penalize moving the same piece multiple times in the opening
    if gs.num_moves < 12 and hasattr(gs, 'moveLog') and len(gs.moveLog) > 0:
        piece_moves_count = {}
        for move in gs.moveLog:
            piece_key = f"{move.pieceMoved}_{move.startRow}_{move.startCol}"
            if piece_key not in piece_moves_count:
                piece_moves_count[piece_key] = 0
            piece_moves_count[piece_key] += 1
            
            # Penalize moving the same piece multiple times early
            if piece_moves_count[piece_key] > 1 and move.pieceMoved[1] in ['N', 'B', 'Q']:
                if move.pieceMoved[0] == 'w':
                    development_score -= 0.3 * development_weight
                else:
                    development_score += 0.3 * development_weight
    
    # Bonus for castling (already handled elsewhere, but we could add extra incentive)
    if hasattr(gs, 'whiteHasCastled') and gs.whiteHasCastled:
        development_score += 0.5 * development_weight
    if hasattr(gs, 'blackHasCastled') and gs.blackHasCastled:
        development_score -= 0.5 * development_weight
    
    return development_score

def evaluatePassedPawns(gs):
    """
    Gives bonus points for passed pawns that have a clear path to promotion.
    A passed pawn has no opposing pawns in front of it or on adjacent files.
    Value scales with game phase and advancement.
    """
    score = 0
    
    # Scale based on game phase
    if gs.num_moves < 10:
        phase_multiplier = 0.4  # Less important in opening
    elif gs.num_moves < 25:
        phase_multiplier = 0.8  # Growing importance in middlegame
    else:
        phase_multiplier = 1.5  # Very important in endgame
    
    # Check for white passed pawns
    for col in range(8):
        for row in range(6, 0, -1):  # From rank 2 to 7
            if gs.board[row][col] == 'wp':
                is_passed = True
                
                # Check if there are black pawns that can block
                for check_row in range(row-1, -1, -1):
                    for check_col in range(max(0, col-1), min(8, col+2)):
                        if gs.board[check_row][check_col] == 'bp':
                            is_passed = False
                            break
                    if not is_passed:
                        break
                
                if is_passed:
                    # Base bonus for a passed pawn
                    base_bonus = 0.5
                    
                    # The further advanced the pawn, the higher the bonus (exponential)
                    rank = 7 - row  # Convert to chess rank (0-7)
                    advancement_bonus = 0.2 * (2 ** (rank - 1))  # Exponential growth for advancement
                    
                    # Additional bonus if the pawn is protected
                    is_protected = False
                    for check_row in range(max(0, row-1), min(8, row+2)):
                        for check_col in range(max(0, col-1), min(8, col+2)):
                            if (check_row != row or check_col != col) and gs.board[check_row][check_col][0] == 'w':
                                is_protected = True
                                break
                    
                    protection_bonus = 0.2 if is_protected else 0
                    
                    # Calculate total bonus
                    total_bonus = (base_bonus + advancement_bonus + protection_bonus) * phase_multiplier
                    score += total_bonus
                
                break  # Only check the most advanced pawn in each file
    
    # Check for black passed pawns
    for col in range(8):
        for row in range(1, 7):  # From rank 7 to 2
            if gs.board[row][col] == 'bp':
                is_passed = True
                
                # Check if there are white pawns that can block
                for check_row in range(row+1, 8):
                    for check_col in range(max(0, col-1), min(8, col+2)):
                        if gs.board[check_row][check_col] == 'wp':
                            is_passed = False
                            break
                    if not is_passed:
                        break
                
                if is_passed:
                    # Base bonus for a passed pawn
                    base_bonus = 0.5
                    
                    # The further advanced the pawn, the higher the bonus (exponential)
                    rank = row  # Convert to chess rank (0-7)
                    advancement_bonus = 0.2 * (2 ** (rank - 1))  # Exponential growth for advancement
                    
                    # Additional bonus if the pawn is protected
                    is_protected = False
                    for check_row in range(max(0, row-1), min(8, row+2)):
                        for check_col in range(max(0, col-1), min(8, col+2)):
                            if (check_row != row or check_col != col) and gs.board[check_row][check_col][0] == 'b':
                                is_protected = True
                                break
                    
                    protection_bonus = 0.2 if is_protected else 0
                    
                    # Calculate total bonus
                    total_bonus = (base_bonus + advancement_bonus + protection_bonus) * phase_multiplier
                    score -= total_bonus
                
                break  # Only check the most advanced pawn in each file
    
    return score

def evaluateCenterPawnStructure(gs):
    """
    Evaluates center pawn structure, focusing on center control, 
    pawn chains, and proper development of the pawn structure.
    """
    score = 0
    
    # Scale based on game phase - more important in opening and early middlegame
    if gs.num_moves < 10:
        phase_multiplier = 1.5
    elif gs.num_moves < 25:
        phase_multiplier = 1.0
    else:
        phase_multiplier = 0.7
    
    # 1. Evaluate center control with pawns (d4, e4, d5, e5)
    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    
    for square in center_squares:
        row, col = square
        if gs.board[row][col] == 'wp':
            score += 0.4  # White pawn controlling center
        elif gs.board[row][col] == 'bp':
            score -= 0.4  # Black pawn controlling center
    
    # 2. Evaluate extended center control (c3-c6, f3-f6, d3-d6, e3-e6)
    extended_center = [
        (2, 2), (2, 3), (2, 4), (2, 5),  # Ranks 3
        (5, 2), (5, 3), (5, 4), (5, 5)   # Ranks 6
    ]
    
    for square in extended_center:
        row, col = square
        if gs.board[row][col] == 'wp':
            score += 0.2  # White pawn in extended center
        elif gs.board[row][col] == 'bp':
            score -= 0.2  # Black pawn in extended center
    
    # 3. Evaluate pawn chains and structure
    # Check for white pawn chains
    white_chain_bonus = evaluatePawnChains(gs, 'w')
    black_chain_bonus = evaluatePawnChains(gs, 'b')
    
    score += white_chain_bonus - black_chain_bonus
    
    # 4. Penalize isolated and doubled pawns
    white_structure_penalty = evaluatePawnStructureWeaknesses(gs, 'w')
    black_structure_penalty = evaluatePawnStructureWeaknesses(gs, 'b')
    
    score -= white_structure_penalty - black_structure_penalty
    
    # 5. Penalize excessive pawn movement in opening
    if gs.num_moves < 10:
        white_moved_pawns = 0
        black_moved_pawns = 0
        
        # Count pawns that have moved from their starting positions
        for col in range(8):
            if gs.board[6][col] != 'wp':
                white_moved_pawns += 1
            if gs.board[1][col] != 'bp':
                black_moved_pawns += 1
        
        # Penalize moving more than 3 pawns in the opening
        if white_moved_pawns > 3:
            score -= (white_moved_pawns - 3) * 0.2
        if black_moved_pawns > 3:
            score += (black_moved_pawns - 3) * 0.2
    
    return score * phase_multiplier

def evaluatePawnChains(gs, color):
    """
    Helper function to evaluate pawn chains for a specific color.
    A pawn chain is where pawns protect each other diagonally.
    """
    chain_bonus = 0
    color_char = color  # 'w' or 'b'
    pawn_char = color_char + 'p'
    
    # Direction for checking diagonal protection (up-right and up-left)
    if color_char == 'w':
        protection_directions = [(-1, -1), (-1, 1)]  # White pawns protect diagonally up
    else:
        protection_directions = [(1, -1), (1, 1)]    # Black pawns protect diagonally down
    
    # Check for all pawns
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == pawn_char:
                # Check if this pawn is protected by another pawn
                is_protected = False
                for d_row, d_col in protection_directions:
                    protect_row, protect_col = row + d_row, col + d_col
                    if 0 <= protect_row < 8 and 0 <= protect_col < 8:
                        if gs.board[protect_row][protect_col] == pawn_char:
                            is_protected = True
                            chain_bonus += 0.1  # Bonus for being part of a chain
                
                # Additional bonus if the pawn is in the center
                if is_protected and 2 <= row <= 5 and 2 <= col <= 5:
                    chain_bonus += 0.1  # Extra bonus for central pawn chains
    
    return chain_bonus

def evaluatePawnStructureWeaknesses(gs, color):
    """
    Helper function to evaluate pawn structure weaknesses (isolated and doubled pawns).
    """
    weakness_penalty = 0
    color_char = color  # 'w' or 'b'
    pawn_char = color_char + 'p'
    
    # Count pawns in each file
    pawns_in_file = [0] * 8
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == pawn_char:
                pawns_in_file[col] += 1
    
    # Check for doubled pawns (more than one pawn in a file)
    for col in range(8):
        if pawns_in_file[col] > 1:
            weakness_penalty += 0.3 * (pawns_in_file[col] - 1)  # Penalty for each doubled pawn
    
    # Check for isolated pawns (no friendly pawns in adjacent files)
    for col in range(8):
        if pawns_in_file[col] > 0:
            has_neighbor = False
            if col > 0 and pawns_in_file[col-1] > 0:
                has_neighbor = True
            if col < 7 and pawns_in_file[col+1] > 0:
                has_neighbor = True
            
            if not has_neighbor:
                weakness_penalty += 0.3 * pawns_in_file[col]  # Penalty for each isolated pawn
    
    return weakness_penalty


def penalizeExcessivePawnMovement(gs):
    if gs.num_moves > 10:
        return 0  # Only apply in opening
        
    penalty = 0
    white_moved_pawns = 0
    black_moved_pawns = 0
    
    # Count pawns that have moved from their starting positions
    for col in range(8):
        if gs.board[6][col] != 'wp':
            white_moved_pawns += 1
        if gs.board[1][col] != 'bp':
            black_moved_pawns += 1
    
    # Penalize moving more than 2-3 pawns in the opening
    if white_moved_pawns > 3:
        penalty -= (white_moved_pawns - 3) * 0.2
    if black_moved_pawns > 3:
        penalty += (black_moved_pawns - 3) * 0.2
        
    return penalty


def evaluateRookPositioning(gs):
    """
    Evaluates rook positioning, giving bonus points for:
    - White rooks on 7th rank (row 1)
    - Black rooks on 2nd rank (row 6)
    """
    rook_score = 0
    rook_seventh_rank_bonus = 0.7  # Substantial bonus for a rook on 7th/2nd rank
    
    # Check white rooks on 7th rank (row 1)
    for col in range(8):
        if gs.board[1][col] == 'wR':
            rook_score += rook_seventh_rank_bonus
    
    # Check black rooks on 2nd rank (row 6)
    for col in range(8):
        if gs.board[6][col] == 'bR':
            rook_score -= rook_seventh_rank_bonus
    
    # Additional bonus for controlling open or semi-open files
    rook_score += evaluateRooksOnOpenFiles(gs)
    
    return rook_score

def evaluateRooksOnOpenFiles(gs):
    """
    Gives bonus points for rooks on open or semi-open files.
    - Open file: No pawns on the file
    - Semi-open file: No friendly pawns on the file
    """
    score = 0
    open_file_bonus = 0.3
    semi_open_file_bonus = 0.15
    
    # Check each file (column)
    for col in range(8):
        white_pawn_in_file = False
        black_pawn_in_file = False
        white_rook_in_file = False
        black_rook_in_file = False
        
        # Check for pawns and rooks in this file
        for row in range(8):
            piece = gs.board[row][col]
            if piece == 'wp':
                white_pawn_in_file = True
            elif piece == 'bp':
                black_pawn_in_file = True
            elif piece == 'wR':
                white_rook_in_file = True
            elif piece == 'bR':
                black_rook_in_file = True
        
        # Apply bonuses for rooks on open or semi-open files
        if white_rook_in_file:
            if not white_pawn_in_file and not black_pawn_in_file:  # Open file
                score += open_file_bonus
            elif not white_pawn_in_file:  # Semi-open file
                score += semi_open_file_bonus
        
        if black_rook_in_file:
            if not white_pawn_in_file and not black_pawn_in_file:  # Open file
                score -= open_file_bonus
            elif not black_pawn_in_file:  # Semi-open file
                score -= semi_open_file_bonus
    
    return score



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