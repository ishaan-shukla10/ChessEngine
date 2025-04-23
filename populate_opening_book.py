import os
import argparse
import re
import json
from openingbook import OpeningBook
from chessengine import GameState, Move

class MoveEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for Move objects
    """
    def default(self, obj):
        if isinstance(obj, Move):
            # Convert Move object to a serializable dictionary
            return {
                'startRow': obj.startRow,
                'startCol': obj.startCol,
                'endRow': obj.endRow,
                'endCol': obj.endCol,
                'pieceMoved': obj.pieceMoved,
                'pieceCaptured': obj.pieceCaptured,
                'moveID': obj.moveID if hasattr(obj, 'moveID') else None,
                'isEnPassantMove': obj.isEnPassantMove if hasattr(obj, 'isEnPassantMove') else False,
                'isPawnPromotion': obj.isPawnPromotion if hasattr(obj, 'isPawnPromotion') else False,
                'promotionChoice': obj.promotionChoice if hasattr(obj, 'promotionChoice') else None,
                'isCastleMove': obj.isCastleMove if hasattr(obj, 'isCastleMove') else False,
                'isCapture': obj.isCapture if hasattr(obj, 'isCapture') else False
            }
        return super().default(obj)

class CustomOpeningBook(OpeningBook):
    """
    Extended OpeningBook class with improved JSON serialization
    """
    def save_book(self):
        """
        Save the opening book to file with proper JSON serialization
        """
        try:
            with open(self.book_file, 'w') as f:
                # Convert integer keys to strings for JSON compatibility and use custom encoder
                json.dump({str(k): v for k, v in self.opening_positions.items()}, f, indent=2, cls=MoveEncoder)
            print(f"Saved {len(self.opening_positions)} opening positions")
        except Exception as e:
            print(f"Error saving opening book: {str(e)}")

class PgnParser:
    """
    A more robust PGN parser for chess games
    """
    def __init__(self):
        # Regex for extracting moves from PGN
        self.move_regex = re.compile(r'(?:\d+\.\s*)(?:(?P<white>[a-zA-Z0-9+#=\-]+)(?:\s+|\{[^}]*\}\s*)(?P<black>[a-zA-Z0-9+#=\-]+)?)')
        # Regex for extracting just a single move
        self.single_move_regex = re.compile(r'[a-zA-Z0-9+#=\-]+')
        
    def parse_pgn_file(self, file_path):
        """
        Parse all games from a PGN file
        Returns a list of games, each game being a list of move texts
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Split the content into individual games
            game_texts = re.split(r'\n\n\[Event ', content)
            if len(game_texts) > 1:
                # Fix the first split
                game_texts = [game_texts[0]] + ['[Event ' + game for game in game_texts[1:]]
            
            games = []
            for game_text in game_texts:
                if not game_text.strip():
                    continue
                    
                # Extract the moves section (everything after the last header)
                moves_text = re.split(r']\s*\n', game_text)[-1]
                
                # Remove comments and annotations
                moves_text = re.sub(r'\{[^}]*\}', ' ', moves_text)
                moves_text = re.sub(r'\([^)]*\)', ' ', moves_text)
                moves_text = re.sub(r'\$\d+', '', moves_text)
                
                # Extract moves using regex
                moves = []
                for match in self.move_regex.finditer(moves_text):
                    if match.group('white'):
                        moves.append(match.group('white'))
                    if match.group('black'):
                        moves.append(match.group('black'))
                
                # If regex didn't work well, try simple extraction
                if not moves:
                    moves = [m for m in self.single_move_regex.findall(moves_text) 
                             if not m.endswith('.') and not m.isdigit() and m != '-']
                
                games.append(moves)
            
            return games
        except Exception as e:
            print(f"Error parsing PGN file {file_path}: {str(e)}")
            return []

    def find_matching_move(self, move_text, valid_moves):
        """
        Find a valid move that matches the PGN move text
        """
        # Try direct notation matching
        for valid_move in valid_moves:
            if valid_move.getChessNotation() == move_text:
                return valid_move
        
        # If direct matching fails, try to parse pawn moves like "d5"
        if len(move_text) == 2 and move_text[0] in 'abcdefgh' and move_text[1] in '12345678':
            file_char, rank_char = move_text[0], move_text[1]
            end_col = ord(file_char) - ord('a')
            end_row = 8 - int(rank_char)
            
            # Find pawn moves to this target square
            for valid_move in valid_moves:
                if valid_move.pieceMoved[1] == 'p' and valid_move.endRow == end_row and valid_move.endCol == end_col:
                    return valid_move
        
        # Handle captures like "dxe5"
        if len(move_text) == 4 and move_text[0] in 'abcdefgh' and move_text[1] == 'x' and move_text[2] in 'abcdefgh' and move_text[3] in '12345678':
            start_file, end_file, rank_char = move_text[0], move_text[2], move_text[3]
            start_col = ord(start_file) - ord('a')
            end_col = ord(end_file) - ord('a')
            end_row = 8 - int(rank_char)
            
            # Find pawn capture moves
            for valid_move in valid_moves:
                if (valid_move.pieceMoved[1] == 'p' and valid_move.startCol == start_col and 
                    valid_move.endCol == end_col and valid_move.endRow == end_row and valid_move.isCapture):
                    return valid_move
        
        # Handle piece moves like "Nf3"
        if len(move_text) == 3 and move_text[0] in 'NBRQK' and move_text[1] in 'abcdefgh' and move_text[2] in '12345678':
            piece_type, file_char, rank_char = move_text[0], move_text[1], move_text[2]
            end_col = ord(file_char) - ord('a')
            end_row = 8 - int(rank_char)
            
            # Find piece moves to this target square
            for valid_move in valid_moves:
                if valid_move.pieceMoved[1] == piece_type and valid_move.endRow == end_row and valid_move.endCol == end_col:
                    return valid_move
                
        # Handle disambiguated piece moves like "Nbd2" (Knight from b-file to d2)
        if len(move_text) == 4 and move_text[0] in 'NBRQK' and move_text[1] in 'abcdefgh' and move_text[2] in 'abcdefgh' and move_text[3] in '12345678':
            piece_type, from_file, to_file, rank_char = move_text[0], move_text[1], move_text[2], move_text[3]
            from_col = ord(from_file) - ord('a')
            end_col = ord(to_file) - ord('a')
            end_row = 8 - int(rank_char)
    
            for valid_move in valid_moves:
                if (valid_move.pieceMoved[1] == piece_type and 
                    valid_move.startCol == from_col and
                    valid_move.endRow == end_row and 
                    valid_move.endCol == end_col):
                    return valid_move
        

                    
        # Handle piece captures like "Nxd5"
        if len(move_text) == 4 and move_text[0] in 'NBRQK' and move_text[1] == 'x' and move_text[2] in 'abcdefgh' and move_text[3] in '12345678':
            piece_type, file_char, rank_char = move_text[0], move_text[2], move_text[3]
            end_col = ord(file_char) - ord('a')
            end_row = 8 - int(rank_char)
            
            # Find piece capture moves to this target square
            for valid_move in valid_moves:
                if (valid_move.pieceMoved[1] == piece_type and valid_move.endRow == end_row and 
                    valid_move.endCol == end_col and valid_move.isCapture):
                    return valid_move
        
        # Handle castling
        if move_text == "O-O" or move_text == "0-0":  # Kingside castling
            for valid_move in valid_moves:
                if valid_move.isCastleMove and valid_move.endCol > valid_move.startCol:
                    return valid_move
        if move_text == "O-O-O" or move_text == "0-0-0":  # Queenside castling
            for valid_move in valid_moves:
                if valid_move.isCastleMove and valid_move.endCol < valid_move.startCol:
                    return valid_move
                    
        # Handle moves with check/checkmate symbols
        if move_text.endswith('+') or move_text.endswith('#'):
            return self.find_matching_move(move_text[:-1], valid_moves)
        
        return None

