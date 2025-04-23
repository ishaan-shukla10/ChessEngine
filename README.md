This repository hosts a Python-based Chess Engine

## INSPIRATION AND BASE CODE ##
The initial motivation and a significant portion of the foundational codebase for this project were derived from the excellent chess programming tutorials by YouTuber and Professor **Eddie Sharick**.
His clear explanations and well-structured code provided a solid starting point for this engine.
You can find his original tutorials on his YouTube channel (search for "Eddie Sharick Chess Engine in Python").


## ENHANCEMENTS AND ADDITIONS ##
Building upon Sharick's work, this code incorporates several improvements and new features:

* **Improved AI:** The AI component has been significantly enhanced to provide a stronger and more challenging opponent. This includes modifications and additions to the search algorithms and evaluation functions.
  1) Taught multiple openings to give the engine some background on opening theory.
  2) Added heuristic scores for concepts of forks, pawn weaknesses (doubled pawns, isolated pawns), king safety
  3) While searching for moves, engine follows the order of checks -> captures -> threats which is more intuitive and less time consuming
* **Enhanced User Interaction:** The user interface (UI) has been revamped to offer a more intuitive and user-friendly experience when interacting with the chessboard.
  1) Easy-on-the-eyes board color
  2) Drag and drop feature for pieces
  3) Drawing arrows with RMB (right mouse button) for easier calculations during move making

**Installation:**

1.  Clone this repository to your local machine:
    ```bash
    git clone https://github.com/ishaan-shukla10/ChessEngine.git
    cd ChessEngine
    ```
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

**Running the Engine:**

1.  Navigate to the project directory in your terminal.
    ```bash
    cd ChessEngine
    ```
2.  Run the main script:
    ```bash
    python chessmain.py
    ```
