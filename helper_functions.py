

def initMvvLva():
    """Initialize the MVV-LVA (Most Valuable Victim - Least Valuable Attacker) table"""
    # Piece values: None, pawn, knight, bishop, rook, queen, king
    piece_values = {'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 10}
    mvv_lva = {}
    
    # Fill the table: 10 * victim value - attacker value
    # This ensures capturing a queen with a pawn (9*10-1=89) is better than 
    # capturing a pawn with a queen (1*10-9=1)
    for attacker in piece_values:
        mvv_lva[attacker] = {}
        for victim in piece_values:
            mvv_lva[attacker][victim] = piece_values[victim] * 10 - piece_values[attacker]
    
    return mvv_lva