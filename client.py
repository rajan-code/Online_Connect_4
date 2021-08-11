import sys
import pygame
import socket
from connect_4_game import Game
import pygame_input
import pickle
# from network import Network

pygame.init()

NUM_ROWS = 6
NUM_COLUMNS = 7

RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
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
TITLE_FONT = pygame.font.SysFont("times new roman", 70, True)
SMALL_FONT = pygame.font.SysFont("arial", 30)


class Network:
    def __init__(self, game_type=''):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "172.105.20.159"
        # self.server = 'localhost'
        self.port = 5555
        self.addr = (self.server, self.port)
        self.game_type = game_type  # "public" or "private"
        print('here')
        self.client.connect(self.addr)
        if game_type == 'public':
            print('Client sent:', game_type)
            self.client.send(str.encode(game_type))
            self.p = self.connect()

       # print('network.p value:', self.p)

    def getP(self):
        return self.p

    def connect(self):
        #try:
        # self.client.connect(self.addr)
       # if self.game_type != '':
       #     self.client.send(str.encode(self.game_type))
        return self.client.recv(2048).decode()
       # except:
          #  print('Error connecting. See network.py')

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            # print('used pickle', flush=True)
            # return None
            # return self.client.recv(2048).decode()
            a = pickle.loads(self.client.recv(2048*8))
            return a
        except socket.error as e:
            return str(e)

    def send_and_receive(self, data):
        try:
            self.client.send(str.encode(data))
            a = self.client.recv(1024).decode('utf-8')
            return a
        except socket.error as e:
            return str(e)


class PrivateGameNetwork(Network):
    def __init__(self, p: int, game_type=''):
        super().__init__(game_type)
        print('here')
        # print('Client sent:', game_type)
        # self.client.send(str.encode(game_type))
        self.p = p


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


def main(game_type='', game_code='', the_network=None):
    run = True
    clock = pygame.time.Clock()
    if not the_network:
        n = Network(game_type)
    else:
        n = the_network
    # n.client.send(str.encode('public'))

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
    if game_type == 'public':
        text = SMALL_FONT.render("Finding opponent...", 1, (255, 0, 0), True)
    else:  # game_type == 'private'
        text = SMALL_FONT.render("Waiting for opponent... game code: " + str(game_code), 1, (255, 0, 0), True)
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

    # both players have joined the game
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
                        # pygame.event.pump()  # does not work
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
                    label = font1.render("You Won!", 1, player_to_colour[player])
                else:
                    label = font1.render("You lost.", 1, player_to_colour[player])

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


