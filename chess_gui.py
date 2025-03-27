# chess_gui.py (Refactored for In-Pygame Buttons)

import pygame
from pygame import mixer
import sys
import os
import time

# --- python-chess Integration ---
try:
    import chess
    import chess.engine
    PYTHON_CHESS_AVAILABLE = True
except ImportError:
    PYTHON_CHESS_AVAILABLE = False # Flag will be checked later

from chess_logic import ChessGame, WHITE, BLACK, EMPTY_SQUARE, BOARD_SIZE, KING, QUEEN, ROOK, BISHOP, KNIGHT
from chess_logic import coords_to_algebraic, algebraic_to_coords, is_on_board, get_color

# --- Constants ---
WIDTH, HEIGHT = 600, 650; SQUARE_SIZE = WIDTH // BOARD_SIZE
BOARD_OFFSET_X, BOARD_OFFSET_Y = 0, 0; STATUS_HEIGHT = 50
# Colors
COLOR_WHITE_SQUARE = pygame.Color(238, 238, 210); COLOR_BLACK_SQUARE = pygame.Color(118, 150, 86)
COLOR_HIGHLIGHT_SELECT = pygame.Color(246, 246, 105, 180); COLOR_HIGHLIGHT_VALID = pygame.Color(80, 140, 80, 150)
COLOR_HIGHLIGHT_CHECK = pygame.Color(255, 50, 50, 150); COLOR_STATUS_BG = pygame.Color(50, 50, 50)
COLOR_STATUS_TEXT = pygame.Color(230, 230, 230); COLOR_STATUS_ALERT = pygame.Color(255, 200, 0)
COLOR_BUTTON = pygame.Color(80, 80, 150); COLOR_BUTTON_HOVER = pygame.Color(110, 110, 180)
COLOR_BUTTON_DISABLED = pygame.Color(100, 100, 100); COLOR_BUTTON_TEXT = pygame.Color('white')
COLOR_MENU_BG = pygame.Color(40, 40, 60); COLOR_PROMOTION_BG = pygame.Color(60, 60, 80, 220) # Slightly transparent

# STOCKFISH_PATH = r"C:\Users\SwiftGo\Documents\Chess\assets\stockfish-3-win\Windows\Intel 64\stockfish-3-64-ja.exe" # Verify path
# STOCKFISH_PATH = r"C:\Users\SwiftGo\Documents\Chess\assets\stockfish-20-ja\Windows\stockfish-20-64-ja.exe"
STOCKFISH_PATH = r"C:\Users\SwiftGo\Documents\Chess\assets\stockfish_10_ja\stockfish.exe"
# --- Game States ---
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PROMOTION = 2
STATE_GAME_OVER = 3

# --- Game Modes ---
HUMAN_VS_HUMAN = 0
HUMAN_VS_AI = 1

