import pygame as p
import chessengine
import smartmovefinder
from multiprocessing import Process, Queue
import math

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
    playerTwo = True # For black player, if true -> human plays
    AIThinking = False
    moveFinderProcess = None
    moveUndone = False

    # Added variables for board flipping
    boardFlipped = False # Track if board is currently flipped (False = white's POV, True = black's POV)
    autoFlip = True # If True, board will flip automatically after each move
    fixedBlackPOV = not playerOne and playerTwo # If True, board will stay in black's POV


    startDrawingArrow = False
    startCoordArrows = ()
    endCoordArrows = ()
    rightClickedSquares = []
    arrows = []

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
                        rightClickedSquares = []
                        arrows = []
                        location = p.mouse.get_pos() # get current location of mouse cursor click
                        
                        # Adjust column based on board orientation
                        col = (location[0] - NOTATION_WIDTH_VT) // SQ_SIZE
                        row = location[1] // SQ_SIZE
                        
                        # Convert coordinates if board is flipped
                        if boardFlipped:
                            col = 7 - col
                            row = 7 - row
                        
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
                                    
                                    # Flip board based on settings after a move is made
                                    if autoFlip and not fixedBlackPOV:
                                        boardFlipped = not boardFlipped
                                    break

                            if not moveMade: # if no move made, retain the first square selected
                                playerClicks = [sqSelected]
                        
                    if e.button == 3:
                        
                        location = p.mouse.get_pos()
                        col = (location[0] - NOTATION_WIDTH_VT) // SQ_SIZE
                        row = location[1] // SQ_SIZE

                        if boardFlipped:
                            col = 7 - col
                            row = 7 - row

                        if 0 <= row < 8 and 0 <= col < 8:
                            if (row, col) not in rightClickedSquares:
                                rightClickedSquares.append((row, col))
                        
                            startDrawingArrow = True
                            startCoordArrows = (row, col)



            # when stopped clicking    
            elif e.type == p.MOUSEBUTTONUP:

                if piece_dragging and e.button == 1: # if was LMB
                    location = p.mouse.get_pos()
                    col = (location[0] - NOTATION_WIDTH_VT) // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    
                    # Convert coordinates if board is flipped
                    if boardFlipped:
                        col = 7 - col
                        row = 7 - row

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
                                    # Adjust promotion UI based on board orientation
                                    promo_col = col if not boardFlipped else 7 - col
                                    promo_row = 2 if is_white else 1
                                    if boardFlipped:
                                        promo_row = 7 - promo_row
                                    promotionChoice = drawPromotionSelection(screen, promo_row, promo_col, is_white, boardFlipped)
                            
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
                                    
                                    # Flip board based on settings after a move is made
                                    if autoFlip and not fixedBlackPOV:
                                        boardFlipped = not boardFlipped
                                    break
                    
                    # reset all dragging variables after dropping it
                    piece_dragging = False
                    dragged_piece = None
                    dragged_piece_pos = ()
                    dragged_piece_initial_pos = ()

                    if not moveMade and sqSelected != ():
                        playerClicks = [sqSelected]
            
                if e.button == 3 and startDrawingArrow:
                    location = p.mouse.get_pos()
                    col = (location[0] - NOTATION_WIDTH_VT) // SQ_SIZE
                    row = location[1] // SQ_SIZE

                    if boardFlipped:
                        col = 7 - col
                        row = 7 - row

                    if 0 <= row < 8 and 0 <= col < 8:
                        endCoordArrows = (row, col)
                        if startCoordArrows != (row, col):
                            arrows.append((startCoordArrows, endCoordArrows))
                        startDrawingArrow = False
                    
            
            # detects mouse drag
            elif e.type == p.MOUSEMOTION:
                if piece_dragging:
                    dragged_piece_pos = p.mouse.get_pos()
            
            # detect keyboard inputs
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # if Z key pressed
                    gs.undoMove() # undo last move
                    moveMade = True
                    animate = False
                    gameOver = False
                    if AIThinking: # if computer was calculating, terminate the process and after new move start thinking again
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                    
                    # When undoing a move, flip the board too if autoFlip is enabled
                    if autoFlip and not fixedBlackPOV:
                        boardFlipped = not boardFlipped

                if e.key == p.K_r: # if R key pressed, then reset the board to the very start
                    gs = chessengine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    rightClickedSquares = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                    
                    # Reset board orientation
                    if fixedBlackPOV:
                        boardFlipped = True
                    else:
                        boardFlipped = False
                        
                if e.key == p.K_f: # if F key pressed, flip the board manually
                    boardFlipped = not boardFlipped
                    
                if e.key == p.K_a: # if A key pressed, toggle auto-flip
                    autoFlip = not autoFlip
                
        
        # Set board orientation if playing as black only
        if not playerOne and playerTwo and not fixedBlackPOV:
            fixedBlackPOV = True
            boardFlipped = True
        
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
                
                # Flip board after AI moves if auto-flip is enabled
                if autoFlip and not fixedBlackPOV:
                    boardFlipped = not boardFlipped

        # reset variables after move is made
        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, sqSelected, gs.board, clock, boardFlipped)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        # draw the board representing current game state
        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont, startCoordArrows, endCoordArrows, piece_dragging, dragged_piece, dragged_piece_pos, boardFlipped, rightClickedSquares, arrows)
        
        # Draw board orientation controls
        drawBoardControls(screen, autoFlip, boardFlipped)
        
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



