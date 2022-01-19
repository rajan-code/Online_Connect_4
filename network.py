import socket
import pickle


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "170.187.181.231"
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

