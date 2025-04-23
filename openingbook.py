import json
import os
import random
from zobrist_hash import ZobristHash
from chessengine import Move

class OpeningBook:
    def __init__(self, book_file="opening_book.json"):
        
        self.book_file = book_file
        self.opening_positions = {}
        self.zobrist = ZobristHash()
        self.load_book()
    
    def load_book(self):
        
        if os.path.exists(self.book_file):
            try:
                with open(self.book_file, 'r') as f:
                    data = json.load(f)
                    
                    
                    for position_hash, moves in data.items():
                        
                        if position_hash.isdigit():
                            position_hash_int = int(position_hash)
                        else:
                            position_hash_int = position_hash
                        
                        self.opening_positions[position_hash_int] = []
                        
                        for move_data in moves:
                            
                            self.opening_positions[position_hash_int].append(move_data)
                            
                print(f"Loaded {len(self.opening_positions)} opening positions")
            except Exception as e:
                print(f"Error loading opening book: {e}")
                self.opening_positions = {}
    
    def save_book(self):
        
        try:
            with open(self.book_file, 'w') as f:

                json.dump({str(k): v for k, v in self.opening_positions.items()}, f, indent=2)
            print(f"Saved {len(self.opening_positions)} opening positions")
        except Exception as e:
            print(f"Error saving opening book: {e}")
    
    def get_position_hash(self, board):
        
        return self.zobrist.hash_position(board)
    
    def json_move_to_move_object(self, move_data, board):
    
        m = move_data["move"]
    
    
        return Move(
        (m["startRow"], m["startCol"]), 
        (m["endRow"], m["endCol"]), 
        board,
        isEnPassantMove=m.get("isEnPassantMove", False),  
        isCastleMove=m.get("isCastleMove", False),        
        isPawnPromotion=m.get("isPawnPromotion", False)   
    )
    
    def add_position(self, board, move, quality=1):
        
        position_hash = self.get_position_hash(board)
        
        
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
                "promotionChoice": getattr(move, 'promotionChoice', "Q"),
                "isCastleMove": move.isCastleMove,
                "isCapture": move.pieceCaptured != "--"
            },
            "freq": 1,
            "quality": quality
        }
        
        if position_hash in self.opening_positions:
           
            for existing_move in self.opening_positions[position_hash]:
                if (existing_move["move"]["startRow"] == move.startRow and
                    existing_move["move"]["startCol"] == move.startCol and
                    existing_move["move"]["endRow"] == move.endRow and
                    existing_move["move"]["endCol"] == move.endCol):
                    
                    existing_move["freq"] += 1
                    existing_move["quality"] = max(existing_move["quality"], quality)
                    break
            else:
                
                self.opening_positions[position_hash].append(move_data)
        else:
            
            self.opening_positions[position_hash] = [move_data]
        
        return position_hash
    
    def get_book_move(self, board, white_to_move=None, castling_rights=None, en_passant_col=None, selection_mode="mixed"):
    
        position_hash = self.get_position_hash(board)
    
        if position_hash not in self.opening_positions:
            return None
    
        moves = self.opening_positions[position_hash]
    
        if not moves:
            return None
    
    
        if selection_mode == "random":
        # Completely random selection (equal probability)
            move_data = random.choice(moves)
            return self.json_move_to_move_object(move_data, board)
    
        elif selection_mode == "quality":
        # Weight by quality instead of frequency
            total_quality = sum(move["quality"] for move in moves)
            choice = random.random() * total_quality
        
            current = 0
            for move_data in moves:
                current += move_data["quality"]
                if current >= choice:
                    return self.json_move_to_move_object(move_data, board)
    
        elif selection_mode == "mixed":
        # Mixed approach - use sqrt of frequency to reduce impact of high frequency moves
            weights = [move["freq"] ** 0.5 * move["quality"] for move in moves]
            total_weight = sum(weights)
            choice = random.random() * total_weight
        
            current = 0
            for i, move_data in enumerate(moves):
                current += weights[i]
                if current >= choice:
                    return self.json_move_to_move_object(move_data, board)
    
        else:  
        # weighted frequency selection
            total_freq = sum(move["freq"] for move in moves)
            choice = random.random() * total_freq
        
            current = 0
            for move_data in moves:
                current += move_data["freq"]
                if current >= choice:
                    return self.json_move_to_move_object(move_data, board)
    
    
        return self.json_move_to_move_object(moves[0], board)

    def import_from_file(self, filename, max_moves=15, quality=1):
        
        try:
            with open(filename, 'r') as f:
                pgn_text = f.read()
            
            
            games = pgn_text.split("[Event ")
            
            total_imported = 0
            for i, game in enumerate(games[1:]):  
                game_text = "[Event " + game
                moves_imported = self.import_pgn_game(game_text, max_moves, quality)
                total_imported += moves_imported
                print(f"Imported {moves_imported} moves from game {i+1}")
            
            print(f"Total imported: {total_imported} moves from {len(games)-1} games")
            self.save_book()
            return total_imported
        except Exception as e:
            print(f"Error importing from file: {e}")
            return 0