# --- Simple Button Class ---
# (Keep Button class exactly as in the previous version)
class Button:
    def __init__(self, x, y, width, height, text, font, color, hover_color, disabled_color, callback, enabled=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.disabled_color = disabled_color
        self.callback = callback
        self.enabled = enabled
        self.is_hovered = False
        self._update_text_surf()

    def _update_text_surf(self):
        self.text_surf = self.font.render(self.text, True, COLOR_BUTTON_TEXT)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def set_enabled(self, enabled_status):
        self.enabled = enabled_status

    def draw(self, surface):
        if not self.enabled: draw_color = self.disabled_color
        elif self.is_hovered: draw_color = self.hover_color
        else: draw_color = self.color
        pygame.draw.rect(surface, draw_color, self.rect, border_radius=8)
        surface.blit(self.text_surf, self.text_rect)

    def handle_event(self, event):
        if not self.enabled: self.is_hovered = False; return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                if self.callback: self.callback(); return True
        return False


# --- Pygame Setup / Asset Loading / Fonts ---
pygame.init()
mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Chess")
try: # Font loading (keep as before)
    status_font = pygame.font.SysFont(None, 28); button_font_small = pygame.font.SysFont(None, 24); button_font_large = pygame.font.SysFont(None, 36)
    menu_title_font = pygame.font.SysFont(None, 72); game_over_font = pygame.font.SysFont(None, 48); piece_font_fallback = pygame.font.SysFont(None, int(SQUARE_SIZE * 0.6))
except Exception as e:
    print(f"Font loading error: {e}. Using default."); status_font = pygame.font.Font(None, 28); button_font_small = pygame.font.Font(None, 24); button_font_large = pygame.font.Font(None, 36)
    menu_title_font = pygame.font.Font(None, 72); game_over_font = pygame.font.Font(None, 48); piece_font_fallback = pygame.font.Font(None, int(SQUARE_SIZE * 0.6))

# --- Sound Loading --- (Keep as before)
move_sound, capture_sound = None, None; sound_folder = 'assets'
try:
    move_sound_path=os.path.join(sound_folder,'move.mp3'); capture_sound_path=os.path.join(sound_folder,'capture.mp3')
    if os.path.exists(move_sound_path): move_sound = mixer.Sound(move_sound_path); print(f"Loaded sound: {move_sound_path}")
    else: print(f"Warning: Sound file not found: {move_sound_path}")
    if os.path.exists(capture_sound_path): capture_sound = mixer.Sound(capture_sound_path); print(f"Loaded sound: {capture_sound_path}")
    else: print(f"Warning: Sound file not found: {capture_sound_path}")
except Exception as e: print(f"Error loading sounds: {e}. Sounds disabled.")

# --- Image Loading (with SyntaxError fix) ---
piece_images = {}
def load_images():
    """Loads piece images from the 'assets' directory."""
    global piece_images
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    img_folder = 'assets'

    if not os.path.isdir(img_folder):
        print(f"Error: Image folder '{img_folder}' not found.")
        return

    print(f"Loading images from: {os.path.abspath(img_folder)}")
    loaded_count = 0
    for piece in pieces:
        path = os.path.join(img_folder, f"{piece}.png")

        # *** FIX: Check for file existence *before* the try block ***
        if not os.path.exists(path):
            print(f"Warning: Image file not found: {path}")
            continue # Skip to the next piece in the loop

        # *** Now, try to load the image, knowing it exists ***
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (SQUARE_SIZE, SQUARE_SIZE))
            piece_images[piece] = img
            loaded_count += 1
        except pygame.error as e:
            print(f"Pygame Error loading image {path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred loading {path}: {e}")

    # --- Report loading status ---
    if loaded_count > 0: print(f"Successfully loaded {loaded_count} piece images.")
    if loaded_count < len(pieces): print(f"Warning: {len(pieces) - loaded_count} images missing/failed.")
    if loaded_count == 0: print("Warning: No images loaded. Using fallback drawing.")

# --- Fallback Drawing --- (Keep as before)
def draw_piece_fallback(surface, piece_char, rect):
    if piece_char == EMPTY_SQUARE: return; color = pygame.Color('whitesmoke') if piece_char.isupper() else pygame.Color('dimgray'); text_color = pygame.Color('dimgray') if piece_char.isupper() else pygame.Color('whitesmoke')
    center = rect.center; radius = int(SQUARE_SIZE * 0.38); pygame.draw.circle(surface, color, center, radius); letter = piece_char.upper(); text_surf = piece_font_fallback.render(letter, True, text_color)
    text_rect = text_surf.get_rect(center=center); surface.blit(text_surf, text_rect)
