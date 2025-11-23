#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai

# Functions to define:
#   - legal move checker and other rules should be in def possible()
#   - compute best move should check for the heuristic score that lets the player choose the best move in the tree (min max tree should be implemented for this)


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    # N.B. This is a very naive implementation.
    def compute_best_move(self, game_state: GameState) -> None:
        board = game_state.board
        N = board.N
        taboo = game_state.taboo_moves

        # Allowed squares for this player (None means "all squares allowed")
        allowed = game_state.player_squares()
        if allowed is None:
            allowed = [(i, j) for i in range(N) for j in range(N)]

        # ---------- C0 CHECKS (row / column / block uniqueness) ----------

        def row_has_value(i, value):
            for col in range(N):
                cell = board.get((i, col))
                if cell != SudokuBoard.empty and cell == value:
                    return True
            return False

        def col_has_value(j, value):
            for row in range(N):
                cell = board.get((row, j))
                if cell != SudokuBoard.empty and cell == value:
                    return True
            return False

        def block_has_value(i, j, value):
            m = board.region_height()
            n = board.region_width()
            bi = (i // m) * m
            bj = (j // n) * n
            for r in range(bi, bi + m):
                for c in range(bj, bj + n):
                    cell = board.get((r, c))
                    if cell != SudokuBoard.empty and cell == value:
                        return True
            return False

        # ------------------ master legality checker ----------------------

        def is_legal_move(i, j, value):
            # Must be in allowed squares
            if (i, j) not in allowed:
                return False

            # Must be empty
            if board.get((i, j)) != SudokuBoard.empty:
                return False

            # Value in range
            if not (1 <= value <= N):
                return False

            # Not a taboo move
            for t in taboo:
                if t.square == (i, j) and t.value == value:
                    return False

            # C0: uniqueness rule
            if row_has_value(i, value):
                return False
            if col_has_value(j, value):
                return False
            if block_has_value(i, j, value):
                return False

            return True

        # ------------- very simple score function -----------------

        def move_score(i, j, value):
            """
            Very basic heuristic:
            prefer moves in rows / columns / blocks that are already "crowded"
            (i.e., have many filled cells). Idea: this tends to complete
            regions faster and should give points more often than random play.
            """
            score = 0

            # count filled cells in the row (including this move)
            for col in range(N):
                if col == j:
                    score += 1  # the move itself
                elif board.get((i, col)) != SudokuBoard.empty:
                    score += 1

            # count filled cells in the column
            for row in range(N):
                if row == i:
                    continue  # already counted this cell in the row loop
                if row == i and j == j:
                    score += 1
                elif board.get((row, j)) != SudokuBoard.empty:
                    score += 1

            # count filled cells in the block
            m = board.region_height()
            n = board.region_width()
            bi = (i // m) * m
            bj = (j // n) * n
            for r in range(bi, bi + m):
                for c in range(bj, bj + n):
                    if r == i and c == j:
                        score += 1  # the move itself
                    elif board.get((r, c)) != SudokuBoard.empty:
                        score += 1

            return score

        # ---------------- collect all legal moves -----------------

        legal_moves = []
        for (i, j) in allowed:
            if board.get((i, j)) != SudokuBoard.empty:
                continue
            for value in range(1, N + 1):
                if is_legal_move(i, j, value):
                    legal_moves.append((i, j, value))

        # No move available -> propose nothing (opponent wins)
        if not legal_moves:
            return

        # ------------- pick the move with highest score -------------

        best_score = None
        best_moves = []

        for (i, j, value) in legal_moves:
            s = move_score(i, j, value)
            if best_score is None or s > best_score:
                best_score = s
                best_moves = [(i, j, value)]
            elif s == best_score:
                best_moves.append((i, j, value))

        # break ties randomly among best-scoring moves
        i, j, value = random.choice(best_moves)
        move = Move((i, j), value)
        self.propose_move(move)

        # Keep proposing the same move until the time limit is reached.
        while True:
            time.sleep(0.1)
            self.propose_move(move)
