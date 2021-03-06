import smtplib
import socket
import random
import string
from _thread import *
import time
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
    host='170.187.181.231',
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
conn_to_addr = dict()  # socket -> str

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
def get_coins(username: str) -> int:
    mycursor.execute(f"SELECT coins FROM Store WHERE username='{username}'")
    return int(mycursor.fetchone()[0])


def get_top_ten_public():
    lst = []
    mycursor.execute("SELECT * FROM Games ORDER BY pointsPercentage DESC")
    for row in mycursor:
        lst.append(row)
    return lst[:10]


def get_top_ten_friends(username: str):
    """
    Return a list of the top 10 players, only including <username> and
    <username>'s friends.
    """
    # see if this function works if username is not in top 10
    lst = []
    username_in_top_ten = False
    counter = 1  # the ranking of each player
    username_stats = tuple()  # <username>'s stats
    mycursor.execute(f"SELECT * FROM Games WHERE (username='{username}' OR username in (SELECT friend FROM Friends WHERE username='{username}')) ORDER BY pointsPercentage DESC")
    for i, row in enumerate(mycursor):
        if row[0] == username:
            username_in_top_ten = True
            username_stats = row

        r = list(row)
        r.insert(0, counter)
        lst.append(r)
        counter += 1
    if username_in_top_ten:
        return lst[:10]
    else:
        return lst[:10] + username_stats


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


def get_friends(username: str) -> List[str]:
    lst = []
    cmd = f"SELECT friend FROM Friends WHERE username='{username}'"
    mycursor.execute(cmd)
    for x in mycursor:
        lst.append(x[0])
    return lst


def get_friends_with_status(username: str) -> List[Tuple[str, bool]]:
    """

    :param username:
    :return: A list of this user's friends along with whether or not
             they are online

    >>> get_friends_with_status('baldski')
    [('Chingers', True), ('testUser', False)]
    """
    friends = get_friends(username)
    ans = []
    for friend in friends:
        if friend in username_to_status:
            ans.append((friend, username_to_status[friend]))
        else:
            ans.append((friend, False))  # they are offline
    return ans


def get_email(username: str):
    cmd = f"SELECT email FROM Players WHERE username='{username}'"
    mycursor.execute(cmd)
    return mycursor.fetchone()[0]


