from helper_functions import isValidEnPassant
from collections import Counter
import copy 

# --- Global Variables ---
# Simple material values for pieces (used in evaluation/move scoring potentially)
# Note: King is 0 as losing it ends the game, its value isn't material based.
pieceScores = {'K': 0, 'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}

# --- Game State Class ---
class GameState():
    """
    Represents the current state of a chess game. 
    Includes the board layout, whose turn it is, move history, 
    castling rights, en passant possibility, and game status flags.
    """
    def __init__(self):
        """Initializes the game state to the standard starting chess position."""
        # The board is represented as an 8x8 2D list.
        # Each element is a 2-character string: "wK" (white King), "bp" (black pawn), "--" (empty square).
        # Row 0 is the black side (rank 8), Row 7 is the white side (rank 1).
        # Column 0 is the 'a' file, Column 7 is the 'h' file.
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
        # Dictionary mapping piece types ('p', 'R', 'N', etc.) to their move generation functions.
        # This allows for easy lookup when generating moves for a specific piece.
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'Q': self.getQueenMoves, 
                              'N': self.getKnightMoves, 'B': self.getBishopMoves, 'K': self.getKingMoves}
        
        self.whiteToMove = True # White starts the game
        self.moveLog = [] # Stores a list of Move objects representing the game history

        # Keep track of King locations for quick access (check detection, castling)
        self.whiteKingLocation = (7, 4) # (row, col) format
        self.blackKingLocation = (0, 4)
        
        # Game status flags
        # self.inCheck = False # This seems unused, replaced by checkForPinsAndChecks return value
        self.checkmate = False # True if the current player is checkmated
        self.stalemate = False # True if the current player is stalemated

        # Information about checks and pins on the current player's pieces
        # These are calculated by checkForPinsAndChecks()
        self.pins = []   # List of pinned pieces and the direction of the pin
        self.checks = [] # List of pieces currently checking the king and their attack direction

        # En Passant tracking
        self.enPassantPossible = () # Stores the *target square* for a possible en passant capture, e.g., (2, 3)
                                    # Empty tuple means no en passant capture is possible this turn.
        self.enPassantPossibleLog = [self.enPassantPossible] # Log to store previous en passant states for undoing moves

        # Castling rights tracking
        # Uses a separate CastlingRights object to store the four rights (wK, bK, wQ, bQ)
        self.currentCastlingRights = CastlingRights(True, True, True, True) # Initially, all rights are available
        # Log to store previous castling rights states for undoing moves
        self.castlingRightsLog = [
            CastlingRights(
                self.currentCastlingRights.wks,
                self.currentCastlingRights.bks,
                self.currentCastlingRights.wqs,
                self.currentCastlingRights.bqs,
            )
        ]

        # --- Potential evaluation/analysis attributes ---
        # Dictionaries to count how many opponent pieces each side attacks/defends.
        # These might be used for simple board evaluation heuristics.
        # (Populated by countAttacksAndDefends method)
        self.white_attacks = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.black_attacks = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.white_defends = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.black_defends = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        
        # --- Game Rule Tracking ---
        self.num_moves = 0 # Counter for the total number of half-moves made
        self.whiteHasCastled = False # Flag if white has castled (might be useful for evaluation)
        self.blackHasCastled = False # Flag if black has castled

        # Fifty-move rule counter: Increments for each move unless it's a pawn move or capture.
        # A draw can be claimed if this reaches 100 (50 full moves).
        self.halfmove_clock = 0 

        # Threefold repetition tracking
        # Stores a history of board positions (as strings) to detect repetitions.
        self.position_history = [] 
        self.last_position = () # Seems unused? Maybe intended for incremental hashing later.

    def record_position(self):
        """Captures the current board state, turn, castling rights, and en passant 
           square to check for threefold repetition later."""
        # Need a deep copy so modifications to self.board don't affect the history
        board_state = copy.deepcopy(self.board) 
        # Create a dictionary representing the key aspects of the position
        position = {
            'board': board_state,
            'whiteToMove': self.whiteToMove,
            'castling': (self.currentCastlingRights.wks, self.currentCastlingRights.wqs,
                         self.currentCastlingRights.bks, self.currentCastlingRights.bqs),
            'enPassant': self.enPassantPossible
        }
        
        # Convert the position dictionary to a string so it can be hashed and stored easily.
        # Using str() might not be the most robust hashing method, but works for simple cases.
        position_str = str(position)
        self.position_history.append(position_str)

    def is_threefold_repetition(self):
        """Checks if the current position has occurred three or more times in the game."""
        # Count how many times each unique position string has appeared in the history
        position_counts = Counter(self.position_history)
        
        # Check if any position's count is 3 or more
        for position, count in position_counts.items():
            if count >= 3:
                return True # Repetition detected
        
        return False # No repetition found

    def is_fifty_move_rule(self):
        """Checks if the half-move clock has reached 100 (50 full moves without pawn move or capture)."""
        # The rule is 50 moves by each player = 100 half-moves.
        return self.halfmove_clock >= 100
    
    def is_draw(self):
        """Checks if the game is a draw due to stalemate, threefold repetition, or the fifty-move rule."""
        # Check for stalemate first (no legal moves, king not in check)
        if self.stalemate:
            return True
        
        # Check for threefold repetition
        if self.is_threefold_repetition():
            # Note: Technically, repetition needs to be claimed. Here we assume it ends the game.
            return True
        
        # Check for the fifty-move rule
        if self.is_fifty_move_rule():
            # Note: Also needs to be claimed in official rules.
            return True
            
        # Could also add checks for insufficient material here if needed.

        return False # No draw condition met yet


    def makeMove(self, move):
        """
        Applies a given move to the board and updates the game state.
        Assumes the move is valid (doesn't check for legality here).
        Handles piece movement, captures, pawn promotion, en passant, castling, 
        updating king locations, turn switching, move logs, and game rule counters.
        """
        # Basic move: Clear the start square, place the moved piece on the end square
        self.board[move.startRow][move.startCol] = "--" 
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move) # Add the move to the history log
        self.num_moves += 1 # Increment the half-move counter
        self.whiteToMove = not self.whiteToMove # Switch turns

        # --- Update Game Rule Counters ---
        # Reset the half-move clock if it was a pawn move or a capture
        if move.pieceMoved[1] == 'p' or move.isCapture:
            self.halfmove_clock = 0
        else:
            # Otherwise, increment the clock
            self.halfmove_clock += 1

        # --- Update Analysis Attributes (Optional) ---
        self.countAttacksAndDefends() # Recalculate attack/defense counts if used

        # --- Update King Locations ---
        # If a king moved, update its stored location
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        # --- Handle Special Moves ---
        # Pawn Promotion
        if move.isPawnPromotion:
            promotedPiece = move.promotionChoice 
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + promotedPiece # Update board with promoted piece

        # En Passant Capture
        if move.isEnPassantMove:
            # The captured pawn is actually on the *start* row of the moving pawn, 
            # but the *same column* as the end square.
            self.board[move.startRow][move.endCol] = '--' # Clear the captured pawn's square

        # --- Set En Passant Possibility for the *Next* Turn ---
        # If a pawn moved two squares forward...
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            # ...the square *behind* it becomes the target square for en passant.
            self.enPassantPossible = ((move.startRow + move.endRow)//2, move.startCol) 
        else:
            # Otherwise, no en passant is possible on the next move.
            self.enPassantPossible = ()

        # Castling
        if move.isCastleMove:
            if move.endCol - move.startCol == 2: # King-side castle (King moves 2 squares right)
                # Move the rook from the corner to the square the king skipped over
                self.board[move.endRow][move.endCol-1] = self.board[move.endRow][move.endCol+1] 
                self.board[move.endRow][move.endCol+1] = "--" # Empty the rook's original square
            else: # Queen-side castle (King moves 2 squares left)
                # Move the rook from the corner to the square the king skipped over
                self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-2]
                self.board[move.endRow][move.endCol-2] = '--' # Empty the rook's original square
            
            # Update castling flags (used for evaluation perhaps)
            if move.pieceMoved[0] == 'w':
                self.whiteHasCastled = True
            else:
                self.blackHasCastled = True

        # --- Update Logs for Undo ---
        self.enPassantPossibleLog.append(self.enPassantPossible) # Log the new en passant state

        # Update castling rights based on the move (e.g., if King or Rook moved)
        self.updateCastlingRights(move) 
        # Log the new castling rights state
        self.castlingRightsLog.append(CastlingRights(self.currentCastlingRights.wks,self.currentCastlingRights.bks,
                                         self.currentCastlingRights.wqs, self.currentCastlingRights.bqs,))
        
        # --- Record Position for Repetition Check ---
        self.record_position() # Record the state *after* the move is fully completed
        

    def undoMove(self):
        """
        Reverts the last move made, restoring the previous game state.
        Handles undoing all aspects managed by makeMove (board, logs, flags, counters).
        """
        if len(self.moveLog) != 0: # Check if there is a move to undo
            # --- Undo Repetition Tracking ---
            if self.position_history: # Make sure history isn't empty
                self.position_history.pop() # Remove the state that resulted from the move we're undoing

            # --- Get the Last Move ---
            move = self.moveLog.pop() # Remove and retrieve the last move from the log
            self.num_moves -= 1 # Decrement the half-move counter

            # --- Revert Half-Move Clock ---
            # This is slightly tricky. We need to restore the clock to its state *before* the undone move.
            # The current implementation checks if the *new* last move (after popping) was also non-resetting.
            # A more robust way might be to log the halfmove_clock value itself.
            if move.pieceMoved[1] == 'p' or move.isCapture:
                 # If the undone move *reset* the clock, we need to figure out the previous value.
                 # This looks complex - assumes the clock only increments by 1 if not reset.
                 # It checks the move *before* the undone one to see if it also reset the clock.
                 # If the move *before* the one being undone reset the clock, the clock was 0 before the undone move.
                 # If the move *before* the one being undone *didn't* reset the clock, then the clock was likely 1 higher.
                if len(self.moveLog) > 0:
                    last_move = self.moveLog[-1] 
                    # Check the move *before* the one we just popped
                    if last_move.pieceMoved[1] == 'p' or last_move.isCapture:
                        # If the move before the undone one also reset the clock, it must have been 0
                        self.halfmove_clock = 0 
                    else:
                        # If the move before didn't reset, decrement the current clock (which was likely > 0)
                         self.halfmove_clock = max(0, self.halfmove_clock - 1) # This line seems wrong if the undone move reset the clock to 0. It should probably look at a history log for the clock value.
                else: # If it was the very first move
                    self.halfmove_clock = 0

            else: # If the undone move did *not* reset the clock
                # Just decrement the clock value (ensure it doesn't go below 0)
                self.halfmove_clock = max(0, self.halfmove_clock - 1) 

            # --- Restore Board State ---
            # Put the moved piece back on its starting square
            self.board[move.startRow][move.startCol] = move.pieceMoved 
            # Put the captured piece (if any) back on the ending square ("--" if no capture)
            self.board[move.endRow][move.endCol] = move.pieceCaptured 
            self.whiteToMove = not self.whiteToMove # Switch turn back

            # --- Update Analysis Attributes (Optional) ---
            self.countAttacksAndDefends() # Recalculate based on the restored board

            # --- Restore King Locations ---
            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)

            # --- Undo Special Moves ---
            # Undo En Passant Capture
            if move.isEnPassantMove:
                self.board[move.endRow][move.endCol] = '--' # The landing square becomes empty again
                # Place the captured pawn back on its square (startRow of mover, endCol of mover)
                self.board[move.startRow][move.endCol] = move.pieceCaptured 
                # Note: pieceCaptured should be 'bp' or 'wp' in this case

            # Undo En Passant Possibility State
            self.enPassantPossibleLog.pop() # Remove the state *after* the undone move
            self.enPassantPossible = self.enPassantPossibleLog[-1] # Restore the state *before* the undone move
            
            # Undo Castling Rights State
            self.castlingRightsLog.pop() # Remove the state *after* the undone move
            newRights = self.castlingRightsLog[-1] # Get the state *before* the undone move
            # Create a new CastlingRights object with the restored values
            self.currentCastlingRights = CastlingRights(newRights.wks, newRights.bks, newRights.wqs, newRights.bqs) 

            # Undo Castling Move (move the rook back)
            if move.isCastleMove:
                if move.endCol - move.startCol == 2: # King-side castle undo
                    # Move the rook from beside the king back to the corner
                    self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-1]
                    self.board[move.endRow][move.endCol-1] = '--' # Empty the square beside the king
                else: # Queen-side castle undo
                     # Move the rook from beside the king back to the corner
                    self.board[move.endRow][move.endCol-2] = self.board[move.endRow][move.endCol+1]
                    self.board[move.endRow][move.endCol+1] = '--' # Empty the square beside the king

                # Revert castling flags (might need more logic if eval depends on it)
                # This simplified version just assumes if we undo a castle move, the flag resets.
                # A more robust approach might store these flags in the log too.
                if move.pieceMoved[0] == 'w':
                    self.whiteHasCastled = False
                else:
                    self.blackHasCastled = False
            
            # --- Reset Game End Flags ---
            # If we undo a move, the game cannot be over by checkmate or stalemate anymore.
            self.checkmate = False
            self.stalemate = False

    # --- Check and Pin Detection ---
    def checkForPinsAndChecks(self):
        """
        Identifies if the current player's king is in check, and finds any pieces 
        that are pinned to the king (cannot move off the line of attack).
        Also returns a list of squares/directions from which checks originate.
        """
        pins = []   # Stores info about pinned pieces: (row, col, pin_direction_x, pin_direction_y)
        checks = [] # Stores info about checking pieces: (row, col, attack_direction_x, attack_direction_y)
        inCheck = False # Flag: Is the current player's king under attack?
        
        # Determine enemy/ally colors and the king's position based on whose turn it is
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

        # Check outward from the king in all 8 directions (Rook + Bishop directions)
        directions = ((0, 1), (0, -1), (1, 0), (-1, 0),  # Rook directions (horizontal/vertical)
                      (1, 1), (-1, -1), (1, -1), (-1, 1)) # Bishop directions (diagonals)
        
        for j in range(len(directions)): # Iterate through each direction
            d = directions[j]
            possiblePin = () # Reset possible pin for each new direction
            
            for i in range(1, 8): # Check up to 7 squares away along the current direction
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                
                if 0 <= endRow < 8 and 0 <= endCol < 8: # Check if the square is on the board
                    endPiece = self.board[endRow][endCol] # Get the piece on that square
                    
                    if endPiece[0] == allyColor and endPiece[1] != 'K': 
                        # Found an allied piece (not the king). Could it be pinned?
                        if possiblePin == (): # If this is the *first* allied piece found along this ray...
                            possiblePin = (endRow, endCol, d[0], d[1]) # ...record it as potentially pinned.
                        else: # If we already found an allied piece closer to the king...
                            break # ...then there's no pin along this line, stop searching this direction.
                              
                    elif endPiece[0] == enemyColor:
                        # Found an enemy piece. Does it attack the king along this line?
                        type = endPiece[1] # Get the enemy piece type ('R', 'B', 'Q', 'p', 'K')

                        # Check if the enemy piece type can attack along the current direction 'j':
                        # 1. Rook/Queen on straight lines (j=0-3)
                        # 2. Bishop/Queen on diagonal lines (j=4-7)
                        # 3. Pawn on adjacent diagonal (only distance i=1 matters)
                        #    (complex condition checks pawn color and attack direction index j)
                        # 4. King on adjacent square (only distance i=1 matters)
                        if (0 <= j <= 3 and type == 'R') or \
                           (4 <= j <= 7 and type == 'B') or \
                           (i == 1 and type == 'p' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                           (type == 'Q') or \
                           (i == 1 and type == 'K'):
                           
                            # If this attacking enemy piece was found *before* any blocking allied piece...
                            if possiblePin == (): 
                                # ...it's a direct check!
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1])) 
                                break # Stop searching this direction (check confirmed)
                            else: # If there *was* an allied piece blocking the way...
                                # ...that allied piece is pinned!
                                pins.append(possiblePin) 
                                break # Stop searching this direction (pin confirmed)
                        else: 
                            # The enemy piece found doesn't attack along this line (e.g., Rook on diagonal).
                            break # Stop searching this direction.

                else: # Off-board square encountered
                    break # Stop searching this direction.

        # Check for Knight checks separately (they don't attack along lines)
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8: # Check if on board
                endPiece = self.board[endRow][endCol]
                # If there's an enemy Knight on a square it can attack from...
                if endPiece[0] == enemyColor and endPiece[1] == 'N': 
                    # ...it's a check!
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1])) # Store knight location and relative move
        
        # Return the results of the check/pin scan
        return inCheck, pins, checks

    
    def updateCastlingRights(self, move):
        """
        Updates the castling rights based on the move made. 
        Castling rights are lost if the King moves, or if a Rook moves 
        from its starting square, or if a Rook is captured on its starting square.
        """
        # If the white king moved
        if move.pieceMoved == "wK":
            self.currentCastlingRights.wks = False
            self.currentCastlingRights.wqs = False
        # If the black king moved
        elif move.pieceMoved == "bK":
            self.currentCastlingRights.bks = False
            self.currentCastlingRights.bqs = False
        # If a white rook moved
        elif move.pieceMoved == "wR":
            if move.startRow == 7: # Check if it started on rank 1
                if move.startCol == 0: # Queen-side rook (a1)
                    self.currentCastlingRights.wqs = False
                elif move.startCol == 7: # King-side rook (h1)
                    self.currentCastlingRights.wks = False
        # If a black rook moved
        elif move.pieceMoved == "bR":
            if move.startRow == 0: # Check if it started on rank 8
                if move.startCol == 0: # Queen-side rook (a8)
                    self.currentCastlingRights.bqs = False
                elif move.startCol == 7: # King-side rook (h8)
                    self.currentCastlingRights.bks = False
        
        # Check if a rook was captured *on its starting square*
        # If black captured white's queen-side rook on a1
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRights.wqs = False
                # If black captured white's king-side rook on h1
                elif move.endCol == 7:
                    self.currentCastlingRights.wks = False
        # If white captured black's queen-side rook on a8
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRights.bqs = False
                # If white captured black's king-side rook on h8
                elif move.endCol == 7:
                    self.currentCastlingRights.bks = False


    
    # --- Primary Move Generation ---
    def getValidMoves(self):
        """
        Generates all *legal* moves for the current player.
        This version uses the make-move/undo-move approach for validation.
        It generates all pseudo-legal moves first, then checks each one
        to ensure it doesn't leave the king in check. Also handles castling.
        """
        # --- Save current state that might be modified during validation ---
        # Store the en passant state before starting validation
        tempEnpassantPossible = self.enPassantPossible 
        # Store the castling rights before starting validation
        tempCastleRights = CastlingRights(
            self.currentCastlingRights.wks,
            self.currentCastlingRights.bks,
            self.currentCastlingRights.wqs,
            self.currentCastlingRights.bqs,
        )
        
        # 1. Generate all pseudo-legal moves (moves that follow piece rules but might leave king in check)
        moves = self.getAllPossibleMoves()
        
        # 2. Validate each pseudo-legal move
        # Iterate backwards because we might remove moves from the list
        for i in range(len(moves) - 1, -1, -1): 
            # --- Potential Issue: Redundant variable? ---
            # `undoMove` should already restore `self.enPassantPossible` from the log. 
            # Storing it here in `current_en_passant` and restoring it manually after undo 
            # might be unnecessary or could even cause issues if `undoMove`'s logic changes.
            # current_en_passant = self.enPassantPossible # Store EP state before making the move

            # Make the move temporarily on the board
            self.makeMove(moves[i]) 
            
            # Switch turns to check if the *opponent* can now attack our king
            self.whiteToMove = not self.whiteToMove 
            
            # Check if the player who just moved is now in check
            if self.inCheck(): 
                # If they are in check, the move was illegal
                moves.remove(moves[i]) # Remove it from the list
            
            # Switch turns back
            self.whiteToMove = not self.whiteToMove 
            
            # Undo the temporary move to restore the original board state
            self.undoMove() 

            # --- Potential Issue: Redundant restoration? ---
            # self.enPassantPossible = current_en_passant # Restore EP state (might be redundant, see above)

        # 3. Check for Checkmate / Stalemate
        if len(moves) == 0: # If no legal moves were found...
            if self.inCheck(): # ...and the king is currently in check...
                self.checkmate = True # ...it's checkmate!
            else: # ...and the king is *not* in check...
                self.stalemate = True # ...it's stalemate!
        else: # If there are legal moves...
            # ...reset the flags (in case they were set previously, e.g., after undo)
            self.checkmate = False
            self.stalemate = False

        # 4. Check for Draws by Rule
        # If a draw condition like threefold repetition or 50-move rule is met, set stalemate flag.
        # (Note: Technically these are draws, not stalemates, but using the flag might be convenient)
        if self.is_threefold_repetition() or self.is_fifty_move_rule():
            self.stalemate = True # Treat these draws like stalemate for game ending logic?
        
        # 5. Add Castling Moves (if legal)
        # Castling needs special validation (king not in check, squares not attacked, rights available)
        # This is done *after* filtering normal moves.
        if self.whiteToMove:
            self.getCastleMoves(
                self.whiteKingLocation[0], self.whiteKingLocation[1], moves
            )
        else:
            self.getCastleMoves(
                self.blackKingLocation[0], self.blackKingLocation[1], moves
            )

        # --- Restore Original State ---
        # Restore the en passant and castling rights that were saved at the beginning.
        # This is crucial because `makeMove`/`undoMove` within the loop modified the current state.
        self.enPassantPossible = tempEnpassantPossible
        self.currentCastlingRights = tempCastleRights
        
        # Return the final list of fully legal moves
        return moves
    
    # --- Helper Methods for Move Validation ---
    def inCheck(self):
        """Checks if the current player's king is under attack."""
        if self.whiteToMove:
            # Check if the white king's square is attacked by black
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            # Check if the black king's square is attacked by white
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    def squareUnderAttack(self, r, c):
        """
        Checks if the square (r, c) is attacked by any of the opponent's pieces.
        Uses a trick: temporarily switches turns, generates all opponent moves, 
        and checks if any land on the target square.
        """
        self.whiteToMove = not self.whiteToMove # Temporarily switch to opponent's turn
        oppoMoves = self.getAllPossibleMoves() # Generate all pseudo-legal moves for opponent
        self.whiteToMove = not self.whiteToMove # Switch back to original player's turn
        
        # Check if any opponent move ends on the target square (r, c)
        for move in oppoMoves:
            if move.endRow == r and move.endCol == c:
                return True # Square is under attack
        return False # Square is safe

    # --- Alternative/Specialized Pin Detection (Potentially redundant?) ---
    # These seem to duplicate or specialize the pin logic already in `checkForPinsAndChecks`.
    # Might be intended for specific evaluation functions rather than core move validation.
    def detectAllPins(self):
        """Detects pins to both the King and the Queen."""
        pins = []
        # Find pins to the King
        kingPins = self.detectPinsToRoyalPiece(isKing=True)
        pins.extend(kingPins)
        # Find pins to the Queen (less common, but maybe useful for eval)
        queenPins = self.detectPinsToRoyalPiece(isKing=False)
        pins.extend(queenPins)
        return pins
    
    def detectPinsToRoyalPiece(self, isKing=True):
        """
        Detects pieces pinned to either the King or the Queen.
        Similar logic to checkForPinsAndChecks ray casting.
        Returns pins as (row, col, dir_x, dir_y, isKingPin_boolean).
        """
        pins = []
        # Determine colors
        if self.whiteToMove:
            allyColor = 'w'
            enemyColor = 'b'
        else:
            allyColor = 'b'
            enemyColor = 'w'

        # Find the location of the piece to check pins against (King or Queen)
        pieceLocation = None
        if isKing:
            pieceLocation = self.whiteKingLocation if self.whiteToMove else self.blackKingLocation
        else: # Find the Queen
            for r in range(8):
                for c in range(8):
                    if self.board[r][c] == allyColor + 'Q':
                        pieceLocation = (r, c)
                        break
                if pieceLocation:
                    break
            
        if not pieceLocation: # If no King/Queen found (shouldn't happen in normal game)
            return pins
        
        startRow, startCol = pieceLocation

        # Ray casting logic (similar to checkForPinsAndChecks)
        directions = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1))
        for d_index, d in enumerate(directions): # Use enumerate to get index easily
            possiblePin = () # Potential pinned piece info (row, col, dx, dy)
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
            
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                
                    # Found an allied piece (that isn't the King/Queen itself)
                    if endPiece[0] == allyColor and (endPiece[1] != 'K' and endPiece[1] != 'Q'): 
                        if possiblePin == (): # First allied piece on this ray
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else: # Second allied piece, blocks any pin
                            break  
                        
                    elif endPiece[0] == enemyColor: # Found an enemy piece
                        piece_type = endPiece[1]
                        valid_pin = False # Can this enemy piece pin along this direction?
                        
                        # Check if it's a sliding piece valid for this direction
                        if 0 <= d_index <= 3: # Straight directions (N, S, E, W)
                            if piece_type == 'R' or piece_type == 'Q':
                                valid_pin = True
                        elif 4 <= d_index <= 7: # Diagonal directions
                            if piece_type == 'B' or piece_type == 'Q':
                                valid_pin = True
                        
                        # If it's a valid pinner AND we found an allied piece blocking earlier
                        if valid_pin and possiblePin != ():
                            # It's a pin! Record the pinned piece location, direction, and target (King/Queen)
                            pins.append((possiblePin[0], possiblePin[1], possiblePin[2], possiblePin[3], isKing))
                        # In any case, hitting an enemy piece stops the ray for pin detection
                        break 
                    elif endPiece != "--": # Found another allied piece (King/Queen) - stops ray
                         break
                else: # Off board
                    break # Stop searching this direction
    
        return pins
    
    # --- Move Scoring and Ordering (for AI/Search) ---
    def scoreMove(self, move):
        """
        Assigns a simple heuristic score to a move. Used for move ordering 
        in search algorithms (e.g., alpha-beta) to explore promising moves first.
        This is NOT a full board evaluation.
        """
        score = 0

        # --- Check Bonus ---
        # Temporarily make the move to see if it delivers check
        self.makeMove(move)
        self.whiteToMove = not self.whiteToMove # Switch to opponent's perspective
        if self.inCheck(): # If the opponent is now in check...
            score += 10000 # ...give a large bonus (checking is usually good)
        self.whiteToMove = not self.whiteToMove # Switch back
        self.undoMove() # Undo the temporary move

        # --- Piece Threat Bonus ---
        # Calculate value of enemy pieces threatened by the moved piece *after* the move
        enemy_color = 'b' if self.whiteToMove else 'w'
        r, c = move.endRow, move.endCol # Location of the piece after moving

        piece_threatens = 0 # Value of pieces threatened
        # Get squares attacked by the piece *from its destination square*
        attack_squares = self.getPieceAttackSquares(r, c) 
        if attack_squares:
            for square in attack_squares:
                target_r, target_c = square
                if 0 <= target_r < 8 and 0 <= target_c < 8: # Check if on board
                    target_piece = self.board[target_r][target_c]
                    # If the attacked square has an enemy piece...
                    if target_piece != '--' and target_piece[0] == enemy_color:
                        # ...add its value (scaled) to the threatened score
                        piece_threatens += pieceScores.get(target_piece[1], 0) * 10 
        
        score += piece_threatens # Add threat bonus to the total score

        # --- Center Control Bonus ---
        # Give a bonus for moving a piece to one of the four central squares
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        if (move.endRow, move.endCol) in center_squares:
            score += 50 # Small bonus for controlling the center

        # --- Pawn Advancement Bonus ---
        if move.pieceMoved[1] == 'p':
            # Calculate how far the pawn has advanced up the board
            if self.whiteToMove:  # White pawns advance from row 6 down to row 0
                pawn_advance = 7 - move.endRow # Higher number means more advanced
            else:  # Black pawns advance from row 1 up to row 7
                pawn_advance = move.endRow # Higher number means more advanced
            
            # Give a small bonus based on how far the pawn advanced
            score += pawn_advance * 2
    
        # --- Castling Bonus ---
        # Castling is generally a good move for king safety and rook activation
        if move.isCastleMove:
            score += 500 # Give a significant bonus for castling
    
        # Return the calculated heuristic score for the move
        return score
    
    def orderMoves(self, moves):
        """
        Sorts a list of moves based on their heuristic score (using scoreMove).
        Moves with higher scores (likely better moves) come first.
        This improves efficiency of search algorithms like alpha-beta pruning.
        """
        moveScores = [] # List to hold tuples of (move, score)

        # Calculate the score for each move in the input list
        for move in moves:
            moveScores.append((move, self.scoreMove(move)))

        # Sort the list of tuples based on the score (the second element, x[1])
        # `reverse=True` puts the highest scores first.
        moveScores.sort(key=lambda x: x[1], reverse=True)

        # Return just the list of moves, now sorted in order of preference
        return [move_tuple[0] for move_tuple in moveScores]

    # --- Attack/Defense Counting (for evaluation/analysis) ---
    def countAttacksAndDefends(self):
        """
        Calculates how many times each piece type attacks enemy pieces 
        and defends friendly pieces across the entire board.
        Updates the self.*_attacks and self.*_defends dictionaries.
        """
        # Reset counts before recalculating
        self.white_attacks = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.white_defends = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.black_attacks = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}
        self.black_defends = {'p': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0, 'K': 0, 'total': 0}

        # Iterate through every square on the board
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                piece = self.board[r][c] # Get the piece on the square
                if piece != '--': # If the square is not empty
                    color = piece[0]      # 'w' or 'b'
                    piece_type = piece[1] # 'p', 'N', 'R', etc.

                    # Get all squares this piece attacks (pseudo-legally)
                    attack_squares = self.getPieceAttackSquares(r, c)
                    if attack_squares is not None: # Make sure we got a list back
                        
                        # Check each square the piece attacks
                        for square in attack_squares:
                            target_r, target_c = square
                            # Ensure target is on board (getPieceAttackSquares should handle this, but double check)
                            if 0 <= target_r < 8 and 0 <= target_c < 8: 
                                target_piece = self.board[target_r][target_c] # Get piece on attacked square

                                if target_piece != '--': # If the attacked square is not empty
                                    target_color = target_piece[0]

                                    # If the attacker and target have different colors -> Attack
                                    if color != target_color:
                                        if color == 'w':
                                            self.white_attacks[piece_type] += 1
                                            self.white_attacks["total"] += 1
                                        else:
                                            self.black_attacks[piece_type] += 1
                                            self.black_attacks["total"] += 1
                                    # If the attacker and target have the same color -> Defense
                                    else: 
                                        if color == 'w':
                                            self.white_defends[piece_type] += 1
                                            self.white_defends['total'] += 1
                                        else:
                                            self.black_defends[piece_type] += 1
                                            self.black_defends['total'] += 1
        
        # Method updates self attributes directly, but could return them too
        return (self.white_attacks, self.white_defends, self.black_attacks, self.black_defends)

    # --- Helper: Get Squares Attacked by a Piece ---
    def getPieceAttackSquares(self, r, c):
        """
        Returns a list of squares (tuples) that the piece at (r, c) attacks.
        This considers only the piece's movement rules, not board boundaries 
        or whether the move is currently legal (ignores pins, checks, etc.).
        Returns an empty list if the square (r,c) is empty.
        """
        piece = self.board[r][c]
        if piece == '--': # If no piece at source square
            return []
        
        color = piece[0]
        piece_type = piece[1]
        attack_squares = [] # List to store (row, col) tuples of attacked squares

        # --- Pawn Attacks ---
        if piece_type == 'p':
            # Pawns attack diagonally forward one square.
            if color == 'w':  # White pawn attacks
                # Check diagonal left (r-1, c-1) and diagonal right (r-1, c+1)
                if c-1 >= 0 and r-1 >= 0: attack_squares.append((r-1, c-1))
                if c+1 < 8 and r-1 >= 0: attack_squares.append((r-1, c+1))
            else:  # Black pawn attacks
                # Check diagonal left (r+1, c-1) and diagonal right (r+1, c+1)
                if c-1 >= 0 and r+1 < 8: attack_squares.append((r+1, c-1))
                if c+1 < 8 and r+1 < 8: attack_squares.append((r+1, c+1))
        
        # --- Knight Attacks ---
        elif piece_type == 'N':
            # Knights attack in an 'L' shape (2 squares in one cardinal direction, then 1 perpendicular)
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
            for move in knight_moves:
                end_row = r + move[0]
                end_col = c + move[1]
                # Check if the potential attack square is on the board
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    attack_squares.append((end_row, end_col))

        # --- Sliding Pieces (Rook, Bishop, Queen) and King Attacks ---
        elif piece_type in ['B', 'R', 'Q', 'K']:
            directions = [] # List to store direction vectors (dr, dc)
            # Add diagonal directions for Bishop and Queen
            if piece_type in ['B', 'Q']: directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
            # Add straight directions for Rook and Queen
            if piece_type in ['R', 'Q']: directions.extend([(-1, 0), (0, -1), (1, 0), (0, 1)])
            # King attacks all adjacent squares (uses all 8 directions)
            if piece_type == 'K': directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

            # Iterate through each valid direction for the piece type
            for d in directions:
                # Iterate outwards along the direction
                for i in range(1, 8): # Max 7 steps away
                    end_row = r + d[0] * i
                    end_col = c + d[1] * i
                    
                    if 0 <= end_row < 8 and 0 <= end_col < 8: # Check if on board
                        # Add the square as attacked regardless of occupancy for now
                        attack_squares.append((end_row, end_col))
                        
                        # --- Stopping Conditions for Sliding Pieces ---
                        # If the square is occupied OR if it's a King (only moves 1 step), stop extending along this ray.
                        # A piece attacks the square it lands on, even if occupied.
                        if self.board[end_row][end_col] != '--' or piece_type == 'K':
                            break 
                    else: # Off board
                        break # Stop extending along this ray

        # Return the list of attacked squares
        return attack_squares
    
    # --- Pseudo-Legal Move Generation ---
    def getAllPossibleMoves(self):
        """
        Generates all *pseudo-legal* moves for the current player.
        Pseudo-legal means the moves follow the rules for how pieces move,
        but they DO NOT account for checks (i.e., a move might be generated
        that leaves the king in check). Pin handling is done within piece move functions.
        """
        moves = [] # Initialize list to store generated Move objects
        # Iterate through every square on the board
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0] # Get the color ('w', 'b', or '-') of the piece
                # Check if the piece belongs to the player whose turn it is
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1] # Get the piece type ('p', 'N', etc.)
                    # Call the appropriate move generation function for this piece type
                    # using the moveFunctions dictionary. Pass the current location (r, c)
                    # and the list `moves` to append generated moves to.
                    self.moveFunctions[piece](r, c, moves) 
        
        return moves # Return the list of all generated pseudo-legal moves

    
    # --- Individual Piece Move Generation Functions ---
    # These generate pseudo-legal moves for a specific piece type at (r, c).
    # They consider board boundaries, empty squares vs captures, and basic special moves.
    # Crucially, they also check for *pins* against the king.

    def getPawnMoves(self, r, c, moves):
        """Generates pseudo-legal pawn moves for the pawn at (r, c)."""
        # --- Check if Pinned ---
        piecePinned = False
        pinDirection = () # Direction of the pin (dx, dy)
        # Iterate through the list of pins calculated earlier
        for i in range(len(self.pins)-1, -1, -1): # Iterate backwards for safe removal
            if self.pins[i][0] == r and self.pins[i][1] == c: # If this pawn is pinned
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                # Remove the pin from the list once handled (prevents re-checking)
                # Note: Queens are handled in both Rook and Bishop moves, so don't remove if Queen?
                # This check seems specific to not removing Queen pins here.
                if self.board[r][c][1] != 'Q': # This check seems misplaced in getPawnMoves
                     self.pins.remove(self.pins[i]) # Remove the pin after finding it for this pawn.
                break # Stop searching for pins for this piece

        # --- Determine Pawn Movement Parameters based on Color ---
        if self.whiteToMove:
            moveAmount = -1    # White pawns move "up" the board (decreasing row index)
            startRow = 6       # White pawns start on row 6 (rank 2)
            backRow = 0        # White pawns promote on row 0 (rank 8)
            enemyColor = 'b'   # White's enemy is black
        else: # Black pawn
            moveAmount = 1     # Black pawns move "down" the board (increasing row index)
            startRow = 1       # Black pawns start on row 1 (rank 7)
            backRow = 7        # Black pawns promote on row 7 (rank 1)
            enemyColor = 'w'   # Black's enemy is white
        
        isPawnPromotion = False # Flag to indicate if a move results in promotion

        # --- En Passant Capture ---
        if self.enPassantPossible: # Check if an en passant capture is possible this turn
            ep_row, ep_col = self.enPassantPossible # Target square for EP capture
            
            # Check if this pawn is correctly positioned to perform the capture:
            # 1. Must be on the correct rank (rank 5 for white, rank 4 for black)
            # 2. Must be adjacent horizontally to the pawn that just moved two squares
            if r == (ep_row - moveAmount) and abs(c - ep_col) == 1: 
                 # Check pin restriction: Pawn must move along the pin line if pinned.
                 # The move direction is (moveAmount, ep_col - c) diagonally.
                if not piecePinned or pinDirection == (moveAmount, ep_col - c):
                    # Add the en passant move (destination is the EP target square)
                    moves.append(Move((r, c), (ep_row, ep_col), self.board, isEnPassantMove=True))

        # --- Forward Moves ---
        # Check 1 square forward
        if 0 <= r + moveAmount < 8: # Ensure target row is on board
            if self.board[r+moveAmount][c] == "--": # Check if the square in front is empty
                # Check pin restriction: If pinned, can only move forward if pin is vertical.
                if not piecePinned or pinDirection == (moveAmount, 0):
                    # Check for promotion when reaching the back rank
                    if r + moveAmount == backRow: isPawnPromotion = True
                    moves.append(Move((r, c), (r+moveAmount, c), self.board, isPawnPromotion=isPawnPromotion))
                    
                    # Check 2 squares forward (only from starting row)
                    if r == startRow and (0 <= r + 2*moveAmount < 8) and self.board[r+2*moveAmount][c] == "--": 
                        # No need to check pin here again, as moving 2 squares requires vertical pin too.
                        moves.append(Move((r, c), (r+2*moveAmount, c), self.board))
        
        # --- Pawn Captures ---
        # Capture Left
        if c - 1 >= 0: # Check if column is on board
            if 0 <= r + moveAmount < 8: # Check if row is on board
                # Check pin restriction: Can only capture if pin is along the capture diagonal.
                if not piecePinned or pinDirection == (moveAmount, -1):
                    # Check if there's an enemy piece on the diagonal square
                    if self.board[r+moveAmount][c-1][0] == enemyColor:
                        # Check for promotion on capture
                        if r + moveAmount == backRow: isPawnPromotion = True
                        moves.append(Move((r, c), (r+moveAmount, c-1), self.board, isPawnPromotion=isPawnPromotion))

        # Capture Right
        if c + 1 <= 7: # Check if column is on board
             if 0 <= r + moveAmount < 8: # Check if row is on board
                # Check pin restriction: Can only capture if pin is along the capture diagonal.
                if not piecePinned or pinDirection == (moveAmount, 1):
                    # Check if there's an enemy piece on the diagonal square
                    if self.board[r+moveAmount][c+1][0] == enemyColor:
                         # Check for promotion on capture
                        if r + moveAmount == backRow: isPawnPromotion = True
                        moves.append(Move((r, c), (r+moveAmount, c+1), self.board, isPawnPromotion=isPawnPromotion))


    def getRookMoves(self, r, c, moves):
        """Generates pseudo-legal rook moves for the piece at (r, c). Also used by Queen."""
        # --- Check Pin --- (Similar to Pawn)
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                # Don't remove the pin if it's a Queen, as getBishopMoves will need it too.
                if self.board[r][c][1] != 'Q': 
                    self.pins.remove(self.pins[i])
                break
        
        # Rooks move horizontally and vertically
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1)) # Up, Left, Down, Right
        enemyColor = 'b' if self.whiteToMove else 'w'
        
        for d in directions: # Iterate through each of the 4 directions
            for i in range(1, 8): # Check up to 7 squares away
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: # Check if on board
                    # Check pin restriction: Can only move along the pin line (forward or backward).
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--": # If the square is empty
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor: # If it's an enemy piece
                            moves.append(Move((r, c), (endRow, endCol), self.board)) # Capture move
                            break # Stop searching further in this direction (blocked by capture)
                        else: # If it's a friendly piece
                            break # Stop searching further in this direction (blocked by friendly piece)
                else: # Off board
                    break # Stop searching further in this direction


    def getKnightMoves(self, r, c, moves):
        """Generates pseudo-legal knight moves for the knight at (r, c)."""
         # --- Check Pin --- Knights cannot move if pinned, as they can't stay on the pin line.
        piecePinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i]) # Remove the pin, knight can't move anyway
                break 
        
        # If the knight is pinned, it has no legal moves.
        if piecePinned:
            return # Exit the function early

        # Define the 8 possible L-shaped knight moves
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = 'w' if self.whiteToMove else 'b'
        
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8: # Check if the destination square is on the board
                 # Since we already checked for pins, any on-board move is potentially valid
                 endPiece = self.board[endRow][endCol]
                 # Check if the destination square is empty or occupied by an enemy piece
                 if endPiece[0] != allyColor: 
                     moves.append(Move((r, c), (endRow, endCol), self.board))


    def getBishopMoves(self, r, c, moves):
        """Generates pseudo-legal bishop moves for the piece at (r, c). Also used by Queen."""
        # --- Check Pin --- (Similar to Rook)
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                break
        
        # Bishops move diagonally
        directions = ((1, 1), (1, -1), (-1, 1), (-1, -1)) # Down-Right, Down-Left, Up-Right, Up-Left
        enemyColor = 'b' if self.whiteToMove else 'w'
        
        for d in directions: # Iterate through the 4 diagonal directions
            for i in range(1, 8): # Check up to 7 squares away
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: # Check if on board
                    # Check pin restriction: Can only move along the pin line.
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--": # Empty square
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor: # Enemy piece
                            moves.append(Move((r, c), (endRow, endCol), self.board)) # Capture
                            break # Stop searching further (blocked)
                        else: # Friendly piece
                            break # Stop searching further (blocked)
                else: # Off board
                    break # Stop searching further


    def getKingMoves(self, r, c, moves):
        """Generates pseudo-legal king moves for the king at (r, c)."""
        # Define the 8 adjacent squares the king can potentially move to
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = 'w' if self.whiteToMove else 'b'
        
        for i in range(8): # Check each of the 8 adjacent squares
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8: # Check if the square is on the board
                endPiece = self.board[endRow][endCol]
                # Check if the destination square is empty or contains an enemy piece
                if endPiece[0] != allyColor:
                    # --- Crucial Check: Does the move place the King in check? ---
                    # Temporarily update the king's location in the GameState
                    # This is needed because checkForPinsAndChecks relies on the stored location.
                    originalKingLocation = (r, c) # Store original location
                    if allyColor == 'w':
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    
                    # Check if the king would be in check *after* moving to the new square
                    # Note: This recalculates all checks/pins, which is slightly inefficient.
                    # A faster way would be to just check if the destination square is attacked.
                    inCheck, pins, checks = self.checkForPinsAndChecks() 
                    
                    if not inCheck: # If the king is NOT in check on the destination square...
                        # ...then the move is legal (at least regarding checks).
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    
                    # --- Restore King Location ---
                    # IMPORTANT: Restore the king's location back to the original position
                    # regardless of whether the move was added or not.
                    if allyColor == 'w':
                        self.whiteKingLocation = originalKingLocation
                    else:
                        self.blackKingLocation = originalKingLocation
        
        # Note: Castling moves are handled separately in getCastleMoves, not here.

    # --- Castling Move Generation ---
    def getCastleMoves(self, r, c, moves):
        """
        Generates legal castling moves (if available) for the king at (r, c).
        Appends valid castling moves to the `moves` list.
        Checks: King not currently in check, castling rights available.
        Side-specific checks (empty squares, non-attacked squares) are in helper methods.
        """
        # Cannot castle if the king is currently in check.
        if self.squareUnderAttack(r, c):
            return # Exit, no castling allowed
        
        # Check King-side Castling rights
        if (self.whiteToMove and self.currentCastlingRights.wks) or \
           (not self.whiteToMove and self.currentCastlingRights.bks):
            self.getKingSideCastleMoves(r, c, moves) # Check conditions for king-side
            
        # Check Queen-side Castling rights
        if (self.whiteToMove and self.currentCastlingRights.wqs) or \
           (not self.whiteToMove and self.currentCastlingRights.bqs):
            self.getQueenSideCastleMoves(r, c, moves) # Check conditions for queen-side
        
    def getKingSideCastleMoves(self, r, c, moves):
        """Checks conditions and generates King-side castling move."""
        # Check if the squares between king and rook (f1/f8, g1/g8) are empty
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
            # Check if the king passes through or lands on an attacked square (f1/f8, g1/g8)
            if not self.squareUnderAttack(r, c+1) and not self.squareUnderAttack(r, c+2):
                # If all conditions met, add the king-side castle move
                moves.append(Move((r, c), (r, c+2), self.board, isCastleMove=True))

    def getQueenSideCastleMoves(self, r, c, moves):
        """Checks conditions and generates Queen-side castling move."""
        # Check if the squares between king and rook (d1/d8, c1/c8, b1/b8) are empty
        if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--':
             # Check if the king passes through or lands on an attacked square (d1/d8, c1/c8)
             # Note: King doesn't move to b1/b8, so no need to check attack there.
            if not self.squareUnderAttack(r, c-1) and not self.squareUnderAttack(r, c-2):
                # If all conditions met, add the queen-side castle move
                moves.append(Move((r, c), (r, c-2), self.board, isCastleMove=True))

    def getQueenMoves(self, r, c, moves):
        """Generates pseudo-legal queen moves by combining Rook and Bishop moves."""
        # A Queen moves like a Rook and a Bishop combined.
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)
        
