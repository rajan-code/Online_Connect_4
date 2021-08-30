import random
import hashlib
import re
import sys
import pygame
import socket
from connect_4_game import Game
import pygame_input
import pickle
import threading
import time
from typing import *

# from network import Network

pygame.init()
pygame.mixer.init()
pygame.mixer.music.set_volume(0.5)  # Sets the volume of the music (0-1.0)
WON_GAME_SOUND = pygame.mixer.Sound('music/won_game.wav')
CLICK_SOUND = pygame.mixer.Sound('music/click_sound.wav')
BACKGROUND_IMG = pygame.image.load('pics/menu_background.jfif')
REFRESH_BUTTON = pygame.image.load('pics/refresh_button.png')

NUM_ROWS = 6
NUM_COLUMNS = 7

RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)

SQUARE_SIZE = 80
WIDTH = NUM_COLUMNS * SQUARE_SIZE
HEIGHT = (NUM_ROWS + 2) * SQUARE_SIZE + SQUARE_SIZE
RADIUS = (SQUARE_SIZE // 2) - 5
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Client')

font = pygame.font.SysFont("comicsans", 80)
font1 = pygame.font.SysFont("monospace", 45)
FONT2 = pygame.font.SysFont("times new roman", 40)  # used for timer
MEDIUM_FONT = pygame.font.SysFont("times new roman", 60)
TITLE_FONT = pygame.font.SysFont("times new roman", 70, True)
SMALL_FONT = pygame.font.SysFont("arial", 30)
VERY_SMALL_FONT = pygame.font.SysFont("arial", 24, True)
VERY_SMALL_FONT2 = pygame.font.SysFont("arial", 20)

curr_screen_is_menu_screen = True
print_lock = threading.Lock()
player_username = ''   # use this in menu_screen()
player_friend_code = ''
music_on = True


class Network:
    def __init__(self, username='Guest', game_type=''):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = 5555
        self.game_type = game_type  # "public" or "private"
        try:
            self.server = "172.105.20.159"
            self.addr = (self.server, self.port)
            self.client.connect(self.addr)
        except ConnectionRefusedError:
            self.server = 'localhost'
            self.addr = (self.server, self.port)
            self.client.connect(self.addr)
        if game_type == 'public':
            print('Client sent:', game_type)
            self.client.send(str.encode(username + ':' + game_type))
            self.p = self.client.recv(2048).decode()

    # print('network.p value:', self.p)

    def getP(self):
        return self.p

    def connect(self):
        # try:
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
            a = pickle.loads(self.client.recv(2048 * 8))
            return a
        except socket.error as e:
            return str(e)

    def send_and_receive(self, data):
        try:
            self.client.send(str.encode(data))
            a = self.client.recv(1024).decode('utf-8')
            return a
        except socket.error as e:
            print('socket error')
            return str(e)


general_msgs_network = Network('')


class PrivateGameNetwork(Network):
    def __init__(self, p: int, game_type=''):
        super().__init__(game_type)
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
            pygame.draw.circle(screen, BLACK, (c * SQUARE_SIZE + SQUARE_SIZE // 2, r * SQUARE_SIZE + SQUARE_SIZE // 2), RADIUS)
    pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
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


class GetOpponentsMoveThread(threading.Thread):
    def __init__(self, network):
        threading.Thread.__init__(self)
        self.network = network

    def run(self):
        get_opponents_move(self.network)


def is_valid_email(email: str) -> bool:
    """
    Return True iff <email> is a valid email address.
    >>> a = 'a@gmail.com'
    >>> is_valid_email(a)
    True
    """
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w+$'
    return bool(re.search(regex, email))


def notify_server_and_leave():
    global player_username
    if player_username != '':
        general_msgs_network.client.send(str.encode('GENERAL_NOW_OFFLINE:' + player_username))
    else:
        general_msgs_network.client.send(str.encode('GENERAL_someone_leaving'))
    print('Client sent: ', 'GENERAL_someone_leaving')
    pygame.quit()
    sys.exit(0)


def add_friend(line: str) -> None:
    """
    Make these two users friends in the database by sending info to the server.
    :param line: <username_friendsUsername>
    """
    username, friend = line.split('_')
    new_line = 'GENERAL_ADD_FRIEND:' + username + ',' + friend
    general_msgs_network.client.send(str.encode(new_line))


def register_user(line: str) -> None:
    """
    Register the user by sending their information to the server.
    :param line:<username_email_password>
    """
    print('registering user')
    username, email, password = line.split('_')
    encoded_pswd = hashlib.sha256(password.encode('utf-8')).hexdigest()
    new_line = 'GENERAL_NEW_USER:' + username + ',' + email + ',' + encoded_pswd
    general_msgs_network.client.send(str.encode(new_line))


def middle_of_screen(txt: pygame.Surface) -> int:
    return WIDTH // 2 - txt.get_width() // 2


def friends_screen():
    """
    Precondition: player_username != ''
    """
    global player_username
    screen.fill(BLACK)
    curr_time = time.time()
    friends_and_status = general_msgs_network.send('GENERAL_GET_FRIENDS_AND_STATUS:' + player_username)
    screen.blit(REFRESH_BUTTON, (WIDTH - REFRESH_BUTTON.get_width(), 0))
    refresh_rect = pygame.Rect((WIDTH - REFRESH_BUTTON.get_width(), 0, REFRESH_BUTTON.get_width(), REFRESH_BUTTON.get_height()))
    print(friends_and_status)
    online_friends, offline_friends = [], []
    for friend, status in friends_and_status:
        if status:
            online_friends.append(friend)
        else:
            offline_friends.append(friend)

    num_friends = len(online_friends) + len(offline_friends)
    # TODO add refresh button

    title_text = MEDIUM_FONT.render("Friends", 1, CYAN)
    screen.blit(title_text, (middle_of_screen(title_text), 5))
    num_friends_text = SMALL_FONT.render(str(num_friends) + " Friends", 1, WHITE)
    screen.blit(num_friends_text, (middle_of_screen(num_friends_text), 65))
    online_text = SMALL_FONT.render(str(len(online_friends)) + " Online", 1, GREEN)
    offline_text = SMALL_FONT.render(str(len(offline_friends)) + " Offline", 1, RED)

    screen.blit(online_text, (WIDTH//2 - online_text.get_width() - 100, 100))
    screen.blit(offline_text, (WIDTH//2 + offline_text.get_width() + 10, 100))

    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE+25, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
    screen.blit(main_menu_text, (10, HEIGHT - 50))

   # refresh_text = FONT2.render("Refresh")

    online_horizontal, offline_horizontal = 140, 140
    for friend in online_friends:
        text = SMALL_FONT.render(friend, 1, WHITE)
        screen.blit(text, (WIDTH//2 - online_text.get_width() - 130, online_horizontal))
        pygame.draw.circle(screen, GREEN, (43, online_horizontal + 20), 8)
        # pygame.draw.circle()
        online_horizontal += 50
    for friend in offline_friends:
        text = SMALL_FONT.render(friend, 1, WHITE)
        screen.blit(text, (WIDTH - online_text.get_width() - 130, offline_horizontal))
        pygame.draw.circle(screen, RED, (322, offline_horizontal + 20), 8)
        # pygame.draw.circle()
        offline_horizontal += 50

    pygame.display.update()
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                notify_server_and_leave()
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(event.pos)
                if main_menu_rect.collidepoint(event.pos):
                    run = False
                    menu_screen()
                elif refresh_rect.collidepoint(event.pos) and curr_time + 5 < time.time():  # if it's been at least 5 seconds since last refresh
                    friends_screen()


# friends_screen()

def leaderboard_screen(only_friends=False):
    global player_username
    # public
    screen.fill(BLACK)
    if not only_friends:  # display public leaderboard
        public_text = SMALL_FONT.render("Public", 1, GREEN)
        friends_text = SMALL_FONT.render("Friends", 1, WHITE)
    else:  # display friends leaderboard
        public_text = SMALL_FONT.render("Public", 1, WHITE)
        friends_text = SMALL_FONT.render("Friends", 1, GREEN)

    screen.blit(public_text, (WIDTH//2 - public_text.get_width() - 100, 40))
    screen.blit(friends_text, (WIDTH//2 + friends_text.get_width(), 40))

    public_rect = pygame.Rect((110, 44), (public_text.get_width(), public_text.get_height()))
    friends_rect = pygame.Rect((360, 44), (friends_text.get_width(), friends_text.get_height()))
    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
    screen.blit(main_menu_text, (10, HEIGHT - 75))
    pygame.draw.line(screen, WHITE, (75, int(SQUARE_SIZE)), (75, HEIGHT-SQUARE_SIZE-10), 1)  # ranking
    pygame.draw.line(screen, WHITE, (225, int(SQUARE_SIZE)), (225, HEIGHT-SQUARE_SIZE-10), 1)  # username
    pygame.draw.line(screen, WHITE, (275, int(SQUARE_SIZE)), (275, HEIGHT-SQUARE_SIZE-10), 1)  # gp
    pygame.draw.line(screen, WHITE, (325, int(SQUARE_SIZE)), (325, HEIGHT-SQUARE_SIZE-10), 1)  # w
    pygame.draw.line(screen, WHITE, (375, int(SQUARE_SIZE)), (375, HEIGHT-SQUARE_SIZE-10), 1)  # d
    pygame.draw.line(screen, WHITE, (425, int(SQUARE_SIZE)), (425, HEIGHT-SQUARE_SIZE-10), 1)  # l
    pygame.draw.line(screen, WHITE, (475, int(SQUARE_SIZE)), (475, HEIGHT-SQUARE_SIZE-10), 1)  # pts
    pygame.draw.line(screen, WHITE, (0, 133), (WIDTH, 133), 1)   # horizontal line
    text1 = MEDIUM_FONT.render("#", 1, BLUE)
    screen.blit(text1, (23, 70))
    text2 = SMALL_FONT.render("Username", 1, BLUE)
    screen.blit(text2, (90, 80))
    text2 = SMALL_FONT.render("GP", 1, BLUE)
    screen.blit(text2, (235, 82))
    text2 = SMALL_FONT.render("W", 1, BLUE)
    screen.blit(text2, (290, 82))
    text2 = SMALL_FONT.render("D", 1, BLUE)
    screen.blit(text2, (340, 82))
    text2 = SMALL_FONT.render("L", 1, BLUE)
    screen.blit(text2, (392, 82))
    text2 = VERY_SMALL_FONT.render("PTS", 1, BLUE)
    screen.blit(text2, (430, 87))
    text2 = SMALL_FONT.render("P%", 1, BLUE)
    screen.blit(text2, (490, 82))

    pygame.display.update()
    if not only_friends:
        top_ten = general_msgs_network.send('GENERAL_GET_TOP_TEN_PUBLIC')  # use pickle
    else:
        top_ten = general_msgs_network.send('GENERAL_GET_TOP_TEN_FRIENDS:' + player_username)  # use pickle

    horizontal_line = 135
    this_player_is_user = False
    ranking = 1
    if not only_friends:
        for i in range(len(top_ten)):  # assign ranking (1, 2, 3...) to each player
            top_ten[i] = list(top_ten[i])
            top_ten[i].insert(0, ranking)
            ranking += 1

    for player in top_ten:
        print(player)
        # print this username in yellow
        ranking, name, gp, wins, draws, losses, points, points_percentage = player
        ranking_txt = SMALL_FONT.render(str(ranking), 1, WHITE)
        screen.blit(ranking_txt, (75//2 - ranking_txt.get_width()//2, horizontal_line))
        if name == player_username:
            name_txt = VERY_SMALL_FONT2.render(name, 1, YELLOW)
            this_player_is_user = True
        else:
            name_txt = VERY_SMALL_FONT2.render(name, 1, WHITE)

        screen.blit(name_txt, (80, horizontal_line+5))
        vertical_line = 250
        for stat in [gp, wins, draws, losses, points]:
            if this_player_is_user:
                stat_text = SMALL_FONT.render(str(stat), 1, YELLOW)
            else:
                stat_text = SMALL_FONT.render(str(stat), 1, WHITE)
            screen.blit(stat_text, (vertical_line-stat_text.get_width()//2, horizontal_line))
            vertical_line += 50

        if this_player_is_user:
            points_percentage_txt = SMALL_FONT.render(str(points_percentage), 1, YELLOW)
        else:
            points_percentage_txt = SMALL_FONT.render(str(points_percentage), 1, WHITE)
        screen.blit(points_percentage_txt, (480, horizontal_line))
        horizontal_line += 45
        if this_player_is_user:
            this_player_is_user = False

    pygame.display.update()
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(event.pos)
                if main_menu_rect.collidepoint(event.pos):
                    run = False
                    menu_screen()
                if only_friends and public_rect.collidepoint(event.pos):
                    leaderboard_screen(only_friends=False)
                if not only_friends and friends_rect.collidepoint(event.pos):
                    leaderboard_screen(only_friends=True)
            if event.type == pygame.QUIT:
                notify_server_and_leave()


def register_screen():
    global player_username
    screen.fill(BLACK)
    twenty_chars = SMALL_FONT.render("M"*20, 1, WHITE)
    title_text = TITLE_FONT.render("Register", 1, (255, 255, 0))
    screen.blit(title_text, (middle_of_screen(title_text), 25))
    username_text = SMALL_FONT.render("Username:", 1, WHITE)
    # len(username) <= 15
    screen.blit(username_text, (middle_of_screen(username_text), 125))
    screen.blit(username_text, (middle_of_screen(username_text), 125))
    username_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 160, 10 + twenty_chars.get_width(), 27))

    username_text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20)
    username_text_input.max_string_length = 15
    username_text_input.set_cursor_color(WHITE)

    email_text = SMALL_FONT.render("Email:", 1, WHITE)
    screen.blit(email_text, (middle_of_screen(email_text), 200))
    email_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 235, 10 + twenty_chars.get_width(), 27))

    email_text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20)
    email_text_input.max_string_length = 47
    email_text_input.set_cursor_color(WHITE)

    password_text = SMALL_FONT.render("Password:", 1, WHITE)
    screen.blit(password_text, (middle_of_screen(password_text), 275))
    password_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 310, 10 + twenty_chars.get_width(), 27))
    password_text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20, password=True)
    password_text_input.max_string_length = 30
    # len(password) <= 30
    password_text_input.set_cursor_color(WHITE)

    clicked_username_box, clicked_email_box, clicked_password_box, clicked_code_box = False, False, False, False
    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
    screen.blit(main_menu_text, (10, HEIGHT - 75))

    register_text = SMALL_FONT.render("Register", 1, WHITE)
    screen.blit(register_text, (middle_of_screen(register_text), 415))
    register_rect = pygame.draw.rect(screen, WHITE, (230, 415, register_text.get_width() + 10, register_text.get_height() + 5), 1)
    pygame.display.update()
    run = True
    emailed_code = False
    errors = ""
    while run:
        mouse_pos = pygame.mouse.get_pos()
        if not emailed_code:
            if username_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
                clicked_username_box = True
                clicked_email_box = False
                clicked_password_box = False
            elif email_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
                clicked_username_box = False
                clicked_email_box = True
                clicked_password_box = False
            elif password_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
                clicked_username_box = False
                clicked_email_box = False
                clicked_password_box = True
            elif pygame.mouse.get_pressed()[0] == 1:
                clicked_username_box = False
                clicked_email_box = False
                clicked_password_box = False

        curr_events = pygame.event.get()
        if not emailed_code:
            if clicked_username_box:
                username_text_input.update(curr_events)
            elif clicked_email_box:
                email_text_input.update(curr_events)
            elif clicked_password_box:
                password_text_input.update(curr_events)

        pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 160, 10 + twenty_chars.get_width(), 27))  # username rect
        screen.blit(username_text_input.get_surface(), (WIDTH // 2 - (10 + twenty_chars.get_width() // 2) + 5, 160))
        pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 235, 10 + twenty_chars.get_width(), 27))  # email rect
        screen.blit(email_text_input.get_surface(), (WIDTH // 2 - (10 + twenty_chars.get_width() // 2) + 5, 235))
        pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 310, 10 + twenty_chars.get_width(), 27))  # password rect
        screen.blit(password_text_input.get_surface(), (WIDTH // 2 - (10 + twenty_chars.get_width() // 2) + 5, 310))
        pygame.display.update()
        for event in curr_events:
            if event.type == pygame.QUIT:
                run = False
                notify_server_and_leave()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_menu_rect.collidepoint(event.pos):
                    run = False
                    menu_screen()
                if register_rect.collidepoint(event.pos) and not emailed_code:
                    username = username_text_input.get_text()
                    email = email_text_input.get_text()
                    password = password_text_input.get_text()
                    if len(username) == 0:
                        errors += 'Username cannot be empty. '
                    elif not username.isalnum():
                        errors += 'Username can only contain numbers and letters. '
                    elif username == 'Guest':
                        errors += 'Username is invalid. '
                    if len(password) < 4:
                        errors += 'Password must be at least 4 characters long. '
                    if not is_valid_email(email):
                        errors += 'Email is invalid. '
                    if errors != '':
                        error_txt = VERY_SMALL_FONT.render(errors, 1, RED)
                        pygame.draw.rect(screen, BLACK, (0, 350, WIDTH, 60))
                        # screen.blit(error_txt, (middle_of_screen(error_txt), 395))
                        blit_text(screen, errors, (5, 350), VERY_SMALL_FONT, RED)
                        errors = ''
                        pygame.display.update()
                    else:  # check if username and email are being used by someone else
                        errors = ''
                        usernames = general_msgs_network.send('GENERAL_get_all_usernames')  # use pickle
                        print(type(usernames))
                        print(usernames)
                        emails = general_msgs_network.send('GENERAL_get_all_emails')
                        if username in usernames:
                            errors += 'This username is not available. '
                        if email_text_input.get_text() in emails:
                            errors += 'This email is associated with an existing account. '
                        pygame.draw.rect(screen, BLACK, (0, 350, WIDTH, 60))
                        blit_text(screen, errors, (5, 350), VERY_SMALL_FONT, RED)
                        pygame.display.update()
                        if errors == '':  # all info is good, confirm email
                            print('here')
                            emailed_code = True
                            email_txt2 = VERY_SMALL_FONT.render("A code has been sent to: " + email, 1, WHITE)
                            code_text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20)
                            code_text_input.max_string_length = 6
                            code_text_input.set_cursor_color(WHITE)
                            code_text = SMALL_FONT.render("Enter code: ", 1, BLUE)
                            screen.blit(code_text, (middle_of_screen(email_txt2) + email_txt2.get_width()//2 - code_text.get_width() - 10, 495))
                            code_rect = pygame.draw.rect(screen, BLUE, (middle_of_screen(email_txt2) + email_txt2.get_width()//2, 505, twenty_chars.get_width()//4, 27))
                            screen.blit(email_txt2, (middle_of_screen(email_txt2), 465))
                            pygame.draw.rect(screen, BLACK, (230, 415, register_text.get_width() + 10, register_text.get_height() + 5))
                            register_text = SMALL_FONT.render("Register", 1, WHITE)
                            screen.blit(register_text, (middle_of_screen(register_text), 615))
                            register_rect = pygame.draw.rect(screen, WHITE, (230, 615, register_text.get_width() + 10, register_text.get_height() + 5), 1)
                            pygame.display.update()
                            the_code = general_msgs_network.send_and_receive('GENERAL_SEND_CODE_TO_' + email)
                            # print(the_code)
                            while True:
                                mouse_pos = pygame.mouse.get_pos()
                                if code_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
                                    clicked_code_box = True
                                elif pygame.mouse.get_pressed()[0] == 1:
                                    clicked_code_box = False
                                curr_events = pygame.event.get()
                                if clicked_code_box:
                                    code_text_input.update(curr_events)
                                pygame.draw.rect(screen, BLUE, (middle_of_screen(email_txt2) + email_txt2.get_width()//2, 505, twenty_chars.get_width()//4, 27))
                                screen.blit(code_text_input.get_surface(), (middle_of_screen(email_txt2) + email_txt2.get_width()//2 + 5, 505))
                                pygame.display.update()
                                for event in curr_events:
                                    if event.type == pygame.QUIT:
                                        notify_server_and_leave()

                                    if event.type == pygame.MOUSEBUTTONDOWN:
                                        if main_menu_rect.collidepoint(event.pos):
                                            run = False
                                            menu_screen()
                                        if register_rect.collidepoint(event.pos) and the_code == code_text_input.get_text():
                                            general_msgs_network.client.send(str.encode('GENERAL_NOW_ONLINE:' + username))
                                            line = username + '_' + email + '_' + password
                                            register_user(line)
                                            pygame.draw.rect(screen, BLACK, (0, 539, WIDTH, 69))
                                            player_username = username
                                            text1 = SMALL_FONT.render("Registration successful!", 1, GREEN)
                                            screen.blit(text1, (middle_of_screen(text1), 555))
                                            pygame.display.update()
                                            pygame.time.delay(500)
                                            menu_screen()
                                        elif register_rect.collidepoint(event.pos):  # they enter incorrect code
                                            pygame.draw.rect(screen, BLACK, (0, 539, WIDTH, 69))
                                            incorrect_code_text = SMALL_FONT.render("Incorrect code.", 1, RED)
                                            screen.blit(incorrect_code_text, (middle_of_screen(incorrect_code_text), 555))
                                            pygame.display.update()

                                # if they enter correct code:

                                # register_user(line)
                                # general_msgs_network.client.send(str.encode('GENERAL_NEW_USER_'))


def blit_text(surface, text, pos, font, color=pygame.Color('black')):
    words = [word.split(' ') for word in text.splitlines()]  # 2D array where each row is a list of words.
    space = font.size(' ')[0]  # The width of a space.
    max_width, max_height = surface.get_size()
    word_height = 0
    x, y = pos
    for line in words:
        for word in line:
            word_surface = font.render(word, 0, color)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width:
                x = pos[0]  # Reset the x.
                y += word_height  # Start on new row.
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]  # Reset the x.
        y += word_height  # Start on new row.


def login_screen():
    global player_username
    screen.fill(BLACK)
    twenty_chars = SMALL_FONT.render("M"*20, 1, WHITE)
    title_text = TITLE_FONT.render("Login", 1, (255, 255, 0))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    username_text = SMALL_FONT.render("Username/email:", 1, WHITE)
    screen.blit(username_text, (middle_of_screen(username_text), 175))

    username_text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20)
    username_text_input.max_string_length = 47
    username_text_input.set_cursor_color(WHITE)
    username_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 210, 10 + twenty_chars.get_width(), 27))

    password_text = SMALL_FONT.render("Password:", 1, WHITE)
    screen.blit(password_text, (middle_of_screen(password_text), 275))
    password_text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20, password=True)
    password_text_input.max_string_length = 30
    password_text_input.set_cursor_color(WHITE)
    password_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 310, 10 + twenty_chars.get_width(), 27))
    clicked_username_box, clicked_password_box = False, False

    show_pswd_rect = pygame.draw.rect(screen, WHITE, (5 + middle_of_screen(twenty_chars) + twenty_chars.get_width(), 310, 60, 27))
    show_password = True
    show_password_text = {False: VERY_SMALL_FONT.render("Hide", 1, BLACK), True: VERY_SMALL_FONT.render("Show", 1, BLACK)}
    screen.blit(show_password_text[True], (WIDTH - 60, 310))

    login_text = SMALL_FONT.render("Login", 1, WHITE)
    login_rect = pygame.draw.rect(screen, WHITE, (246, 380, login_text.get_width() + 10, login_text.get_height() + 5), 1)
    screen.blit(login_text, (middle_of_screen(login_text) + 1, 380))

    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
    screen.blit(main_menu_text, (10, HEIGHT - 75))

    #TODO forgot password option

    pygame.display.update()
    run = True
    correct_info = False
    clicked_login = False
    print(show_password)
    while run:
        mouse_pos = pygame.mouse.get_pos()

        if username_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
            clicked_username_box = True
            clicked_password_box = False
        elif password_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
            clicked_password_box = True
            clicked_username_box = False
        elif pygame.mouse.get_pressed()[0] == 1:
            clicked_username_box, clicked_password_box = False, False

        curr_events = pygame.event.get()
        if clicked_username_box:
            username_text_input.update(curr_events)
        elif clicked_password_box:
            password_text_input.update(curr_events)

        pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 210, 10 + twenty_chars.get_width(), 27))  # username rect
        screen.blit(username_text_input.get_surface(), (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 210))
        pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 310, 10 + twenty_chars.get_width(), 27))  # password rect
        screen.blit(password_text_input.get_surface(), (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 310))
        pygame.display.update()
        clicked_login = False
        for event in curr_events:
            if event.type == pygame.QUIT:
                run = False
                notify_server_and_leave()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    clicked_login = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_menu_rect.collidepoint(event.pos):
                    run = False
                    menu_screen()
                elif show_pswd_rect.collidepoint(mouse_pos):
                    show_password = not show_password
                    password_text_input.password = show_password  # whether or not password will be filled with *
                    clicked_username_box, clicked_password_box = False, False
                    password_text_input.update([])
                    the_text = show_password_text[show_password]
                    show_pswd_rect = pygame.draw.rect(screen, WHITE, (5 + middle_of_screen(twenty_chars) + twenty_chars.get_width(), 310, 60, 27))
                    screen.blit(the_text, (WIDTH - 60, 310))
                    pygame.draw.rect(screen, BLUE, (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 310, 10 + twenty_chars.get_width(), 27))  # password rect
                    screen.blit(password_text_input.get_surface(), (WIDTH // 2 - (10 + twenty_chars.get_width() // 2), 310))
                    pygame.display.update()
                elif login_rect.collidepoint(event.pos):
                    clicked_login = True

            if clicked_login:
                errors = ''
                username = username_text_input.get_text()
                password = password_text_input.get_text()
                encoded_pswd = hashlib.sha256(password.encode('utf-8')).hexdigest()
                if is_valid_email(username):  # if they are logging in with email
                    print('email is valid')
                    email = username
                    emails = general_msgs_network.send('GENERAL_get_all_emails')  # uses pickle
                    if email in emails:
                        expected_password = general_msgs_network.send_and_receive('GENERAL_get_password_given_email:' + email)
                        if encoded_pswd == expected_password:  # login successful
                            print('logging in...')
                            correct_info = True
                            player_username = general_msgs_network.send_and_receive('GENERAL_get_username_given_email:' + email)

                else:  # they are logging in with their username
                    usernames = general_msgs_network.send('GENERAL_get_all_usernames')  # uses pickle
                    if username in usernames:
                        expected_password = general_msgs_network.send_and_receive('GENERAL_get_password_given_username:' + username)
                        if encoded_pswd == expected_password:  # login successful
                            player_username = username
                            correct_info = True

                if correct_info:
                    print('logging in...')
                    # send msg to server
                    pygame.draw.rect(screen, BLACK, (0, 548, WIDTH, 54))
                    text1 = SMALL_FONT.render("Signing in...", 1, GREEN)
                    screen.blit(text1, (middle_of_screen(text1), 555))
                    pygame.display.update()
                    # send msg to server
                    general_msgs_network.client.send(str.encode('GENERAL_NOW_ONLINE:' + username))
                    pygame.time.delay(500)
                    menu_screen()
                else:
                    errors = 'Login information is invalid.'
                    pygame.draw.rect(screen, BLACK, (0, 546, WIDTH, 54))
                    text1 = SMALL_FONT.render(errors, 1, RED)
                    screen.blit(text1, (middle_of_screen(text1), 555))
                    pygame.display.update()



def my_account_screen():
    global player_username, player_friend_code
    screen.fill(BLACK)
    username_text = MEDIUM_FONT.render(player_username, 1, CYAN)
    screen.blit(username_text, (middle_of_screen(username_text), 0))
    # email = general_msgs_network.send_and_receive('GENERAL_get_email_given_username:' + player_username)
    if player_friend_code == '':
        my_friend_code = general_msgs_network.send_and_receive('GENERAL_get_friend_code:' + player_username)
        player_friend_code = my_friend_code
    else:
        my_friend_code = player_friend_code
    # print(email)
    # email_text = SMALL_FONT.render(email, 1, WHITE)
    # screen.blit(email_text, (middle_of_screen(email_text), 60))
    friend_code_text = SMALL_FONT.render(f"My friend code: {my_friend_code}", 1, BLUE)
    screen.blit(friend_code_text, (middle_of_screen(friend_code_text), 60))

    stats_text = SMALL_FONT.render("Stats", 1, WHITE)
    screen.blit(stats_text, (middle_of_screen(stats_text), 105))

    add_friends_text = SMALL_FONT.render("Add friend", 1, WHITE)
    screen.blit(add_friends_text, (middle_of_screen(add_friends_text), HEIGHT - 255))
    pygame.draw.line(screen, WHITE, (222, 498), (337, 498), 1)
    info_text = VERY_SMALL_FONT2.render("You need your friends' username and friend code to add them.", 1, WHITE)
    screen.blit(info_text, (middle_of_screen(info_text), HEIGHT - 215))

    # username, date account created, show stats (gp, w, d, l), friends+ current status(online/offline)
    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE+25, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
    screen.blit(main_menu_text, (10, HEIGHT - 50))
    print('here ', main_menu_text.get_width() + 15)

    add_friends_text2 = SMALL_FONT.render("Add friend", 1, BLUE)
    screen.blit(add_friends_text2, (middle_of_screen(add_friends_text2), HEIGHT - 115))
    add_friend_rect = pygame.draw.rect(screen, BLUE, (220, 605, add_friends_text2.get_width()+5, add_friends_text2.get_height()), 1)

    friends_text = SMALL_FONT.render("Friends", 1, WHITE)
    friends_rect = pygame.draw.rect(screen, WHITE, (234, 205, friends_text.get_width() + 10, friends_text.get_height()), 1)
    screen.blit(friends_text, (middle_of_screen(friends_text), 205))

    fifteen_chars = VERY_SMALL_FONT.render("M"*15, 1, BLUE)
    username_text = SMALL_FONT.render("Their username: ", 1, BLUE)
    username_rect = pygame.draw.rect(screen, BLUE, (middle_of_screen(username_text) - 140 + username_text.get_width(), 535, fifteen_chars.get_width()+5, 27))
    screen.blit(username_text, (WIDTH // 2 - username_text.get_width() // 2 - 140, 525))
    username_text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20)
    username_text_input.max_string_length = 15

    friend_code_text = SMALL_FONT.render("Their friend code: ", 1, BLUE)
    friend_code_rect = pygame.draw.rect(screen, BLUE, (middle_of_screen(username_text) - 70 + username_text.get_width(), 575, 100, 27))
    screen.blit(friend_code_text, (WIDTH // 2 - friend_code_text.get_width() // 2 - 70, 565))
    friend_code_input = pygame_input.TextInput(text_color=WHITE, font_family='arial', font_size=20)
    friend_code_input.max_string_length = 6
    pygame.display.update()
    clicked_username_box, clicked_friend_code_box = False, False
    run = True
    while run:
        mouse_pos = pygame.mouse.get_pos()
        if username_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
            clicked_username_box = True
            clicked_friend_code_box = False
        elif friend_code_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
            clicked_username_box = False
            clicked_friend_code_box = True
        elif pygame.mouse.get_pressed()[0] == 1:
            clicked_username_box, clicked_friend_code_box = False, False

        curr_events = pygame.event.get()
        if clicked_username_box:
            username_text_input.update(curr_events)
        elif clicked_friend_code_box:
            friend_code_input.update(curr_events)

        username_rect = pygame.draw.rect(screen, BLUE, (middle_of_screen(username_text) - 140 + username_text.get_width(), 535, fifteen_chars.get_width()+5, 27))
        screen.blit(username_text_input.get_surface(), (middle_of_screen(username_text) - 135 + username_text.get_width(), 535))
        friend_code_rect = pygame.draw.rect(screen, BLUE, (middle_of_screen(username_text) - 70 + username_text.get_width(), 575, 100, 27))
        screen.blit(friend_code_input.get_surface(), (middle_of_screen(username_text) - 65 + username_text.get_width(), 575))

        pygame.display.update()
        correct_info = False
        for event in curr_events:
            if event.type == pygame.QUIT:
                notify_server_and_leave()
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(event.pos)
                if main_menu_rect.collidepoint(event.pos):
                    run = False
                    menu_screen()
                elif friends_rect.collidepoint(event.pos):
                    run = False
                    friends_screen()
                elif add_friend_rect.collidepoint(event.pos):
                    errors = ''
                    # username = player_username
                    friends_username = username_text_input.get_text()
                    friend_code = friend_code_input.get_text()
                    friends = general_msgs_network.send('GENERAL_get_friends:' + player_username)  # get this user's friends
                    if player_username == friends_username:
                        errors = 'Information is invalid.'
                    elif friends_username in friends:
                        errors = f"{friends_username} is already a friend."
                    else:
                        usernames = general_msgs_network.send('GENERAL_get_all_usernames')  # uses pickle
                        if friends_username in usernames:
                            expected_friend_code = general_msgs_network.send_and_receive('GENERAL_get_friend_code:' + friends_username)
                            if friend_code == expected_friend_code:
                                correct_info = True

                    if correct_info:
                        pygame.draw.rect(screen, BLACK, (205, 667, WIDTH, 54))
                        text1 = SMALL_FONT.render("Adding friend...", 1, GREEN)
                        screen.blit(text1, (middle_of_screen(text1) + 85, HEIGHT - 50))
                        add_friend(f"{player_username}_{friends_username}")
                        pygame.display.update()
                        pygame.time.delay(500)
                        pygame.draw.rect(screen, BLACK, (211, 667, WIDTH, 54))
                        text1 = SMALL_FONT.render("Added friend!", 1, GREEN)
                        screen.blit(text1, (middle_of_screen(text1) + 85, HEIGHT - 50))
                        pygame.display.update()
                        # menu_screen()
                    else:
                        if not errors:
                            errors = 'Information is invalid'
                        pygame.draw.rect(screen, BLACK, (205, 667, WIDTH, 54))
                        text1 = SMALL_FONT.render(errors, 1, RED)
                        screen.blit(text1, (middle_of_screen(text1) + 85, HEIGHT - 50))
                        pygame.display.update()


def get_opponents_move(n) -> str:  # fix
    msg = n.client.recv(1024).decode('utf-8')
    if not msg:
        print_lock.release()
    else:
        return msg


def main(game_type='', game_code='', the_network=None, is_rematch=False, prev_score=(0, 0), prev_went_first=0):
    global player_username, music_on
    run = True
    clock = pygame.time.Clock()
    screen.fill(BLACK)
    player_to_colour = {0: RED, 1: YELLOW}
    if not is_rematch:
        if not the_network:
            if not player_username:
                n = Network('Guest', game_type)
            else:
                n = Network(player_username, game_type)
        else:
            n = the_network
        # n.client.send(str.encode('public'))

        player = int(n.getP())  # 0 or 1
        screen.fill(BLACK)
        # p0 is red and p1 is yellow
        player_to_colour = {0: RED, 1: YELLOW}
        print("You are player", player)
        if not player_username:
            msg = 'P' + str(player) + 'ready:Guest'
        else:
            msg = 'P' + str(player) + 'ready:' + player_username
        # peek = n.client.recv(1024, socket.MSG_PEEK).decode('utf-8')
        msg = n.send_and_receive(msg)   # '0_move' or '1_move'
        print('Client received: ', msg)
        if game_type == 'public':
            text = SMALL_FONT.render("Finding opponent...", 1, (255, 0, 0),
                                     True)
        else:  # game_type == 'private'
            text = SMALL_FONT.render("Waiting for opponent... game code: " + str(game_code), 1,
                (255, 0, 0), True)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2,
                           HEIGHT // 2 - text.get_height() // 2))
        main_menu_text = FONT2.render("Main Menu", 1, WHITE)
        main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15,
        main_menu_text.get_height() + 5), 1)
        screen.blit(main_menu_text, (10, HEIGHT - 75))
        pygame.display.update()

        got_game = False

        while not got_game:
            # try:
            pass
            game = n.send("get")
            # print('Game:', game)
            got_game = game.p0_ready and game.p1_ready
            # print('who is ready ', game.p0_ready, game.p1_ready)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    notify_server_and_leave()
                if event.type == pygame.MOUSEBUTTONDOWN and main_menu_rect.collidepoint(event.pos):
                    msg = 'P' + str(player) + 'left'
                    n.client.send(str.encode(msg))
                    print('Client sent:', msg)
                    menu_screen()

                # print(game.con)
            # except:
            #   run = False
            #   print("Couldn't get game")
            #   sys.exit()
        screen.fill(BLACK)
        if game_type == 'public':
            opponent_username = n.send_and_receive('get_opponent_username')
            text = SMALL_FONT.render("Found opponent: " + opponent_username, 1, CYAN, True)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        else:
            text = SMALL_FONT.render("Found opponent", 1, CYAN, True)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        pygame.display.update()
        # screen.fill(BLACK)

        goes_first = 0  # if this is the first game, p0 goes first

        if player == 0:
            label = font1.render("Your turn", 1, RED)
        else:
            label = font1.render("Opponent's turn", 1, RED)
    else:
        n = the_network
        print('old player ', n.p)
        # n.p = int(not int(n.p)) # here
        player = int(n.getP())  # 0 or 1
        print('new player ', player)
        game = n.send("get_rematch")
        opponent_username = game.usernames[int(not player)]
        # msg = '0_move'
        # msg = n.client.recv(1024).decode('utf-8')  # '0_move' or '1_move'
        # print('QHERE ', msg)
        goes_first = int(not prev_went_first)
        msg = str(goes_first) + '_move'
        if player == goes_first:
            label = font1.render("Your turn", 1, RED)
        else:
            label = font1.render("Opponent's turn", 1, RED)
        text = MEDIUM_FONT.render("Starting rematch...", 1, CYAN, True)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2,
                           HEIGHT // 2 - text.get_height() // 2))

    # both players have joined the game
    if goes_first == 0:  # red goes first
        goes_first_text = SMALL_FONT.render("Red goes first", 1, RED)
        screen.blit(goes_first_text, (middle_of_screen(goes_first_text), HEIGHT // 2 - goes_first_text.get_height() // 2 + text.get_height() + 10))
    else:
        goes_first_text = SMALL_FONT.render("Yellow goes first", 1, YELLOW)
        screen.blit(goes_first_text, (middle_of_screen(goes_first_text), HEIGHT // 2 - goes_first_text.get_height() // 2 + text.get_height() + 10))
    pygame.display.update()
    pygame.time.wait(1500)
    screen.fill(BLACK)
    draw_board()
    bug = False
    requested_rematch, opponent_requested_rematch, rejected_rematch = False, False, False
    game.score = list(prev_score)

    screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
    pygame.display.update()

    while run:
        clock.tick(30)

        # print('message: ', msg)
        # print('player: ', player)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                notify_server_and_leave()
            if msg in ['0_move', '1_move'] and int(msg[0]) == player:  # this player must move
                label = font1.render("Your turn", 1, player_to_colour[player])
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
                screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                pygame.display.update()
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
                    x_pos = event.pos[0]
                    column = x_pos // SQUARE_SIZE
                    # check if move is valid TODO
                    if game.is_valid_location(column):
                        pygame.mixer.Sound.play(CLICK_SOUND)
                        pending_move = str(player) + ':' + str(column)  # e.g. '0:3' player 0 places piece in col 3
                        the_row = game.get_next_open_row(column)
                        print('the row', the_row)
                        game.drop_piece(the_row, column, player + 1)
                        updateBoard(game, the_row, column, player + 1)
                        # print(game.board)
                        label = font1.render("Opponent's turn", 1,
                                             player_to_colour[player])
                        pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
                        screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                        pygame.display.update()
                        print("Opponent's turn...")
                        print('Client sent:', pending_move)
                        msg = n.send_and_receive(pending_move)
                        # start_new_thread(get_opponents_move, (n, ))
                        # thread_ = GetOpponentsMoveThread(n)
                        #thread_.start()
                        # msg = thread_.join()  # wait until process is completed
                        # with concurrent.futures.ThreadPoolExecutor() as executor:
                        #   future = executor.submit(get_opponents_move, n)
                        #    msg = future.result()
                        # peek = n.client.recv(1024, socket.MSG_PEEK).decode('utf-8')  # make function for this
                        # print('peek:', peek)
                        if msg == 'opponent_left':
                            # msg = n.client.recv(1024).decode('utf-8')
                            run3 = True
                            main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                            main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
                            pygame.draw.rect(screen, BLACK, (main_menu_text.get_width() + 20, HEIGHT - SQUARE_SIZE, WIDTH, main_menu_text.get_height() + 5))
                            screen.blit(main_menu_text, (10, HEIGHT - 75))
                            opponent_left_text = SMALL_FONT.render('Your opponent has left.', 1, WHITE)
                            screen.blit(opponent_left_text, (WIDTH - opponent_left_text.get_width() - 10, HEIGHT - 80 - SQUARE_SIZE + 40))
                            pygame.display.update()
                            while run3:
                                # pygame.time.wait(3000)
                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        notify_server_and_leave()
                                    if event.type == pygame.MOUSEBUTTONDOWN:
                                        if main_menu_rect.collidepoint(event.pos):
                                            run3 = False
                                            menu_screen()
                        # pygame.event.pump()  # does not work
                        if '_move' in msg:
                            # msg = n.client.recv(1024).decode('utf-8')  # '0_move' or '1_move'
                            game.turn = int(not player)
                            print('Client received1: ', msg)
                        if len(msg) == 7 and 0 <= int(msg[0]) <= 1 and 0 <= int(
                                msg[3]) <= 5 and 0 <= int(msg[5]) <= 6:
                            # msg = n.client.recv(1024).decode('utf-8')
                            print('Client received1: ', msg)

                            # player_who_just_moved, row, col = int(msg[0]), int(msg[3]), int(msg[5])
                            # game.drop_piece(row, col, player_who_just_moved + 1)
                            # updateBoard(game, row, col, player_who_just_moved + 1)
                            # game.print_board(game.board)
                            # break

            else:
                game.turn = int(not player)
                label = font1.render("Opponent's turn", 1,
                                     player_to_colour[player])
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
                screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                pygame.display.update()
                print("Opponent's turn")
                # peek = n.client.recv(1024, socket.MSG_PEEK, ).decode('utf-8')
                # if peek:
                n.client.setblocking(False)  # make socket non-blocking
                while True:  # loop waits for opponent to move
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            notify_server_and_leave()
                        if event.type == pygame.MOUSEMOTION:
                            # print('mouse moved')
                            pygame.draw.rect(screen, BLACK,
                                             (0, 0, WIDTH, SQUARE_SIZE))
                            x_pos = event.pos[0]
                            if player == 0:
                                pygame.draw.circle(screen, RED,
                                                   (x_pos, SQUARE_SIZE // 2),
                                                   RADIUS)
                            else:
                                pygame.draw.circle(screen, YELLOW,
                                                   (x_pos, SQUARE_SIZE // 2),
                                                   RADIUS)
                            pygame.display.update()
                    try:
                        msg = n.client.recv(1024).decode(
                            'utf-8')  # 1:(0,1) get opponent's move
                        print('received opponents move')
                        break
                    except BlockingIOError:
                        pass
                n.client.setblocking(True)  # make socket blocking
                print('Client received2: ', msg)
                if len(msg) == len('P0_WONopponent_requested_rematch') and 'WON' in msg:
                    # game_winner = int(msg[1])  # 0 or 1
                    # game.score[game_winner] += 1
                    # print('score ', game.score)
                    # pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
                    # main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                    # main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15,
                    # main_menu_text.get_height() + 5), 1)
                    # screen.blit(main_menu_text, (10, HEIGHT - 75))
                    opponent_requested_rematch = True
                    msg = msg[:6]

                elif len(msg) == len('0:(1,4)P0_WON') and (msg[-3:] == 'WON' or 'DRAW' in msg):  # bug
                    pygame.mixer.Sound.play(CLICK_SOUND)
                    player_who_just_moved, row, col = int(msg[0]), int(msg[3]), int(msg[5])
                    game.drop_piece(row, col, player_who_just_moved + 1)
                    updateBoard(game, row, col, player_who_just_moved + 1)
                    game.print_board(game.board)
                    game.turn = int(not player_who_just_moved)  # can remove game.turn stuff
                    msg = msg[7:]

                elif msg == 'opponent_left':
                    run3 = True
                    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                    main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15,
                    main_menu_text.get_height() + 5), 1)
                    screen.blit(main_menu_text, (10, HEIGHT - 75))
                    opponent_left_text = SMALL_FONT.render('Your opponent has left.', 1, WHITE)
                    pygame.draw.rect(screen, BLACK, (main_menu_text.get_width() + 20, HEIGHT - SQUARE_SIZE, WIDTH, main_menu_text.get_height() + 5), 1)
                    screen.blit(opponent_left_text, (WIDTH - opponent_left_text.get_width() - 10, HEIGHT - 80 - SQUARE_SIZE + 40))
                    pygame.display.update()
                    while run3:
                        # pygame.time.wait(3000)
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                notify_server_and_leave()
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                if main_menu_rect.collidepoint(event.pos):
                                    run3 = False
                                    menu_screen()
                label = font1.render("Your turn", 1, player_to_colour[player])
                pygame.draw.rect(screen, BLACK, (
                0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
                screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                pygame.display.update()
                if len(msg) == len('1:(1,0)0_move') and '_move' in msg and ':' in msg:  # don't need anymore
                    print('bug happened')
                    bug = True
                    msg, other_msg = msg[:7], msg[7:]

            if len(msg) == 7 and 0 <= int(msg[0]) <= 1 and 0 <= int(msg[3]) <= 5 and 0 <= int(msg[5]) <= 6:  # received player:(row,col)
                pygame.mixer.Sound.play(CLICK_SOUND)
                player_who_just_moved, row, col = int(msg[0]), int(msg[3]), int(msg[5])
                game.drop_piece(row, col, player_who_just_moved + 1)
                updateBoard(game, row, col, player_who_just_moved + 1)
                game.print_board(game.board)
                game.turn = int(not player_who_just_moved)  # can remove game.turn stuff
                try:
                    if bug and other_msg:
                        msg = other_msg
                        bug = False
                        other_msg = ''
                        print('new msg:', msg)
                except (UnboundLocalError, NameError):
                    peek = n.client.recv(1024, socket.MSG_PEEK).decode('utf-8')
                    if peek[1:] == '_move':
                        msg = n.client.recv(1024).decode(
                            'utf-8')  # '0_move' or '1_move'
                        print('Client received3: ', msg)
            elif (len(msg) == 6 and 'WON' in msg) or msg == 'DRAW':  # game is over
                game_winner = int(msg[1])  # 0 or 1
                game.score[game_winner] += 1
                print('score ', game.score)
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
                main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15,
                main_menu_text.get_height() + 5), 1)
                screen.blit(main_menu_text, (10, HEIGHT - 75))
                accept_text = FONT2.render("Accept", 1, WHITE)
                reject_text = FONT2.render("Reject", 1, WHITE)
                request_rematch_text = FONT2.render("Request rematch", 1, WHITE)
                request_rematch_rect = pygame.Rect(WIDTH - request_rematch_text.get_width() - 20, HEIGHT - SQUARE_SIZE, request_rematch_text.get_width() + 15, request_rematch_text.get_height() + 5)
                try:  # if var does not exist
                    print(opponent_username)
                except (NameError, UnboundLocalError):
                    opponent_username = 'Opponent'
                if player == 0:
                    score_txt = SMALL_FONT.render(("You " + str(game.score[0]) + ' - ' + str(game.score[1]) + " " + opponent_username), 1, WHITE)
                else:
                    score_txt = SMALL_FONT.render(("You " + str(game.score[1]) + ' - ' + str(game.score[0]) + " " + opponent_username), 1, WHITE)
                screen.blit(score_txt, (WIDTH - score_txt.get_width() - 10, HEIGHT - 75 - SQUARE_SIZE))
                if 'WON' in msg:
                    if game_winner == player:
                        label = font1.render("You Won!", 1, player_to_colour[player])
                        pygame.mixer.Sound.play(WON_GAME_SOUND)
                    else:
                        label = font1.render("You lost.", 1, player_to_colour[player])
                else:
                    label = font1.render("It's a draw", 1, player_to_colour[player])

                screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
                pygame.display.update()
                pygame.time.wait(1000)

                if not opponent_requested_rematch:
                    request_rematch_rect = pygame.draw.rect(screen, WHITE, (WIDTH - request_rematch_text.get_width() - 20, HEIGHT - SQUARE_SIZE, request_rematch_text.get_width() + 15, request_rematch_text.get_height() + 5), 1)
                    screen.blit(request_rematch_text, (WIDTH - request_rematch_text.get_width() - 10, HEIGHT - 80))

                else:
                    pygame.draw.rect(screen, BLACK, (0, HEIGHT - 80 - SQUARE_SIZE + 40, WIDTH, SQUARE_SIZE * 2))
                    pygame.draw.rect(screen, BLACK, (0, HEIGHT-SQUARE_SIZE*2, WIDTH//2, label.get_height()+5))
                    main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                    main_menu_rect = pygame.draw.rect(screen, WHITE,(0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
                    screen.blit(main_menu_text, (10, HEIGHT - 75))
                    opponent_requested_rematch = True
                    rematch_text2 = SMALL_FONT.render("Your opponent has requested a rematch.", 1, WHITE)
                    screen.blit(rematch_text2, (WIDTH - rematch_text2.get_width() - 10, HEIGHT - 80 - SQUARE_SIZE + 40))
                    accept_rect = pygame.draw.rect(screen, WHITE, (WIDTH - accept_text.get_width() - reject_text.get_width() - 40, HEIGHT - SQUARE_SIZE, accept_text.get_width() + 15, accept_text.get_height() + 5), 1)
                    reject_rect = pygame.draw.rect(screen, WHITE, (WIDTH - reject_text.get_width() - 20, HEIGHT - SQUARE_SIZE, reject_text.get_width() + 15, reject_text.get_height() + 5), 1)
                    screen.blit(reject_text, (WIDTH - reject_text.get_width() - 10, HEIGHT - 80))
                    screen.blit(accept_text, (WIDTH - accept_text.get_width() - reject_text.get_width() - 34, HEIGHT - 80))
                pygame.display.update()

                # note that accept_text and rect are not drawn to screen yet

                # note that these are not drawn to screen yet
                accept_rect = pygame.draw.rect(screen, WHITE, (WIDTH - accept_text.get_width() - reject_text.get_width() - 40, HEIGHT - SQUARE_SIZE, accept_text.get_width() + 15, accept_text.get_height() + 5), 1)
                reject_rect = pygame.draw.rect(screen, WHITE, (WIDTH - reject_text.get_width() - 20, HEIGHT - SQUARE_SIZE, reject_text.get_width() + 15, reject_text.get_height() + 5), 1)
                run2 = True
                n.client.setblocking(False)  # make socket non-blocking
                while run2:
                    # pygame.time.wait(3000)
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            notify_server_and_leave()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if main_menu_rect.collidepoint(event.pos):
                                run2 = False
                                # rejected_rematch = True
                                n.client.setblocking(True)  # make socket blocking
                                n.client.send(str.encode('opponent_left'))
                                menu_screen()
                            if request_rematch_rect.collidepoint(event.pos) and not (requested_rematch or opponent_requested_rematch):  # offer rematch
                                pygame.draw.rect(screen, BLACK, (
                                0, HEIGHT - SQUARE_SIZE * 2, WIDTH,
                                SQUARE_SIZE * 2))
                                main_menu_text = FONT2.render("Main Menu", 1,
                                                              WHITE)
                                main_menu_rect = pygame.draw.rect(screen, WHITE,
                                                                  (0,
                                                                   HEIGHT - SQUARE_SIZE,
                                                                   main_menu_text.get_width() + 15,
                                                                   main_menu_text.get_height() + 5),
                                                                  1)
                                screen.blit(main_menu_text, (10, HEIGHT - 75))
                                requested_rematch = True
                                rematch_text2 = SMALL_FONT.render(
                                    "Rematch requested...", 1, WHITE)
                                screen.blit(rematch_text2, (WIDTH - rematch_text2.get_width() - 10, HEIGHT - 80 - SQUARE_SIZE + 30))
                                pygame.display.update()
                                n.client.setblocking(True)  # make socket blocking
                                n.client.send(str.encode('rematch_requested'))
                                print('Client sent: ', 'rematch_requested')
                                n.client.setblocking(False)  # make socket non-blocking

                            if accept_rect.collidepoint(
                                    event.pos) and opponent_requested_rematch:  # accept rematch offer
                                n.client.setblocking(
                                    True)  # make socket blocking
                                n.client.send(str.encode('rematch_accepted'))
                                print('Client sent: ', 'rematch_accepted')
                                # n.client.send(str.encode(game_type))
                                # n.p = n.connect()
                                main(game_type, game_code, n, True,
                                     tuple(game.score), goes_first)

                            if reject_rect.collidepoint(event.pos) and opponent_requested_rematch:
                                rejected_rematch = True
                                n.client.setblocking(True)  # make socket blocking
                                n.client.send(str.encode('rematch_rejected'))
                                pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE * 2))
                                rematch_text2 = SMALL_FONT.render("Rematch rejected.", 1, WHITE)
                                screen.blit(rematch_text2, (WIDTH - rematch_text2.get_width() - 10, HEIGHT - 80 - SQUARE_SIZE + 30))
                                main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                                main_menu_rect = pygame.draw.rect(screen, WHITE,
                                                                  (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
                                screen.blit(main_menu_text, (10, HEIGHT - 75))
                                pygame.display.update()
                    try:
                        if not rejected_rematch:
                            msg = n.client.recv(1024).decode('utf-8')  # check if opponent requested rematch
                            print('Client received: ', msg)
                            if msg == 'opponent_requested_rematch':
                                pygame.draw.rect(screen, BLACK, (0, HEIGHT - 80 - SQUARE_SIZE + 40, WIDTH, SQUARE_SIZE * 2))
                                pygame.draw.rect(screen, BLACK, (0, HEIGHT-SQUARE_SIZE*2, WIDTH//2, label.get_height()+5))
                                main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                                main_menu_rect = pygame.draw.rect(screen, WHITE,(0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
                                screen.blit(main_menu_text, (10, HEIGHT - 75))
                                opponent_requested_rematch = True
                                rematch_text2 = SMALL_FONT.render("Your opponent has requested a rematch.", 1, WHITE)
                                screen.blit(rematch_text2, (WIDTH - rematch_text2.get_width() - 10, HEIGHT - 80 - SQUARE_SIZE + 40))
                                accept_rect = pygame.draw.rect(screen, WHITE, (WIDTH - accept_text.get_width() - reject_text.get_width() - 40, HEIGHT - SQUARE_SIZE, accept_text.get_width() + 15, accept_text.get_height() + 5), 1)
                                reject_rect = pygame.draw.rect(screen, WHITE, (WIDTH - reject_text.get_width() - 20, HEIGHT - SQUARE_SIZE, reject_text.get_width() + 15, reject_text.get_height() + 5), 1)
                                screen.blit(reject_text, (WIDTH - reject_text.get_width() - 10, HEIGHT - 80))
                                screen.blit(accept_text, (WIDTH - accept_text.get_width() - reject_text.get_width() - 34, HEIGHT - 80))

                                pygame.display.update()
                            elif msg == 'rematch_accepted':
                                n.client.setblocking(True)  # make socket blocking
                                # n.client.send(str.encode(game_type))
                                # n.p = n.connect()
                                main(game_type, game_code, n, True,
                                     tuple(game.score), goes_first)

                            elif msg == 'rematch_rejected':
                                rejected_rematch = True
                                n.client.setblocking(
                                    True)  # make socket blocking
                                pygame.draw.rect(screen, BLACK, (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
                                rematch_text2 = SMALL_FONT.render(
                                    "Rematch rejected.", 1, WHITE)
                                screen.blit(rematch_text2, (WIDTH - rematch_text2.get_width() - 10, HEIGHT - 80 - SQUARE_SIZE + 30))
                                pygame.display.update()

                            elif msg == 'opponent_left':
                                run3 = True
                                pygame.draw.rect(screen, BLACK, (WIDTH - request_rematch_text.get_width() - 20, HEIGHT - SQUARE_SIZE*2, request_rematch_text.get_width() + 15, request_rematch_text.get_height() + 5 + 30))
                                pygame.draw.rect(screen, BLACK, (261, 633, WIDTH, HEIGHT))
                                # main_menu_text = FONT2.render("Main Menu", 1, WHITE)
                                # main_menu_rect = pygame.draw.rect(screen, WHITE, (0, HEIGHT - SQUARE_SIZE, main_menu_text.get_width() + 15, main_menu_text.get_height() + 5), 1)
                                # screen.blit(main_menu_text, (10, HEIGHT - 75))
                                opponent_left_text = SMALL_FONT.render('Your opponent has left.', 1, WHITE)
                                screen.blit(opponent_left_text, (WIDTH - opponent_left_text.get_width() - 10, HEIGHT - 80 - SQUARE_SIZE + 40))
                                pygame.display.update()
                                while run3:
                                    # pygame.time.wait(3000)
                                    for event in pygame.event.get():
                                        if event.type == pygame.QUIT:
                                            notify_server_and_leave()
                                        if event.type == pygame.MOUSEBUTTONDOWN:
                                            print(event.pos)
                                            if main_menu_rect.collidepoint(event.pos):
                                                run3 = False
                                                menu_screen()

                    except BlockingIOError:
                        pass
                n.client.setblocking(True)  # make socket blocking
                # run = False

            # updateBoard(game, 0, 3, 0)
            pygame.draw.rect(screen, BLACK,
                             (0, HEIGHT - SQUARE_SIZE * 2, WIDTH, SQUARE_SIZE))
            screen.blit(label, (15, HEIGHT - 75 - SQUARE_SIZE))
            pygame.display.update()


def setup_private_game():
    screen.fill(BLACK)
    title_text = TITLE_FONT.render("Private Game", 1, (255, 255, 0))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 75))
    or_text = SMALL_FONT.render("or", 1, WHITE)
    screen.blit(or_text, (WIDTH // 2 - or_text.get_width() // 2, 375))
    host_game_text = SMALL_FONT.render("Host Game", 1, BLUE)
    host_game_rect = pygame.draw.rect(screen, BLUE, (210, 278, 139, 32), 1)
    screen.blit(host_game_text,
                (WIDTH // 2 - host_game_text.get_width() // 2, 275))
    # join_game_text = SMALL_FONT.render("Join Game", 1, BLUE)
    # screen.blit(join_game_text, (WIDTH // 2 - join_game_text.get_width() // 2, 375))
    code_text = SMALL_FONT.render("Enter code: ", 1, BLUE)
    code_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - code_text.get_width() // 2 - 70 + code_text.get_width(), 440, 60, 27))
    screen.blit(code_text, (WIDTH // 2 - code_text.get_width() // 2 - 70, 430))
    text_input = pygame_input.TextInput(text_color=WHITE, font_family='arial',
                                        font_size=20)
    text_input.max_string_length = 4
    join_game_text2 = SMALL_FONT.render("Join Game", 1, BLUE)
    text_input.set_cursor_color(WHITE)
    screen.blit(join_game_text2,
                (WIDTH // 2 - join_game_text2.get_width() // 2, 475))
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
            host_game_rect = pygame.draw.rect(screen, GREEN,
                                              (210, 278, 139, 32), 1)
        else:
            host_game_text = SMALL_FONT.render("Host Game", 1, BLUE)
            host_game_rect = pygame.draw.rect(screen, BLUE, (210, 278, 139, 32),
                                              1)
        if join_game_rect2.collidepoint(mouse_pos):
            join_game_text2 = SMALL_FONT.render("Join Game", 1, GREEN)
            join_game_rect2 = pygame.draw.rect(screen, GREEN,
                                               (210, 478, 139, 32), 1)
        else:
            join_game_text2 = SMALL_FONT.render("Join Game", 1, BLUE)
            join_game_rect2 = pygame.draw.rect(screen, BLUE,
                                               (210, 478, 139, 32), 1)

        if code_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] == 1:
            clicked_text_box = True
        elif pygame.mouse.get_pressed()[0] == 1:  # clicked on screen but outside text box
            clicked_text_box = False
        curr_events = pygame.event.get()
        if clicked_text_box:
            x = text_input.update(curr_events)
            # print(text_input.get_text())  # prints name
        # pygame.draw.rect(screen, BLACK, (WIDTH // 2 - code_text.get_width() // 2 - 70 + code_text.get_width(), 440, 60, 27), 1)
        code_rect = pygame.draw.rect(screen, BLUE, (WIDTH // 2 - code_text.get_width() // 2 - 70 + code_text.get_width(), 440, 80, 27))
        screen.blit(text_input.get_surface(), (WIDTH // 2 - code_text.get_width() // 2 - 65 + code_text.get_width(), 440))
        pygame.display.update()
        for event in curr_events:
            if event.type == pygame.QUIT:
                run = False
                notify_server_and_leave()
                # break
            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_menu_rect.collidepoint(event.pos):
                    menu_screen()
                if join_game_rect2.collidepoint(event.pos):
                    n = PrivateGameNetwork(1, 'private')
                    print('Client sent: ', 'P2_joined_' + text_input.get_text())
                    if player_username != '':
                        msg = n.send_and_receive(player_username + ':P2_joined_' + text_input.get_text())
                    else:
                        msg = n.send_and_receive('Guest:P2_joined_' + text_input.get_text())
                    print('Client received: ', msg)
                    if msg == 'joined_game_successfully':
                        main('private', '', n, False)  # here
                    elif msg == 'joined_game_failed':
                        incorrect_code_text = SMALL_FONT.render(
                            "Incorrect code.", 1, RED)
                        screen.blit(incorrect_code_text, (WIDTH // 2 - incorrect_code_text.get_width() // 2, 475 + join_game_text2.get_height()))

                if host_game_rect.collidepoint(event.pos):
                    n = PrivateGameNetwork(0, 'private')
                    print('Client sent:', 'private')
                    if player_username != '':
                        game_code = n.send_and_receive(player_username + ':private')
                    else:
                        game_code = n.send_and_receive('Guest:private')
                    game_code = game_code[13:]
                    print('Client received: game code', game_code)
                    run = False
                    main('private', game_code, n, False)  # here
        screen.blit(join_game_text2, (WIDTH // 2 - join_game_text2.get_width() // 2, 475))
        screen.blit(host_game_text, (WIDTH // 2 - host_game_text.get_width() // 2, 275))
        pygame.display.update()


def refresh() -> Tuple[int, int]:
    """
    Refresh and return the number of players online and the number of players
    currently in a game.
    """
    global curr_screen_is_menu_screen, general_msgs_network
    # t1 = threading.Timer(5.0, refresh)
    # t1.daemon = True  # thread will be killed when the main program exits
    # if curr_screen_is_menu_screen:
    #    t1.start()
    num_people_online = general_msgs_network.send_and_receive('GENERAL_get_num_people_online')
    num_people_in_game = general_msgs_network.send_and_receive('GENERAL_get_num_people_in_game')
    return max(0, int(num_people_online)), max(0, int(num_people_in_game))


def menu_screen():
    global curr_screen_is_menu_screen, player_username
    screen.fill(BLACK)
    screen.blit(BACKGROUND_IMG, (0, 0))
    screen.blit(REFRESH_BUTTON, (WIDTH - REFRESH_BUTTON.get_width(), 0))
    refresh_rect = pygame.Rect((WIDTH - REFRESH_BUTTON.get_width(), 0, REFRESH_BUTTON.get_width(), REFRESH_BUTTON.get_height()))
    if player_username == '':  # if user is not signed in
        username_text = VERY_SMALL_FONT.render('Playing as Guest', 1, WHITE)
        leaderboard_text = FONT2.render("Leaderboard", 1, GRAY)
        leaderboard_rect = pygame.draw.rect(screen, GRAY, (5, HEIGHT - SQUARE_SIZE+25, leaderboard_text.get_width() + 15, leaderboard_text.get_height() + 5), 1)
        my_account_text = FONT2.render("My Account", 1, GRAY)
        my_account_rect = pygame.draw.rect(screen, GRAY, (5, HEIGHT - SQUARE_SIZE+25-(leaderboard_text.get_height() + 5)-5, my_account_text.get_width() + 15, my_account_text.get_height() + 5), 1)
        register_text = SMALL_FONT.render("Register", 1, WHITE)
        login_text = SMALL_FONT.render("Login", 1, WHITE)
        register_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - register_text.get_width() - 40, 180, register_text.get_width() + 10, register_text.get_height() + 5), 1)
        login_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 + 30, 180, login_text.get_width() + 10, login_text.get_height() + 5), 1)
    else:
        username_text = VERY_SMALL_FONT.render('Signed in as ' + player_username, 1, GREEN)
        leaderboard_text = FONT2.render("Leaderboard", 1, WHITE)
        leaderboard_rect = pygame.draw.rect(screen, WHITE, (5, HEIGHT - SQUARE_SIZE+25, leaderboard_text.get_width() + 15, leaderboard_text.get_height() + 5), 1)
        my_account_text = FONT2.render("My Account", 1, WHITE)
        my_account_rect = pygame.draw.rect(screen, WHITE, (5, HEIGHT - SQUARE_SIZE+25-(leaderboard_text.get_height() + 5)-5, my_account_text.get_width() + 15, my_account_text.get_height() + 5), 1)
        register_text = SMALL_FONT.render("Register", 1, GRAY)
        login_text = SMALL_FONT.render("Login", 1, GRAY)
        register_rect = pygame.draw.rect(screen, GRAY, (WIDTH // 2 - register_text.get_width() - 40, 180, register_text.get_width() + 10, register_text.get_height() + 5), 1)
        login_rect = pygame.draw.rect(screen, GRAY, (WIDTH // 2 + 30, 180, login_text.get_width() + 10, login_text.get_height() + 5), 1)

    screen.blit(my_account_text, (10, HEIGHT - 110))
    screen.blit(leaderboard_text, (10, HEIGHT - 50))
    screen.blit(username_text, (5, 5))

    curr_screen_is_menu_screen = True
    curr_time = time.time()
    num_people_online, num_people_in_game = refresh()  # refresh number of people in game every 5 seconds
    num_people_online_text = VERY_SMALL_FONT.render('Number of players online: ' + str(num_people_online), 1, WHITE)
    num_ppl_in_game_text = VERY_SMALL_FONT.render('Number of players in a game: ' + str(num_people_in_game), 1, WHITE)
    screen.blit(num_people_online_text, (WIDTH - num_people_online_text.get_width() - 10, HEIGHT - 55))
    screen.blit(num_ppl_in_game_text, (WIDTH - num_ppl_in_game_text.get_width() - 10, HEIGHT - 30))
    updated = True
    pygame.display.update()
    # print(f'There are {num_people_in_game} people in a game right now.')
    # print('client sent: ', 'get_num_people_online')
    # num_people_online = int(num_people_online)
    # print('number of people online: ', num_people_online)

    print(WIDTH, 'x', HEIGHT)
    run = True
    clock = pygame.time.Clock()
    #    num_ppl_online_text = VERY_SMALL_FONT.render('Number of people online: ' + str(num_people_online), 1, WHITE)
    # screen.blit(num_ppl_online_text, (WIDTH - num_ppl_online_text.get_width() - 10, HEIGHT - 45))
    title_text = TITLE_FONT.render("Connect 4", 1, (255, 255, 0))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 75))
    pygame.display.update()
    pointer = 185  # starting vertical line

    # pygame.draw.line(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 1)
    # register_text = SMALL_FONT.render("Register", 1, WHITE)
    screen.blit(register_text, (WIDTH // 2 - register_text.get_width() - 35, pointer - 5))
    # login_text = SMALL_FONT.render("Login", 1, WHITE)
    screen.blit(login_text, (WIDTH // 2 + 35, pointer - 5))

    pointer += 70

    online_text = FONT2.render("Online", 1, BLUE)
    screen.blit(online_text, (WIDTH // 2 - online_text.get_width() // 2, pointer))

    public_text = SMALL_FONT.render("Public", 1, WHITE)
    public_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - public_text.get_width() - 40, pointer + 50 - 5, public_text.get_width() + 10, public_text.get_height() + 5), 1)
    screen.blit(public_text, (WIDTH // 2 - public_text.get_width() - 35,
                              pointer + online_text.get_height()))
    private_text = SMALL_FONT.render("Private", 1, WHITE)
    private_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 + 30, pointer + 50 - 5, private_text.get_width() + 10, private_text.get_height() + 5), 1)
    screen.blit(private_text, (WIDTH // 2 + 35, pointer + online_text.get_height()))

    pointer += 120
    online_text = FONT2.render("Offline", 1, BLUE)
    screen.blit(online_text, (WIDTH // 2 - online_text.get_width() // 2, pointer))
    vs_cpu_text = SMALL_FONT.render("Single Player", 1, WHITE)
    vs_cpu_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - vs_cpu_text.get_width() // 2, pointer + 55 - 5, vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)
    screen.blit(vs_cpu_text, (WIDTH // 2 - vs_cpu_text.get_width() // 2 + 5,
                              pointer + vs_cpu_text.get_height() + 13))
    two_player_text = SMALL_FONT.render("Two Players", 1, WHITE)
    two_player_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - vs_cpu_text.get_width() // 2, pointer + 60 + vs_cpu_text.get_height(), vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)
    screen.blit(two_player_text, (WIDTH // 2 - two_player_text.get_width() // 2 + 5, pointer + two_player_text.get_height() + 25 + vs_cpu_text.get_height()))
    pygame.display.update()
    pointer = 185 + 70
    show_text = False  # show_text is for showing 'You must be signed in to use this feature...'
    updating_text = VERY_SMALL_FONT.render('Updating...', 1, WHITE)
    screen.blit(updating_text, (WIDTH - updating_text.get_width() - 10, HEIGHT - 80))

    while run:
        clock.tick(60)
        # make refresh button instead
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                notify_server_and_leave()
                # break
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(event.pos)
                if public_rect.collidepoint(event.pos):  # public game
                    curr_screen_is_menu_screen = False
                    print('public game')
                    # run = False
                    main('public', '', None, False)
                elif refresh_rect.collidepoint(event.pos) and curr_time + 5 < time.time():
                    curr_time = time.time()
                    num_people_online, num_people_in_game = refresh()  # refresh number of people in game
                    pygame.draw.rect(screen, BLACK, (246, 667, WIDTH-246, HEIGHT-656))
                    updating_text = VERY_SMALL_FONT.render('Updating...', 1, WHITE)
                    num_people_online_text = VERY_SMALL_FONT.render('Number of players online: ' + str(num_people_online), 1, WHITE)
                    num_ppl_in_game_text = VERY_SMALL_FONT.render('Number of players in a game: ' + str(num_people_in_game), 1, WHITE)
                    screen.blit(num_people_online_text, (WIDTH - num_people_online_text.get_width() - 10, HEIGHT - 55))
                    screen.blit(num_ppl_in_game_text, (WIDTH - num_ppl_in_game_text.get_width() - 10, HEIGHT - 30))
                    screen.blit(updating_text, (WIDTH - updating_text.get_width() - 10, HEIGHT - 80))
                    pygame.display.update()
                    updated = True
                    print('refreshed', curr_time)

                elif login_rect.collidepoint(event.pos) and not player_username:
                    login_screen()
                elif register_rect.collidepoint(event.pos) and not player_username:  # if they are currently playing as guest
                    register_screen()
                elif private_rect.collidepoint(event.pos):  # private game
                    curr_screen_is_menu_screen = False
                    setup_private_game()
                elif two_player_rect.collidepoint(event.pos):  # human vs human (offline)
                    g = Game(0)
                    g.run(screen)
                    menu_screen()
                elif my_account_rect.collidepoint(event.pos) and player_username:  # remember to add 'and player_username'
                    my_account_screen()
                elif leaderboard_rect.collidepoint(event.pos) and player_username:
                    leaderboard_screen()
                # draw_board()
            mouse_pos = pygame.mouse.get_pos()
            # if event.type == pygame.MOUSEMOTION:
            if (my_account_rect.collidepoint(mouse_pos) or leaderboard_rect.collidepoint(mouse_pos)) and not player_username:
                show_text = True
            else:
                show_text = False

            if public_rect.collidepoint(mouse_pos):  # public game
                public_text = SMALL_FONT.render("Public", 1, GREEN)
                public_rect = pygame.draw.rect(screen, (0, 255, 0), (WIDTH // 2 - public_text.get_width() - 40, pointer + 50 - 5,
                public_text.get_width() + 10, public_text.get_height() + 5), 1)
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
                two_player_rect = pygame.draw.rect(screen, GREEN, (WIDTH // 2 - vs_cpu_text.get_width() // 2, 375 + 60 + vs_cpu_text.get_height(), vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5),
                                                   1)
            else:
                two_player_text = SMALL_FONT.render("Two Players", 1, WHITE)
                two_player_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - vs_cpu_text.get_width() // 2, 375 + 60 + vs_cpu_text.get_height(), vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5),
                                                   1)
            if vs_cpu_rect.collidepoint(mouse_pos):
                vs_cpu_text = SMALL_FONT.render("Single Player", 1, GREEN)
                vs_cpu_rect = pygame.draw.rect(screen, GREEN, (WIDTH // 2 - vs_cpu_text.get_width() // 2, 375 + 55 - 5, vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5),
                                               1)
            else:
                vs_cpu_text = SMALL_FONT.render("Single Player", 1, WHITE)
                vs_cpu_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - vs_cpu_text.get_width() // 2, 375 + 55 - 5, vs_cpu_text.get_width() + 10, vs_cpu_text.get_height() + 5), 1)

        if updated and curr_time + 1 < time.time():
            pygame.draw.rect(screen, BLACK, (440, 639, WIDTH-440, updating_text.get_height()))  # cover 'Updating...'
            pygame.display.update()
            updated = False
        if show_text:
            small_txt = VERY_SMALL_FONT.render("You must be signed in to use this feature.", 1, WHITE)
            screen.blit(small_txt, (10, HEIGHT - 150))
        else:
            pygame.draw.rect(screen, BLACK, (0, 569, 405, 30))

        screen.blit(public_text, (WIDTH // 2 - public_text.get_width() - 35,
                                  pointer + online_text.get_height()))
        screen.blit(private_text,
                    (WIDTH // 2 + 35, pointer + online_text.get_height()))
        screen.blit(two_player_text, (WIDTH // 2 - two_player_text.get_width() // 2 + 5, 375 + two_player_text.get_height() + 25 + vs_cpu_text.get_height()))
        screen.blit(vs_cpu_text, (WIDTH // 2 - vs_cpu_text.get_width() // 2 + 5, 375 + vs_cpu_text.get_height() + 13))
        pygame.display.update()


if __name__ == '__main__':
    # while True:
    general_msgs_network.client.send(str.encode('GENERAL_someone_joined'))
    time.sleep(0.5)
    menu_screen()
