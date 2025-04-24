import pygame as p
import chessengine
import smartmovefinder
from multiprocessing import Process, Queue

'''
Variables defined globally to be used in functions
'''

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
NOTATION_HEIGHT_HZ = NOTATION_WIDTH_VT = 20
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // 8
MAX_FPS = 15
IMAGES = {}
SOUNDS = {}

'''
Load Images of pieces from directory using pygame
'''

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(f'images/{piece}.png'), (SQ_SIZE, SQ_SIZE))


'''
Load sounds for different piece movements 
'''

def loadSounds():
    types = ["capture", "castle", "move-check", "move-self", "promote", "notify"]
    for type in types:
        SOUNDS[type] = p.mixer.Sound("sounds/" + type + ".mp3")


'''
Main function which runs the chessboard
'''
def main():
    p.init() # initialize pygame
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH + NOTATION_WIDTH_VT, BOARD_HEIGHT + NOTATION_HEIGHT_HZ)) # set screen dimensions and display
    clock = p.time.Clock() # set clock to define fps later
    screen.fill(p.Color('white')) # start with white screen
    gs = chessengine.GameState() # initialize the GameState variable to access current state of game
    validMoves = gs.getValidMoves() # generate the set of valid moves possible
    moveMade = False # no move is made yet
    animate = False # no animations have to be done yet

    moveLogFont = p.font.SysFont("Arial", 14, False, False) # set font for printing move logs
    
    # load images and sound only once
    loadImages() 
    loadSounds()

    # set necessary variables for later use

    running = True # loop for running game
    sqSelected = () # coordinates of square selected by player
    playerClicks = [] # log of clicks made by player
    gameOver = False
    playerOne = True # For white player, if true -> no computer
    playerTwo = False # For black player, if false -> computer plays
    AIThinking = False
    moveFinderProcess = None
    moveUndone = False

    # necessary variables for dragging and dropping pieces
    piece_dragging = False
    dragged_piece = None
    dragged_piece_pos = ()
    dragged_piece_initial_pos = ()

    # running the game
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo) # if human is playing
        for e in p.event.get():
            
            # stop the game if closed window
            if e.type == p.QUIT: 
                running = False

            # detect mouse clicks and movements
            elif e.type == p.MOUSEBUTTONDOWN:
                    if not gameOver and humanTurn and e.button == 1: # LMB clicks and drags

                        location = p.mouse.get_pos() # get current location of mouse cursor click
                        col = (location[0] - NOTATION_WIDTH_VT) //SQ_SIZE # detect column
                        row = location[1]//SQ_SIZE # detect row
                        
                        if 0 <= col < 8 and 0 <= row < 8: # if bounds satisfied detect square
                            piece = gs.board[row][col]

                            if sqSelected == (row, col) or col >= 8: # double click on same square = unclick
                                sqSelected = ()
                                playerClicks = []
                            else: # if first click, log it
                                sqSelected = (row, col)
                                playerClicks.append(sqSelected)
                            
                            # if piece exists and move order is correct, drag piece
                            if piece != '--' and ((piece[0] == 'w' and gs.whiteToMove) or (piece[0] == 'b' and not gs.whiteToMove)):
                                piece_dragging = True
                                dragged_piece = piece
                                dragged_piece_pos = location
                                dragged_piece_initial_pos = (row, col)

                        # if two squares clicked one after the other
                        if len(playerClicks) == 2:
                            move = chessengine.Move(playerClicks[0], playerClicks[1], gs.board) # detect the move
                            # parse through all valid moves
                            for i in range(len(validMoves)):
                                if move == validMoves[i]: # if move is valid
                                    gs.makeMove(validMoves[i]) # make the move
                                    moveMade = True
                                    playMoveSound(move, gs) # play sound accordingly
                                    animate = True # for animations
                                    sqSelected = () 
                                    playerClicks = []
                                    piece_dragging = False
                                    break

                            if not moveMade: # if no move made, retain the first square selected
                                playerClicks = [sqSelected]

            # when stopped clicking    
            elif e.type == p.MOUSEBUTTONUP:
                if piece_dragging and e.button == 1: # if was LMB
                    location = p.mouse.get_pos()
                    col = (location[0] - NOTATION_WIDTH_VT) //SQ_SIZE
                    row = location[1]//SQ_SIZE

                    # if within bounds, drag the piece
                    if 0 <= col < 8 and 0 <= row < 8:
                        if (row, col) != dragged_piece_initial_pos: # if not dropped into starting square
                            start_row, start_col = dragged_piece_initial_pos
                            
                            isPawnPromotion = False
                            promotionChoice = 'Q' 
                            
                            # detect pawn promotion
                            if gs.board[start_row][start_col][1] == 'p':
                                
                                if (gs.board[start_row][start_col][0] == 'w' and row == 0) or \
                                (gs.board[start_row][start_col][0] == 'b' and row == 7):
                                    isPawnPromotion = True
                                    
                                    is_white = gs.board[start_row][start_col][0] == 'w'
                                    promotionChoice = drawPromotionSelection(screen, 2 if is_white else 1, col, is_white)
                            
                           # set the move after dropping
                            move = chessengine.Move(dragged_piece_initial_pos, (row, col), gs.board, 
                                                isPawnPromotion=isPawnPromotion, 
                                                promotionChoice=promotionChoice)
                            
                            # parse through valid moves
                            for i in range(len(validMoves)):
                                valid_move = validMoves[i]

                                # if move is valid
                                if move.startRow == valid_move.startRow and move.startCol == valid_move.startCol and \
                                move.endRow == valid_move.endRow and move.endCol == valid_move.endCol:
                                    
                                    if isPawnPromotion:
                                        validMoves[i].promotionChoice = promotionChoice
                                    
                                    gs.makeMove(validMoves[i])
                                    moveMade = True
                                    playMoveSound(move, gs)
                                    animate = False
                                    sqSelected = ()
                                    playerClicks = []
                                    break
                    
                    # reset all dragging variables after dropping it
                    piece_dragging = False
                    dragged_piece = None
                    dragged_piece_pos = ()
                    dragged_piece_initial_pos = ()

                    if not moveMade and sqSelected != ():
                        playerClicks = [sqSelected]
            
            # detects mouse drag
            elif e.type == p.MOUSEMOTION:
                if piece_dragging:
                    dragged_piece_pos = p.mouse.get_pos()
            
            # detect keyboard inputs
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # if Z key pressed
                    gs.undoMove() # undo last move
                    moveMade = True
                    playMoveSound(move, gs)
                    animate = False
                    gameOver = False
                    if AIThinking: # if computer was calculating, terminate the process and after new move start thinking again
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True

                if e.key == p.K_r: # if R key pressed, then reset the board to the very start
                    gs = chessengine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
        
        # for computer mvove finding
        if not gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                AIThinking = True
                print("Thinking...")
                returnQueue = Queue()
                moveFinderProcess = Process(target=smartmovefinder.findBestMove, args=(gs, validMoves, returnQueue))
                moveFinderProcess.start()

            if not moveFinderProcess.is_alive():
                print("Done thinking")
                AIMove = returnQueue.get() # get the best move
                if AIMove is None: # if all moves lead to same score, then choose randomly
                    AIMove = smartmovefinder.findRandomMove(validMoves)
                gs.makeMove(AIMove)
                moveMade = True

                playMoveSound(AIMove, gs)
                animate = True
                AIThinking = False

        # reset variables after move is made
        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, sqSelected, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        # draw the board representing current game state
        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont, piece_dragging, dragged_piece, dragged_piece_pos)
        
        # print text accordingly if game over
        if gs.checkmate:
            gameOver = True
            if gs.whiteToMove:
                drawEndGameText(screen, 'Black wins by checkmate')
            else:
                drawEndGameText(screen, 'White wins by checkmate')
        elif gs.stalemate:
            gameOver = True
            drawEndGameText(screen, 'Stalemate')

        clock.tick(MAX_FPS) # set FPS
        p.display.flip()


