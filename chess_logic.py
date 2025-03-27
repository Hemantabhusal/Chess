# chess_logic.py
import copy

# --- Constants ---
BOARD_SIZE = 8
EMPTY_SQUARE = '.'
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 'P', 'N', 'B', 'R', 'Q', 'K'
WHITE, BLACK = 'white', 'black'
PIECE_ORDER = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK] # For setup

# --- Helper Functions ---
def get_color(piece):
    """Returns the color of a piece ('white', 'black', or None)."""
    if piece == EMPTY_SQUARE: return None
    return WHITE if piece.isupper() else BLACK

def is_on_board(r, c):
    """Checks if coordinates (r, c) are within the board."""
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def algebraic_to_coords(alg_notation):
    """Converts algebraic notation (e.g., 'e4') to (row, col) tuple."""
    if not isinstance(alg_notation, str) or len(alg_notation) != 2: return None
    col_char = alg_notation[0].lower()
    row_char = alg_notation[1]
    if not ('a' <= col_char <= 'h' and '1' <= row_char <= '8'): return None
    col = ord(col_char) - ord('a')
    row = BOARD_SIZE - int(row_char) # Board row 0 is rank 8
    return row, col

def coords_to_algebraic(r, c):
    """Converts (row, col) tuple to algebraic notation."""
    if not is_on_board(r, c): return None
    col_char = chr(ord('a') + c)
    row_char = str(BOARD_SIZE - r)
    return col_char + row_char

