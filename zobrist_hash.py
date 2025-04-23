import random

class ZobristHash:
    def __init__(self, seed=42):
        
        random.seed(seed) 
        
        
        self.piece_keys = {}
        for piece in ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']:
            self.piece_keys[piece] = {}
            for row in range(8):
                for col in range(8):
                    self.piece_keys[piece][(row, col)] = random.getrandbits(64)
        
        
        self.side_to_move_key = random.getrandbits(64)
        
        
        self.castling_keys = {
            'K': random.getrandbits(64),  
            'Q': random.getrandbits(64),  
            'k': random.getrandbits(64),  
            'q': random.getrandbits(64)   
        }
        
        
        self.en_passant_keys = {}
        for col in range(8):
            self.en_passant_keys[col] = random.getrandbits(64)
    
    def hash_position(self, board, white_to_move=True, castling_rights=None, en_passant_col=-1):
        
        h = 0
        
        
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != "--":
                    h ^= self.piece_keys[piece][(row, col)]
        
        
        if not white_to_move:
            h ^= self.side_to_move_key
        
        
        if castling_rights:
            if castling_rights.wks:
                h ^= self.castling_keys['K']
            if castling_rights.wqs:
                h ^= self.castling_keys['Q']
            if castling_rights.bks:
                h ^= self.castling_keys['k']
            if castling_rights.bqs:
                h ^= self.castling_keys['q']
        
        
        if 0 <= en_passant_col < 8:
            h ^= self.en_passant_keys[en_passant_col]
        
        return h
    
    def update_hash(self, h, move, board, white_to_move, prev_castling, new_castling, 
                    prev_en_passant_col, new_en_passant_col):
        
        h ^= self.side_to_move_key
        
       
        if 0 <= prev_en_passant_col < 8:
            h ^= self.en_passant_keys[prev_en_passant_col]
        if 0 <= new_en_passant_col < 8:
            h ^= self.en_passant_keys[new_en_passant_col]
        
        
        if prev_castling.wks != new_castling.wks:
            h ^= self.castling_keys['K']
        if prev_castling.wqs != new_castling.wqs:
            h ^= self.castling_keys['Q']
        if prev_castling.bks != new_castling.bks:
            h ^= self.castling_keys['k']
        if prev_castling.bqs != new_castling.bqs:
            h ^= self.castling_keys['q']
        
        
        start_row, start_col = move.startRow, move.startCol
        end_row, end_col = move.endRow, move.endCol
        
        piece_moved = move.pieceMoved
        h ^= self.piece_keys[piece_moved][(start_row, start_col)]
        
        
        if move.isCapture:
            if move.isEnPassantMove:
                
                captured_row = start_row
                captured_col = end_col
                captured_piece = 'wp' if piece_moved[0] == 'b' else 'bp'
                h ^= self.piece_keys[captured_piece][(captured_row, captured_col)]
            else:
               
                h ^= self.piece_keys[move.pieceCaptured][(end_row, end_col)]
        
        
        if move.isCastleMove:
            rook_start_row = start_row
            rook_start_col = 0 if end_col < start_col else 7  
            rook_end_col = 3 if end_col < start_col else 5    
            
            rook_piece = 'wR' if piece_moved[0] == 'w' else 'bR'
            
            
            h ^= self.piece_keys[rook_piece][(rook_start_row, rook_start_col)]
            
            
            h ^= self.piece_keys[rook_piece][(rook_start_row, rook_end_col)]
        
       
        if move.isPawnPromotion:
            promoted_piece = piece_moved[0] + move.promotionChoice
            h ^= self.piece_keys[promoted_piece][(end_row, end_col)]
        else:
            
            h ^= self.piece_keys[piece_moved][(end_row, end_col)]
        
        return h