# play sounds according to type of each move
def playMoveSound(move, gs):
    if gs.inCheck():
        p.mixer.Sound.play(SOUNDS["move-check"])
    elif move.isCapture:
        p.mixer.Sound.play(SOUNDS["capture"])
    elif move.isCastleMove:
        p.mixer.Sound.play(SOUNDS["castle"])
    else:
        p.mixer.Sound.play(SOUNDS["move-self"])

# draw board, highlighted squares if clicked, pieces, move log and notation helpers
def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont, piece_dragging=False, dragged_piece=None, dragged_piece_pos=()):
    drawBoard(screen)
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board, sqSelected, piece_dragging, dragged_piece, dragged_piece_pos)
    drawMoveLog(screen, gs, moveLogFont)
    drawNotationHelper(screen)


# draw 8 x 8 chessboard
def drawBoard(screen):
    global colors
    colors = [p.Color(241, 207, 167), p.Color(186, 99, 52)]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c)%2)]
            p.draw.rect(screen, color, p.Rect(NOTATION_WIDTH_VT + c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


# highlight valid moves when clicked on a piece
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if 0 <= r <8 and 0 <= c < 8:
            if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
                s = p.Surface((SQ_SIZE, SQ_SIZE))
                s.set_alpha(100)
                s.fill(p.Color('blue'))
                screen.blit(s, (NOTATION_WIDTH_VT + c*SQ_SIZE, r*SQ_SIZE))
                s.fill(p.Color('yellow'))
                for move in validMoves:
                    if move.startRow == r and move.startCol == c:
                        screen.blit(s, (NOTATION_WIDTH_VT + move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))


# draw pieces on top of board and highlight squares
def drawPieces(screen, board, sqSelected, piece_dragging=False, dragged_piece=None, dragged_piece_pos=()):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                if not (piece_dragging and (r, c) == sqSelected):
                    screen.blit(IMAGES[piece], p.Rect(NOTATION_WIDTH_VT + c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
    
    if piece_dragging and dragged_piece and dragged_piece_pos:
        # Center the piece on the cursor
        x = min(max(dragged_piece_pos[0] - SQ_SIZE//2, NOTATION_WIDTH_VT), BOARD_WIDTH + NOTATION_WIDTH_VT - SQ_SIZE)
        y = min(max(dragged_piece_pos[1] - SQ_SIZE//2, 0), BOARD_HEIGHT - SQ_SIZE)
        screen.blit(IMAGES[dragged_piece], p.Rect(x, y, SQ_SIZE, SQ_SIZE))


# draw notation helper (1-8) vertically and (a-h) horizontally
def drawNotationHelper(screen):
    font = p.font.SysFont("Georgia", 16, False, False)

    for c in range(DIMENSION):
        file_letter = chr(ord('a') + c)
        textObject = font.render(file_letter, True, p.Color('black'))
        x = c * SQ_SIZE + (SQ_SIZE // 2) - (textObject.get_width() // 2) + 20
        y = BOARD_HEIGHT - (NOTATION_HEIGHT_HZ // 2) - (textObject.get_height() // 2)

        screen.blit(textObject, (x, BOARD_HEIGHT))

    for r in range(DIMENSION):
        rank_number = str(DIMENSION - r)

        textObject = font.render(rank_number, True, p.Color('black'))

        x = (NOTATION_WIDTH_VT // 2) - (textObject.get_width() // 2) + 20
        y = r * SQ_SIZE + (SQ_SIZE // 2) - (textObject.get_height() // 2) 

        screen.blit(textObject, (5, y))
    
    notation_corner = p.Rect(0, BOARD_HEIGHT, NOTATION_WIDTH_VT, NOTATION_HEIGHT_HZ)
    p.draw.rect(screen, p.Color('white'), notation_corner)


# draw move log to see series of moves that lead to current position in game
def drawMoveLog(screen, gs, font):
    moveLogRect = p.Rect(BOARD_WIDTH + NOTATION_WIDTH_VT, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("Black"), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = "   " + str(i//2 + 1) + ". " + str(moveLog[i]) + "  "
        if i + 1 < len(moveLog):
            moveString += str(moveLog[i+1])
        moveTexts.append(moveString)
    movesPerRow = 3
    padding = 5
    textY = padding
    lineSpacing = 2
    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i + j < len(moveTexts):
                text +=  moveTexts[i+j]
        textObject = font.render(text, True, p.Color('White'))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing


# draw text in the middle of the board after game is over
def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    textObject = font.render(text, 0, p.Color('Gray'))
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH//2 - textObject.get_width()/2, BOARD_HEIGHT//2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color('Black'))
    screen.blit(textObject, textLocation.move(2, 2))


# animate pieces going from one square to another
def animateMove(move, screen, sqSelected, board, clock):
    global colors
    coords = []
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 5
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount+1):
        r,c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board, sqSelected)
        color = colors[(move.endRow + move.endCol) %2]
        endSquare = p.Rect(NOTATION_WIDTH_VT + move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        if move.pieceCaptured != '--':
            screen.blit(IMAGES[move.pieceCaptured], endSquare)

        screen.blit(IMAGES[move.pieceMoved], p.Rect(NOTATION_WIDTH_VT + c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

# UI aided selection of piece to promote to, once pawn reaches back rank
def drawPromotionSelection(screen, row, col, is_white):
    if is_white:
        pieces = ['wQ', 'wR', 'wB', 'wN']
    else:
        pieces = ['bQ', 'bR', 'bB', 'bN']

    selection_rect = p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, 4*SQ_SIZE)
    p.draw.rect(screen, p.Color('gray'), selection_rect)
    p.draw.rect(screen, p.Color('black'), selection_rect, 2)

    for i, piece in enumerate(pieces):
        piece_rect = p.Rect(col*SQ_SIZE, (row+i)*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        screen.blit(IMAGES[piece], piece_rect)

    p.display.flip()

    waiting_for_selection = True
    while waiting_for_selection:
        for e in p.event.get():
            if e.type == p.QUIT:
                return 'Q' 
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos()
                click_col = (location[0] - NOTATION_WIDTH_VT) // SQ_SIZE
                click_row = location[1] // SQ_SIZE
                
                if click_col == col and row <= click_row < row + 4:
                    selection_index = click_row - row
                    piece_type = pieces[selection_index][1]
                    p.mixer.Sound.play(SOUNDS["promote"])
                    return piece_type


if __name__ == "__main__":
    main()

