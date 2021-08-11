import socket
import random
from _thread import *
import pickle
from connect_4_game import Game
import pygame

pygame.init()

server = ""
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clients = []

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
print("Waiting for a connection, Server Started")

connected = set()
games = dict()  # used for public and private games
game_id_to_players = dict()  # used for public and private games
private_game_ids = set()  # set of ints
publicIdCount = 0
privateIdCount = 1000

"""
class Server:
    def __init__(self):
        self.clients = []  # 
        self.names = [] # List[str]
    
    def broadcast(self, message: bytes):
        for client in self.clients:
            client.send(message)
"""


def threaded_client(conn, p: int, gameId: int, game_type: str):
    global publicIdCount
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
            print('Server received1: ', data)

            if gameId in games:
                game = games[gameId]
                print('here1')
              #  if not game.is_running:
                  #  game.run()

                if not data2:
                    break
                else:
                    # data = conn.recv(1024*4).decode()
                    if data2 == "reset":
                        # game.resetWent()
                        pass
                    elif 'ready' in data2:
                        if data2[1] == '0':
                            game.p0_ready = True
                        else:
                            game.p1_ready = True
                        game.ready = game.p0_ready and game.p1_ready
                    elif 'left' in data2:  # a user is no longer searching for opponent
                        the_player = int(data2[1])
                        if the_player == 0:
                            game.p0_ready = False
                        else:
                            game.p1_ready = False
                        game.ready = game.p0_ready and game.p1_ready
                    elif data2 == 'get':
                        print('using pickle')
                        # size = len(pickle.dumps(game, -1))
                        # print('size of picked obj:', size)
                        print(game.id, 'aq')
                        print(len(pickle.dumps(game, -1)))
                        conn.sendall(pickle.dumps(game))
                        print('Server sent game.')
                        print('is game connected', game.connected())
                    elif len(data2) == 3 and data2[1] == ':' and (data2[0] == '0' or data2[0] == '1'):  # received player:column
                        turn, col = int(data2[0]), int(data2[2])
                        the_row = game.get_next_open_row(col)
                        msg = data2[0] + ':(' + str(the_row) + ',' + str(col) + ')'  # format: turn:(row,col)
                        for client in game_id_to_players[gameId]:
                            client.sendall(msg.encode('utf-8'))  # send to both clients
                        # conn.sendall(str.encode(msg))
                        print('Server sent:', msg)
                        print(game.print_board(game.board))

                        game.drop_piece(the_row, col, turn + 1)
                        if game.is_winner(1):  # if the game is over
                            print(game.print_board(game.board))
                            print('Player 1 has won the game!')
                            game.score[0] += 1
                            msg = 'P0_WON'
                            for client in game_id_to_players[gameId]:
                                client.sendall(msg.encode('utf-8'))  # send to both clients
                            print('Server sent:', msg)
                            # TODO

                        elif game.is_winner(2):
                            print(game.print_board(game.board))
                            print('Player 2 has won the game!')
                            game.score[1] += 1
                            msg = 'P1_WON'
                            for client in game_id_to_players[gameId]:
                                client.sendall(msg.encode('utf-8'))  # send to both clients
                            print('Server sent:', msg)

                        else:  # game is not over yet
                            # p += 1
                            # p = p % 2  # 0 if turn is even, else 1
                            not_p = int(not p)
                            msg = str(not_p) + '_move'  # ask other player for move
                            for client in game_id_to_players[gameId]:
                                client.sendall(str.encode(msg))
                            print('Server sent:', msg)
                    # else:
                       # conn.sendall(pickle.dumps(game))

            else:
                break
        except:
            break

    print("Lost connection")
    try:
        del games[gameId]
        print("Closing Game", gameId)
    except:
        pass
    publicIdCount -= 1  # only if game was public
    conn.close()


while True:
    # pygame.display.quit()
    conn, addr = s.accept()
    clients.append(conn)
    print('Clients:', clients)
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
