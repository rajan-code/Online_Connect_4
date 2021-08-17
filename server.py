import smtplib
import socket
import random
import string
from _thread import *
import pickle
from connect_4_game import Game
import pygame
import mysql.connector
import os
from datetime import date
import datetime
from typing import *

pygame.init()

db = mysql.connector.connect(
    host='172.105.20.159',
    user='rajan',
    passwd=os.environ.get('SQL_PASSWORD'),
    database='Online_Connect_4'
)
mycursor = db.cursor()
server = ""
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clients = set()

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
print("Waiting for a connection, Server Started")

# connected = set()
games = dict()  # used for public and private games
game_id_to_players = dict()  # used for public and private games
private_game_ids = set()  # set of ints
publicIdCount = 0
privateIdCount = 1000
numPeopleOnline = 0
numGamesCompleted = 0
numPeopleInGame = 0
username_to_status = dict()  # keeps track of which users are currently online

"""
class Server:
    def __init__(self):
        self.clients = []  # 
        self.names = [] # List[str]
    
    def broadcast(self, message: bytes):
        for client in self.clients:
            client.send(message)
"""


# Database functions
def get_data(column_name: str) -> List[str]:
    """
    :param column_name: "username" or "email"
    Return the requested data. e.g. if <column_name> == 'username' then return
    a list of all usernames in the table.
    """
    lst = []
    cmd = 'SELECT ' + column_name + ' FROM Players'
    mycursor.execute(cmd)
    for row in mycursor:
        lst.append(row[0])
    return lst


def add_user_to_database(username, email, pswd) -> None:
    """
    Add this new user to the database.
    """
    print('adding user')
    insert = f"INSERT INTO Players (username, email, password, dateCreated) VALUES ('{username}', '{email}', '{pswd}', CURDATE())"
    mycursor.execute(insert)
    db.commit()


# Server Functions
def send_email(email: str) -> str:
    """
    Send email to <email> and return the 6-char long code
    """
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login('noreplymessagingapp@gmail.com', os.environ.get('EMAIL_PASSWORD'))

        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        subject = 'Account Almost Created!'
        body = 'Please enter the following code in the app to validate your account: ' + code

        msg = f'Subject: {subject}\n\n{body}'
        smtp.sendmail('noreplymessagingapp@gmail.com', email, msg)
    return code