def drawArrow(screen, start, end, boardFlipped=False):
    if start == end:
        return 

    startRow, startCol = start
    endRow, endCol = end
    
    if boardFlipped:
        startRow, startCol = 7 - startRow, 7 - startCol
        endRow, endCol = 7 - endRow, 7 - endCol
    
    # Calculate center points of squares
    startX = NOTATION_WIDTH_VT + startCol * SQ_SIZE + SQ_SIZE // 2
    startY = startRow * SQ_SIZE + SQ_SIZE // 2
    endX = NOTATION_WIDTH_VT + endCol * SQ_SIZE + SQ_SIZE // 2
    endY = endRow * SQ_SIZE + SQ_SIZE // 2
    
    # Calculate angle and distance
    dx = endX - startX
    dy = endY - startY
    angle = math.atan2(dy, dx)
    
    # Arrow styling
    arrowhead_size = 30
    line_width = 8
    arrow_color = p.Color(89, 164, 93)
    
    # Adjustment coefficient for gap between arrow line and head
    adjustment_factor = 0.8
    line_end_x = endX - adjustment_factor * arrowhead_size * math.cos(angle)
    line_end_y = endY - adjustment_factor * arrowhead_size * math.sin(angle)
    
    # Draw arrow line
    p.draw.line(screen, arrow_color, (startX, startY), (line_end_x, line_end_y), line_width)
    
    # Draw arrowhead
    p.draw.polygon(screen, arrow_color, [
        (endX, endY),
        (endX - arrowhead_size * math.cos(angle - math.pi/6), 
         endY - arrowhead_size * math.sin(angle - math.pi/6)),
        (endX - arrowhead_size * math.cos(angle + math.pi/6), 
         endY - arrowhead_size * math.sin(angle + math.pi/6))
    ])
        

'''
play sounds according to type of each move
''' 
playedOnceWhite = False
playedOnceBlack = False
def playMoveSound(move, gs):
    global playedOnceBlack, playedOnceWhite
    if gs.inCheck():
        p.mixer.Sound.play(SOUNDS["move-check"])
    elif move.isCapture:
        p.mixer.Sound.play(SOUNDS["capture"])
    elif gs.whiteHasCastled and not playedOnceWhite:
        p.mixer.Sound.play(SOUNDS["castle"])
        playedOnceWhite = True
    elif gs.blackHasCastled and not playedOnceBlack:
        p.mixer.Sound.play(SOUNDS["castle"])
        playedOnceBlack = True
    else:
        p.mixer.Sound.play(SOUNDS["move-self"])

'''
draw board, highlighted squares if clicked, pieces, move log and notation helpers
'''
def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont, startCoordArrows, endCoordArrows, piece_dragging=False, dragged_piece=None, dragged_piece_pos=(), boardFlipped=False, rightClickedSquares=None, arrows=None):
    drawBoard(screen)
    highlightSquares(screen, gs, validMoves, sqSelected, rightClickedSquares, boardFlipped)

    if arrows:
        for start, end in arrows:
            drawArrow(screen, start, end, boardFlipped)

    if startCoordArrows != () and endCoordArrows != ():
        drawArrow(screen, startCoordArrows, endCoordArrows, boardFlipped)
    
    drawPieces(screen, gs.board, sqSelected, piece_dragging, dragged_piece, dragged_piece_pos, boardFlipped)
    drawMoveLog(screen, gs, moveLogFont)
    drawNotationHelper(screen, boardFlipped)

