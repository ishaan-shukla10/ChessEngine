import random
from openingbook import OpeningBook

# Piece values - pretty standard stuff
pieceScores = {'K': 0, 'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}

knightScores = [[0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 2, 2, 2, 2, 1, 0],
                [0, 1, 2, 3, 3, 2, 1, 0],
                [0, 1, 2, 3, 3, 2, 1, 0],
                [0, 1, 2, 2, 2, 2, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0]]


# Bishops also better in center, but some tweaking might be required.
bishopScores = [[0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 2, 2, 2, 2, 1, 0],
                [0, 1, 2, 3, 3, 2, 1, 0],
                [0, 1, 2, 3, 3, 2, 1, 0],
                [0, 1, 2, 2, 2, 2, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0]]

# Cannot figure out best positions on board for queens and rooks
queenScores = [[0 for _ in range(8)] for _ in range(8)]
rookScores = [[0 for _ in range(8)] for _ in range(8)]

# White pawns get better as they advance
# Extra points for central pawns too
whitePawnScores = [[8, 8, 8, 8, 8, 8, 8, 8], 
                   [5, 5, 5, 5, 5, 5, 5, 5],
                   [3, 3, 4, 4, 4, 4, 3, 3],
                   [2, 2, 3, 4, 4, 3, 2, 2],
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [1, 1, 1, 2, 2, 1, 1, 1],
                   [1, 1, 1, 0, 0, 1, 1, 1], 
                   [0, 0, 0, 0, 0, 0, 0, 0]]

# Same idea for black pawns, just flipped
blackPawnScores = [[0, 0, 0, 0, 0, 0, 0, 0],
                   [1, 1, 1, 0, 0, 1, 1, 1],
                   [1, 1, 1, 2, 2, 1, 1, 1], 
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [2, 2, 3, 4, 4, 3, 2, 2],
                   [3, 3, 4, 4, 4, 4, 3, 3],
                   [5, 5, 5, 5, 5, 5, 5, 5],
                   [8, 8, 8, 8, 8, 8, 8, 8]]

# Bundle them all together for easier access
piecePositionScores = {'N': knightScores, 'Q': queenScores, 'R': rookScores, 'B': bishopScores, 'bp': blackPawnScores, 
                       'wp': whitePawnScores}

# Constants - might experiment with deeper search later if I can optimize this more
CHECKMATE = 1000
STALEMATE = 0
DEPTH = 2 


# Set up our opening book - Can choose opening based on your preferences
opening_book = OpeningBook("opening_books/carokann.json")
USE_OPENING_BOOK = True  # Set to False if you want pure engine calculation
MAX_BOOK_MOVE = 10  # How deep into the game we'll use the book

def findRandomMove(validMoves):
    # Not using this much, but nice for testing or introducing randomness
    return validMoves[random.randint(0, len(validMoves)-1)]


def findGreedyMove(gs, validMoves):
    # Simple 2-ply greedy search - looks for material gain
    # Not as sophisticated as the full minimax but way faster
    turnMultiplier = 1 if gs.whiteToMove else -1
    bestPlayerMove = None
    opponentMinMaxScore = CHECKMATE
    random.shuffle(validMoves)  # Avoid predictable tie-breaking

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
    
    # Try to use opening book first if we're still in the opening
    if USE_OPENING_BOOK and len(gs.moveLog) < 2 * MAX_BOOK_MOVE:
        book_move = opening_book.get_book_move(gs.board, gs.whiteToMove, gs.currentCastlingRights, 
                                            gs.enPassantPossible[1] if gs.enPassantPossible else -1)
        if book_move:
            print("Using book move:", book_move.getChessNotation())
            returnQueue.put(book_move)
            return
    
    # Shuffle moves for variety when scores are equal
    random.shuffle(validMoves)
    
    # This pin detection was a huge improvement! Really helps avoid blunders
    current_pins = gs.detectAllPins()
    ordered_moves = gs.orderMoves(validMoves)  # Move ordering makes alpha-beta way more effective

    # The main search function - alpha-beta pruning with negamax
    findMoveNegaMaxAlphaBeta(gs, ordered_moves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)

    returnQueue.put(nextMove) 


def moveTargetsPinnedPiece(gs, move, pins):
    # Bonus for targeting pinned pieces - these are often free captures
    pinned_squares = [(pin[0], pin[1]) for pin in pins]

    if (move.endRow, move.endCol) in pinned_squares:
        target_piece = gs.board[move.endRow][move.endCol]
        if target_piece[1] != 'p':  # Pawns aren't worth as much
            return pieceScores[target_piece[1]]
    
    return 0


def findMoveMinMax(gs, validMoves, depth, whiteToMove):
    # Traditional minimax - this is actually pretty slow compared to negamax
    # I'm keeping it for reference, but not using it anymore
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
    # More elegant than minimax, but still no pruning
    # I've mostly switched to the alpha-beta version below
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
    # This is the good stuff - probably 10x faster than plain minimax
    # Alpha-beta pruning makes a huge difference for chess
    global nextMove

    if depth == 0:
        return turnMultiplier * scoreBoard(gs)
    
    # Only order moves at shallower depths - ordering at every level is too expensive
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
                # Debug info to help understand what's happening with attacks
                print("White attacks, ", gs.white_attacks)
                print("White defends, ", gs.white_defends)
                print("Black attacks, ", gs.black_attacks)
                print("Black defends, ", gs.black_defends)
        
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break  # This is the pruning part - huge speedup!

    return maxScore


# This fork detection was a gamechanger! My engine plays much more tactically now
def detectForks(gs, color):
    """
    Detects forks for all piece types - situations where one piece attacks 
    two or more valuable pieces simultaneously.
    
    Args:
        gs: GameState object
        color: 'w' for white, 'b' for black
        
    Returns:
        A list of dictionaries containing information about each fork.
    """
    forks = []
    attacking_color = color
    defending_color = 'b' if color == 'w' else 'w'
    
    # Get all pieces of the attacking color
    attacking_pieces = []
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece != '--' and piece[0] == attacking_color:
                attacking_pieces.append((row, col, piece))
    
    # For each attacking piece, check if it attacks multiple valuable pieces
    for attacker_row, attacker_col, attacker in attacking_pieces:
        # Get attack squares based on piece type
        if attacker[1] == 'p':
            attack_squares = []
            # Pawns attack diagonally
            if attacker[0] == 'w':
                if attacker_row > 0:
                    if attacker_col > 0:
                        attack_squares.append((attacker_row - 1, attacker_col - 1))
                    if attacker_col < 7:
                        attack_squares.append((attacker_row - 1, attacker_col + 1))
            else:  # Black pawn
                if attacker_row < 7:
                    if attacker_col > 0:
                        attack_squares.append((attacker_row + 1, attacker_col - 1))
                    if attacker_col < 7:
                        attack_squares.append((attacker_row + 1, attacker_col + 1))
        else:
            # For other pieces, use the existing attack square function
            attack_squares = gs.getPieceAttackSquares(attacker_row, attacker_col)
        
        if not attack_squares:
            continue
            
        # Find valuable targets being attacked
        valuable_targets = []
        for target_row, target_col in attack_squares:
            target = gs.board[target_row][target_col]
            # Only consider opponent's pieces as targets
            if target != '--' and target[0] == defending_color:
                # Consider piece value - kings are always valuable
                if target[1] == 'K' or pieceScores[target[1]] >= 3:  # Only consider valuable pieces (≥ knight)
                    valuable_targets.append((target_row, target_col, target))
        
        # If attacking multiple valuable pieces, it's a fork
        if len(valuable_targets) >= 2:
            # Calculate fork value based on the pieces being attacked
            fork_value = sum(pieceScores[target[1]] for _, _, target in valuable_targets)
            
            # Add piece type to the fork info
            forks.append({
                'attacker': (attacker_row, attacker_col, attacker),
                'targets': valuable_targets,
                'value': fork_value,
                'piece_type': attacker[1]
            })
    
    return forks


def evaluateForkPotential(gs):
    """
    Evaluates potential fork positions for all piece types based on mobility
    and proximity to opponent's valuable pieces.
    
    Returns:
        A score reflecting fork potential, positive for white advantage
    """
    fork_potential_score = 0
    
    # Dictionary for piece mobility - how many squares they can potentially attack
    piece_mobility = {
        'N': evaluate_knight_fork_potential(gs, 'w', 'b'),
        'B': evaluate_bishop_fork_potential(gs, 'w', 'b'),
        'R': evaluate_rook_fork_potential(gs, 'w', 'b'),
        'Q': evaluate_queen_fork_potential(gs, 'w', 'b'),
        'p': evaluate_pawn_fork_potential(gs, 'w', 'b')
    }
    
    # Add up all potential scores for white pieces
    for piece_type, potential in piece_mobility.items():
        fork_potential_score += potential
    
    # Repeat for black pieces
    black_piece_mobility = {
        'N': evaluate_knight_fork_potential(gs, 'b', 'w'),
        'B': evaluate_bishop_fork_potential(gs, 'b', 'w'),
        'R': evaluate_rook_fork_potential(gs, 'b', 'w'),
        'Q': evaluate_queen_fork_potential(gs, 'b', 'w'),
        'p': evaluate_pawn_fork_potential(gs, 'b', 'w')
    }
    
    # Subtract black potential from white potential
    for piece_type, potential in black_piece_mobility.items():
        fork_potential_score -= potential
    
    return fork_potential_score

def evaluate_piece_fork_potentials(gs, attacking_color, defending_color):
    """
    Helper function that combines all piece-specific fork potential functions.
    
    Args:
        gs: GameState object
        attacking_color: Color of the attacking pieces ('w' or 'b')
        defending_color: Color of the defending pieces ('w' or 'b')
        
    Returns:
        Dictionary containing fork potential for each piece type
    """
    return {
        'N': evaluate_knight_fork_potential(gs, attacking_color, defending_color),
        'B': evaluate_bishop_fork_potential(gs, attacking_color, defending_color),
        'R': evaluate_rook_fork_potential(gs, attacking_color, defending_color),
        'Q': evaluate_queen_fork_potential(gs, attacking_color, defending_color),
        'p': evaluate_pawn_fork_potential(gs, attacking_color, defending_color)
    }


# Helper functions for each piece type
def evaluate_knight_fork_potential(gs, attacking_color, defending_color):
    """Evaluates knight fork potential"""
    potential_score = 0
    
    # Find all knights of the attacking color
    knights = []
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == attacking_color + 'N':
                knights.append((row, col))
    
    # Find all valuable pieces of the defending color
    valuable_pieces = []
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece != '--' and piece[0] == defending_color and (piece[1] == 'K' or pieceScores[piece[1]] >= 3):
                valuable_pieces.append((row, col, piece))
    
    # For each knight, calculate fork potential
    for knight_row, knight_col in knights:
        potential_targets = []
        
        for val_row, val_col, val_piece in valuable_pieces:
            row_diff = abs(knight_row - val_row)
            col_diff = abs(knight_col - val_col)
            
            # Knight can directly attack or reach in 2 moves
            if (row_diff == 1 and col_diff == 2) or (row_diff == 2 and col_diff == 1):
                potential_targets.append((val_row, val_col, val_piece, 1.0))  # 1.0 = direct attack
            elif row_diff + col_diff <= 5:
                potential_targets.append((val_row, val_col, val_piece, 0.3))  # 0.3 = can reach in 2-3 moves
        
        # Calculate potential score if knight can attack multiple targets
        if len(potential_targets) >= 2:
            # Value decreases with more pieces to avoid overvaluation
            proximity_score = sum(0.1 * pieceScores[piece[1]] * weight for _, _, piece, weight in potential_targets)
            potential_score += proximity_score * 1.2  # Knights are good at forking
    
    return potential_score


def evaluate_bishop_fork_potential(gs, attacking_color, defending_color):
    """Evaluates bishop fork potential"""
    potential_score = 0
    
    # Find all bishops of the attacking color
    bishops = []
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == attacking_color + 'B':
                bishops.append((row, col))
    
    # Find all valuable pieces of the defending color
    valuable_pieces = []
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece != '--' and piece[0] == defending_color and (piece[1] == 'K' or pieceScores[piece[1]] >= 3):
                valuable_pieces.append((row, col, piece))
    
    # For each bishop, calculate fork potential
    for bishop_row, bishop_col in bishops:
        potential_targets = []
        
        for val_row, val_col, val_piece in valuable_pieces:
            row_diff = abs(bishop_row - val_row)
            col_diff = abs(bishop_col - val_col)
            
            # Bishop attacks diagonally
            if row_diff == col_diff:
                # Check if path is clear
                is_clear = True
                row_step = 1 if val_row > bishop_row else -1
                col_step = 1 if val_col > bishop_col else -1
                
                check_row, check_col = bishop_row + row_step, bishop_col + col_step
                while check_row != val_row and check_col != val_col:
                    if gs.board[check_row][check_col] != '--':
                        is_clear = False
                        break
                    check_row += row_step
                    check_col += col_step
                
                if is_clear:
                    potential_targets.append((val_row, val_col, val_piece, 1.0))  # 1.0 = direct attack
            elif (row_diff + col_diff) % 2 == 0 and row_diff + col_diff <= 6:
                # Can potentially reach in a couple moves
                potential_targets.append((val_row, val_col, val_piece, 0.2))
        
        # Calculate potential score if bishop can attack multiple targets
        if len(potential_targets) >= 2:
            proximity_score = sum(0.1 * pieceScores[piece[1]] * weight for _, _, piece, weight in potential_targets)
            potential_score += proximity_score * 1.0  # Standard weight for bishops
    
    return potential_score


def evaluate_rook_fork_potential(gs, attacking_color, defending_color):
    """Evaluates rook fork potential"""
    potential_score = 0
    
    # Find all rooks of the attacking color
    rooks = []
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == attacking_color + 'R':
                rooks.append((row, col))
    
    # Find all valuable pieces of the defending color
    valuable_pieces = []
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece != '--' and piece[0] == defending_color and (piece[1] == 'K' or pieceScores[piece[1]] >= 3):
                valuable_pieces.append((row, col, piece))
    
    # For each rook, calculate fork potential
    for rook_row, rook_col in rooks:
        potential_targets = []
        
        for val_row, val_col, val_piece in valuable_pieces:
            # Rook attacks along ranks and files
            if rook_row == val_row or rook_col == val_col:
                # Check if path is clear
                is_clear = True
                row_step = 0 if rook_row == val_row else (1 if val_row > rook_row else -1)
                col_step = 0 if rook_col == val_col else (1 if val_col > rook_col else -1)
                
                check_row, check_col = rook_row + row_step, rook_col + col_step
                while check_row != val_row or check_col != val_col:
                    if gs.board[check_row][check_col] != '--':
                        is_clear = False
                        break
                    check_row += row_step
                    check_col += col_step
                
                if is_clear:
                    potential_targets.append((val_row, val_col, val_piece, 1.0))  # 1.0 = direct attack
            elif abs(rook_row - val_row) + abs(rook_col - val_col) <= 4:
                # Can potentially reach in a couple moves
                potential_targets.append((val_row, val_col, val_piece, 0.15))
        
        # Calculate potential score if rook can attack multiple targets
        if len(potential_targets) >= 2:
            proximity_score = sum(0.1 * pieceScores[piece[1]] * weight for _, _, piece, weight in potential_targets)
            potential_score += proximity_score * 0.9  # Slightly lower weight for rooks
    
    return potential_score


def evaluate_queen_fork_potential(gs, attacking_color, defending_color):
    """Evaluates queen fork potential"""
    potential_score = 0
    
    # Find all queens of the attacking color
    queens = []
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == attacking_color + 'Q':
                queens.append((row, col))
    
    # Find all valuable pieces of the defending color
    valuable_pieces = []
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece != '--' and piece[0] == defending_color and (piece[1] == 'K' or pieceScores[piece[1]] >= 3):
                valuable_pieces.append((row, col, piece))
    
    # For each queen, calculate fork potential
    for queen_row, queen_col in queens:
        potential_targets = []
        
        for val_row, val_col, val_piece in valuable_pieces:
            row_diff = abs(queen_row - val_row)
            col_diff = abs(queen_col - val_col)
            
            # Queen attacks along diagonals, ranks, and files
            is_diagonal = row_diff == col_diff
            is_straight = queen_row == val_row or queen_col == val_col
            
            if is_diagonal or is_straight:
                # Check if path is clear
                is_clear = True
                row_step = 0
                if queen_row != val_row:
                    row_step = 1 if val_row > queen_row else -1
                
                col_step = 0
                if queen_col != val_col:
                    col_step = 1 if val_col > queen_col else -1
                
                check_row, check_col = queen_row + row_step, queen_col + col_step
                while check_row != val_row or check_col != val_col:
                    if gs.board[check_row][check_col] != '--':
                        is_clear = False
                        break
                    check_row += row_step
                    check_col += col_step
                
                if is_clear:
                    potential_targets.append((val_row, val_col, val_piece, 1.0))  # 1.0 = direct attack
            elif row_diff + col_diff <= 5:
                # Can potentially reach in a couple moves
                potential_targets.append((val_row, val_col, val_piece, 0.1))
        
        # Calculate potential score if queen can attack multiple targets
        if len(potential_targets) >= 2:
            proximity_score = sum(0.1 * pieceScores[piece[1]] * weight for _, _, piece, weight in potential_targets)
            # Lower weight for queens because using your queen for forks isn't always smart
            # Better to use minor pieces usually and keep queen safe
            potential_score += proximity_score * 0.7  # Lower weight for queens
    
    return potential_score


def evaluate_pawn_fork_potential(gs, attacking_color, defending_color):
    """Evaluates pawn fork potential"""
    potential_score = 0
    
    # Find all pawns of the attacking color
    pawns = []
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == attacking_color + 'p':
                pawns.append((row, col))
    
    # Find all valuable pieces of the defending color
    valuable_pieces = []
    for row in range(8):
        for col in range(8):
            piece = gs.board[row][col]
            if piece != '--' and piece[0] == defending_color and (piece[1] == 'K' or pieceScores[piece[1]] >= 3):
                valuable_pieces.append((row, col, piece))
    
    # For each pawn, calculate fork potential
    for pawn_row, pawn_col in pawns:
        potential_targets = []
        
        for val_row, val_col, val_piece in valuable_pieces:
            # Pawns attack diagonally forward
            if attacking_color == 'w':
                # White pawn attacks diagonally forward
                if pawn_row - val_row == 1 and abs(pawn_col - val_col) == 1:
                    potential_targets.append((val_row, val_col, val_piece, 1.0))  # 1.0 = direct attack
                elif pawn_row - val_row <= 3 and abs(pawn_col - val_col) <= 2:
                    # Could potentially reach in a few moves
                    potential_targets.append((val_row, val_col, val_piece, 0.15))
            else:
                # Black pawn attacks diagonally forward
                if val_row - pawn_row == 1 and abs(pawn_col - val_col) == 1:
                    potential_targets.append((val_row, val_col, val_piece, 1.0))  # 1.0 = direct attack
                elif val_row - pawn_row <= 3 and abs(pawn_col - val_col) <= 2:
                    # Could potentially reach in a few moves
                    potential_targets.append((val_row, val_col, val_piece, 0.15))
        
        # Calculate potential score if pawn can attack multiple targets
        if len(potential_targets) >= 2:
            proximity_score = sum(0.1 * pieceScores[piece[1]] * weight for _, _, piece, weight in potential_targets)
            potential_score += proximity_score * 1.5  # Higher weight for pawns (very valuable forks)
    
    return potential_score


def scoreBoard(gs):
    """
    Main evaluation function that calculates the overall score of the board.
    Positive score favors white, negative score favors black.
    """
    score = 0

    # Check for checkmate or stalemate first
    if gs.checkmate:
        if gs.whiteToMove:
            return -CHECKMATE  # Black wins
        else:
            return CHECKMATE   # White wins
    elif gs.stalemate:
        return STALEMATE  # Draw
    
    # Add positional evaluation for early game piece development
    development_score = evaluateDevelopment(gs)
    score += development_score
    
    # Evaluate rook positioning (rooks on 7th rank, open files, etc)
    rook_positioning_score = evaluateRookPositioning(gs)
    score += rook_positioning_score

    # Detect tactical opportunities - forks for both sides
    white_forks = detectForks(gs, 'w')
    black_forks = detectForks(gs, 'b')

    # Process white forks and add to score
    for fork in white_forks:
        # Base score calculation - more valuable pieces being forked = higher score
        fork_score = 0.5 + (fork['value'] * 0.2)
        
        # Adjust score based on which piece is creating the fork
        # Pawns and knights creating forks are especially valuable
        if fork['piece_type'] == 'p':
            fork_score *= 1.5  # Pawn forks are very valuable
        elif fork['piece_type'] == 'N':
            fork_score *= 1.2  # Knight forks are valuable
        elif fork['piece_type'] == 'B':
            fork_score *= 1.1  # Bishop forks
        elif fork['piece_type'] == 'R':
            fork_score *= 0.9  # Rook forks
        elif fork['piece_type'] == 'Q':
            fork_score *= 0.8  # Queen forks (less optimal use of queen)
        
        # Extra bonus if king is one of the forked pieces
        if any(target[2][1] == 'K' for target in fork['targets']):
            fork_score *= 1.5
        
        score += fork_score

    # Process black forks - same logic but subtract from score
    for fork in black_forks:
        fork_score = 0.5 + (fork['value'] * 0.2)
        
        if fork['piece_type'] == 'p':
            fork_score *= 1.5
        elif fork['piece_type'] == 'N':
            fork_score *= 1.2
        elif fork['piece_type'] == 'B':
            fork_score *= 1.1
        elif fork['piece_type'] == 'R':
            fork_score *= 0.9
        elif fork['piece_type'] == 'Q':
            fork_score *= 0.8
        
        if any(target[2][1] == 'K' for target in fork['targets']):
            fork_score *= 1.5
        
        score -= fork_score

    # Look ahead for potential forks
    fork_potential = evaluateForkPotential(gs)
    score += fork_potential
    
    # Find all pinned pieces on the board
    pins = gs.detectAllPins()
    pinned_pieces = [(pin[0], pin[1]) for pin in pins]

    # Gather info about each pinned piece
    pinned_pieces_info = {}
    for pin in pins:
        row, col = pin[0], pin[1]
        piece = gs.board[row][col]
        is_king_pin = pin[4]  # True if the pin is against the king

        pinned_pieces_info[(row, col)] = {
            'piece': piece,
            'is_king_pin': is_king_pin,
            'direction': (pin[2], pin[3])
        }

    # Find pieces that are attacking pinned pieces
    attacking_pinned_pieces = []
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece != '--':
                # If it's the current player's piece
                if (gs.whiteToMove and piece[0] == 'w') or (not gs.whiteToMove and piece[0] == 'b'):
                    
                    # Get all squares this piece can attack
                    attack_squares = gs.getPieceAttackSquares(r, c)
                    if attack_squares:
                        for square in attack_squares:
                            if square in pinned_pieces:
                                target_piece = gs.board[square[0]][square[1]]
                                
                                # Don't count attacks on pawns (less valuable)
                                if target_piece[1] != 'p':
                                    attacking_pinned_pieces.append({
                                        'attacker': (r, c),
                                        'target': square,
                                        'piece_value': pieceScores[target_piece[1]],
                                        'is_king_pin': pinned_pieces_info[square]['is_king_pin']
                                    })

    # Give bonus points for attacking pinned pieces
    for attack in attacking_pinned_pieces:
        # More valuable pieces give higher bonus when pinned
        pin_bonus = attack['piece_value'] * 0.3  
        
        # Extra bonus for pieces pinned to the king
        if attack['is_king_pin']:
            pin_bonus *= 1.5
            
        if gs.whiteToMove:
            score += pin_bonus
        else:
            score -= pin_bonus
    
    # Check if the opponent is in check, which is a slight advantage
    gs.whiteToMove = not gs.whiteToMove
    if gs.inCheck():
        score += 0.2 if gs.whiteToMove else -0.2
    gs.whiteToMove = not gs.whiteToMove

    # Add attack and defense count bonuses
    # More attacks and defended pieces = better position
    totalAttacks = gs.white_attacks['total'] if gs.whiteToMove else gs.black_attacks['total']
    totalDefends = gs.white_defends['total'] if gs.whiteToMove else gs.black_defends['total']

    if gs.whiteToMove:
        score += totalAttacks * 0.08 + totalDefends * 0.05
    else:
        score -= totalAttacks * 0.08 + totalDefends * 0.05

    # Evaluate each piece on the board based on position and value
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != '--':  # If square is not empty
                piecePositionScore = 0
                # Get positional score (where on board is good for this piece)
                if square[1] != 'K':  # Not a king
                    if square[1] == 'p':  # Pawns have special position tables
                        piecePositionScore = piecePositionScores[square][row][col]
                    else:
                        piecePositionScore = piecePositionScores[square[1]][row][col]
                
                # Bonus for pieces that are maintaining pins
                pin_maintainer_bonus = 0
                if (row, col) in [attack['attacker'] for attack in attacking_pinned_pieces]:
                    pin_maintainer_bonus = 0.4  
                
                # Add piece value + position bonus + pin maintainer bonus
                piece_value = pieceScores[square[1]]
                if square[0] == 'w':
                    score += piece_value + piecePositionScore * 0.05 + pin_maintainer_bonus
                elif square[0] == 'b':
                    score -= piece_value + piecePositionScore * 0.05 + pin_maintainer_bonus
                
                # Apply penalty for being pinned
                if (row, col) in pinned_pieces:
                    pin_info = pinned_pieces_info[(row, col)]
                    
                    # Penalty based on piece value
                    pin_penalty = piece_value * 0.1  
                    
                    # Higher penalty for king pins
                    if pin_info['is_king_pin']:
                        pin_penalty *= 1.2
                    
                    if square[0] == 'w':
                        score -= pin_penalty
                    else:
                        score += pin_penalty

    # Uncomment this section to add castling incentives in mid/late game
    # if gs.num_moves > 20:
    #     if not gs.blackHasCastled:
    #         score += 2 ** (gs.num_moves - 20)
    #     if not gs.whiteHasCastled:
    #         score -= 2 ** (gs.num_moves - 20)
    
    return score

def evaluateDevelopment(gs):
    """
    Evaluates piece development in the opening.
    Penalizes undeveloped minor pieces and rewards proper development.
    Returns a score bonus/penalty that's weighted by game phase.
    """
    # Only apply this evaluation in opening/early middlegame
    if gs.num_moves > 20:  
        return 0
    
    development_score = 0
    
    # Scale development weight based on game phase - very important early, less so later
    if gs.num_moves <= 10:  # Early opening
        development_weight = 4.0 - gs.num_moves * 0.2  # Starts high and decreases
    else:
        development_weight = max(1.0, 3.0 - gs.num_moves * 0.1)
    
    # Check white minor pieces (knights and bishops)
    # Starting positions: knights at b1/g1, bishops at c1/f1
    white_minor_starting_positions = [(7, 1), (7, 6), (7, 2), (7, 5)]
    white_undeveloped = 0
    
    for pos in white_minor_starting_positions:
        piece = gs.board[pos[0]][pos[1]]
        if (piece == 'wN' and pos in [(7, 1), (7, 6)]) or (piece == 'wB' and pos in [(7, 2), (7, 5)]):
            white_undeveloped += 1
    
    # Check black minor pieces
    # Starting positions: knights at b8/g8, bishops at c8/f8
    black_minor_starting_positions = [(0, 1), (0, 6), (0, 2), (0, 5)]
    black_undeveloped = 0
    
    for pos in black_minor_starting_positions:
        piece = gs.board[pos[0]][pos[1]]
        if (piece == 'bN' and pos in [(0, 1), (0, 6)]) or (piece == 'bB' and pos in [(0, 2), (0, 5)]):
            black_undeveloped += 1
    
    # Apply penalties for undeveloped pieces
    # 0.5 points per undeveloped piece, scaled by game phase
    development_penalty = 0.5 * development_weight  
    development_score = (black_undeveloped - white_undeveloped) * development_penalty
    
    # Check if knights and bishops are developed to good squares
    good_development_bonus = 0.2 * development_weight
    
    # Good squares for knights (center and near-center)
    white_good_knight_squares = [(5, 2), (5, 5), (4, 3), (4, 4), (5, 3), (5, 4)]
    black_good_knight_squares = [(2, 2), (2, 5), (3, 3), (3, 4), (2, 3), (2, 4)]
    
    # Good squares for bishops (diagonals and fianchetto positions)
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
    # This encourages developing different pieces instead of moving the same one
    if gs.num_moves < 12 and hasattr(gs, 'moveLog') and len(gs.moveLog) > 0:
        piece_moves_count = {}
        for move in gs.moveLog:
            piece_key = f"{move.pieceMoved}_{move.startRow}_{move.startCol}"
            if piece_key not in piece_moves_count:
                piece_moves_count[piece_key] = 0
            piece_moves_count[piece_key] += 1
            
            # Penalty for moving minor pieces or queen multiple times
            if piece_moves_count[piece_key] > 1 and move.pieceMoved[1] in ['N', 'B', 'Q']:
                if move.pieceMoved[0] == 'w':
                    development_score -= 0.3 * development_weight
                else:
                    development_score += 0.3 * development_weight
    
    # Bonus for castling - important for king safety and rook development
    if hasattr(gs, 'whiteHasCastled') and gs.whiteHasCastled:
        development_score += 0.5 * development_weight
    if hasattr(gs, 'blackHasCastled') and gs.blackHasCastled:
        development_score -= 0.5 * development_weight
    
    return development_score

def evaluatePassedPawns(gs):
    """
    Gives bonus points for passed pawns that have a clear path to promotion.
    A passed pawn has no opposing pawns in front of it or on adjacent files.
    Bonus scales with game phase and pawn advancement.
    """
    score = 0
    
    # Passed pawns become more important as the game progresses
    if gs.num_moves < 10:
        phase_multiplier = 0.4  # Less important in opening
    elif gs.num_moves < 25:
        phase_multiplier = 0.8  # Growing importance in middlegame
    else:
        phase_multiplier = 1.5  # Very important in endgame
    
    # Check for white passed pawns
    for col in range(8):
        for row in range(6, 0, -1):  # From rank 2 to 7 (bottom to top)
            if gs.board[row][col] == 'wp':
                is_passed = True
                
                # Check if there are black pawns that can block or capture
                for check_row in range(row-1, -1, -1):
                    for check_col in range(max(0, col-1), min(8, col+2)):
                        if gs.board[check_row][check_col] == 'bp':
                            is_passed = False
                            break
                    if not is_passed:
                        break
                
                if is_passed:
                    # Base bonus for having a passed pawn
                    base_bonus = 0.5
                    
                    # The further advanced, the higher the bonus (exponential growth)
                    rank = 7 - row  # Convert to chess rank (0-7)
                    advancement_bonus = 0.2 * (2 ** (rank - 1))  # Grows exponentially with rank
                    
                    # Additional bonus if the pawn is protected by friendly pieces
                    is_protected = False
                    for check_row in range(max(0, row-1), min(8, row+2)):
                        for check_col in range(max(0, col-1), min(8, col+2)):
                            if (check_row != row or check_col != col) and gs.board[check_row][check_col][0] == 'w':
                                is_protected = True
                                break
                    
                    protection_bonus = 0.2 if is_protected else 0
                    
                    # Total bonus for this passed pawn
                    total_bonus = (base_bonus + advancement_bonus + protection_bonus) * phase_multiplier
                    score += total_bonus
                
                break  # Only check the most advanced pawn in each file
    
    # Check for black passed pawns - same logic but subtract from score
    for col in range(8):
        for row in range(1, 7):  # From rank 7 to 2 (top to bottom)
            if gs.board[row][col] == 'bp':
                is_passed = True
                
                # Check if there are white pawns that can block or capture
                for check_row in range(row+1, 8):
                    for check_col in range(max(0, col-1), min(8, col+2)):
                        if gs.board[check_row][check_col] == 'wp':
                            is_passed = False
                            break
                    if not is_passed:
                        break
                
                if is_passed:
                    base_bonus = 0.5
                    
                    rank = row  # Convert to chess rank (0-7)
                    advancement_bonus = 0.2 * (2 ** (rank - 1))
                    
                    is_protected = False
                    for check_row in range(max(0, row-1), min(8, row+2)):
                        for check_col in range(max(0, col-1), min(8, col+2)):
                            if (check_row != row or check_col != col) and gs.board[check_row][check_col][0] == 'b':
                                is_protected = True
                                break
                    
                    protection_bonus = 0.2 if is_protected else 0
                    
                    total_bonus = (base_bonus + advancement_bonus + protection_bonus) * phase_multiplier
                    score -= total_bonus
                
                break
    
    return score

def evaluateCenterPawnStructure(gs):
    """
    Evaluates pawn structure, focusing on center control, pawn chains,
    and proper development. Good pawn structure is key to controlling
    the board and having a solid positional advantage.
    """
    score = 0
    
    # Pawn structure is most important in opening and middlegame
    if gs.num_moves < 10:
        phase_multiplier = 1.5  # Very important in opening
    elif gs.num_moves < 25:
        phase_multiplier = 1.0  # Important in middlegame
    else:
        phase_multiplier = 0.7  # Less important in endgame
    
    # 1. Evaluate center control with pawns (d4, e4, d5, e5)
    # These are the four central squares
    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    
    for square in center_squares:
        row, col = square
        if gs.board[row][col] == 'wp':
            score += 0.4  # White pawn directly controlling center
        elif gs.board[row][col] == 'bp':
            score -= 0.4  # Black pawn directly controlling center
    
    # 2. Evaluate extended center control (c3-c6, f3-f6, d3-d6, e3-e6)
    # The squares surrounding the center
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
    # Good pawn chains provide protection and control space
    white_chain_bonus = evaluatePawnChains(gs, 'w')
    black_chain_bonus = evaluatePawnChains(gs, 'b')
    
    score += white_chain_bonus - black_chain_bonus
    
    # 4. Penalize isolated and doubled pawns (structural weaknesses)
    white_structure_penalty = evaluatePawnStructureWeaknesses(gs, 'w')
    black_structure_penalty = evaluatePawnStructureWeaknesses(gs, 'b')
    
    score -= white_structure_penalty - black_structure_penalty
    
    # 5. Penalize excessive pawn movement in opening
    # Moving too many pawns early weakens position and delays development
    if gs.num_moves < 10:
        white_moved_pawns = 0
        black_moved_pawns = 0
        
        # Count pawns that have moved from their starting positions
        for col in range(8):
            if gs.board[6][col] != 'wp':  # White pawns start on row 6
                white_moved_pawns += 1
            if gs.board[1][col] != 'bp':  # Black pawns start on row 1
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
    These provide strong structure and spatial control.
    """
    chain_bonus = 0
    color_char = color  # 'w' or 'b'
    pawn_char = color_char + 'p'
    
    # Direction for checking diagonal protection
    if color_char == 'w':
        protection_directions = [(-1, -1), (-1, 1)]  # White pawns protect diagonally up
    else:
        protection_directions = [(1, -1), (1, 1)]    # Black pawns protect diagonally down
    
    # Check all pawns on the board
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
                
                # Additional bonus if the pawn is in the center area
                if is_protected and 2 <= row <= 5 and 2 <= col <= 5:
                    chain_bonus += 0.1  # Extra bonus for central pawn chains
    
    return chain_bonus

def evaluatePawnStructureWeaknesses(gs, color):
    """
    Helper function to evaluate pawn structure weaknesses.
    Identifies and penalizes isolated and doubled pawns.
    These are structural weaknesses that can be exploited.
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
    # These are harder to advance and can be blockaded
    for col in range(8):
        if pawns_in_file[col] > 1:
            weakness_penalty += 0.3 * (pawns_in_file[col] - 1)  # Penalty for each doubled pawn
    
    # Check for isolated pawns (no friendly pawns in adjacent files)
    # These can't be protected by other pawns
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
    """
    Penalizes moving too many pawns in the opening phase.
    Moving too many pawns early delays piece development and can
    weaken king safety.
    """
    # Only apply in opening phase
    if gs.num_moves > 10:
        return 0
        
    penalty = 0
    white_moved_pawns = 0
    black_moved_pawns = 0
    
    # Count pawns that have moved from their starting positions
    for col in range(8):
        if gs.board[6][col] != 'wp':  # White pawns start on row 6
            white_moved_pawns += 1
        if gs.board[1][col] != 'bp':  # Black pawns start on row 1
            black_moved_pawns += 1
    
    # Penalize moving more than 3 pawns in the opening
    # General guideline: focus on developing pieces first, control center with 2-3 pawns
    if white_moved_pawns > 3:
        penalty -= (white_moved_pawns - 3) * 0.2
    if black_moved_pawns > 3:
        penalty += (black_moved_pawns - 3) * 0.2
        
    return penalty


def evaluateRookPositioning(gs):
    """
    Evaluates rook positioning, giving bonus points for favorable positions.
    Rooks on the 7th rank are particularly strong, as are rooks on open files.
    """
    rook_score = 0
    rook_seventh_rank_bonus = 0.7  # Substantial bonus for a rook on 7th/2nd rank
    
    # Check white rooks on 7th rank (row 1) - threatening enemy pawns and king
    for col in range(8):
        if gs.board[1][col] == 'wR':
            rook_score += rook_seventh_rank_bonus
    
    # Check black rooks on 2nd rank (row 6) - threatening enemy pawns and king
    for col in range(8):
        if gs.board[6][col] == 'bR':
            rook_score -= rook_seventh_rank_bonus
    
    # Additional bonus for controlling open or semi-open files
    # Rooks are most powerful when they have vertical mobility
    rook_score += evaluateRooksOnOpenFiles(gs)
    
    return rook_score

def evaluateRooksOnOpenFiles(gs):
    """
    Gives bonus points for rooks on open or semi-open files.
    - Open file: No pawns on the file (maximum mobility)
    - Semi-open file: No friendly pawns on the file (good for attacking)
    """
    score = 0
    open_file_bonus = 0.3      # No pawns at all on file
    semi_open_file_bonus = 0.15  # No friendly pawns on file
    
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
    """
    Calculates the raw material score by adding up the value
    of all pieces on the board.
    Positive score favors white, negative score favors black.
    """
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':  # White piece
                score += pieceScores[square[1]]
            elif square[0] == 'b':  # Black piece
                score -= pieceScores[square[1]]

    return score


def record_move_to_opening_book(gs, move, quality=1):
    """
    Records a move to the opening book database if it's within the
    first MAX_BOOK_MOVE moves of the game.
    Used for training and building the engine's opening repertoire.
    """
    if len(gs.moveLog) <= MAX_BOOK_MOVE:
        position_hash = opening_book.add_position(gs.board, move, quality)
        print(f"Added position {position_hash} to opening book")
        opening_book.save_book()