def threaded_client(conn, p: int, gameId: int, game_type: str):
    global publicIdCount, numGamesCompleted, numPeopleInGame
    if game_type == 'public':
        conn.send(str.encode(str(p)))
        print('Server sent:', str(p))
    msg = '0_move'
    conn.send(str.encode(msg))
    print('Server sent:', msg)
    reply = ""

    while True:
        try:
            # peek = conn.recv(1024*4, socket.MSG_PEEK).decode('utf-8')
            data2 = conn.recv(1024 * 4).decode()
            # data = conn.recv(1024).decode()
            print('Server received1: ', data2)

            if gameId in games:
                game = games[gameId]
              #  if not game.is_running:
                  #  game.run()

                if not data2:
                    for client in game_id_to_players[gameId]:
                        print(client._closed)
                    break
                else:
                    # data = conn.recv(1024*4).decode()
                    if data2 == "reset":
                        # game.resetWent()
                        pass
                    elif data2 == 'rematch_accepted':
                        numPeopleInGame += 2
                        msg = 'rematch_accepted'
                        for client in game_id_to_players[gameId]:
                            if client != conn:
                                client.sendall(msg.encode('utf-8'))  # send to the other client
                    elif data2 == 'rematch_requested':
                        msg = 'opponent_requested_rematch'
                        for client in game_id_to_players[gameId]:
                            if client != conn:
                                client.sendall(msg.encode('utf-8'))  # send to the other client
                    elif data2 == 'rematch_rejected':
                        msg = 'rematch_rejected'
                        for client in game_id_to_players[gameId]:
                            if client != conn:
                                client.sendall(msg.encode('utf-8'))  # send to the other client
                    elif data2 == 'get_rematch':
                        the_clients = []
                        for client in game_id_to_players[gameId]:
                            the_clients.append(client)
                        games[gameId] = Game(gameId)
                        games[gameId].p0_ready, games[gameId].p1_ready = True, True
                        game_id_to_players[gameId] = []
                        for client in the_clients:
                            game_id_to_players[gameId].append(client)
                        game = games[gameId]
                        conn.sendall(pickle.dumps(game))  # send rematch game
                        # for client in the_clients:
                            # client.send(str.encode('0_move'))
                    elif 'ready' in data2:
                        if data2[1] == '0':
                            game.p0_ready = True
                        else:
                            game.p1_ready = True
                        game.ready = game.p0_ready and game.p1_ready
                        if game.ready:
                            numPeopleInGame += 2
                    elif data2[2:] == 'left' and data2[1] in ['0', '1']:  # a user is no longer searching for opponent
                        the_player = int(data2[1])
                        if the_player == 0:
                            game.p0_ready = False
                        else:
                            game.p1_ready = False
                        game.ready = game.p0_ready and game.p1_ready
                        if gameId in private_game_ids:
                            private_game_ids.remove(gameId)
                            game_id_to_players[gameId] = []
                    elif data2 == 'get':
                        # print('using pickle')
                        # size = len(pickle.dumps(game, -1))
                        # print('size of picked obj:', size)
                        # print(game.id, 'aq')
                        # print(len(pickle.dumps(game, -1)))
                        conn.sendall(pickle.dumps(game))
                        # print('Server sent game.')
                        if game.connected():
                            print('Both players are ready.')
                    elif len(data2) == 3 and data2[1] == ':' and (data2[0] in ['0', '1']):  # received player:column
                        turn, col = int(data2[0]), int(data2[2])
                        the_row = game.get_next_open_row(col)
                        msg = data2[0] + ':(' + str(the_row) + ',' + str(col) + ')'  # format: turn:(row,col)
                        for client in game_id_to_players[gameId]:
                            client.send(msg.encode('utf-8'))  # send to both clients
                        # conn.sendall(str.encode(msg))
                        print('Server sent:', msg)
                        # print(game.print_board(game.board))

                        game.drop_piece(the_row, col, turn + 1)
                        if game.is_winner(1):  # if the game is over
                            numPeopleInGame -= 2
                            numGamesCompleted += 1
                            # print(game.print_board(game.board))
                            print('Player 1 has won the game!')
                            game.score[0] += 1
                            msg = 'P0_WON'
                            for client in game_id_to_players[gameId]:
                                client.sendall(msg.encode('utf-8'))  # send to both clients
                            print('Server sent:', msg)

                        elif game.is_winner(2):
                            numGamesCompleted += 1
                            numPeopleInGame -= 2
                            print(game.print_board(game.board))
                            print('Player 2 has won the game!')
                            print(numGamesCompleted)
                            game.score[1] += 1
                            msg = 'P1_WON'
                            for client in game_id_to_players[gameId]:
                                client.sendall(msg.encode('utf-8'))  # send to both clients
                            print('Server sent:', msg)

                        elif game.is_draw():
                            numGamesCompleted += 1
                            numPeopleInGame -= 2
                            msg = 'DRAW'
                            for client in game_id_to_players[gameId]:
                                client.sendall(msg.encode('utf-8'))  # send to both clients
                            print('Server sent:', msg)

                        else:  # game is not over yet
                            # p += 1
                            # p = p % 2  # 0 if turn is even, else 1
                            print(p, type(p))
                            not_p = int(not p)
                            msg = str(not_p) + '_move'  # ask other player for move
                            for client in game_id_to_players[gameId]:
                                client.send(str.encode(msg))
                            print('Server sent:', msg)

                    elif data2 == 'someone_leaving':
                        clients.remove(conn)
                        conn.close()
                    # else:
                      # conn.sendall(pickle.dumps(game))

            else:
                for client in game_id_to_players[gameId]:
                    print(client)
                break
        except (ConnectionResetError, ConnectionAbortedError, ConnectionError):
            break

    print("Lost connection")
    # send msg to player in game that their opponent has left
   # if game_type == 'public':
      #  publicIdCount -= 1  # only if game was public
    clients.remove(conn)
    game_id_to_players[gameId].remove(conn)
    print('b ', game_id_to_players[gameId])
    conn.close()
    try:
        other_player = game_id_to_players[gameId][0]
        other_player.send(str.encode('opponent_left'))
        print('Server sent:', 'opponent_left')
        game = games[gameId]
        if not(game.is_winner(1) or game.is_winner(2) or game.is_draw()):  # if game was not over and a player left
            numPeopleInGame -= 2
    except IndexError:
        pass
    if gameId in private_game_ids:
        private_game_ids.remove(gameId)
    try:
        del games[gameId]
        print("Closing Game", gameId)
    except KeyError:
        pass
    # del game_id_to_players[gameId]


