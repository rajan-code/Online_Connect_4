import numpy as np
import pygame
import sys
import math
from typing import *

pygame.init()

NUM_ROWS = 6
NUM_COLUMNS = 7

RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

SQUARE_SIZE = 80
WIDTH = NUM_COLUMNS * SQUARE_SIZE
HEIGHT = (NUM_ROWS + 2) * SQUARE_SIZE + SQUARE_SIZE
RADIUS = (SQUARE_SIZE // 2) - 5
#

font1 = pygame.font.SysFont("monospace", 45)
FONT2 = pygame.font.SysFont("times new roman", 40)


class Game:
    def __init__(self, id):
        self.game_over = False
        self.ready = False
        self.p0_ready, self.p1_ready = False, False
        self.turn = 0  # 0 or 1
        self.id = id
        self.score = [0, 0]
        self.board = self.create_board()
        self.is_running = False
        self.usernames = ['', '']
       # self.draw_board()

    def connected(self):
        return self.ready

    def create_board(self) -> np.ndarray:
        board = np.zeros((6, 7))
        return board

    def drop_piece(self, row: int, col: int, piece: int) -> None:
        """
        :param: piece: 1 or 2
        Precondition: board[row][col] == 0
        """
        self.board[row][col] = piece

    def is_valid_location(self, col: int) -> bool:
        """
        Return True iff column <col> of <board> is a valid column.
        """
        return self.board[NUM_ROWS - 1][col] == 0

    # what if there is no open row
    def get_next_open_row(self, col: int) -> int:
        """
        Precondition: there is an open row.
        """
        for r in range(NUM_ROWS):
            if self.board[r][col] == 0:
                return r

    def print_board(self, board) -> None:
        print(np.flip(board, 0))  # flip board over the x-axis and print it

    def is_winner(self, piece: int) -> bool:
        """
        Precondition: <piece> has just been played on the board.
        Return True iff this player has won the game.
        """
        # check horizontal
        winning_row = np.array([piece, piece, piece, piece])

        for r in range(NUM_ROWS):
            for c in range(NUM_COLUMNS - 3):
                if (self.board[r][c:c + 4] == winning_row).all():  # if player <piece> has won
                    return True

        # check vertical
        for c in range(NUM_COLUMNS):
            for r in range(NUM_ROWS - 3):
                if all(self.board[r + i][c] == piece for i in range(4)):
                    return True

        # check diagonals with +ve slope
        for c in range(NUM_COLUMNS - 3):
            for r in range(NUM_ROWS - 3):
                if all(self.board[r + i][c + i] == piece for i in range(4)):
                    return True

        # check diagonals with -ve slope
        for c in range(NUM_COLUMNS - 3):
            for r in range(3, NUM_ROWS):
                if all(self.board[r - i][c + i] == piece for i in range(4)):
                    return True
        return False

    def is_draw(self):
        return 0. not in self.board

    def draw_board(self, win):
        pygame.draw.rect(win, BLACK, (0, 0, WIDTH, SQUARE_SIZE))  # black rect at top of screen
        pygame.draw.rect(win, BLACK, (SQUARE_SIZE, HEIGHT - SQUARE_SIZE, WIDTH, SQUARE_SIZE*2))  # black rect at bottom of screen
        pygame.draw.rect(win, BLUE, (0, SQUARE_SIZE, WIDTH, HEIGHT - (SQUARE_SIZE * 3)))
        for c in range(NUM_COLUMNS):
            for r in range(NUM_ROWS + 1):
                # pygame.draw.rect(win, BLUE, (c * SQUARE_SIZE, r * SQUARE_SIZE + SQUARE_SIZE, SQUARE_SIZE,SQUARE_SIZE))
                pygame.draw.circle(win, BLACK, (
                c * SQUARE_SIZE + SQUARE_SIZE // 2,
                r * SQUARE_SIZE + SQUARE_SIZE // 2), RADIUS)

        for c in range(NUM_COLUMNS):
            for r in range(NUM_ROWS):
                if self.board[r][c] == 1:
                    pygame.draw.circle(win, RED, (c * SQUARE_SIZE + SQUARE_SIZE // 2, (HEIGHT - (r + 2) * SQUARE_SIZE + SQUARE_SIZE // 2) - SQUARE_SIZE), RADIUS)
                elif self.board[r][c] == 2:
                    pygame.draw.circle(win, YELLOW, (c * SQUARE_SIZE + SQUARE_SIZE // 2, (HEIGHT - (r + 2) * SQUARE_SIZE + SQUARE_SIZE // 2) - SQUARE_SIZE), RADIUS)
        pygame.display.update()

    def run(self, win):
        win.fill(BLACK)
        self.draw_board(win)
        self.is_running = True
        while not self.game_over:
            if self.turn == 0:
                label = font1.render("Player 1's turn", 1, RED)
            else:
                label = font1.render("Player 2's turn", 1, YELLOW)
            pygame.draw.rect(win, BLACK,
                             (0, HEIGHT - SQUARE_SIZE*2, WIDTH, SQUARE_SIZE*2))
            win.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
            pygame.display.update((0, HEIGHT - SQUARE_SIZE*2, WIDTH, SQUARE_SIZE*2))

            if 0. not in self.board:
                label = font1.render("It's a tie!", 1, WHITE)
                pygame.draw.rect(win, BLACK,
                                 (0, HEIGHT - SQUARE_SIZE, WIDTH, SQUARE_SIZE))
                win.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                pygame.display.update((0, HEIGHT - SQUARE_SIZE*2, WIDTH, SQUARE_SIZE*2))
                self.game_over = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEMOTION:
                    pygame.draw.rect(win, BLACK, (0, 0, WIDTH, SQUARE_SIZE))
                    x_pos = event.pos[0]
                    if self.turn == 0:
                        pygame.draw.circle(win, RED,
                                           (x_pos, SQUARE_SIZE // 2), RADIUS)
                    else:
                        pygame.draw.circle(win, YELLOW,
                                           (x_pos, SQUARE_SIZE // 2), RADIUS)
                pygame.display.update()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.turn == 0:  # Ask player 1 for input
                        label = font1.render("Player 1's turn", 1, RED)
                        x_pos = event.pos[0]
                        column = x_pos // SQUARE_SIZE

                        if self.is_valid_location(column):
                            the_row = self.get_next_open_row(column)
                            self.drop_piece(the_row, column, 1)

                            if self.is_winner(1):
                                print('Player 1 has won the game!')
                                label = font1.render("Player 1 wins!", 1, RED)
                                win.blit(label, (45, HEIGHT - 75 - SQUARE_SIZE))
                                self.score[0] += 1
                                pygame.display.update()
                                self.game_over = True

                    else:  # Ask player 2 for input
                        label = font1.render("Player 2's turn", 1, YELLOW)
                        x_pos = event.pos[0]
                        column = x_pos // SQUARE_SIZE

                        if self.is_valid_location(column):
                            the_row = self.get_next_open_row(column)
                            self.drop_piece(the_row, column, 2)

                            if self.is_winner(2):
                                print('Player 2 has won the game!')
                                win.blit(label, (45, HEIGHT - 75 - SQUARE_SIZE))
                                self.score[1] += 1
                                label = font1.render("Player 2 wins!", 1,  YELLOW)
                                self.game_over = True

                    self.turn += 1
                    self.turn = self.turn % 2  # 0 if turn is even, else 1
                    try:
                        pygame.draw.rect(win, BLACK, (0, HEIGHT - SQUARE_SIZE*2, WIDTH, SQUARE_SIZE*2))
                        win.blit(label, (45, HEIGHT - 75 - SQUARE_SIZE))
                        pygame.display.update()
                    except NameError:
                        pass
                    self.draw_board(win)
                    if self.game_over:
                        main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                        main_menu_rect = pygame.draw.rect(win, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
                        win.blit(main_menu_text, (10, HEIGHT - 75))
                        pygame.display.update()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if main_menu_rect.collidepoint(event.pos):
                                break
                        # pygame.time.wait(1500)
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and main_menu_rect.collidepoint(event.pos):
                    run = False


if __name__ == '__main__':
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    g = Game(0)
    g.run(screen)
