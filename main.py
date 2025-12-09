import pygame
import random
from dataclasses import dataclass
from typing import List, Generator, Tuple

# --- Configuration Constants ---
CELL_SIZE = 30
COLS = 20
ROWS = 15
MINES_COUNT = 30
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE

# Color palette definition for easy theme adjustments
COLORS = {
    'bg': (192, 192, 192),
    'grid': (128, 128, 128),
    'mine': (255, 0, 0),
    'text': (0, 0, 0),
    'flag': (255, 255, 0),
    'overlay': (0, 0, 0, 128),
    'white': (255, 255, 255)
}


@dataclass
class Cell:
    """
    Represents the state of a single cell on the game board.
    Attributes:
        is_mine (bool): True if the cell contains a mine.
        is_open (bool): True if the cell has been revealed by the player.
        is_flagged (bool): True if the player has placed a flag on this cell.
        adjacent_mines (int): The number of mines in the 8 neighboring cells.
    """
    is_mine: bool = False
    is_open: bool = False
    is_flagged: bool = False
    adjacent_mines: int = 0


class GameBoard:
    """
    Manages the core game logic, board state, and rule enforcement.
    """

    def __init__(self, cols: int, rows: int, mines: int):
        """
        Initializes the game board.

        Args:
            cols (int): Number of columns in the grid.
            rows (int): Number of rows in the grid.
            mines (int): Total number of mines to place.
        """
        self.cols = cols
        self.rows = rows
        self.mines = mines
        self.game_over = False
        self.won = False
        self.board: List[List[Cell]] = []

        # Initialize the game state immediately upon creation
        self.reset_game()

    def reset_game(self):
        """
        Resets the game to its initial state: clears the board,
        places new mines, and recalculates adjacencies.
        """
        self.game_over = False
        self.won = False
        # Create a 2D grid of fresh Cell objects using list comprehension
        self.board = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
        self._place_mines()
        self._calculate_adjacent_mines()

    def _get_neighbors(self, r: int, c: int) -> Generator[Tuple[int, int], None, None]:
        """
        A generator that yields valid coordinates for neighbors of a specific cell.
        This helper method handles boundary checks to prevent IndexError.
        Args:
            r (int): Row index.
            c (int): Column index.

        Yields:
            Tuple[int, int]: Coordinates (row, col) of a valid neighbor.
        """
        # Iterate through 3x3 grid around the cell
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue  # Skip the cell itself

                nr, nc = r + dr, c + dc

                # Check bounds to ensure the neighbor is within the grid
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def _place_mines(self):
        """Randomly distributes mines across the board."""
        # Generate a list of all possible coordinates
        all_coords = [(r, c) for r in range(self.rows) for c in range(self.cols)]

        # Select unique coordinates for mines
        for r, c in random.sample(all_coords, self.mines):
            self.board[r][c].is_mine = True

    def _calculate_adjacent_mines(self):
        """
        Pre-calculates the 'adjacent_mines' count for every cell on the board.
        This optimization avoids recalculating neighbors during the game loop.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c].is_mine:
                    # Sum up the number of neighbors that contain mines
                    self.board[r][c].adjacent_mines = sum(
                        1 for nr, nc in self._get_neighbors(r, c)
                        if self.board[nr][nc].is_mine
                    )

    def handle_click(self, r: int, c: int, button: int):
        """
        Dispatches mouse click events to the appropriate game action.
        Args:
            r (int): Row index of the clicked cell.
            c (int): Column index of the clicked cell.
            button (int): Mouse button ID (1 for Left Click, 3 for Right Click).
        """
        # If the game ended, a click restarts it
        if self.game_over:
            self.reset_game()
            return

        if button == 1:  # Left Mouse Button -> Reveal
            self.open_cell(r, c)
        elif button == 3:  # Right Mouse Button -> Toggle Flag
            self.toggle_flag(r, c)

        self._check_win()

    def open_cell(self, r: int, c: int):
        """
        Reveals a cell. Implements the Flood Fill algorithm for empty areas.
        Args:
            r (int): Row index.
            c (int): Column index.
        """
        cell = self.board[r][c]

        # Base case: Do nothing if cell is already processed or protected by a flag
        if cell.is_open or cell.is_flagged:
            return

        cell.is_open = True

        if cell.is_mine:
            self.game_over = True
            return

        # Recursive step: If the cell has no adjacent mines, automatically open neighbors
        if cell.adjacent_mines == 0:
            for nr, nc in self._get_neighbors(r, c):
                self.open_cell(nr, nc)

    def toggle_flag(self, r: int, c: int):
        """Toggles the flag state, but only for closed cells."""
        if not self.board[r][c].is_open:
            self.board[r][c].is_flagged = not self.board[r][c].is_flagged

    def _check_win(self):
        """
        Checks victory condition: The game is won if all non-mine cells are open.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                # If there is a safe cell that is still closed, the game continues
                if not cell.is_mine and not cell.is_open:
                    return

        self.won = True
        self.game_over = True


def main():
    """
    Main entry point. Initializes Pygame, handles the event loop, and rendering.
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Minesweeper (Press R to Reset)")

    # Fonts initialization
    font_numbers = pygame.font.SysFont('Arial', CELL_SIZE // 2)
    font_game_over = pygame.font.SysFont('Arial', 40)

    game = GameBoard(COLS, ROWS, MINES_COUNT)
    clock = pygame.time.Clock()

    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset_game()

            # Mouse input
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Convert pixel coordinates to grid indices
                game.handle_click(my // CELL_SIZE, mx // CELL_SIZE, event.button)

        # --- Rendering ---
        screen.fill(COLORS['bg'])

        for r in range(ROWS):
            for c in range(COLS):
                cell = game.board[r][c]
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)

                # Draw cell border
                pygame.draw.rect(screen, COLORS['grid'], rect, 1)

                if cell.is_open:
                    if cell.is_mine:
                        # Draw mine (Red Circle)
                        pygame.draw.circle(screen, COLORS['mine'], rect.center, CELL_SIZE // 3)
                    elif cell.adjacent_mines > 0:
                        # Draw neighbor count number
                        text = font_numbers.render(str(cell.adjacent_mines), True, COLORS['text'])
                        screen.blit(text, text.get_rect(center=rect.center))
                elif cell.is_flagged:
                    # Draw flag (Yellow Triangle)
                    pygame.draw.polygon(screen, COLORS['flag'], [
                        (rect.left + 5, rect.top + 5),
                        (rect.right - 5, rect.centery),
                        (rect.left + 5, rect.bottom - 5)
                    ])

        # --- Game Over / Victory Overlay ---
        if game.game_over:
            # Create a semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill(COLORS['overlay'])
            screen.blit(overlay, (0, 0))

            # Prepare status message
            msg = "VICTORY!" if game.won else "GAME OVER"
            color = (0, 255, 0) if game.won else (255, 0, 0)

            # Render text centered on screen
            text = font_game_over.render(msg, True, color)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

            restart_text = font_numbers.render("Press R or Click to Restart", True, COLORS['white'])
            screen.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

        # Update display and cap the frame rate
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()