'''
draw 8 x 8 chessboard
'''
def drawBoard(screen):
    global colors
    colors = [p.Color(241, 207, 167), p.Color(186, 99, 52)]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c)%2)]
            p.draw.rect(screen, color, p.Rect(NOTATION_WIDTH_VT + c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

'''
highlight valid moves when clicked on a piece
'''
def highlightSquares(screen, gs, validMoves, sqSelected, rightClickedSquares = None, boardFlipped=False):

    if rightClickedSquares is None:
        rightClickedSquares = []


    if sqSelected != ():
        r, c = sqSelected
        if 0 <= r < 8 and 0 <= c < 8:
            if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
                s = p.Surface((SQ_SIZE, SQ_SIZE))
                s.set_alpha(100)
                s.fill(p.Color('blue'))
                
                # Convert screen coordinates based on board orientation
                draw_r, draw_c = r, c
                if boardFlipped:
                    draw_r, draw_c = 7 - r, 7 - c
                
                screen.blit(s, (NOTATION_WIDTH_VT + draw_c*SQ_SIZE, draw_r*SQ_SIZE))
                s.fill(p.Color('yellow'))
                for move in validMoves:
                    if move.startRow == r and move.startCol == c:
                        # Convert end position based on board orientation
                        draw_end_r, draw_end_c = move.endRow, move.endCol
                        if boardFlipped:
                            draw_end_r, draw_end_c = 7 - move.endRow, 7 - move.endCol
                        
                        screen.blit(s, (NOTATION_WIDTH_VT + draw_end_c*SQ_SIZE, draw_end_r*SQ_SIZE))
    
    for square in rightClickedSquares:
        r, c = square
        if 0 <= r < 8 and 0 <= c < 8:
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # Transparency
            s.fill(p.Color('red'))  # Red highlight
            
            # Convert screen coordinates based on board orientation
            draw_r, draw_c = r, c
            if boardFlipped:
                draw_r, draw_c = 7 - r, 7 - c
            
            screen.blit(s, (NOTATION_WIDTH_VT + draw_c*SQ_SIZE, draw_r*SQ_SIZE))

'''
draw pieces on top of board and highlight squares
'''
def drawPieces(screen, board, sqSelected, piece_dragging=False, dragged_piece=None, dragged_piece_pos=(), boardFlipped=False):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            # Convert board coordinates to screen coordinates based on orientation
            board_r, board_c = r, c
            if boardFlipped:
                board_r, board_c = 7 - r, 7 - c
                
            piece = board[board_r][board_c]
            if piece != "--":
                if not (piece_dragging and (board_r, board_c) == sqSelected):
                    screen.blit(IMAGES[piece], p.Rect(NOTATION_WIDTH_VT + c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
    
    if piece_dragging and dragged_piece and dragged_piece_pos:
        # Center the piece on the cursor
        x = min(max(dragged_piece_pos[0] - SQ_SIZE//2, NOTATION_WIDTH_VT), BOARD_WIDTH + NOTATION_WIDTH_VT - SQ_SIZE)
        y = min(max(dragged_piece_pos[1] - SQ_SIZE//2, 0), BOARD_HEIGHT - SQ_SIZE)
        screen.blit(IMAGES[dragged_piece], p.Rect(x, y, SQ_SIZE, SQ_SIZE))

'''
draw notation helper (1-8) vertically and (a-h) horizontally, adjusted for board orientation
'''
def drawNotationHelper(screen, boardFlipped=False):
    # Clear previous notations
    notation_area_vertical = p.Rect(0, 0, NOTATION_WIDTH_VT, BOARD_HEIGHT)
    notation_area_horizontal = p.Rect(0, BOARD_HEIGHT, BOARD_WIDTH + NOTATION_WIDTH_VT, NOTATION_HEIGHT_HZ)
    p.draw.rect(screen, p.Color('white'), notation_area_vertical)
    p.draw.rect(screen, p.Color('white'), notation_area_horizontal)
    
    font = p.font.SysFont("Georgia", 16, False, False)

    for c in range(DIMENSION):
        # Adjust file letter based on board orientation
        file_index = c if not boardFlipped else 7 - c
        file_letter = chr(ord('a') + file_index)
        
        textObject = font.render(file_letter, True, p.Color('black'))
        x = c * SQ_SIZE + (SQ_SIZE // 2) - (textObject.get_width() // 2) + 20
        y = BOARD_HEIGHT - (NOTATION_HEIGHT_HZ // 2) - (textObject.get_height() // 2)

        screen.blit(textObject, (x, BOARD_HEIGHT))

    for r in range(DIMENSION):
        # Adjust rank number based on board orientation
        rank_index = r if not boardFlipped else 7 - r
        rank_number = str(DIMENSION - rank_index)

        textObject = font.render(rank_number, True, p.Color('black'))

        x = (NOTATION_WIDTH_VT // 2) - (textObject.get_width() // 2) + 20
        y = r * SQ_SIZE + (SQ_SIZE // 2) - (textObject.get_height() // 2) 

        screen.blit(textObject, (5, y))
    
    notation_corner = p.Rect(0, BOARD_HEIGHT, NOTATION_WIDTH_VT, NOTATION_HEIGHT_HZ)
    p.draw.rect(screen, p.Color('white'), notation_corner)

'''
draw move log to see series of moves that lead to current position in game
'''
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
'''
draw text in the middle of the board after game is over
'''
def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    textObject = font.render(text, 0, p.Color('Gray'))
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH//2 - textObject.get_width()/2, BOARD_HEIGHT//2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color('Black'))
    screen.blit(textObject, textLocation.move(2, 2))

'''
draw UI controls for board orientation
'''
def drawBoardControls(screen, autoFlip, boardFlipped):
    font = p.font.SysFont("Georgia", 14, False, False)
    
    # Draw at the bottom of the move log panel, but slightly higher to avoid the white line
    controlsRect = p.Rect(BOARD_WIDTH + NOTATION_WIDTH_VT, BOARD_HEIGHT - 128, MOVE_LOG_PANEL_WIDTH, 128)
    p.draw.rect(screen, p.Color("dark gray"), controlsRect)
    
    # Draw text for auto-flip status
    autoFlipText = f"Auto-Flip: {'ON' if autoFlip else 'OFF'}"
    autoFlipObj = font.render(autoFlipText, True, p.Color('white'))
    screen.blit(autoFlipObj, (controlsRect.x + 10, controlsRect.y + 10))
    
    # Draw text for current orientation
    orientationText = f"Current View: {'Black' if boardFlipped else 'White'}'s POV"
    orientationObj = font.render(orientationText, True, p.Color('white'))
    screen.blit(orientationObj, (controlsRect.x + 10, controlsRect.y + 30))
    
    # Draw key controls help - now including Z and R
    keysText = "F: Flip Board  |  A: Toggle Auto-Flip"
    keysObj = font.render(keysText, True, p.Color('white'))
    screen.blit(keysObj, (controlsRect.x + 10, controlsRect.y + 50))
    
    # Add Z and R key information
    moreKeysText = "Z: Undo Move  |  R: Reset Board"
    moreKeysObj = font.render(moreKeysText, True, p.Color('white'))
    screen.blit(moreKeysObj, (controlsRect.x + 10, controlsRect.y + 70))

'''
animate pieces going from one square to another
'''
def animateMove(move, screen, sqSelected, board, clock, boardFlipped=False):
    global colors
    # Original board coordinates
    startRow, startCol = move.startRow, move.startCol
    endRow, endCol = move.endRow, move.endCol
    
    # Convert to screen coordinates based on board orientation
    if boardFlipped:
        startRow, startCol = 7 - startRow, 7 - startCol
        endRow, endCol = 7 - endRow, 7 - endCol
    
    dR = endRow - startRow
    dC = endCol - startCol
    framesPerSquare = 5
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    
    for frame in range(frameCount+1):
        r, c = (startRow + dR*frame/frameCount, startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board, sqSelected, boardFlipped=boardFlipped)
        
        # Get proper color for the destination square
        board_end_row, board_end_col = move.endRow, move.endCol
        color = colors[(board_end_row + board_end_col) %2]
        
        # Draw end square and captured piece if any
        endSquare = p.Rect(NOTATION_WIDTH_VT + endCol*SQ_SIZE, endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        if move.pieceCaptured != '--':
            screen.blit(IMAGES[move.pieceCaptured], endSquare)

        # Draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(NOTATION_WIDTH_VT + c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

'''
UI aided selection of piece to promote to, once pawn reaches back rank
'''
def drawPromotionSelection(screen, row, col, is_white, boardFlipped=False):
    if is_white:
        pieces = ['wQ', 'wR', 'wB', 'wN']
    else:
        pieces = ['bQ', 'bR', 'bB', 'bN']

    # Calculate the rectangle position
    selection_rect = p.Rect(NOTATION_WIDTH_VT + col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, 4*SQ_SIZE)
    p.draw.rect(screen, p.Color('gray'), selection_rect)
    p.draw.rect(screen, p.Color('black'), selection_rect, 2)

    # Draw pieces for selection
    for i, piece in enumerate(pieces):
        piece_rect = p.Rect(NOTATION_WIDTH_VT + col*SQ_SIZE, (row+i)*SQ_SIZE, SQ_SIZE, SQ_SIZE)
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
                
                # Verify click is within the selection rectangle
                if click_col == col and row <= click_row < row + 4:
                    selection_index = click_row - row
                    piece_type = pieces[selection_index][1]
                    p.mixer.Sound.play(SOUNDS["promote"])
                    return piece_type
    
    return 'Q'  # Default to Queen if selection fails


if __name__ == "__main__":
    main()