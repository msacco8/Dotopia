import socket
import threading
import random
import time
import struct

MSG_SIZE = 1024
PORT = 6000
PREFIX_FORMAT = "!I"
MOVE_SPEED = 3

class Server():

    def __init__(self):

        # accounts[username][connection] = ip address
        # accounts[username][pos] = position
        # store mapping from username to game data
        self.accounts = {}

        self.connections = {}

        self.powerUps = []

        # initialize server socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def CreateUser(self, clientSocket, clientAddress, username):
        if username in self.accounts:
            print("Error creating user -- username already taken.")
            clientSocket.close()
        else:
            # store relevant user data in the accounts dictionary, random start position
            self.accounts[username] = {
                "x": random.randrange(50, 1230),
                "y": random.randrange(30, 690),
                "score": 0
            }
            self.connections[username] = (clientAddress, clientSocket)


    def Move(self, clientSocket, username, movementString):
        movementArray = [True if x == "1" else False for x in movementString]

        if movementArray[0]:
            self.accounts[username]["y"] -= MOVE_SPEED
        if movementArray[1]:
            self.accounts[username]["y"] += MOVE_SPEED
        if movementArray[2]:
            self.accounts[username]["x"] -= MOVE_SPEED
        if movementArray[3]:
            self.accounts[username]["x"] += MOVE_SPEED
    
    
    def BroadcastGameState(self):
        # "user1|x:y|user2|x:y"
        while True:
            gameStatePickle = ''
            for user in self.accounts.keys():
                gameStatePickle += (user + "|" + str(self.accounts[user]["x"]) + ":" + 
                                    str(self.accounts[user]["y"]) + ":" + str(self.accounts[user]["score"]) + "|")

            time.sleep(0.05)

            gameStatePickle = gameStatePickle[:-1] + "~"

            for powerUp in self.powerUps:
                gameStatePickle += (powerUp["type"] + "|" + str(powerUp["x"]) + "|" + str(powerUp["y"]) + "|")

            gameStatePickle = gameStatePickle[:-1]
            prefix = struct.pack(PREFIX_FORMAT, len(gameStatePickle))

            for _, socket in self.connections.values():
                socket.sendall(prefix + gameStatePickle.encode())


    def RenderPowerUps(self):
        types = ["money", "speed"]

        while True:
            time.sleep(5)
            self.powerUps.append({
                "type": random.choice(types),
                "x": random.randrange(50, 1230),
                "y": random.randrange(30, 690)
            })


    def Listen(self):

        # bind socket to host address and port
        ADDR = socket.gethostbyname(socket.gethostname())
        self.sock.bind((ADDR, PORT))

        # become a server socket
        self.sock.listen(5)
        print("Listening on " + ADDR + ":" + str(PORT))

        gameStateThread = threading.Thread(target=self.BroadcastGameState)
        gameStateThread.start()

        powerUpThread = threading.Thread(target=self.RenderPowerUps)
        powerUpThread.start()

        while True:
            # accept connections from outside
            (clientSocket, clientAddress) = self.sock.accept()
            print(clientAddress[0] + ":" + str(clientAddress[1]) + ' connected!')

            clientThread = threading.Thread(target=self.ClientThread, args=(clientSocket, clientAddress))
            clientThread.start()

        self.sock.close()

    def ClientThread(self, clientSocket, clientAddress):

        # Store mapping from user to address and port
        # Store mapping from user to attributes (pos for now) 

        # receive MSG_SIZE until 0 bytes are received and exit control loop
        while True:
            try:
                clientRequest = clientSocket.recv(MSG_SIZE).decode()
            except:
                break
            if clientRequest:
                # scan request string by pipe delimiter
                clientRequest = clientRequest.strip().split("|")

                # first element of request determines the action called by client
                opCode = clientRequest[0]

                if opCode == "0":
                    self.CreateUser(clientSocket, clientAddress, clientRequest[1])

                if opCode == "1":
                    self.Move(clientSocket, clientRequest[1], clientRequest[2])
                #     self.LogIn(clientSocket, clientAddress, clientRequest[1])

        # remove client from connection list when they send 0 bytes
        for user, ((addr, port), _) in self.connections.items():
            if addr == clientAddress[0] and port == clientAddress[1]:
                print("User " + user + " at " + addr + ":" + str(port) + " disconnected")
                del self.accounts[user]
                del self.connections[user]
                break
        clientSocket.close()   


if __name__ == '__main__':
    server = Server()
    server.Listen()