def get_password(column_name: str, data: str) -> str:
    """
    Return this users password given their username or email.
    Preconditions:
        <data> is in the table.
        <column> == 'username' or 'email'

    >>> str(get_password('username', 'baldski'))
    '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    if column_name == 'username':
        cmd = f"SELECT password FROM Players WHERE username= + '{data}'"
    else:
        cmd = f"SELECT password FROM Players WHERE email= + '{data}'"
    mycursor.execute(cmd)
    return mycursor.fetchone()[0]


def add_user_to_database(username, email, pswd) -> None:
    """
    Add this new user to the database.
    """
    print('adding user')
    insert = f"INSERT IGNORE INTO Players (username, email, password, dateCreated) VALUES ('{username}', '{email}', '{pswd}', CURDATE())"
    mycursor.execute(insert)
    insert2 = f"INSERT IGNORE INTO Games (username, pointsPercentage) VALUES ('{username}', 0.000)"
    mycursor.execute(insert2)
    mycursor.execute(f"UPDATE Players SET friendCode = FLOOR(RAND()*(99999-10000)+10000) WHERE username='{username}'")
    insert3 = f"INSERT IGNORE INTO Store (username) VALUES ('{username}')"
    mycursor.execute(insert3)
    db.commit()


def add_friend(username, friend) -> None:
    """
    Make these two users friends in the database.

    """
    insert = f"INSERT IGNORE INTO Friends (username, friend) VALUES ('{username}', '{friend}')"
    mycursor.execute(insert)
    insert = f"INSERT IGNORE INTO Friends (username, friend) VALUES ('{friend}', '{username}')"
    mycursor.execute(insert)
    db.commit()

def get_username(email: str) -> str:
    """
    Return this player's username given their email.
    """
    cmd = f"SELECT username FROM Players WHERE email='{email}'"
    mycursor.execute(cmd)
    return mycursor.fetchone()[0]

def get_friend_code(username: str) -> str:
    cmd = f"SELECT friendCode FROM Players WHERE username='{username}'"
    mycursor.execute(cmd)
    return str(mycursor.fetchone()[0])


def update_store_table(username: str, item_bought: str, price: int):
    print(username, item_bought, price)
    cmd2 = f"SELECT {item_bought} FROM Store WHERE username='{username}'"
    mycursor.execute(cmd2)
    curr_status = int(mycursor.fetchone()[0])
    if curr_status != 1:
        cmd1 = f"UPDATE Store SET coins = coins - {price} WHERE username='{username}'"
        mycursor.execute(cmd1)
        cmd2 = f"UPDATE Store SET {item_bought} = 1 WHERE username='{username}'"
        mycursor.execute(cmd2)
        db.commit()
    else:
        print(f"{username} already owns this item.")


def get_items_bought(username: str) -> Dict[str, int]:
    """
    Return a dict that maps the name of an item in the store (e.g.
    differentColours) and whether or not this user owns it (0 or 1)
    """
    columns = []
    ans = dict()
    cmd1 = f"SHOW COLUMNS FROM Store"
    mycursor.execute(cmd1)
    for x in mycursor:
        columns.append(x[0])
    columns = columns[2:]
    for col in columns:
        cmd1 = f"SELECT {col} FROM Store WHERE username='{username}'"
        mycursor.execute(cmd1)
        ans[col] = int(mycursor.fetchone()[0])
    return ans


def update_games_table(winner: str, loser: str, is_draw=False):
    """
    Update the games table. Also, update the coins of the winner in the Store
    table.
    :param winner: The username of the winner of the game.
    :param loser: The username of the loser of the game.
    :param is_draw: True iff the game was a draw.
    """
    # update games played
    if winner != 'Guest':
        cmd1 = f"UPDATE LOW_PRIORITY Games SET gamesPlayed = gamesPlayed + 1 WHERE username='{winner}'"
        mycursor.execute(cmd1)
        cmd = f"UPDATE LOW_PRIORITY Store SET coins = coins + 10 WHERE username='{winner}'"
        mycursor.execute(cmd)
    if loser != 'Guest':
        cmd1 = f"UPDATE LOW_PRIORITY Games SET gamesPlayed = gamesPlayed + 1 WHERE username='{loser}'"
        mycursor.execute(cmd1)
    if not is_draw:
        # update winner's data
        if winner != 'Guest':
            cmd2 = f"UPDATE LOW_PRIORITY Games SET wins = wins + 1 WHERE username='{winner}'"
            mycursor.execute(cmd2)
        # update loser's data
        if loser != 'Guest':
            cmd3 = f"UPDATE LOW_PRIORITY Games SET losses = losses + 1 WHERE username='{loser}'"
            mycursor.execute(cmd3)
    else:
        if winner != 'Guest':
            cmd4 = f"UPDATE LOW_PRIORITY Games SET draws = draws + 1 WHERE username='{winner}'"
            mycursor.execute(cmd4)
        if loser != 'Guest':
            cmd4 = f"UPDATE LOW_PRIORITY Games SET draws = draws + 1 WHERE username ='{loser}'"
            mycursor.execute(cmd4)
    mycursor.execute("UPDATE LOW_PRIORITY Games SET pointsPercentage=(points/(gamesPlayed*2)) WHERE gamesPlayed>0")
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
        print(code)
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
            if data2 != 'get':
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
                        time.sleep(0.1)
                        for client in game_id_to_players[gameId]:
                            if client != conn:
                                client.sendall(msg.encode('utf-8'))  # send to the other client
                    elif data2 == 'rematch_rejected':
                        msg = 'rematch_rejected'
                        for client in game_id_to_players[gameId]:
                            if client != conn:
                                client.sendall(msg.encode('utf-8'))  # send to the other client
                    elif data2 == 'opponent_left':
                        msg = 'opponent_left'
                        for client in game_id_to_players[gameId]:
                            if client != conn:
                                client.sendall(msg.encode('utf-8'))  # send to the other client
                    elif data2 == 'get_rematch':
                        the_clients = []
                        the_usernames = games[gameId].usernames
                        for client in game_id_to_players[gameId]:
                            the_clients.append(client)
                        games[gameId] = Game(gameId)
                        games[gameId].p0_ready, games[gameId].p1_ready = True, True
                        game_id_to_players[gameId] = []
                        for client in the_clients:
                            game_id_to_players[gameId].append(client)
                        game = games[gameId]
                        games[gameId].usernames = the_usernames
                        conn.sendall(pickle.dumps(game))  # send rematch game
                        # for client in the_clients:
                            # client.send(str.encode('0_move'))
                    elif 'ready' in data2:
                        print('AA ', data2)
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
                        game_id_to_players[gameId] = []
                        if gameId in private_game_ids:
                            private_game_ids.remove(gameId)
                        else:
                            publicIdCount -= 1
                            print('publicID', publicIdCount)
                            games[gameId].p0_ready = False
                            games[gameId].usernames[0] = ''
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
                    elif data2 == 'get_opponent_username':
                        for i in range(len(game_id_to_players[gameId])):
                            client = game_id_to_players[gameId][i]
                            if conn != client:
                                msg = game.usernames[i]
                                conn.send(msg.encode('utf-8'))  # send to other client

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
                        if game.is_winner(1):  # if player one has won
                            print(game.usernames)
                            if conn_to_addr[game_id_to_players[gameId][0]] != conn_to_addr[game_id_to_players[gameId][1]]:
                                if game.usernames[0] != 'Guest' or game.usernames[1] != 'Guest':
                                    update_games_table(game.usernames[0], game.usernames[1])
                            else:
                                print('game was offline so do not update leaderboard')
                            numPeopleInGame -= 2
                            numGamesCompleted += 1
                            # print(game.print_board(game.board))
                            print('Player 1 has won the game!')
                            game.score[0] += 1
                            msg = 'P0_WON'
                            time.sleep(0.1)
                            for client in game_id_to_players[gameId]:
                                client.send(msg.encode('utf-8'))  # send to both clients
                            print('Server sent:', msg)

                        elif game.is_winner(2):
                            print(game.usernames)
                            if conn_to_addr[game_id_to_players[gameId][0]] != conn_to_addr[game_id_to_players[gameId][1]]:
                                if game.usernames[0] != 'Guest' or game.usernames[1] != 'Guest':
                                    update_games_table(game.usernames[1], game.usernames[0])
                            else:
                                print('game was offline so do not update leaderboard')
                            numGamesCompleted += 1
                            numPeopleInGame -= 2
                            print(game.print_board(game.board))
                            print('Player 2 has won the game!')
                            print(numGamesCompleted)
                            game.score[1] += 1
                            msg = 'P1_WON'
                            time.sleep(0.1)
                            for client in game_id_to_players[gameId]:
                                client.send(msg.encode('utf-8'))  # send to both clients
                            print('Server sent:', msg)

                        elif game.is_draw():
                            if conn_to_addr[game_id_to_players[gameId][0]] != conn_to_addr[game_id_to_players[gameId][1]]:
                                if game.usernames[0] != 'Guest' or game.usernames[1] != 'Guest':
                                    update_games_table(game.usernames[0], game.usernames[1], True)
                            else:
                                print('game was offline so do not update leaderboard')
                            numGamesCompleted += 1
                            numPeopleInGame -= 2
                            msg = 'DRAW'
                            time.sleep(0.1)
                            for client in game_id_to_players[gameId]:
                                client.send(msg.encode('utf-8'))  # send to both clients
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
    if conn in game_id_to_players[gameId]:
        game_id_to_players[gameId].remove(conn)

    print('b ', game_id_to_players[gameId])
    conn.close()
    del conn_to_addr[conn]
    try:
        other_player = game_id_to_players[gameId][0]
        other_player.send(str.encode('opponent_left'))
        print('Server sent:', 'opponent_left')
        game = games[gameId]
        if not(game.is_winner(1) or game.is_winner(2) or game.is_draw()):  # if game was not over and a player left
            numPeopleInGame -= 2
    except (IndexError, KeyError):
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
    elif 'GENERAL_NOW_ONLINE:' in curr_data:
        colon_index = curr_data.index(':')
        username = curr_data[colon_index + 1:]
        username_to_status[username] = True
        print(username_to_status)
    elif curr_data == 'GENERAL_someone_joined':
        numPeopleOnline += 1
        print('number of ppl online:', numPeopleOnline)
    elif curr_data == 'GENERAL_someone_leaving':
        numPeopleOnline -= 1
        print('number of ppl online:', numPeopleOnline)
    elif 'GENERAL_NOW_OFFLINE:' in curr_data:
        colon_index_ = curr_data.index(':')
        username = curr_data[colon_index_ + 1:]
        username_to_status[username] = False
        print(username_to_status)
        numPeopleOnline -= 1
        print('number of ppl online:', numPeopleOnline)
        conn.close()
    elif curr_data == 'GENERAL_get_num_people_online':
        conn.send(str.encode(str(numPeopleOnline)))
    elif curr_data == 'GENERAL_get_all_usernames':
        usernames = get_data('username')
        conn.send(pickle.dumps(usernames))
    elif curr_data == 'GENERAL_get_all_emails':
        emails = get_data('email')
        conn.send(pickle.dumps(emails))
    elif curr_data[:17] == 'GENERAL_NEW_USER:':  # someone just registered account
        username, email, encoded_pswd = curr_data[17:].split(',')
        add_user_to_database(username, email, encoded_pswd)
    elif 'GENERAL_ADD_FRIEND:' in curr_data:
        username, friend = curr_data[19:].split(',')
        add_friend(username, friend)
    elif curr_data[:21] == 'GENERAL_SEND_CODE_TO_':  # send code to this email
        email = curr_data[21:]
        the_code = send_email(email)
        conn.send(str.encode(the_code))
    elif 'GENERAL_get_password_given_email:' in curr_data:  # get password of the user with this email
        email = curr_data[33:]
        password = get_password('email', email)
        conn.send(str.encode(password))
    elif 'GENERAL_get_username_given_email:' in curr_data:
        email = curr_data[len('GENERAL_get_username_given_email:'):]
        username = get_username(email)
        conn.send(str.encode(username))
    elif 'GENERAL_get_password_given_username:' in curr_data:
        username = curr_data[len('GENERAL_get_password_given_username:'):]
        password = get_password('username', username)
        conn.send(str.encode(password))
    elif curr_data == 'GENERAL_GET_TOP_TEN_PUBLIC':
        top_ten = get_top_ten_public()
        conn.send(pickle.dumps(top_ten))
    elif 'GENERAL_GET_TOP_TEN_FRIENDS:' in curr_data:
        colon_index1 = curr_data.index(':')
        username = curr_data[colon_index1+1:]
        top_ten = get_top_ten_friends(username)
        print(top_ten)
        conn.send(pickle.dumps(top_ten))
    elif 'GENERAL_get_email_given_username:' in curr_data:
        username = curr_data[len('GENERAL_get_email_given_username:'):]
        email = get_email(username)
        conn.send(str.encode(email))
    elif 'GENERAL_get_friend_code:' in curr_data:
        username = curr_data[len('GENERAL_get_friend_code:'):]
        friend_code = get_friend_code(username)
        conn.send(str.encode(friend_code))
    elif 'GENERAL_get_friends:' in curr_data:
        username = curr_data[len('GENERAL_get_friends:'):]
        friends = get_friends(username)
        conn.send(pickle.dumps(friends))
    elif curr_data[:31] == 'GENERAL_GET_FRIENDS_AND_STATUS:':
        colon_index1 = curr_data.index(':')
        username = curr_data[colon_index1+1:]
        friends_and_status = get_friends_with_status(username)
        conn.send(pickle.dumps(friends_and_status))
    elif curr_data[:18] == 'GENERAL_GET_COINS:':
        colon_index1 = curr_data.index(':')
        username = curr_data[colon_index1 + 1:]
        coins = get_coins(username)
        conn.send(str.encode(str(coins)))
    elif curr_data[:20] == 'GENERAL_BOUGHT_ITEM:':
        colon_index1 = curr_data.index(':')
        semicolon_index = curr_data.index(';')
        comma_index = curr_data.index(',')
        username = curr_data[colon_index1 + 1:semicolon_index]
        item_bought = curr_data[semicolon_index + 1: comma_index]
        price = int(curr_data[comma_index + 1:])
        print('updating store table')
        update_store_table(username, item_bought, price)
    elif curr_data[:25] == 'GENERAL_GET_ITEMS_BOUGHT:':
        colon_index1 = curr_data.index(':')
        username = curr_data[colon_index1 + 1:]
        items_bought = get_items_bought(username)
        conn.send(pickle.dumps(items_bought))

    while True:
        try:
            data3 = conn.recv(1024 * 4).decode()
            # print('Server received3:', data3)
            if data3 == 'GENERAL_get_num_people_in_game':
                conn.send(str.encode(str(numPeopleInGame)))
                print('Server sent: ', numPeopleInGame)
            elif 'GENERAL_NOW_ONLINE:' in data3:
                colon_index_ = data3.index(':')
                username = data3[colon_index_ + 1:]
                username_to_status[username] = True
                print(username_to_status)
            elif data3 == 'GENERAL_someone_joined':
                numPeopleOnline += 1
                print('number of ppl online:', numPeopleOnline)
            elif data3 == 'GENERAL_someone_leaving':
                numPeopleOnline -= 1
                print('number of ppl online:', numPeopleOnline)
                conn.close()
            elif 'GENERAL_NOW_OFFLINE:' in data3:
                colon_index_ = data3.index(':')
                username = data3[colon_index_ + 1:]
                username_to_status[username] = False
                print(username_to_status)
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
            elif 'GENERAL_ADD_FRIEND:' in data3:
                username, friend = data3[19:].split(',')
                add_friend(username, friend)
            elif data3[:21] == 'GENERAL_SEND_CODE_TO_':  # send code to this email
                email = data3[21:]
                the_code = send_email(email)
                conn.send(str.encode(the_code))
            elif 'GENERAL_get_password_given_email:' in data3:  # get password of the user with this email
                email = data3[33:]
                password = get_password('email', email)
                conn.send(str.encode(password))
            elif 'GENERAL_get_username_given_email:' in data3:
                email = data3[len('GENERAL_get_username_given_email:'):]
                username = get_username(email)
                conn.send(str.encode(username))
            elif 'GENERAL_get_password_given_username:' in data3:
                username = data3[len('GENERAL_get_password_given_username:'):]
                password = get_password('username', username)
                conn.send(str.encode(password))
            elif data3 == 'GENERAL_GET_TOP_TEN_PUBLIC':
                top_ten = get_top_ten_public()
                conn.send(pickle.dumps(top_ten))
            elif 'GENERAL_GET_TOP_TEN_FRIENDS:' in data3:
                colon_index1 = data3.index(':')
                username = data3[colon_index1+1:]
                top_ten = get_top_ten_friends(username)
                conn.send(pickle.dumps(top_ten))
            elif 'GENERAL_get_email_given_username:' in data3:
                username = data3[len('GENERAL_get_email_given_username:'):]
                email = get_email(username)
                conn.send(str.encode(email))
            elif 'GENERAL_get_friend_code:' in data3:
                username = data3[len('GENERAL_get_friend_code:'):]
                friend_code = get_friend_code(username)
                conn.send(str.encode(friend_code))
            elif data3[:20] == 'GENERAL_get_friends:':
                username = data3[len('GENERAL_get_friends:'):]
                friends = get_friends(username)
                conn.send(pickle.dumps(friends))
            elif data3[:31] == 'GENERAL_GET_FRIENDS_AND_STATUS:':
                colon_index1 = data3.index(':')
                username = data3[colon_index1+1:]
                friends_and_status = get_friends_with_status(username)
                conn.send(pickle.dumps(friends_and_status))
            elif data3[:18] == 'GENERAL_GET_COINS:':
                colon_index1 = data3.index(':')
                username = data3[colon_index1 + 1:]
                coins = get_coins(username)
                conn.send(str.encode(str(coins)))
            elif data3[:20] == 'GENERAL_BOUGHT_ITEM:':
                colon_index1 = data3.index(':')
                semicolon_index = data3.index(';')
                comma_index = data3.index(',')
                username = data3[colon_index1 + 1:semicolon_index]
                item_bought = data3[semicolon_index + 1: comma_index]
                price = int(data3[comma_index + 1:])
                print('updating store table')
                update_store_table(username, item_bought, price)
            elif data3[:25] == 'GENERAL_GET_ITEMS_BOUGHT:':
                colon_index1 = data3.index(':')
                username = data3[colon_index1 + 1:]
                items_bought = get_items_bought(username)
                conn.send(pickle.dumps(items_bought))

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
    conn_to_addr[conn] = addr[0]  # connection to ip address

    try:
        data = conn.recv(1024).decode('utf-8')
        print('Server received2: ', data)

        if data[-7:] == ':public':
            publicIdCount += 1
            p = 0
            gameId = (publicIdCount - 1)//2
            # privateGameId
            print('public id', publicIdCount)
            if publicIdCount % 2 == 1:
                games[gameId] = Game(gameId)
                game_id_to_players[gameId] = [conn]
                print(games)
                print("Creating a new public game...")
                games[gameId].p0_ready = True
                games[gameId].usernames[0] = data[:-7]
            else:
                # games[gameId].ready = True
                games[gameId].p1_ready = True
                game_id_to_players[gameId].append(conn)
                p = 1
                games[gameId].usernames[1] = data[:-7]
            start_new_thread(threaded_client, (conn, p, gameId, 'public'))

        elif data[-8:] == ':private':  # data == '[username]:private'
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
            colon_index = data.index(':')
            games[privateGameId] = Game(privateGameId)
            games[privateGameId].usernames[0] = data[:colon_index]
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
        elif ':P2_joined_' in data:  # p2 joined private game
            colon_index = data.index(':')
            try:
                this_game_id = int(data[colon_index+11:])
                p = 1
                if this_game_id in private_game_ids:
                    games[this_game_id].usernames[1] = data[:colon_index]
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
    except:
        pass
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