# --- Castling Rights Class ---
class CastlingRights():
    """Simple data class to store the four castling rights flags."""
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks # White King Side castling available
        self.bks = bks # Black King Side castling available
        self.wqs = wqs # White Queen Side castling available
        self.bqs = bqs # Black Queen Side castling available


# Represents a single move in the chess game.
class Move():
    """
    Stores all the information about a single chess move, including start/end squares,
    pieces involved, and whether it's a special move like castling, en passant, or promotion.
    Also includes methods for generating standard chess notation and comparing moves.
    """

    # --- Class Variables for Notation Conversion ---
    # Dictionaries to map between chess notation (ranks '1'-'8', files 'a'-'h')
    # and the internal list indices (rows 0-7, cols 0-7).
    # Useful for parsing and generating human-readable moves.
    # '1' corresponds to row 7, '8' to row 0. 'a' corresponds to col 0, 'h' to col 7.
    ranksToRows = {'1':7, '2':6, '3':5, '4':4, '5':3, '6':2, '7':1, '8':0}
    rowsToRanks = {v:k for k,v in ranksToRows.items()} # Reverse mapping (row index to rank char)
    filesToCols = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7}
    colsToFiles = {v:k for k,v in filesToCols.items()} # Reverse mapping (col index to file char)


    def __init__(self, startSq, endSq, board, isPawnPromotion = False, isEnPassantMove = False, isCastleMove = False, promotionChoice='Q'):
        """
        Initializes a Move object.

        Args:
            startSq (tuple): (row, col) of the starting square.
            endSq (tuple): (row, col) of the ending square.
            board (list[list[str]]): The current state of the board (needed to determine pieces moved/captured).
            isPawnPromotion (bool, optional): Flag if the move is a pawn promotion. Defaults to False.
            isEnPassantMove (bool, optional): Flag if the move is an en passant capture. Defaults to False.
            isCastleMove (bool, optional): Flag if the move is castling. Defaults to False.
            promotionChoice (str, optional): The piece chosen for promotion ('Q', 'R', 'B', 'N'). Defaults to 'Q'.
        """
        # Store the start and end square coordinates
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        
        # Determine the piece being moved and the piece being captured (if any)
        # by looking at the board state *when the move object is created*.
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol] # Will be '--' if no capture
        
        # Simple flag to check if the move is a capture
        self.isCapture = (self.pieceCaptured != "--")
        
        # --- Pawn Promotion ---
        # Store the promotion flag passed in or determined automatically
        self.isPawnPromotion = isPawnPromotion
        self.promotionChoice = promotionChoice # Default to Queen if not specified otherwise

        # Automatically set isPawnPromotion flag if a pawn reaches the back rank.
        # This handles cases where the flag wasn't explicitly set during move generation.
        if (self.pieceMoved == 'wp' and self.endRow == 0) or \
           (self.pieceMoved == 'bp' and self.endRow == 7):
            self.isPawnPromotion = True
            # Note: We still need the `promotionChoice` to be set correctly elsewhere,
            # this just ensures the flag is true if a pawn reaches the end.
        
        # --- En Passant ---
        # Store the en passant flag
        self.isEnPassantMove = isEnPassantMove
        # Special case for en passant: the captured pawn is *not* on the end square.
        # We need to explicitly set the captured piece based on the moving pawn's color.
        if self.isEnPassantMove:
            self.pieceCaptured = 'wp' if self.pieceMoved == 'bp' else 'bp' # Correctly identify the captured pawn
            self.isCapture = True # En passant is always a capture

        # --- Castling ---
        # Store the castling flag
        self.isCastleMove = isCastleMove

        # --- Move Identification ---
        # Generate a unique integer ID for this move based on start/end squares.
        # Useful for comparing moves quickly (e.g., in `__eq__`).
        # Format: startRow * 1000 + startCol * 100 + endRow * 10 + endCol
        # Example: e2e4 -> 6*1000 + 4*100 + 4*10 + 4 = 6444
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol 

    
    def __eq__(self, other):
        """
        Overrides the default equality comparison (==) for Move objects.
        Two moves are considered equal if they have the same start and end squares (same moveID).
        Note: This does NOT compare promotion choice or other flags, only the basic movement.
        """
        if isinstance(other, Move): # Check if the other object is also a Move instance
            return self.moveID == other.moveID # Compare based on the pre-calculated moveID
        return False # Not equal if the other object is not a Move

    def getChessNotation(self, board=None, getAllPossibleMoves=None):
        """
        Generates the Standard Algebraic Notation (SAN) string for the move.
        Handles piece names, captures, checks, checkmates, promotions, castling,
        and disambiguation (e.g., Raxd1 vs R1xd1).

        Args:
            board (list[list[str]], optional): The current board state. Needed ONLY for disambiguation.
            getAllPossibleMoves (function, optional): A function reference (like GameState.getAllPossibleMoves).
                                                     Needed ONLY for disambiguation logic.

        Returns:
            str: The move in standard algebraic notation.
        """
        
        # --- Handle Castling First ---
        if self.isCastleMove:
            # King-side castle ends on column 6 (g-file)
            # Queen-side castle ends on column 2 (c-file)
            return "O-O" if self.endCol == 6 else "O-O-O"
        
        moveString = "" # Start building the notation string
        
        # --- Piece Prefix (omit for pawns) ---
        if self.pieceMoved[1] != 'p': # If it's not a pawn move...
            moveString = self.pieceMoved[1] # ...add the piece letter (N, B, R, Q, K)
            
            # --- Disambiguation Logic ---
            # Check if multiple pieces of the same type could have moved to the same square.
            # This requires the board state and a way to generate moves for other pieces.
            if board is not None and getAllPossibleMoves is not None:
                sameTypePiecesToSameSquare = [] # List to store locations of ambiguous pieces
                color = self.pieceMoved[0]
                piece_type = self.pieceMoved[1]
                
                # Find other pieces of the same type and color
                for r in range(8):
                    for c in range(8):
                        # If it's the same piece type/color, but NOT the piece making the current move...
                        if board[r][c] == color + piece_type and (r, c) != (self.startRow, self.startCol):
                            # ...generate its possible moves to see if it could also reach the target square
                            possibleMoves = []
                            
                            # Check if any generated move ends on the same square as our current move
                            for move in possibleMoves: # Need to generate these moves! This part is incomplete/conceptual.
                                if move.endRow == self.endRow and move.endCol == self.endCol:
                                    sameTypePiecesToSameSquare.append((r, c)) # Found an ambiguous piece
                                    break # No need to check other moves for this piece
                
                # If ambiguous pieces were found...
                if sameTypePiecesToSameSquare:
                    # Determine if the ambiguous pieces share the same file or rank as the current piece
                    sameFile = any(c == self.startCol for r, c in sameTypePiecesToSameSquare)
                    sameRank = any(r == self.startRow for r, c in sameTypePiecesToSameSquare)
                    
                    # Add disambiguation to the move string based on standard rules:
                    # 1. If files are different, add the starting file. (e.g., Raxd1)
                    # 2. If files are the same, but ranks are different, add the starting rank. (e.g., R1xd1)
                    # 3. If both file and rank are the same (shouldn't happen with >2 pieces?), add full coords. (e.g., Ra1xd1) - Standard usually just file+rank if needed.
                    if not sameFile:
                        moveString += self.colsToFiles[self.startCol]
                    elif not sameRank:
                        moveString += self.rowsToRanks[self.startRow]
                    else: # Both file and rank are shared by ambiguous pieces
                        moveString += self.colsToFiles[self.startCol] + self.rowsToRanks[self.startRow]

        # --- Pawn Captures (Need starting file) ---
        elif self.pieceMoved[1] == 'p' and self.isCapture:
            # Pawn captures include the starting file letter (e.g., "exd5")
            moveString = self.colsToFiles[self.startCol]
    
        # --- Capture Indicator ---
        if self.isCapture:
            moveString += 'x' # Add 'x' for captures
    
        # --- Destination Square ---
        # Add the destination square in algebraic notation (e.g., "e4", "h8")
        moveString += self.getRankFile(self.endRow, self.endCol)
    
        # --- Promotion ---
        if self.isPawnPromotion:
            # Add the promotion notation (e.g., "=Q")
            moveString += '=' + self.promotionChoice
    
        # --- Checks and Checkmates (Not handled here) ---
        # Note: Adding '+' for check or '#' for checkmate usually requires analyzing
        # the board state *after* the move is made, so it's typically done
        # outside the Move class itself when formatting the final output.
    
        return moveString # Return the constructed notation string
    

    def getRankFile(self, r, c):
        """Helper function to convert row and column indices to algebraic notation (e.g., (0, 4) -> "e8")."""
        return self.colsToFiles[c] + self.rowsToRanks[r]
    
    def __str__(self):
        """
        Overrides the default string conversion (`str(move_object)`).
        Returns the standard algebraic notation of the move.
        Note: Disambiguation requires board state and move generation context.
        """
        # Simply call getChessNotation. If disambiguation is needed and context wasn't provided,
        # it will return the non-disambiguated form.
        moveString = self.getChessNotation() 

        return moveString # Return the generated notation