# --- Core Drawing Functions --- (Keep draw_board, draw_pieces as before)
def draw_board(surface):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE): color = COLOR_WHITE_SQUARE if (r + c) % 2 == 0 else COLOR_BLACK_SQUARE; rect = pygame.Rect(BOARD_OFFSET_X+c*SQUARE_SIZE, BOARD_OFFSET_Y+r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE); pygame.draw.rect(surface, color, rect)
def draw_pieces(surface, board):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece != EMPTY_SQUARE:
                rect = pygame.Rect(BOARD_OFFSET_X+c*SQUARE_SIZE, BOARD_OFFSET_Y+r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                piece_name = ('w' if piece.isupper() else 'b') + piece.upper()
                if piece_name in piece_images:
                    surface.blit(piece_images[piece_name], rect)
                else:
                    draw_piece_fallback(surface, piece, rect)
# --- highlight_square (using fixed version) ---
def highlight_square(surface, r, c, color):
    if not is_on_board(r, c): return
    try:
        local_highlight_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        local_highlight_surf.fill(color); blit_pos = (BOARD_OFFSET_X + c * SQUARE_SIZE, BOARD_OFFSET_Y + r * SQUARE_SIZE)
        surface.blit(local_highlight_surf, blit_pos)
    except Exception as e: print(f"Error in highlight_square for ({r}, {c}) with color {color}: {e}")
# --- Status Bar Drawing --- (Keep as before)
def draw_status(surface, game, game_mode):
    y_pos = BOARD_OFFSET_Y + BOARD_SIZE * SQUARE_SIZE; status_rect = pygame.Rect(0, y_pos, WIDTH, STATUS_HEIGHT); pygame.draw.rect(surface, COLOR_STATUS_BG, status_rect); mode_text = "vs Human" if game_mode == HUMAN_VS_HUMAN else "vs AI"
    turn_text = f"{game.turn.capitalize()}'s Turn ({mode_text})"; text_surf = status_font.render(turn_text, True, COLOR_STATUS_TEXT); surface.blit(text_surf, (10, y_pos + 15))
    if game.status_message: msg_color = COLOR_STATUS_ALERT if ("Check" in game.status_message or "mate" in game.status_message or "Stale" in game.status_message) else COLOR_STATUS_TEXT; status_surf = status_font.render(game.status_message, True, msg_color); status_text_rect = status_surf.get_rect(right=WIDTH - 10, centery=y_pos + STATUS_HEIGHT // 2); surface.blit(status_surf, status_text_rect)

# --- Stockfish Engine Handling --- (Keep as before)
def init_stockfish():
    if not PYTHON_CHESS_AVAILABLE: print("AI disabled: python-chess not found."); return None;
    if not os.path.exists(STOCKFISH_PATH): print(f"AI disabled: Stockfish not found at '{STOCKFISH_PATH}'."); return None
    try: engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH); print(f"Stockfish initialized from: {STOCKFISH_PATH}"); return engine
    except Exception as e: print(f"Error initializing Stockfish: {e}. AI disabled."); return None
def get_ai_move(engine, game, think_time=0.5):
    if not engine or not PYTHON_CHESS_AVAILABLE:
        return None
    try:
        board = chess.Board(fen=game.get_fen())
        if board.is_game_over():
            return None
        result = engine.play(board, chess.engine.Limit(time=think_time))
        if result.move:
            print(f"Stockfish suggests: {result.move.uci()}")
            return result.move.uci()
        else:
            print("Stockfish didn't return a move.")
            return None
    except Exception as e:
        print(f"Error getting AI move: {e}")
        return None


# --- Main Game Function ---
def main():
    """Main function with Pygame states for Menu, Playing, Game Over."""
    game = ChessGame()
    load_images() # Load assets
    stockfish_engine = None
    game_mode = HUMAN_VS_HUMAN # Default, decided by menu
    current_state = STATE_MENU # Start at the menu

    # --- Game Loop Variables ---
    running = True; selected_piece_coords = None; valid_moves_for_selected = set()
    clock = pygame.time.Clock(); ai_thinking = False
    menu_error_message = "" # To display temporary errors on menu screen

    # --- Button Creation & Callbacks ---
    menu_buttons = []; promotion_buttons = []; game_over_buttons = []

    def start_hvh(): # Menu button callback
        nonlocal game_mode, current_state, game, stockfish_engine, menu_error_message
        if stockfish_engine:
            try:
                stockfish_engine.quit()
            except:
                pass
            stockfish_engine = None
        game_mode = HUMAN_VS_HUMAN; current_state = STATE_PLAYING; game.reset_game()
        game.status_message = "Human vs Human game started."; menu_error_message=""
    def start_hvai(): # Menu button callback
        nonlocal game_mode, current_state, game, stockfish_engine, menu_error_message
        stockfish_engine = init_stockfish()
        if stockfish_engine:
             game_mode = HUMAN_VS_AI; current_state = STATE_PLAYING; game.reset_game()
             game.status_message = "Human vs AI game started."; menu_error_message=""
        else:
             menu_error_message = "Failed to start AI engine. Check path/install." # Show error on menu
             for btn in menu_buttons: # Disable button after failed attempt
                 if btn.text == "Human vs AI": btn.set_enabled(False)
    def go_play_again(): # Game Over button callback
        nonlocal current_state, game, selected_piece_coords, valid_moves_for_selected, ai_thinking
        game.reset_game(); selected_piece_coords = None; valid_moves_for_selected = set(); ai_thinking = False
        current_state = STATE_PLAYING; game.status_message = f"New game started ({'HvH' if game_mode == HUMAN_VS_HUMAN else 'HvAI'})."
    def go_quit(): # Game Over button callback
        nonlocal running; running = False
    def make_promo_callback(p_char): # Promotion button callback factory
        def promo_callback():
            nonlocal current_state # Indicate modification
            game.complete_promotion(p_char) # Complete the promotion in logic
            # Check game state *after* promotion is complete
            if game.game_over: current_state = STATE_GAME_OVER
            else: current_state = STATE_PLAYING # Go back to playing
        return promo_callback

    # Create Menu Buttons
    btn_hvh = Button(WIDTH//2 - 150, HEIGHT//2 - 30, 300, 60, "Human vs Human", button_font_large, COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_DISABLED, start_hvh)
    btn_hvai = Button(WIDTH//2 - 150, HEIGHT//2 + 50, 300, 60, "Human vs AI", button_font_large, COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_DISABLED, start_hvai, enabled=PYTHON_CHESS_AVAILABLE)
    menu_buttons.extend([btn_hvh, btn_hvai])
    # Create Game Over Buttons
    btn_again = Button(WIDTH//2 - 160, HEIGHT//2 + 50, 150, 50, "Play Again", button_font_large, COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_DISABLED, go_play_again)
    btn_quit = Button(WIDTH//2 + 10, HEIGHT//2 + 50, 150, 50, "Quit Game", button_font_large, COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_DISABLED, go_quit)
    game_over_buttons.extend([btn_again, btn_quit])


    # --- Main Game Loop ---
    while running:
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()

        # --- Global Event Handling (Quit) ---
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break # Exit event loop if quitting
        if not running: break # Exit main loop

        # --- State-Based Event Handling & Logic ---
        if current_state == STATE_MENU:
            for event in events:
                 for btn in menu_buttons:
                     if btn.handle_event(event): break # Stop processing if button clicked
            # Update button hover state based on current mouse pos
            for btn in menu_buttons:
                 btn.is_hovered = btn.enabled and btn.rect.collidepoint(mouse_pos)

        elif current_state == STATE_PLAYING:
            is_human_turn = (game.turn == WHITE or (game.turn == BLACK and game_mode == HUMAN_VS_HUMAN))
            # Handle Human Input
            if is_human_turn and not ai_thinking:
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # (Keep exact human click handling logic as before)
                        mx, my = event.pos
                        if BOARD_OFFSET_Y <= my < BOARD_OFFSET_Y+BOARD_SIZE*SQUARE_SIZE and BOARD_OFFSET_X <= mx < BOARD_OFFSET_X+BOARD_SIZE*SQUARE_SIZE:
                            c = (mx-BOARD_OFFSET_X)//SQUARE_SIZE; r = (my-BOARD_OFFSET_Y)//SQUARE_SIZE
                            if is_on_board(r, c):
                                coords = (r, c)
                                if selected_piece_coords: # Try move
                                    if coords == selected_piece_coords: selected_piece_coords=None; valid_moves_for_selected=set() # Deselect
                                    elif coords in valid_moves_for_selected: # Attempt move
                                        success = game.make_move(selected_piece_coords, coords)
                                        if success:
                                            if game.last_move_was_capture and capture_sound: capture_sound.play()
                                            elif not game.last_move_was_capture and move_sound: move_sound.play()
                                            selected_piece_coords=None; valid_moves_for_selected=set()
                                            if game.needs_promotion: current_state = STATE_PROMOTION
                                            elif game.game_over: current_state = STATE_GAME_OVER
                                        # else: status updated by logic
                                    else: # Clicked invalid target
                                        piece=game.get_piece(r,c);
                                        if piece!=EMPTY_SQUARE and get_color(piece)==game.turn: # Select other piece
                                            selected_piece_coords=coords; all_moves=game.get_all_legal_moves(game.turn); valid_moves_for_selected=all_moves.get(coords, set())
                                        else: selected_piece_coords=None; valid_moves_for_selected=set() # Deselect
                                else: # Select piece
                                    piece = game.get_piece(r, c)
                                    if piece != EMPTY_SQUARE and get_color(piece) == game.turn:
                                        selected_piece_coords=coords; all_moves=game.get_all_legal_moves(game.turn); valid_moves_for_selected=all_moves.get(coords, set())
                                    else: selected_piece_coords = None; valid_moves_for_selected = set()
                        else: selected_piece_coords = None; valid_moves_for_selected = set() # Click outside board

            # Handle AI move trigger event
            is_ai_turn = (game_mode == HUMAN_VS_AI and game.turn == BLACK)
            if is_ai_turn and not game.game_over and not ai_thinking:
                 ai_thinking = True
                 pygame.time.set_timer(pygame.USEREVENT + 1, 150, loops=1)

            for event in events: # Separate loop for AI event? No, check within main loop
                if event.type == pygame.USEREVENT + 1 and ai_thinking:
                     pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                     ai_move_uci = get_ai_move(stockfish_engine, game, think_time=0.5)
                     if ai_move_uci:
                         ai_start=algebraic_to_coords(ai_move_uci[0:2]); ai_end=algebraic_to_coords(ai_move_uci[2:4])
                         if ai_start and ai_end:
                             success = game.make_move(ai_start, ai_end)
                             if success:
                                 if game.last_move_was_capture and capture_sound: capture_sound.play()
                                 elif not game.last_move_was_capture and move_sound: move_sound.play()
                                 if game.game_over: current_state = STATE_GAME_OVER
                             # else: AI move rejected (shouldn't happen often)
                         # else: Parse error
                     # else: AI failed
                     ai_thinking = False

            # Update button hover states for the current state
            if selected_piece_coords: # Update hover for valid moves (visual only)
                pass # Highlighting handles this visually

        elif current_state == STATE_PROMOTION:
            # Create buttons if they don't exist for this promotion instance
            if not promotion_buttons: # Only create once per promotion state entry
                color = WHITE if game.turn == WHITE else BLACK # Whose turn was it?
                promo_pieces = [QUEEN, ROOK, BISHOP, KNIGHT]
                promo_btn_size = SQUARE_SIZE
                promo_btn_y = HEIGHT // 2 - promo_btn_size // 2
                start_x = WIDTH // 2 - (len(promo_pieces) * (promo_btn_size + 10)) // 2
                for i, piece_char in enumerate(promo_pieces):
                    btn = Button(start_x + i * (promo_btn_size + 10), promo_btn_y, promo_btn_size, promo_btn_size,
                                 piece_char, button_font_large, COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_DISABLED,
                                 make_promo_callback(piece_char)) # Use factory
                    promotion_buttons.append(btn)

            for event in events:
                 for btn in promotion_buttons:
                     if btn.handle_event(event):
                         promotion_buttons = [] # Clear buttons after selection
                         break
            # Update hover state
            for btn in promotion_buttons:
                 btn.is_hovered = btn.enabled and btn.rect.collidepoint(mouse_pos)


        elif current_state == STATE_GAME_OVER:
             for event in events:
                 for btn in game_over_buttons:
                     if btn.handle_event(event): break
             # Update hover state
             for btn in game_over_buttons:
                  btn.is_hovered = btn.enabled and btn.rect.collidepoint(mouse_pos)


        # --- Drawing ---
        screen.fill(COLOR_MENU_BG) # Default background, overwritten by states

        if current_state == STATE_MENU:
            title_surf = menu_title_font.render("Pygame Chess", True, COLOR_STATUS_TEXT); title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3)); screen.blit(title_surf, title_rect)
            for btn in menu_buttons: btn.draw(screen)
            if menu_error_message: status_surf = status_font.render(menu_error_message, True, COLOR_STATUS_ALERT); status_rect = status_surf.get_rect(center=(WIDTH // 2, HEIGHT - 50)); screen.blit(status_surf, status_rect)

        elif current_state == STATE_PLAYING or current_state == STATE_PROMOTION:
            # Draw Board, Pieces, Highlights, Status
            draw_board(screen)
            if selected_piece_coords: highlight_square(screen, *selected_piece_coords, COLOR_HIGHLIGHT_SELECT)
            for r_m, c_m in valid_moves_for_selected: highlight_square(screen, r_m, c_m, COLOR_HIGHLIGHT_VALID)
            king_in_check_pos = None
            if not game.game_over and game.is_in_check(game.turn): king_in_check_pos = game.find_king(game.turn)
            if king_in_check_pos: highlight_square(screen, *king_in_check_pos, COLOR_HIGHLIGHT_CHECK)
            draw_pieces(screen, game.board)
            draw_status(screen, game, game_mode)
            # Draw Promotion Overlay and Buttons if needed
            if current_state == STATE_PROMOTION:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill(COLOR_PROMOTION_BG); screen.blit(overlay, (0, 0))
                for btn in promotion_buttons: btn.draw(screen)

        elif current_state == STATE_GAME_OVER:
            # Draw Final Board State & Status
            draw_board(screen); draw_pieces(screen, game.board)
            if game.winner is not None: loser_color = BLACK if game.winner == WHITE else WHITE; king_pos = game.find_king(loser_color);
            if king_pos: highlight_square(screen, *king_pos, COLOR_HIGHLIGHT_CHECK)
            draw_status(screen, game, game_mode)
            # Draw Game Over Overlay and Buttons
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0, 0))
            go_text = game.status_message; go_surf = game_over_font.render(go_text, True, COLOR_STATUS_ALERT); go_rect = go_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)); screen.blit(go_surf, go_rect)
            for btn in game_over_buttons: btn.draw(screen)

        pygame.display.flip()
        clock.tick(30)

    # --- End of Game Loop ---
    if stockfish_engine: print("Quitting Stockfish engine..."); stockfish_engine.quit()
    pygame.quit(); sys.exit()

# --- Main Execution Guard ---
if __name__ == "__main__":
    if not PYTHON_CHESS_AVAILABLE: print("---\nNOTE: 'python-chess' not installed (pip install python-chess). 'Human vs AI' disabled.\n---")
    main()