def general_connection(conn, curr_data):
    global numPeopleOnline
    if curr_data == 'GENERAL_get_num_people_in_game':
        conn.send(str.encode(str(numPeopleInGame)))
        print('Server sent: ', numPeopleInGame)
    elif curr_data == 'GENERAL_someone_joined':
        numPeopleOnline += 1
        print('number of ppl online:', numPeopleOnline)
    elif curr_data == 'GENERAL_someone_leaving':
        numPeopleOnline -= 1
        print('number of ppl online:', numPeopleOnline)
    elif curr_data == 'GENERAL_get_num_people_online':
        conn.send(str.encode(str(numPeopleOnline)))
    elif curr_data == 'GENERAL_get_all_usernames':
        usernames = get_data('username')
        conn.send(pickle.dumps(usernames))
    elif curr_data == 'GENERAL_get_all_emails':
        emails = get_data('email')
        conn.send(pickle.dumps(emails))
    elif curr_data[:17] == 'GENERAL_NEW_USER:':
        username, email, encoded_pswd = curr_data[17:].split(',')
        add_user_to_database(username, email, encoded_pswd)
    elif curr_data[:21] == 'GENERAL_SEND_CODE_TO_':  # send code to this email
        email = curr_data[21:]
        the_code = send_email(email)
        conn.send(str.encode(the_code))

    while True:
        try:
            data3 = conn.recv(1024 * 4).decode()
            print('Server received3:', data3)
            if data3 == 'GENERAL_get_num_people_in_game':
                conn.send(str.encode(str(numPeopleInGame)))
                print('Server sent: ', numPeopleInGame)
            elif data3 == 'GENERAL_someone_joined':
                numPeopleOnline += 1
                print('number of ppl online:', numPeopleOnline)
            elif data3 == 'GENERAL_someone_leaving':
                numPeopleOnline -= 1
                print('number of ppl online:', numPeopleOnline)
                conn.close()
            elif data3 == 'GENERAL_get_num_people_online':
                conn.send(str.encode(str(numPeopleOnline)))
            elif data3 == 'GENERAL_get_all_usernames':
                usernames = get_data('username')
                conn.send(pickle.dumps(usernames))
            elif data3 == 'GENERAL_get_all_emails':
                emails = get_data('email')
                conn.send(pickle.dumps(emails))
            elif data3[:17] == 'GENERAL_NEW_USER:':
                username, email, encoded_pswd = data3[17:].split(',')
                add_user_to_database(username, email, encoded_pswd)
            elif data3[:21] == 'GENERAL_SEND_CODE_TO_':  # send code to this email
                email = data3[21:]
                the_code = send_email(email)
                conn.send(str.encode(the_code))

        except (OSError, ConnectionResetError, ConnectionAbortedError, ConnectionError):
            break
    conn.close()


while True:
    # pygame.display.quit()
    conn, addr = s.accept()
    clients.add(conn)
    print('Clients:', clients)
    # for client in clients:
      #  print(client._closed)
       # client.send(str.encode('abc'))
    print("Connected to:", addr)
    data = conn.recv(1024).decode('utf-8')
    print('Server received2: ', data)

    if data == 'public':
        publicIdCount += 1
        p = 0
        gameId = (publicIdCount - 1)//2
        # privateGameId
        if publicIdCount % 2 == 1:
            games[gameId] = Game(gameId)
            game_id_to_players[gameId] = [conn]
            print(games)
            print("Creating a new public game...")
            games[gameId].p0_ready = True
        else:
            # games[gameId].ready = True
            games[gameId].p1_ready = True
            game_id_to_players[gameId].append(conn)
            p = 1
        start_new_thread(threaded_client, (conn, p, gameId, 'public'))

    elif data == 'private':  # data == 'private'
        privateIdCount += 1
        p = 0
        # privateGameId = (privateIdCount - 1) // 2  # generate rand int
        while True:
            privateGameId = random.randint(1000, 9999)
            if privateGameId in private_game_ids:
                privateGameId = random.randint(1000, 9999)
            else:
                break
        # privateGameId
        # if privateIdCount % 2 == 1:
        games[privateGameId] = Game(privateGameId)
        game_id_to_players[privateGameId] = [conn]
        private_game_ids.add(privateGameId)
        print(games)
        print("Creating a new private game...")
        print('Server sent: ', 'created_game_' + str(privateGameId))
        conn.send(str.encode('created_game_' + str(privateGameId)))
        games[privateGameId].p0_ready = True
        # else:
            # games[gameId].ready = True
          #  games[gameId].p1_ready = True
          #  game_id_to_players[gameId].append(conn)
           # p = 1

        start_new_thread(threaded_client, (conn, p, privateGameId, 'private'))
    elif 'P2_joined_' in data:  # p2 joined private game
        try:
            this_game_id = int(data[10:])
            p = 1
            if this_game_id in private_game_ids:
                print('p2 joined private game')
                games[this_game_id].p1_ready = True
                game_id_to_players[this_game_id].append(conn)
                conn.send(str.encode('joined_game_successfully'))
                start_new_thread(threaded_client, (conn, p, this_game_id, 'private'))
            else:
                conn.send(str.encode('joined_game_failed'))
        except ValueError:
            conn.send(str.encode('joined_game_failed'))

    elif data == 'get_num_people_online':
        conn.send(str.encode(str(numPeopleOnline)))
        print('Server sent: ', numPeopleOnline)

    elif data[:8] == 'GENERAL_':
        start_new_thread(general_connection, (conn, data))
    """
    elif data == 'GENERAL_get_num_people_in_game':
        start_new_thread(general_connection, (conn, data))
        # conn.send(str.encode(str(numPeopleInGame)))
        # print('Server sent: ', numPeopleInGame)
        # clients.remove(conn)
        # conn.close()

    elif data == 'GENERAL_someone_leaving':
        numPeopleOnline -= 2  # -=2 because a new connection was created to close the old one
        clients.remove(conn)
        conn.close()
    elif data == 'GENERAL_someone_joined':
        numPeopleOnline += 1  #
    elif data == 'GENERAL_someone_joinedget_num_people_online':
        numPeopleOnline += 1
        conn.send(str.encode(str(numPeopleOnline)))
        print('Server sent: ', numPeopleOnline)
    """

