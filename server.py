import socket
from _thread import *
import pickle
from connect_4_game import Game
import pygame

pygame.init()

server = ""
# server = "139.177.194.104"
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
games = dict()
game_id_to_players = dict()
idCount = 0

"""
class Server:
    def __init__(self):
        self.clients = []  # 
        self.names = [] # List[str]
    
    def broadcast(self, message: bytes):
        for client in self.clients:
            client.send(message)
"""


def threaded_client(conn, p: int, gameId: int):
    global idCount
    conn.send(str.encode(str(p)))
    print('Server sent:', str(p))
    msg = '0_move'
    conn.send(msg.encode('utf-8'))
    print('Server sent:', msg)
    reply = ""

    while True:
        try:
        # peek = conn.recv(1024*4, socket.MSG_PEEK).decode('utf-8')
            data = conn.recv(1024 * 4).decode()
        # data = conn.recv(1024).decode()
            print('Server received: ', data)

            if gameId in games:
                game = games[gameId]
                print('here1')
              #  if not game.is_running:
                  #  game.run()

                if not data:
                    break
                else:
                    # data = conn.recv(1024*4).decode()
                    if data == "reset":
                        # game.resetWent()
                        pass
                    elif 'ready' in data:
                        if data[1] == '0':
                            game.p0_ready = True
                        else:
                            game.p1_ready = True
                        game.ready = game.p0_ready and game.p1_ready
                    elif 'left' in data:  # a user is no longer searching for opponent
                        the_player = int(data[1])
                        if the_player == 0:
                            game.p0_ready = False
                        else:
                            game.p1_ready = False
                        game.ready = game.p0_ready and game.p1_ready
                    elif data == 'get':
                        print('using pickle')
                        # size = len(pickle.dumps(game, -1))
                        # print('size of picked obj:', size)
                        print(game.id, 'aq')
                        conn.sendall(pickle.dumps(game))
                        print('Server sent game.')
                        print('is game connected', game.connected())
                    elif len(data) == 3 and data[1] == ':' and (data[0] == '0' or data[0] == '1'):  # received player:column
                        turn, col = int(data[0]), int(data[2])
                        the_row = game.get_next_open_row(col)
                        msg = data[0] + ':(' + str(the_row) + ',' + str(col) + ')'  # format: turn:(row,col)
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
                    else:
                        conn.sendall(pickle.dumps(game))

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
    idCount -= 1
    conn.close()


while True:
    # pygame.display.quit()
    conn, addr = s.accept()
    clients.append(conn)
    print('Clients:', clients)
    print("Connected to:", addr)

    idCount += 1
    p = 0
    gameId = (idCount - 1)//2
    if idCount % 2 == 1:
        games[gameId] = Game(gameId)
        game_id_to_players[gameId] = [conn]
        print(games)
        print("Creating a new game...")
        games[gameId].p0_ready = True
    else:
        # games[gameId].ready = True
        games[gameId].p1_ready = True
        game_id_to_players[gameId].append(conn)
        p = 1

    start_new_thread(threaded_client, (conn, p, gameId))