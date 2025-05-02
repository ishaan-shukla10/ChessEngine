import json
import os
import random
from zobrist_hash import ZobristHash
from chessengine import Move

class OpeningBook:
    def __init__(self, book_file="opening_book.json"):
        # Default to opening_book.json if no file specified
        # This will store our library of known positions
        self.book_file = book_file
        self.opening_positions = {}
        self.zobrist = ZobristHash()  # For fast position hashing
        self.load_book()
    
    def load_book(self):
        # Try to load existing opening book from disk
        # If it doesn't exist, we'll start with an empty one
        if os.path.exists(self.book_file):
            try:
                with open(self.book_file, 'r') as f:
                    data = json.load(f)
                    
                    # Convert string keys back to integers
                    # (JSON only allows string keys but we need int hashes)
                    for position_hash, moves in data.items():
                        
                        # Handle both string and int hash keys
                        # (older versions might have used different formats)
                        if position_hash.isdigit():
                            position_hash_int = int(position_hash)
                        else:
                            position_hash_int = position_hash
                        
                        self.opening_positions[position_hash_int] = []
                        
                        for move_data in moves:
                            # Add each move for this position
                            self.opening_positions[position_hash_int].append(move_data)
                            
                print(f"Loaded {len(self.opening_positions)} opening positions")
            except Exception as e:
                # Something went wrong - just start fresh
                print(f"Error loading opening book: {e}")
                self.opening_positions = {}
    
    def save_book(self):
        # Dump our opening book to disk
        # Need to convert int keys to strings for JSON compatibility
        try:
            with open(self.book_file, 'w') as f:
                # The {str(k): v for...} trick converts all keys to strings
                json.dump({str(k): v for k, v in self.opening_positions.items()}, f, indent=2)
            print(f"Saved {len(self.opening_positions)} opening positions")
        except Exception as e:
            print(f"Error saving opening book: {e}")
    
    def get_position_hash(self, board):
        # Wrapper to calculate Zobrist hash for current board
        return self.zobrist.hash_position(board)
    
    def json_move_to_move_object(self, move_data, board):
        # Convert a move from our JSON format back to a Move object
        # This is needed because we store moves as simple dicts
        m = move_data["move"]
    
        # Recreate a proper Move object from the saved data
        return Move(
        (m["startRow"], m["startCol"]), 
        (m["endRow"], m["endCol"]), 
        board,
        isEnPassantMove=m.get("isEnPassantMove", False),  # Use .get() to handle older data that might be missing fields
        isCastleMove=m.get("isCastleMove", False),        # Same here
        isPawnPromotion=m.get("isPawnPromotion", False)   # And here
    )
    
    def add_position(self, board, move, quality=1):
        # Add a new move to our opening book
        # Quality is how good we think this move is (1=normal, higher=better)
        position_hash = self.get_position_hash(board)
        
        # Package up the move into a dict for storage
        move_data = {
            "move": {
                "startRow": move.startRow,
                "startCol": move.startCol,
                "endRow": move.endRow,
                "endCol": move.endCol,
                "pieceMoved": move.pieceMoved,
                "pieceCaptured": move.pieceCaptured,
                "moveID": getattr(move, 'moveID', 0),
                "isEnPassantMove": move.isEnPassantMove,
                "isPawnPromotion": move.isPawnPromotion,
                "promotionChoice": getattr(move, 'promotionChoice', "Q"),  # Default to queen for promotion
                "isCastleMove": move.isCastleMove,
                "isCapture": move.pieceCaptured != "--"
            },
            "freq": 1,  # First time we've seen this move
            "quality": quality  # How good is this move?
        }
        
        if position_hash in self.opening_positions:
           # We've seen this position before, check if this exact move exists
            for existing_move in self.opening_positions[position_hash]:
                if (existing_move["move"]["startRow"] == move.startRow and
                    existing_move["move"]["startCol"] == move.startCol and
                    existing_move["move"]["endRow"] == move.endRow and
                    existing_move["move"]["endCol"] == move.endCol):
                    
                    # Found the same move, just update its stats
                    existing_move["freq"] += 1
                    existing_move["quality"] = max(existing_move["quality"], quality)
                    break
            else:
                # This is a new move for this position, add it
                self.opening_positions[position_hash].append(move_data)
        else:
            # This is a totally new position, create an entry for it
            self.opening_positions[position_hash] = [move_data]
        
        return position_hash
    
    def get_book_move(self, board, white_to_move=None, castling_rights=None, en_passant_col=None):
        # Find a move from our opening book for the current position
        # The params after board are unused but kept for backward compatibility
        position_hash = self.get_position_hash(board)
    
        if position_hash not in self.opening_positions:
            return None  # No matching position found
    
        moves = self.opening_positions[position_hash]
    
        if not moves:
            return None  # No moves recorded for this position

        # Weight moves by frequency and quality
        # Square root of frequency ensures we don't just pick the most common move every time
        weights = [move["freq"] ** 0.5 * move["quality"] for move in moves]
        total_weight = sum(weights)
        choice = random.random() * total_weight
        
        # Random weighted selection
        current = 0
        for i, move_data in enumerate(moves):
            current += weights[i]
            if current >= choice:
                return self.json_move_to_move_object(move_data, board)
    
        # Fallback to first move (shouldn't get here but just in case)
        return self.json_move_to_move_object(moves[0], board)

    def import_from_file(self, filename, max_moves=15, quality=1):
        # Import PGN file into our opening book
        # max_moves limits how deep we go (usually just want opening moves)
        try:
            with open(filename, 'r') as f:
                pgn_text = f.read()
            
            # Split on event tags to separate games
            games = pgn_text.split("[Event ")
            
            total_imported = 0
            for i, game in enumerate(games[1:]):  # Skip the first empty split
                game_text = "[Event " + game  # Add back the tag we split on
                moves_imported = self.import_pgn_game(game_text, max_moves, quality)
                total_imported += moves_imported
                print(f"Imported {moves_imported} moves from game {i+1}")
            
            print(f"Total imported: {total_imported} moves from {len(games)-1} games")
            self.save_book()  # Don't forget to save to disk!
            return total_imported
        except Exception as e:
            print(f"Error importing from file: {e}")
            return 0