# --- Core Game Logic Class ---
class ChessGame:
    def __init__(self):
        """Initializes or resets the chess game state."""
        self.reset_game()

    def reset_game(self):
        """Resets the game to the initial state."""
        self.board = self.setup_board()
        self.turn = WHITE
        self.game_over = False
        self.winner = None
        self.status_message = "New game started."
        # Castling rights: [White Kingside, White Queenside, Black Kingside, Black Queenside]
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        # Track if King/Rooks have moved
        self.king_moved = {WHITE: False, BLACK: False}
        self.rook_moved = { # Track by algebraic notation of starting square
            WHITE: {coords_to_algebraic(7, 0): False, coords_to_algebraic(7, 7): False}, # a1, h1
            BLACK: {coords_to_algebraic(0, 0): False, coords_to_algebraic(0, 7): False}  # a8, h8
        }
        # En passant target square (algebraic notation e.g., 'e3' or None)
        self.en_passant_target = None
        self.last_move_coords = None # For GUI highlighting: (start_r, start_c, end_r, end_c)
        self.needs_promotion = None # Store coords if promotion needed: (r, c)
        self.last_move_was_capture = False # Flag for sound effects
        # Simple move counters for FEN - can be enhanced later if needed
        self.halfmove_clock = 0
        self.fullmove_number = 1

    def setup_board(self):
        """Initializes the board to the standard starting position."""
        board = [[EMPTY_SQUARE for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        board[0] = [p.lower() for p in PIECE_ORDER]
        board[1] = [PAWN.lower()] * BOARD_SIZE
        board[6] = [PAWN.upper()] * BOARD_SIZE
        board[7] = [p.upper() for p in PIECE_ORDER]
        return board

    def switch_turn(self):
        """Switches the current player's turn and increments move number."""
        if self.turn == BLACK:
            self.fullmove_number += 1 # Increment after Black moves
        self.turn = BLACK if self.turn == WHITE else WHITE

    def get_piece(self, r, c):
        """Gets the piece at a given coordinate."""
        if is_on_board(r, c): return self.board[r][c]
        return None

    def find_king(self, color, board_state=None):
        """Finds the coordinates of the king of the specified color."""
        current_board = board_state if board_state is not None else self.board
        king_char = KING.upper() if color == WHITE else KING.lower()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if current_board[r][c] == king_char:
                    return r, c
        return None # Should not happen

    def is_in_check(self, color, board_state=None):
        """Checks if the king of the specified color is in check on the given board state."""
        current_board = board_state if board_state is not None else self.board
        king_pos = self.find_king(color, current_board)
        if not king_pos: return False # King not found

        opponent_color = BLACK if color == WHITE else WHITE
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = current_board[r][c]
                if get_color(piece) == opponent_color:
                    possible_moves = self._get_valid_moves_for_piece(r, c, current_board, check_king=False)
                    if king_pos in possible_moves:
                        return True # King is attacked
        return False # King is safe

    def get_all_legal_moves(self, color):
        """
        Generates all legal moves for the given color.
        Returns a dictionary: { (start_r, start_c): set([(end_r, end_c), ...]), ... }
        """
        legal_moves = {} # Dictionary to store moves: start_coord -> set(end_coords)
        for r_start in range(BOARD_SIZE):
            for c_start in range(BOARD_SIZE):
                piece = self.board[r_start][c_start]
                if get_color(piece) == color:
                    potential_moves = self._get_valid_moves_for_piece(r_start, c_start, self.board, check_king=True)
                    valid_targets_for_piece = set()
                    for r_end, c_end in potential_moves:
                        temp_board, _, _ = self._simulate_move(r_start, c_start, r_end, c_end)
                        if not self.is_in_check(color, temp_board):
                            valid_targets_for_piece.add((r_end, c_end))
                    if valid_targets_for_piece:
                         legal_moves[(r_start, c_start)] = valid_targets_for_piece
        return legal_moves

    def _simulate_move(self, r_start, c_start, r_end, c_end):
        """
        Simulates making a move on a temporary board for validation purposes.
        Returns (temp_board, temp_en_passant_target, temp_castling_rights)
        Focuses on board state changes for check validation.
        """
        temp_board = copy.deepcopy(self.board)
        piece = temp_board[r_start][c_start]
        color = get_color(piece)
        # Use algebraic target for simulation check if needed
        ep_coords = algebraic_to_coords(self.en_passant_target) if self.en_passant_target else None

        temp_board[r_end][c_end] = piece
        temp_board[r_start][c_start] = EMPTY_SQUARE

        # Simplified special move simulation for check validation
        if piece.upper() == PAWN and (r_end, c_end) == ep_coords:
             captured_pawn_r = r_end + (1 if color == WHITE else -1) # Pawn captured is behind target
             captured_pawn_c = c_end
             if is_on_board(captured_pawn_r, captured_pawn_c):
                 temp_board[captured_pawn_r][captured_pawn_c] = EMPTY_SQUARE

        if piece.upper() == KING and abs(c_start - c_end) == 2:
            rook_start_c = BOARD_SIZE - 1 if c_end > c_start else 0
            rook_end_c = c_end - 1 if c_end > c_start else c_end + 1
            if is_on_board(r_start, rook_start_c) and is_on_board(r_start, rook_end_c):
                rook = temp_board[r_start][rook_start_c]
                temp_board[r_start][rook_start_c] = EMPTY_SQUARE
                temp_board[r_start][rook_end_c] = rook # Place rook

        if piece.upper() == PAWN and (r_end == 0 or r_end == BOARD_SIZE - 1):
             promo_piece = QUEEN.upper() if color == WHITE else QUEEN.lower()
             temp_board[r_end][c_end] = promo_piece

        # Return simplified state (only board matters for is_in_check call)
        return temp_board, None, None # Simplified return


    def _get_valid_moves_for_piece(self, r_start, c_start, board_state, check_king=True):
        """
        Gets all potentially valid moves for a piece based on movement rules.
        Does NOT validate if the move puts the own king in check.
        Returns a set of (r_end, c_end) tuples.
        """
        moves = set()
        piece = board_state[r_start][c_start]
        if piece == EMPTY_SQUARE: return moves

        color = get_color(piece)
        piece_type = piece.upper()
        # Convert algebraic en passant target to coords for easier checking here
        en_passant_coords = algebraic_to_coords(self.en_passant_target) if self.en_passant_target else None

        def add_move_if_valid(r, c):
            """Helper: Adds move if on board & empty or captures opponent."""
            if is_on_board(r, c):
                target_piece = board_state[r][c]
                target_color = get_color(target_piece)
                if target_color != color: # Empty square or opponent's piece
                    moves.add((r, c))
                return target_piece == EMPTY_SQUARE # Path clear for sliding?
            return False

        # --- Pawn Moves ---
        if piece_type == PAWN:
            direction = -1 if color == WHITE else 1
            start_rank = 6 if color == WHITE else 1
            # Forward one step
            one_step = r_start + direction
            if is_on_board(one_step, c_start) and board_state[one_step][c_start] == EMPTY_SQUARE:
                moves.add((one_step, c_start))
                # Forward two steps
                if r_start == start_rank:
                    two_steps = r_start + 2 * direction
                    if is_on_board(two_steps, c_start) and board_state[two_steps][c_start] == EMPTY_SQUARE:
                        moves.add((two_steps, c_start))
            # Diagonal captures
            for dc in [-1, 1]:
                capture_r, capture_c = r_start + direction, c_start + dc
                if is_on_board(capture_r, capture_c):
                    target_piece = board_state[capture_r][capture_c]
                    target_color = get_color(target_piece)
                    if target_color is not None and target_color != color: # Normal capture
                        moves.add((capture_r, capture_c))
                    elif (capture_r, capture_c) == en_passant_coords: # En Passant capture
                         moves.add((capture_r, capture_c))

        # --- Knight Moves ---
        elif piece_type == KNIGHT:
            knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
            for dr, dc in knight_moves: add_move_if_valid(r_start+dr, c_start+dc)

        # --- Rook, Bishop, Queen Moves (Sliding Pieces) ---
        elif piece_type in [ROOK, BISHOP, QUEEN]:
            directions = []
            if piece_type in [ROOK, QUEEN]: directions.extend([(0,1),(0,-1),(1,0),(-1,0)])
            if piece_type in [BISHOP, QUEEN]: directions.extend([(1,1),(1,-1),(-1,1),(-1,-1)])
            for dr, dc in directions:
                r_end, c_end = r_start + dr, c_start + dc
                while add_move_if_valid(r_end, c_end): r_end += dr; c_end += dc

        # --- King Moves ---
        elif piece_type == KING:
            king_moves = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
            for dr, dc in king_moves: add_move_if_valid(r_start + dr, c_start + dc)
            # Castling - add potential moves if basic conditions met
            if check_king and not self.king_moved[color]:
                if self.can_castle(color, 'kingside', board_state): moves.add((r_start, c_start + 2))
                if self.can_castle(color, 'queenside', board_state): moves.add((r_start, c_start - 2))
        return moves

    def can_castle(self, color, side, board_state):
        """Checks basic castling conditions (path clear, pieces haven't moved)."""
        rank = 7 if color == WHITE else 0
        king_home_c = 4
        if self.king_moved[color]: return False

        if side == 'kingside':
            rook_home_c = BOARD_SIZE - 1; castle_key = 'K' if color == WHITE else 'k'
            path_cols = range(king_home_c + 1, rook_home_c); rook_alg = coords_to_algebraic(rank, rook_home_c)
        elif side == 'queenside':
            rook_home_c = 0; castle_key = 'Q' if color == WHITE else 'q'
            path_cols = range(rook_home_c + 1, king_home_c); rook_alg = coords_to_algebraic(rank, rook_home_c)
        else: return False

        if not self.castling_rights.get(castle_key): return False
        # Use .get() with a default value for rook_moved check
        if self.rook_moved[color].get(rook_alg, False): return False
        rook_char = ROOK.upper() if color == WHITE else ROOK.lower()
        if board_state[rank][rook_home_c] != rook_char: return False
        for col in path_cols:
            if board_state[rank][col] != EMPTY_SQUARE: return False
        # Check simulation handled by get_all_legal_moves
        return True

    def make_move(self, start_coords, end_coords):
        """
        Attempts to make a move, updates state including capture flag, halfmove clock.
        Returns True if successful (or pending promotion), False otherwise.
        """
        r_start, c_start = start_coords
        r_end, c_end = end_coords
        piece = self.board[r_start][c_start]
        color = get_color(piece)

        # Validation
        if color != self.turn or self.game_over: return False
        if not is_on_board(r_start, c_start) or not is_on_board(r_end, c_end): return False
        legal_moves_map = self.get_all_legal_moves(color)
        if start_coords not in legal_moves_map or end_coords not in legal_moves_map[start_coords]:
             self.status_message = "Illegal move." # Keep simple
             return False

        # --- Execute ---
        self.status_message = ""
        captured_piece = self.board[r_end][c_end]
        current_ep_target_alg = self.en_passant_target # Store algebraic target

        # Reset flags/counters that depend on move type
        self.last_move_was_capture = (captured_piece != EMPTY_SQUARE)
        is_pawn_move = (piece.upper() == PAWN)
        if self.last_move_was_capture or is_pawn_move:
            self.halfmove_clock = 0 # Reset 50-move counter
        else:
            self.halfmove_clock += 1

        # Move piece
        self.board[r_end][c_end] = piece
        self.board[r_start][c_start] = EMPTY_SQUARE
        self.needs_promotion = None
        self.en_passant_target = None # Reset, will be set below if applicable

        # Calculate direction for pawn moves
        direction = -1 if color == WHITE else 1

        # Handle Pawn double step (create en passant target in algebraic)
        if is_pawn_move and abs(r_start - r_end) == 2:
            ep_target_coords = (r_start + direction, c_start)
            self.en_passant_target = coords_to_algebraic(*ep_target_coords)

        # Handle En Passant capture (remove captured pawn, set flags)
        end_coords_alg = coords_to_algebraic(r_end, c_end) # Target square of the current move
        if is_pawn_move and end_coords_alg == current_ep_target_alg:
             captured_pawn_r = r_end + (1 if color == WHITE else -1) # Pawn was behind target sq
             self.board[captured_pawn_r][c_end] = EMPTY_SQUARE
             self.last_move_was_capture = True # En passant is a capture
             self.halfmove_clock = 0 # Reset clock on EP capture

        # Handle Castling (move rook)
        if piece.upper() == KING and abs(c_start - c_end) == 2:
            rook_start_c = BOARD_SIZE - 1 if c_end > c_start else 0
            rook_end_c = c_end - 1 if c_end > c_start else c_end + 1
            rook = self.board[r_start][rook_start_c]
            self.board[r_start][rook_start_c] = EMPTY_SQUARE
            self.board[r_start][rook_end_c] = rook

        # --- Check Promotion ---
        promo_rank = 0 if color == WHITE else BOARD_SIZE - 1
        if is_pawn_move and r_end == promo_rank:
            self.needs_promotion = (r_end, c_end)
            self.status_message = "Pawn promotion required!"
            self.last_move_coords = (r_start, c_start, r_end, c_end)
            # Do NOT switch turn or update status yet.
            return True # Pending promotion

        # --- Update Castling Rights ---
        if piece.upper() == KING:
            if color == WHITE: self.castling_rights['K'] = self.castling_rights['Q'] = False; self.king_moved[WHITE] = True
            else: self.castling_rights['k'] = self.castling_rights['q'] = False; self.king_moved[BLACK] = True
        # Map of starting squares to rights key and color
        rook_start_pos_map = {
             (7, 0): ('Q', WHITE), (7, 7): ('K', WHITE), # White rooks
             (0, 0): ('q', BLACK), (0, 7): ('k', BLACK)  # Black rooks
        }
        # Check if rook moved FROM its starting square
        start_alg = coords_to_algebraic(r_start, c_start)
        if (r_start, c_start) in rook_start_pos_map:
            key, r_color = rook_start_pos_map[(r_start, c_start)]
            if r_color == color:
                self.castling_rights[key] = False
                # Use .get() for safety when accessing self.rook_moved
                if self.rook_moved.get(color, {}).get(start_alg) is not None:
                     self.rook_moved[color][start_alg] = True

        # Check if a rook was captured ON its starting square
        end_alg = coords_to_algebraic(r_end, c_end)
        if captured_piece != EMPTY_SQUARE and (r_end, c_end) in rook_start_pos_map:
             key, cap_r_color = rook_start_pos_map[(r_end, c_end)]
             if cap_r_color != color: # If it was opponent's rook
                 self.castling_rights[key] = False

        # --- Finalize move (only if no promotion is pending) ---
        self.last_move_coords = (r_start, c_start, r_end, c_end)
        self.switch_turn() # Increments fullmove_number if needed
        self.update_game_status() # Check for check/checkmate/stalemate for the *next* player
        return True

    def complete_promotion(self, promo_piece_char):
        """
        Completes the pawn promotion after the GUI gets the user's choice.
        Updates the board, switches turn, and updates game status.
        """
        if not self.needs_promotion: return False
        r, c = self.needs_promotion
        color = WHITE if r == 0 else BLACK # Color determined by promotion rank

        promo_piece_char = promo_piece_char.upper()
        if promo_piece_char not in (QUEEN, ROOK, BISHOP, KNIGHT): promo_piece_char = QUEEN

        final_piece = promo_piece_char.upper() if color == WHITE else promo_piece_char.lower()
        self.board[r][c] = final_piece
        self.needs_promotion = None # Promotion complete

        # Promotion resets halfmove clock
        self.halfmove_clock = 0

        # Now, finalize the turn
        self.switch_turn()
        self.update_game_status()
        # Set status AFTER update_game_status, as that checks for mate/stale
        if not self.game_over:
             self.status_message = f"Pawn promoted to {final_piece}."
        return True


    def update_game_status(self):
        """Checks for check, checkmate, and stalemate for the player whose turn it CURRENTLY is."""
        current_player_color = self.turn
        is_check = self.is_in_check(current_player_color)
        legal_moves_exist = any(self.get_all_legal_moves(current_player_color))

        if not legal_moves_exist:
            if is_check:
                self.game_over = True; self.winner = BLACK if current_player_color == WHITE else WHITE
                self.status_message = f"Checkmate! {self.winner.capitalize()} wins."
            else:
                self.game_over = True; self.winner = None # Draw
                self.status_message = "Stalemate! The game is a draw."
        elif is_check:
            self.status_message = f"{current_player_color.capitalize()} is in Check!"
        else:
             # Clear previous status only if it was just 'Check!' or requires update
             if "Check!" in self.status_message or "required!" in self.status_message:
                  self.status_message = ""

        # Could add 50-move rule check here:
        # if self.halfmove_clock >= 100: # 100 half-moves = 50 full moves
        #     self.game_over = True; self.winner = None
        #     self.status_message = "Draw by 50-move rule."


    def get_fen(self):
        """Generates the Forsyth-Edwards Notation (FEN) string for the current board state."""
        fen = ""
        # 1. Piece placement (from rank 8 to 1)
        for r in range(BOARD_SIZE):
            empty_count = 0
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece == EMPTY_SQUARE:
                    empty_count += 1
                else:
                    if empty_count > 0: fen += str(empty_count)
                    empty_count = 0; fen += piece
            if empty_count > 0: fen += str(empty_count)
            if r < BOARD_SIZE - 1: fen += '/'
        # 2. Active color ('w' or 'b')
        fen += f" {'w' if self.turn == WHITE else 'b'}"
        # 3. Castling availability (KQkq or -)
        castle_str = ""
        if self.castling_rights.get('K', False): castle_str += 'K'
        if self.castling_rights.get('Q', False): castle_str += 'Q'
        if self.castling_rights.get('k', False): castle_str += 'k'
        if self.castling_rights.get('q', False): castle_str += 'q'
        fen += f" {castle_str if castle_str else '-'}"
        # 4. En passant target square (algebraic or -)
        fen += f" {self.en_passant_target if self.en_passant_target else '-'}"
        # 5. Halfmove clock
        fen += f" {self.halfmove_clock}"
        # 6. Fullmove number
        fen += f" {self.fullmove_number}"
        return fen