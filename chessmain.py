import pygame as p
import chessengine
import smartmovefinder
from multiprocessing import Process, Queue


BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
NOTATION_HEIGHT_HZ = NOTATION_WIDTH_VT = 20
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // 8
MAX_FPS = 15
IMAGES = {}
SOUNDS = {}

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(f'images/{piece}.png'), (SQ_SIZE, SQ_SIZE))


def loadSounds():
    types = ["capture", "castle", "move-check", "move-self", "promote", "notify"]
    for type in types:
        SOUNDS[type] = p.mixer.Sound("sounds/" + type + ".mp3")


def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH + NOTATION_WIDTH_VT, BOARD_HEIGHT + NOTATION_HEIGHT_HZ))
    clock = p.time.Clock()
    screen.fill(p.Color('white'))
    gs = chessengine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False
    animate = False

    moveLogFont = p.font.SysFont("Arial", 14, False, False)
    
    loadImages()
    loadSounds()
    running = True
    sqSelected = ()
    playerClicks = []
    gameOver = False
    playerOne = True
    playerTwo = False
    AIThinking = False
    moveFinderProcess = None
    moveUndone = False

    piece_dragging = False
    dragged_piece = None
    dragged_piece_pos = ()
    dragged_piece_initial_pos = ()

    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        for e in p.event.get():
            
            if e.type == p.QUIT:
                running = False

            elif e.type == p.MOUSEBUTTONDOWN:
                    if not gameOver and humanTurn and e.button == 1:

                        location = p.mouse.get_pos()
                        col = (location[0] - NOTATION_WIDTH_VT) //SQ_SIZE
                        row = location[1]//SQ_SIZE
                        
                        if 0 <= col < 8 and 0 <= row < 8:
                            piece = gs.board[row][col]

                            if sqSelected == (row, col) or col >= 8:
                                sqSelected = ()
                                playerClicks = []
                            else:
                                sqSelected = (row, col)
                                playerClicks.append(sqSelected)

                            if piece != '--' and ((piece[0] == 'w' and gs.whiteToMove) or (piece[0] == 'b' and not gs.whiteToMove)):
                                piece_dragging = True
                                dragged_piece = piece
                                dragged_piece_pos = location
                                dragged_piece_initial_pos = (row, col)


                        if len(playerClicks) == 2:
                            move = chessengine.Move(playerClicks[0], playerClicks[1], gs.board)
                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    moveMade = True
                                    playMoveSound(move, gs)
                                    animate = True
                                    sqSelected = ()
                                    playerClicks = []
                                    piece_dragging = False
                                    break

                            if not moveMade:
                                playerClicks = [sqSelected]
                
            elif e.type == p.MOUSEBUTTONUP:
                if piece_dragging and e.button == 1:
                    location = p.mouse.get_pos()
                    col = (location[0] - NOTATION_WIDTH_VT) //SQ_SIZE
                    row = location[1]//SQ_SIZE

                    if 0 <= col < 8 and 0 <= row < 8:
                        if (row, col) != dragged_piece_initial_pos:
                            start_row, start_col = dragged_piece_initial_pos
                            
                            isPawnPromotion = False
                            promotionChoice = 'Q' 
                            
                            if gs.board[start_row][start_col][1] == 'p':
                                
                                if (gs.board[start_row][start_col][0] == 'w' and row == 0) or \
                                (gs.board[start_row][start_col][0] == 'b' and row == 7):
                                    isPawnPromotion = True
                                    
                                    is_white = gs.board[start_row][start_col][0] == 'w'
                                    promotionChoice = drawPromotionSelection(screen, 2 if is_white else 1, col, is_white)
                            
                           
                            move = chessengine.Move(dragged_piece_initial_pos, (row, col), gs.board, 
                                                isPawnPromotion=isPawnPromotion, 
                                                promotionChoice=promotionChoice)
                            
                            for i in range(len(validMoves)):
                                valid_move = validMoves[i]
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
                    
                    piece_dragging = False
                    dragged_piece = None
                    dragged_piece_pos = ()
                    dragged_piece_initial_pos = ()

                    if not moveMade and sqSelected != ():
                        playerClicks = [sqSelected]
                
            elif e.type == p.MOUSEMOTION:
                if piece_dragging:
                    dragged_piece_pos = p.mouse.get_pos()
            
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    playMoveSound(move, gs)
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True

                if e.key == p.K_r:
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

        if not gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                AIThinking = True
                print("Thinking...")
                returnQueue = Queue()
                moveFinderProcess = Process(target=smartmovefinder.findBestMove, args=(gs, validMoves, returnQueue))
                moveFinderProcess.start()

            if not moveFinderProcess.is_alive():
                print("Done thinking")
                AIMove = returnQueue.get()
            #AIMove = smartmovefinder.findBestMove(gs, validMoves)
                if AIMove is None:
                    AIMove = smartmovefinder.findRandomMove(validMoves)
                gs.makeMove(AIMove)
                moveMade = True

                playMoveSound(AIMove, gs)
                animate = True
                AIThinking = False


        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, sqSelected, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

            
        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont, piece_dragging, dragged_piece, dragged_piece_pos)
        
        if gs.checkmate:
            gameOver = True
            if gs.whiteToMove:
                drawEndGameText(screen, 'Black wins by checkmate')
            else:
                drawEndGameText(screen, 'White wins by checkmate')
        elif gs.stalemate:
            gameOver = True
            drawEndGameText(screen, 'Stalemate')

        clock.tick(MAX_FPS)
        p.display.flip()


def playMoveSound(move, gs):
    if gs.inCheck():
        p.mixer.Sound.play(SOUNDS["move-check"])
    elif move.isCapture:
        p.mixer.Sound.play(SOUNDS["capture"])
    elif move.isCastleMove:
        p.mixer.Sound.play(SOUNDS["castle"])
    else:
        p.mixer.Sound.play(SOUNDS["move-self"])


def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont, piece_dragging=False, dragged_piece=None, dragged_piece_pos=()):
    drawBoard(screen)
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board, sqSelected, piece_dragging, dragged_piece, dragged_piece_pos)
    drawMoveLog(screen, gs, moveLogFont)
    drawNotationHelper(screen)



def drawBoard(screen):
    global colors
    colors = [p.Color(241, 207, 167), p.Color(186, 99, 52)]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c)%2)]
            p.draw.rect(screen, color, p.Rect(NOTATION_WIDTH_VT + c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))



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



def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    textObject = font.render(text, 0, p.Color('Gray'))
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH//2 - textObject.get_width()/2, BOARD_HEIGHT//2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color('Black'))
    screen.blit(textObject, textLocation.move(2, 2))



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