def setup_private_game():
    screen.fill(BLACK)
    title_text = TITLE_FONT.render("Private Game", 1, (255, 255, 0))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 75))
    or_text = SMALL_FONT.render("or", 1, WHITE)
    screen.blit(or_text, (WIDTH // 2 - or_text.get_width() // 2, 375))
    host_game_text = SMALL_FONT.render("Host Game", 1, BLUE)
    host_game_rect = pygame.draw.rect(screen, BLUE, (210, 278, 139, 32), 1)
    screen.blit(host_game_text, (WIDTH // 2 - host_game_text.get_width() // 2, 275))
    # join_game_text = SMALL_FONT.render("Join Game", 1, BLUE)
    # screen.blit(join_game_text, (WIDTH // 2 - join_game_text.get_width() // 2, 375))
    code_text = SMALL_FONT.render("Enter code: ", 1, BLUE)
    code_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - code_text.get_width() // 2 - 70 + code_text.get_width(), 440, 60, 27))
    screen.blit(code_text, (WIDTH // 2 - code_text.get_width() // 2 - 70, 430))
    text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20)
    text_input.max_string_length = 4
    join_game_text2 = SMALL_FONT.render("Join Game", 1, BLUE)
    text_input.set_cursor_color(WHITE)
    screen.blit(join_game_text2, (WIDTH // 2 - join_game_text2.get_width() // 2, 475))
    join_game_rect2 = pygame.draw.rect(screen, BLUE, (210, 478, 139, 32), 1)
    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
    screen.blit(main_menu_text, (10, HEIGHT - 75))
    clicked_text_box = False

    pygame.display.update()
    run = True
    while run:
        mouse_pos = pygame.mouse.get_pos()
        if host_game_rect.collidepoint(mouse_pos):
            host_game_text = SMALL_FONT.render("Host Game", 1, GREEN)
            host_game_rect = pygame.draw.rect(screen, GREEN, (210, 278, 139, 32), 1)
        else:
            host_game_text = SMALL_FONT.render("Host Game", 1, BLUE)
            host_game_rect = pygame.draw.rect(screen, BLUE, (210, 278, 139, 32), 1)
        if join_game_rect2.collidepoint(mouse_pos):
            join_game_text2 = SMALL_FONT.render("Join Game", 1, GREEN)
            join_game_rect2 = pygame.draw.rect(screen, GREEN, (210, 478, 139, 32), 1)
        else:
            join_game_text2 = SMALL_FONT.render("Join Game", 1, BLUE)
            join_game_rect2 = pygame.draw.rect(screen, BLUE, (210, 478, 139, 32), 1)

        if code_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
            clicked_text_box = True
        elif pygame.mouse.get_pressed()[0] == 1:  # clicked on screen but outside text box
            clicked_text_box = False
        curr_events = pygame.event.get()
        if clicked_text_box:
            x = text_input.update(curr_events)
            print(text_input.get_text())  # prints name
        # pygame.draw.rect(screen, BLACK, (WIDTH // 2 - code_text.get_width() // 2 - 70 + code_text.get_width(), 440, 60, 27), 1)
        code_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - code_text.get_width() // 2 - 70 + code_text.get_width(), 440, 60, 27))
        screen.blit(text_input.get_surface(), (WIDTH // 2 - code_text.get_width() // 2 - 65 + code_text.get_width(), 440))
        pygame.display.update()
        for event in curr_events:
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
                # break
            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_menu_rect.collidepoint(event.pos):
                    menu_screen()
                if join_game_rect2.collidepoint(event.pos):
                    n = PrivateGameNetwork(1, 'private')
                    print('Client sent: ', 'P2_joined_' + text_input.get_text())
                    msg = n.send_and_receive('P2_joined_' + text_input.get_text())
                    print('Client received: ', msg)
                    if msg == 'joined_game_successfully':
                        main('private', '', n)  # here
                    elif msg == 'joined_game_failed':
                        pass

                if host_game_rect.collidepoint(event.pos):
                    n = PrivateGameNetwork(0, 'private')
                    print('Client sent:', 'private')
                    game_code = n.send_and_receive('private')
                    game_code = game_code[13:]
                    print('Client received: game code', game_code)
                    run = False
                    main('private', game_code, n)  # here
                print(event.pos)
        screen.blit(join_game_text2, (WIDTH // 2 - join_game_text2.get_width() // 2, 475))
        screen.blit(host_game_text, (WIDTH // 2 - host_game_text.get_width() // 2, 275))
        pygame.display.update()


def menu_screen():
    print(WIDTH, 'x', HEIGHT)
    run = True
    clock = pygame.time.Clock()
    screen.fill(BLACK)
    title_text = TITLE_FONT.render("Connect 4", 1, (255, 255, 0))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 75))
    pygame.display.update()
    pointer = 185  # starting vertical line

    # pygame.draw.line(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 1)
    register_text = SMALL_FONT.render("Register", 1, WHITE)
    screen.blit(register_text, (WIDTH // 2 - register_text.get_width() - 35, pointer))
    print(register_text.get_width())
    register_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - register_text.get_width() - 40, pointer - 5, register_text.get_width() + 10, register_text.get_height() + 5), 1)
    login_text = SMALL_FONT.render("Login", 1, WHITE)
    login_rect = pygame.draw.rect(screen, WHITE, (WIDTH//2+30, pointer - 5, login_text.get_width() + 10, login_text.get_height() + 5), 1)
    screen.blit(login_text, (WIDTH // 2 + 35, pointer))

    pointer += 70

    online_text = FONT2.render("Online", 1, BLUE)
    screen.blit(online_text, (WIDTH // 2 - online_text.get_width() // 2, pointer))

    public_text = SMALL_FONT.render("Public", 1, WHITE)
    public_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - public_text.get_width() - 40, pointer+50 - 5, public_text.get_width() + 10, public_text.get_height() + 5), 1)
    screen.blit(public_text, (WIDTH // 2 - public_text.get_width() - 35, pointer + online_text.get_height()))
    private_text = SMALL_FONT.render("Private", 1, WHITE)
    private_rect = pygame.draw.rect(screen, WHITE, (WIDTH//2+30, pointer+50 - 5, private_text.get_width() + 10, private_text.get_height() + 5), 1)
    screen.blit(private_text, (WIDTH // 2 + 35, pointer + online_text.get_height()))

    pointer += 120
    online_text = FONT2.render("Offline", 1, BLUE)
    screen.blit(online_text, (WIDTH // 2 - online_text.get_width() // 2, pointer))
    vs_cpu_text = SMALL_FONT.render("Single Player", 1, WHITE)
    vs_cpu_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - vs_cpu_text.get_width()// 2, pointer + 55 - 5, vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)
    screen.blit(vs_cpu_text, (WIDTH // 2 - vs_cpu_text.get_width()//2 + 5, pointer + vs_cpu_text.get_height() + 13))
    two_player_text = SMALL_FONT.render("Two Players", 1, WHITE)
    two_player_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - vs_cpu_text.get_width()// 2, pointer + 60 + vs_cpu_text.get_height(), vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)
    screen.blit(two_player_text, (WIDTH // 2 - two_player_text.get_width()//2 + 5, pointer + two_player_text.get_height() + 25 + vs_cpu_text.get_height()))
    pygame.display.update()
    pointer=185+70

    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
                # break
            if event.type == pygame.MOUSEBUTTONDOWN:
                if public_rect.collidepoint(event.pos):  # public game
                    print('public game')
                    # run = False
                    main('public', '')
                elif private_rect.collidepoint(event.pos):  # public game
                    setup_private_game()
                    # main('private')  # change
                elif two_player_rect.collidepoint(event.pos):  # human vs human (offline)
                    # n = Network('public')
                    # g = n.send("get")
                    g = Game(0)
                    g.run(screen)
                    menu_screen()
                # draw_board()
                print(event.pos)
            mouse_pos = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEMOTION:
                if public_rect.collidepoint(mouse_pos):  # public game
                    public_text = SMALL_FONT.render("Public", 1, GREEN)
                    public_rect = pygame.draw.rect(screen, (0, 255, 0), (WIDTH // 2 - public_text.get_width() - 40, pointer+50 - 5, public_text.get_width() + 10, public_text.get_height() + 5), 1)
                else:
                    public_text = SMALL_FONT.render("Public", 1, WHITE)
                    public_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - public_text.get_width() - 40, pointer + 50 - 5, public_text.get_width() + 10, public_text.get_height() + 5), 1)
                if private_rect.collidepoint(mouse_pos):
                    private_text = SMALL_FONT.render("Private", 1, GREEN)
                    private_rect = pygame.draw.rect(screen, GREEN, (WIDTH // 2 + 30, pointer + 50 - 5, private_text.get_width() + 10, private_text.get_height() + 5), 1)
                else:
                    private_text = SMALL_FONT.render("Private", 1, WHITE)
                    private_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 + 30, pointer + 50 - 5, private_text.get_width() + 10, private_text.get_height() + 5), 1)
                if two_player_rect.collidepoint(mouse_pos):
                    two_player_text = SMALL_FONT.render("Two Players", 1, GREEN)
                    two_player_rect = pygame.draw.rect(screen, GREEN, (WIDTH // 2 - vs_cpu_text.get_width() // 2, 375 + 60 + vs_cpu_text.get_height(),vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)
                else:
                    two_player_text = SMALL_FONT.render("Two Players", 1, WHITE)
                    two_player_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - vs_cpu_text.get_width() // 2, 375 + 60 + vs_cpu_text.get_height(), vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)
                if vs_cpu_rect.collidepoint(mouse_pos):
                    vs_cpu_text = SMALL_FONT.render("Single Player", 1, GREEN)
                    vs_cpu_rect = pygame.draw.rect(screen, GREEN, (WIDTH // 2 - vs_cpu_text.get_width() // 2, 375 + 55 - 5, vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)
                else:
                    vs_cpu_text = SMALL_FONT.render("Single Player", 1, WHITE)
                    vs_cpu_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - vs_cpu_text.get_width() // 2, 375 + 55 - 5, vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)

        screen.blit(public_text, (WIDTH // 2 - public_text.get_width() - 35, pointer + online_text.get_height()))
        screen.blit(private_text, (WIDTH // 2 + 35, pointer + online_text.get_height()))
        screen.blit(two_player_text, (WIDTH // 2 - two_player_text.get_width() // 2 + 5, 375 + two_player_text.get_height() + 25 + vs_cpu_text.get_height()))
        screen.blit(vs_cpu_text, (WIDTH // 2 - vs_cpu_text.get_width() // 2 + 5, 375 + vs_cpu_text.get_height() + 13))
        pygame.display.update()
   # main()


while True:
    menu_screen()
