import sys
import pygame
import socket
import pickle
# from network import Network

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
HEIGHT = (NUM_ROWS + 2) * SQUARE_SIZE + (SQUARE_SIZE)
RADIUS = (SQUARE_SIZE // 2) - 5
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Client')

font = pygame.font.SysFont("comicsans", 80)
font1 = pygame.font.SysFont("monospace", 45)
FONT2 = pygame.font.SysFont("times new roman", 40)  # used for timer
MEDIUM_FONT = pygame.font.SysFont("times new roman", 60)


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server = "172.105.20.159"
        self.server = 'localhost'
        self.port = 5555
        self.addr = (self.server, self.port)
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            self.client.connect(self.addr)
            return self.client.recv(2048).decode()
        except:
            print('Error connecting. See network.py')

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            # print('used pickle', flush=True)
            # return None
            # return self.client.recv(2048).decode()
            a = pickle.loads(self.client.recv(2048*2))
            return a
        except socket.error as e:
            return str(e)


def draw_board():
    pygame.draw.rect(screen, BLACK,
                     (0, 0, WIDTH, SQUARE_SIZE))  # black rect at top of screen
    pygame.draw.rect(screen, BLACK, (SQUARE_SIZE, HEIGHT - SQUARE_SIZE, WIDTH,
                                     SQUARE_SIZE))  # black rect at bottom of screen
    pygame.draw.rect(screen, BLUE,
                     (0, SQUARE_SIZE, WIDTH, HEIGHT - (SQUARE_SIZE * 2)))
    for c in range(NUM_COLUMNS):
        for r in range(NUM_ROWS + 1):
            # pygame.draw.rect(screen, BLUE, (c * SQUARE_SIZE, r * SQUARE_SIZE + SQUARE_SIZE, SQUARE_SIZE,SQUARE_SIZE))
            pygame.draw.circle(screen, BLACK, (
                c * SQUARE_SIZE + SQUARE_SIZE // 2,
                r * SQUARE_SIZE + SQUARE_SIZE // 2), RADIUS)
    pygame.draw.rect(screen, BLACK,
                     (0, HEIGHT - SQUARE_SIZE*2, WIDTH, SQUARE_SIZE))
    pygame.display.update()


def updateBoard(game, row: int, col: int, player: int) -> None:
    """
    <player> has just placed a piece at (row, col) Update the board.
    :param row: 0-6
    :param col: 0-7
    :param player: 1 or 2
    """
    if not (game.p0_ready and game.p1_ready):
        print('Game not connected')
        font = pygame.font.SysFont("comicsans", 80)
        text = font.render("Waiting for Player...", 1, (255, 0, 0), True)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2,
                           HEIGHT // 2 - text.get_height() // 2))
    else:
        if player == 1:
            pygame.draw.circle(screen, RED, (col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                             (HEIGHT - (row + 2) * SQUARE_SIZE + SQUARE_SIZE // 2) - SQUARE_SIZE), RADIUS)
        else:
            pygame.draw.circle(screen, YELLOW, (
                col * SQUARE_SIZE + SQUARE_SIZE // 2, (HEIGHT - (row + 2) * SQUARE_SIZE + SQUARE_SIZE // 2) - SQUARE_SIZE), RADIUS)
    pygame.display.update()


def main():
    run = True
    clock = pygame.time.Clock()
    n = Network()
    player = int(n.getP())  # 0 or 1
    screen.fill(BLACK)
    # p0 is red and p1 is yellow
    player_to_colour = {0: RED, 1: YELLOW}
    print("You are player", player)
    msg = 'P' + str(player) + 'ready'
    n.client.send(str.encode(msg))
    # peek = n.client.recv(1024, socket.MSG_PEEK).decode('utf-8')
    msg = n.client.recv(1024).decode('utf-8')  # '0_move' or '1_move'
    print('Client received: ', msg)
    text = MEDIUM_FONT.render("Finding opponent...", 1, (255, 0, 0), True)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2,
                       HEIGHT // 2 - text.get_height() // 2))
    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
    screen.blit(main_menu_text, (10, HEIGHT - 75))
    pygame.display.update()

    got_game = False

    while not got_game:
        # try:
        pass
        game = n.send("get")
        print('Game:', game)
        got_game = game.p0_ready and game.p1_ready
        print('who is ready ', game.p0_ready, game.p1_ready)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONDOWN and main_menu_rect.collidepoint(event.pos):
                msg = 'P' + str(player) + 'left'
                n.client.send(str.encode(msg))
                menu_screen()

            # print(game.con)
        # except:
         #   run = False
         #   print("Couldn't get game")
         #   sys.exit()

    if not (game.p0_ready and game.p1_ready):
        print('here')
        text = MEDIUM_FONT.render("Finding opponent...", 1, (255, 0, 0), True)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        main_menu_text = FONT2.render("Main Menu", 1, WHITE)
        main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
        screen.blit(main_menu_text, (10, HEIGHT - 75))
        pygame.display.update()
    else:
        screen.fill(BLACK)
        text = MEDIUM_FONT.render("Found opponent", 1, (255, 0, 0), True)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        pygame.display.update()
        pygame.time.wait(1000)
        screen.fill(BLACK)
        draw_board()
        if player == 0:
            label = font1.render("Your turn", 1, RED)
        else:
            label = font1.render("Opponent's turn", 1, RED)
        screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
        pygame.display.update()

        while run:
            clock.tick(30)

            # print('message: ', msg)
            # print('player: ', player)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if msg in ['0_move', '1_move'] and int(msg[0]) == player:  # this player must move
                    # msg = n.client.recv(1024).decode('utf-8')  # '0_move' or '1_move'
                    # print(msg)
                    # n.client.send('a'.encode('utf-8'))
                    # game.turn = int(msg[0])
                    # print('Turn: ', game.turn)

                        # print('here3')

                    if event.type == pygame.MOUSEMOTION:
                        # print('mouse moved')
                        pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, SQUARE_SIZE))
                        x_pos = event.pos[0]
                        if player == 0:
                            pygame.draw.circle(screen, RED, (x_pos, SQUARE_SIZE // 2), RADIUS)
                        else:
                            pygame.draw.circle(screen, YELLOW, (x_pos, SQUARE_SIZE // 2), RADIUS)
                        pygame.display.update()

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        print(event.pos)
                        x_pos = event.pos[0]
                        column = x_pos // SQUARE_SIZE
                        # check if move is valid TODO
                        if game.is_valid_location(column):
                            label = font1.render("Opponent's turn", 1, player_to_colour[int(not player)])
                            screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                            pygame.display.update()
                            print("Opponent's turn...")
                            pending_move = str(player) + ':' + str(column)  # e.g. '0:3' player 0 places piece in col 3
                            the_row = game.get_next_open_row(column)
                            print('the row', the_row)
                            game.drop_piece(the_row, column, player + 1)
                            updateBoard(game, the_row, column, player + 1)
                            # print(game.board)
                            n.client.send(pending_move.encode('utf-8'))
                            print('Client sent:', pending_move)

                            peek = n.client.recv(1024, socket.MSG_PEEK).decode('utf-8')
                            print('peek:', peek)
                            pygame.event.pump()
                            if '_move' in peek:
                                msg = n.client.recv(1024).decode('utf-8')  # '0_move' or '1_move'
                                game.turn = int(not player)
                                print('Client received1: ', msg)
                            if len(peek) == 7 and 0 <= int(peek[0]) <= 1 and 0 <= int(peek[3]) <= 5 and 0 <= int(peek[5]) <= 6:
                                msg = n.client.recv(1024).decode('utf-8')
                                print('Client received1: ', msg)

                                # player_who_just_moved, row, col = int(msg[0]), int(msg[3]), int(msg[5])
                                # game.drop_piece(row, col, player_who_just_moved + 1)
                                # updateBoard(game, row, col, player_who_just_moved + 1)
                                # game.print_board(game.board)
                                # break

                else:
                    game.turn = int(not player)
                    label = font1.render("Your turn", 1, player_to_colour[player])
                    msg = n.client.recv(1024).decode('utf-8')  # 1:(0,1)
                    print('Client received2: ', msg)

                if len(msg) == 7 and 0 <= int(msg[0]) <= 1 and 0 <= int(msg[3]) <= 5 and 0 <= int(msg[5]) <= 6:  # received player:(row,col)
                    player_who_just_moved, row, col = int(msg[0]), int(msg[3]), int(msg[5])
                    game.drop_piece(row, col, player_who_just_moved + 1)
                    updateBoard(game, row, col, player_who_just_moved + 1)
                    game.print_board(game.board)
                    game.turn = int(not player_who_just_moved)  # can remove game.turn stuff
                    peek = n.client.recv(1024, socket.MSG_PEEK).decode('utf-8')
                    if peek[1:] == '_move':
                        msg = n.client.recv(1024).decode('utf-8')  # '0_move' or '1_move'
                        print('Client received3: ', msg)
                if len(msg) == 6 and 'WON' in msg:
                    game_winner = int(msg[1])  # 0 or 1
                    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT-SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
                    screen.blit(main_menu_text, (10, HEIGHT - 75))
                    if game_winner == player:
                        label = font1.render("You Won! Click to play again.", 1, player_to_colour[player])
                    else:
                        label = font1.render("You lost. Click to play again.", 1, player_to_colour[player])

                    pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE*2, WIDTH, SQUARE_SIZE))
                    screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                    pygame.display.update()
                    run2 = True
                    while run2:
                        # pygame.time.wait(3000)
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            if event.type == pygame.MOUSEBUTTONDOWN and main_menu_rect.collidepoint(event.pos):
                                run2 = False
                                menu_screen()
                    # run = False

                # updateBoard(game, 0, 3, 0)
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE*2, WIDTH, SQUARE_SIZE))
                screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                pygame.display.update()

                """
                if game.bothWent():
                    # redrawWindow(win, game, player)
                    pygame.time.delay(500)
                    try:
                        game = n.send("reset")
                    except:
                        run = False
                        print("Couldn't get game")
                        break
        
                    pygame.display.update()
                    pygame.time.delay(2000)
                """

    #  for event in pygame.event.get():
    #      if event.type == pygame.QUIT:
    #          run = False
    #          pygame.quit()

    #     if event.type == pygame.MOUSEBUTTONDOWN:
    #         pos = pygame.mouse.get_pos()
    # for btn in btns:
    #  if btn.click(pos) and game.connected():
    #      if player == 0:
    #          if not game.p1Went:
    #              n.send(btn.text)
    #      else:
    #          if not game.p2Went:
    #              n.send(btn.text)

    # redrawWindow(win, game, player)


def menu_screen():
    run = True
    clock = pygame.time.Clock()

    while run:
        clock.tick(60)
        screen.fill((128, 128, 128))
        font = pygame.font.SysFont("comicsans", 60)
        text = font.render("Click to Play!", 1, (255, 0, 0))
        screen.blit(text, (100, 200))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
                # break
            if event.type == pygame.MOUSEBUTTONDOWN:
                # draw_board()
                run = False
                break
    main()


while True:
    menu_screen()
