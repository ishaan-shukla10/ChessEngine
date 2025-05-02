import random

class ZobristHash:
    def __init__(self, seed=42):
        # Set a fixed seed for reproducibility - super important for debugging!
        random.seed(seed) 
        
        # Generate random bitstrings for each piece at each position
        # These are like the unique "fingerprints" for each piece-square combo
        self.piece_keys = {}
        for piece in ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']:
            self.piece_keys[piece] = {}
            for row in range(8):
                for col in range(8):
                    self.piece_keys[piece][(row, col)] = random.getrandbits(64)
        
        # Random key for the side to move - we'll toggle this each move
        # XOR'ing with this essentially flips a bit when the side changes
        self.side_to_move_key = random.getrandbits(64)
        
        # Keys for castling rights - one for each potential castling option
        # K = white kingside, Q = white queenside, k = black kingside, q = black queenside
        self.castling_keys = {
            'K': random.getrandbits(64),  # White kingside
            'Q': random.getrandbits(64),  # White queenside
            'k': random.getrandbits(64),  # Black kingside
            'q': random.getrandbits(64)   # Black queenside
        }
        
        # Keys for en passant possibilities (one for each column)
        # Only need to track the column since the row is implied by the side to move
        self.en_passant_keys = {}
        for col in range(8):
            self.en_passant_keys[col] = random.getrandbits(64)
    
    def hash_position(self, board, white_to_move=True, castling_rights=None, en_passant_col=-1):
        # Calculate the Zobrist hash for a given board position from scratch
        # This is slower than incremental updates but needed for the initial position
        h = 0
        
        # XOR in each piece on the board
        # The magic of Zobrist hashing is that order doesn't matter due to XOR properties
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != "--":  # Only hash actual pieces, not empty squares
                    h ^= self.piece_keys[piece][(row, col)]
        
        # XOR in the side to move (if black)
        if not white_to_move:
            h ^= self.side_to_move_key
        
        # XOR in castling rights - only if they exist
        # Tried to save a few cycles by checking castling_rights first
        if castling_rights:
            if castling_rights.wks:
                h ^= self.castling_keys['K']
            if castling_rights.wqs:
                h ^= self.castling_keys['Q']
            if castling_rights.bks:
                h ^= self.castling_keys['k']
            if castling_rights.bqs:
                h ^= self.castling_keys['q']
        
        # XOR in en passant square if it exists
        # Using -1 as a sentinel value for "no en passant possible"
        if 0 <= en_passant_col < 8:
            h ^= self.en_passant_keys[en_passant_col]
        
        return h
    
    def update_hash(self, h, move, board, white_to_move, prev_castling, new_castling, 
                    prev_en_passant_col, new_en_passant_col):
        # Update existing hash with a new move - WAY faster than recalculating from scratch
        # The key insight is we only need to XOR out the changed bits and XOR in the new bits
        
        # Toggle side to move - always changes after a move
        h ^= self.side_to_move_key
        
        # Update en passant square if needed
        # First remove the old en passant possibility (if there was one)
        if 0 <= prev_en_passant_col < 8:
            h ^= self.en_passant_keys[prev_en_passant_col]
        # Then add the new en passant possibility (if there is one)
        if 0 <= new_en_passant_col < 8:
            h ^= self.en_passant_keys[new_en_passant_col]
        
        # Update castling rights - only XOR if they changed
        if prev_castling.wks != new_castling.wks:
            h ^= self.castling_keys['K']
        if prev_castling.wqs != new_castling.wqs:
            h ^= self.castling_keys['Q']
        if prev_castling.bks != new_castling.bks:
            h ^= self.castling_keys['k']
        if prev_castling.bqs != new_castling.bqs:
            h ^= self.castling_keys['q']
        
        # Get move coordinates - makes the code more readable
        start_row, start_col = move.startRow, move.startCol
        end_row, end_col = move.endRow, move.endCol
        
        # Remove the piece from its starting square
        piece_moved = move.pieceMoved
        h ^= self.piece_keys[piece_moved][(start_row, start_col)]
        
        # Handle captures - need to remove the captured piece from the hash
        if move.isCapture:
            if move.isEnPassantMove:
                # Special case for en passant - captured pawn isn't at the end coordinates!
                captured_row = start_row
                captured_col = end_col
                captured_piece = 'wp' if piece_moved[0] == 'b' else 'bp'  # Opposite color pawn
                h ^= self.piece_keys[captured_piece][(captured_row, captured_col)]
            else:
                # Normal capture - just remove the piece at the destination
                h ^= self.piece_keys[move.pieceCaptured][(end_row, end_col)]
        
        # Handle castling - need to move the rook too
        if move.isCastleMove:
            rook_start_row = start_row
            rook_start_col = 0 if end_col < start_col else 7  # Queenside or kingside
            rook_end_col = 3 if end_col < start_col else 5    # New rook position
            
            rook_piece = 'wR' if piece_moved[0] == 'w' else 'bR'
            
            # Remove rook from starting position
            h ^= self.piece_keys[rook_piece][(rook_start_row, rook_start_col)]
            
            # Add rook at new position
            h ^= self.piece_keys[rook_piece][(rook_start_row, rook_end_col)]
        
        # Handle pawn promotion - the piece type changes!
        if move.isPawnPromotion:
            promoted_piece = piece_moved[0] + move.promotionChoice  # Like 'wQ' for white queen
            h ^= self.piece_keys[promoted_piece][(end_row, end_col)]
        else:
            # Normal move - just add piece at its new square
            h ^= self.piece_keys[piece_moved][(end_row, end_col)]
        
        return h