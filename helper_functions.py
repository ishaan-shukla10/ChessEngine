

def initMvvLva():
    
    piece_values = {'p': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 10}
    mvv_lva = {}
    
    
    for attacker in piece_values:
        mvv_lva[attacker] = {}
        for victim in piece_values:
            mvv_lva[attacker][victim] = piece_values[victim] * 10 - piece_values[attacker]
    
    return mvv_lva