def import_pgn_game_improved(parser, game_moves, opening_book, max_moves=15, quality=1):
    """
    Import moves from a PGN game into the opening book using the improved parser
    """
    gs = GameState()
    moves_imported = 0
    
    for i, move_text in enumerate(game_moves):
        if moves_imported >= max_moves:
            break
            
        # Skip move numbers, comments, etc.
        if not move_text or move_text.isdigit() or move_text.endswith('.'):
            continue
            
        valid_moves = gs.getValidMoves()
        found_move = parser.find_matching_move(move_text, valid_moves)
        
        if found_move:
            # Add to opening book before making the move
            opening_book.add_position(gs.board, found_move, quality)
            gs.makeMove(found_move)
            moves_imported += 1
        else:
            print(f"Move not recognized: {move_text}")
            break
    
    return moves_imported

def populate_from_directory(directory_path, max_moves=15, quality=1):
    """
    Populate the opening book from all PGN files in a directory
    """
    book = CustomOpeningBook()
    parser = PgnParser()
    total_moves = 0
    games_processed = 0
    
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory")
        return 0
    
    # Get all .pgn files in the directory
    pgn_files = [f for f in os.listdir(directory_path) if f.endswith('.pgn')]
    
    if not pgn_files:
        print(f"No PGN files found in {directory_path}")
        return 0
    
    print(f"Found {len(pgn_files)} PGN files to process")
    
    for pgn_file in pgn_files:
        file_path = os.path.join(directory_path, pgn_file)
        print(f"Processing {pgn_file}...")
        
        games = parser.parse_pgn_file(file_path)
        file_moves = 0
        
        for i, game_moves in enumerate(games):
            moves_imported = import_pgn_game_improved(parser, game_moves, book, max_moves, quality)
            file_moves += moves_imported
            total_moves += moves_imported
            games_processed += 1
            
            if (games_processed % 100) == 0:
                print(f"Processed {games_processed} games, imported {total_moves} total moves")
                # Periodically save to avoid losing data if the process stops
                book.save_book()
        
        print(f"Imported {file_moves} moves from {len(games)} games in {pgn_file}")
    
    print(f"Total moves imported: {total_moves} from {games_processed} games")
    book.save_book()
    return total_moves

