# Pygame Chess Game

A functional chess game built using Python and the Pygame library, featuring a graphical user interface, sound effects, and an optional AI opponent powered by Stockfish.

## Features

* **Graphical User Interface:** Visual chessboard and pieces rendered using Pygame.
* **Core Chess Logic:**
    * Standard piece movement (Pawn, Rook, Knight, Bishop, Queen, King).
    * Capturing opponent pieces.
    * Turn-based gameplay.
    * Move validation (prevents illegal moves).
    * Check detection and highlighting.
    * Checkmate and Stalemate detection for game end conditions.
* **Special Moves:**
    * Castling (Kingside and Queenside).
    * En Passant captures.
    * Pawn Promotion (with GUI choice for Queen, Rook, Bishop, or Knight).
* **Game Modes:**
    * Human vs Human.
    * Human vs AI (using Stockfish engine, plays as Black).
* **User Interface:**
    * In-game menu (using Pygame buttons) for selecting game mode.
    * In-game buttons for pawn promotion choices.
    * In-game dialog (using Pygame buttons) at game end to "Play Again" or "Quit Game".
    * Visual highlighting for selected piece, valid moves, and check status.
    * Status bar displaying current turn, game mode, and messages (Check, Checkmate, etc.).
* **Sound Effects:** Basic sounds for piece movement and captures.
* **Assets:** Supports loading custom piece images and sounds. Includes fallback drawing if assets are missing.

## Screenshots

## Technology Stack

* **Python 3.x**
* **Pygame:** For graphics, sound, and event handling.
* **python-chess:** (Optional, for AI mode) For interacting with the UCI chess engine (Stockfish).
* **Stockfish:** (Optional, external dependency) The chess engine used for the AI opponent.

## Setup and Installation

1.  **Install Dependencies:**
    Install the required Python libraries using pip. It's recommended to create a `requirements.txt` file.

    * **Create `requirements.txt`:**
        ```txt
        pygame
        python-chess
        ```
    * **Install:**
        ```bash
        pip install -r requirements.txt
        ```
        *(Note: `python-chess` is only strictly needed if you want to use the AI opponent feature).*

5.  **Set up Assets:**
    * Create an `assets` folder in the main project directory if it doesn't exist.
    * **Piece Images:** Place your chess piece images inside the `assets` folder. They must be named `wP.png`, `wR.png`, `wN.png`, `wB.png`, `wQ.png`, `wK.png`, `bP.png`, `bR.png`, `bN.png`, `bB.png`, `bQ.png`, `bK.png`. PNG format with transparency is recommended.
    * **Sound Files:** Place `move.mp3` and `capture.mp3` inside the `assets` folder.

6.  **Set up Stockfish (Optional, for AI):**
    * Download a Stockfish engine executable suitable for your operating system (e.g., from [stockfishchess.org](https://stockfishchess.org/download/)).
    * Place the Stockfish executable somewhere accessible. You can put it inside the `assets` folder for simplicity (as shown in the example path) or elsewhere on your system.
    * **IMPORTANT:** Open the `chess_gui.py` file and update the `STOCKFISH_PATH` variable (near the top) to the exact path of your Stockfish executable. Use a raw string (e.g., `r"C:\path\to\stockfish.exe"`) on Windows.

## Running the Game

Once setup is complete, navigate to the project directory in your terminal and run:

```bash
python chess_gui.py


## Roadmap & Extensibility (Future Enhancements)

This project provides a solid foundation for a feature-rich chess application. The separation of game logic (`chess_logic.py`) and the graphical interface/interaction (`chess_gui.py`) makes it relatively straightforward to customize and extend.

Here are some exciting directions and planned improvements (coming soon... maybe!):

* **Network Multiplayer:** Implement online play between friends using technologies like **WebSockets** for real-time communication. Imagine challenging anyone, anywhere!
* **Richer Gameplay Features:**
    * Implement **full draw condition detection** (50-move rule, threefold repetition, insufficient material).
    * Add a **move history** display (algebraic notation).
    * Implement **undo/redo** functionality.
    * Introduce **game timers** (Blitz, Rapid, etc.).
* **Enhanced User Experience:**
    * **Drag-and-drop** piece movement as an alternative to click-to-move.
    * Visual **move hints** or **analysis features** (perhaps leveraging the engine).
    * **Customizable themes** (board colors, piece sets). Load different asset packs.
    * Improved menu system and in-game options.
    * Sound customization.
* **Code Refinements:**
    * More comprehensive testing.
    * Further optimization for performance.

The potential is huge! Feel free to fork the project and add your own features. Contributions are welcome (if applicable).