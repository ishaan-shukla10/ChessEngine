This repository hosts a Python-based Chess Engine

## INSPIRATION AND BASE CODE ##
The initial motivation and a significant portion of the foundational codebase for this project were derived from the excellent chess programming tutorials by YouTuber and Professor **Eddie Sharick**.
His clear explanations and well-structured code provided a solid starting point for this engine.
You can find his original tutorials on his YouTube channel (search for "Eddie Sharick Chess Engine in Python").


## ENHANCEMENTS AND ADDITIONS ##
Building upon Sharick's work, this code incorporates several improvements and new features:

* **Improved AI:** The AI component has been significantly enhanced to provide a stronger and more challenging opponent. This includes modifications and additions to the search algorithms and evaluation functions.
  1) Taught multiple openings (scotch, alekhine, caro kann, bogo) to give the engine some background on opening theory, by storing most frequently obtained positions after standard openings.
  2) Added heuristic scores for concepts of forks, pawn weaknesses (doubled pawns, isolated pawns), pawn strengths (pawn chains, center control, and protected pawn promotion), pinning pieces to king and queen, king safety, open files for rooks and piece developments.
  3) While searching for moves, engine follows the order of checks -> captures -> threats which is more intuitive and less time consuming.
  4) Added zobrist hashing for storing moves that occur commonly so that redundant calculcations are eliminated.
  5) Added a scoreMoves function which scores the moves such that more obvious moves are inspected first, thus improving optimization.
* **Enhanced User Interaction:** The user interface (UI) has been revamped to offer a more intuitive and user-friendly experience when interacting with the chessboard.
  1) Easy-on-the-eyes board color.
  2) Drag and drop feature for pieces.
  3) Drawing arrows with RMB (right mouse button) for easier calculations during move making.
  4) Addition of sounds as per moves (different for castling, piece captures, piece movements and promotions).
  5) Highlighting the most recent move made so that the last move made can be detected easily.
  6) UI based piece selection menu for pawn promotion.
  7) Added functionality for flipping the board to change POVs if playing with black against the computer, or playing 1v1 offline with 2 humans.
* **Additional Enhancements:**
  1) Added multiple PGN files for different openings under the openings folder.
  2) Added some trained positions for openings under the opening_books folder.
 
## FUTURE WORK AND POTENTIAL ADDITIONAL ENHANCEMENTS ##
1) Adding more heuristics like concept of batteries (doubled up rooks, or rooks with queens or bishop with queens).
2) Adding timers and 'levels' to the games based on engine depth/ additonal neural network model usage.
3) Training neural networks/ transformers on the dataset of chess puzzles, open sourced by Lichess. (https://huggingface.co/datasets/Lichess/chess-puzzles)

## Installation: ##

1.  Clone this repository to your local machine:
    ```bash
    git clone https://github.com/ishaan-shukla10/ChessEngine.git
    cd ChessEngine
    ```
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Engine: ##

1.  Navigate to the project directory in your terminal.
    ```bash
    cd ChessEngine
    ```
2.  Run the main script:
    ```bash
    python chessmain.py
    ```

## Teaching More Openings: ##
1. Navigate to the directory in your terminal.
   ```bash
    cd ChessEngine
    ```
2. Run populate_opening_book script:
   ```bash
    python .\populate_opening_book.py --dir .\openings\london\ --max-moves 20 --quality 2.0 
    ```

## Adjusting Depth: ##
* To make the engine predict moves more accurately, change the 'DEPTH' variable inside smartmovefinder.py file. 
* More depth -> more accurate moves but increased computational time
* Additional optimizations can be done while finding the move, like using CUDA for parallel computation or using enhanced heuristics.