def populate_from_specific_games(pgn_files, max_moves=15, quality=1):
    """
    Populate the opening book from specific PGN files
    """
    book = CustomOpeningBook()
    parser = PgnParser()
    total_moves = 0
    games_processed = 0
    
    for pgn_file in pgn_files:
        if not os.path.isfile(pgn_file):
            print(f"Warning: {pgn_file} is not a valid file, skipping")
            continue
        
        print(f"Processing {pgn_file}...")
        games = parser.parse_pgn_file(pgn_file)
        file_moves = 0
        
        for i, game_moves in enumerate(games):
            moves_imported = import_pgn_game_improved(parser, game_moves, book, max_moves, quality)
            file_moves += moves_imported
            total_moves += moves_imported
            games_processed += 1
            
            if (games_processed % 100) == 0:
                print(f"Processed {games_processed} games, imported {total_moves} total moves")
                # Periodically save to avoid losing data if the process stops
                book.save_book()
        
        print(f"Imported {file_moves} moves from {len(games)} games in {pgn_file}")
    
    print(f"Total moves imported: {total_moves} from {games_processed} games")
    book.save_book()
    return total_moves

def main():
    parser = argparse.ArgumentParser(description='Populate chess opening book from PGN files')
    
    # Command arguments
    parser.add_argument('--dir', type=str, help='Directory containing PGN files to import')
    parser.add_argument('--file', type=str, nargs='+', help='Specific PGN file(s) to import')
    parser.add_argument('--max-moves', type=int, default=15, 
                        help='Maximum number of moves to import from the start of each game (default: 15)')
    parser.add_argument('--quality', type=float, default=1.0,
                        help='Quality rating to assign to imported moves (default: 1.0)')
    parser.add_argument('--book-file', type=str, default='opening_book.json',
                        help='Opening book file to use/create (default: opening_book.json)')
    
    args = parser.parse_args()
    
    # Set the book file if specified
    if args.book_file and hasattr(OpeningBook, 'book_file'):
        os.environ['OPENING_BOOK_FILE'] = args.book_file
    
    # Process directory
    if args.dir:
        populate_from_directory(args.dir, args.max_moves, args.quality)
    
    # Process specific files
    if args.file:
        populate_from_specific_games(args.file, args.max_moves, args.quality)
    
    # If no action specified, show help
    if not (args.dir or args.file):
        parser.print_help()

if __name__ == "__main__":
    main()