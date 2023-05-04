import socket
import threading
import random
import time
import struct
import json

MSG_SIZE = 1024
PORT = 6000
PREFIX_FORMAT = "!I"
MOVE_SPEED = 3.
START_SIZE = 3
WIDTH = 1280
HEIGHT = 720

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
                "score": 0,
                "speed": MOVE_SPEED,
                "size": START_SIZE
            }
            self.connections[username] = (clientAddress, clientSocket)


    def Move(self, clientSocket, username, movementString):
        movementArray = [True if x == "1" else False for x in movementString]
        currMoveSpeed = self.accounts[username]["speed"]

        xPos = self.accounts[username]["x"]
        yPos = self.accounts[username]["y"]

        if movementArray[0] and yPos > 0:
            self.accounts[username]["y"] = round(self.accounts[username]["y"] - currMoveSpeed, 2)
        if movementArray[1] and yPos < HEIGHT:
            self.accounts[username]["y"] = round(self.accounts[username]["y"] + currMoveSpeed, 2)
        if movementArray[2] and xPos > 0:
            self.accounts[username]["x"] = round(self.accounts[username]["x"] - currMoveSpeed, 2)
        if movementArray[3] and xPos < WIDTH:
            self.accounts[username]["x"] = round(self.accounts[username]["x"] + currMoveSpeed, 2)
        if movementArray[4]:
            if self.accounts[username]["speed"] <= 20 and self.accounts[username]["score"] > 0:
                self.accounts[username]["speed"] = round(self.accounts[username]["speed"] + 0.3, 2)
                self.accounts[username]["score"] -= 1

    
    def BroadcastGameState(self):
        # "user1|x:y|user2|x:y"
        while True:
            gameStatePickle = ''
            for user in self.accounts.keys():
                if self.accounts[user]["speed"] > MOVE_SPEED:
                    self.accounts[user]["speed"] = round(self.accounts[user]["speed"] - 0.05, 2)
                    
                gameStatePickle += (user + "|" + str(self.accounts[user]["x"]) + ":" + 
                                    str(self.accounts[user]["y"]) + ":" + str(self.accounts[user]["score"]) + ":" +
                                    str(self.accounts[user]["size"]) + "|")

            time.sleep(0.05)

            gameStatePickle = gameStatePickle[:-1] + "~"

            for powerUp in self.powerUps:
                gameStatePickle += (powerUp["type"] + "|" + str(powerUp["x"]) + "|" + str(powerUp["y"]) + "|")

            gameStatePickle = gameStatePickle[:-1]
            prefix = struct.pack(PREFIX_FORMAT, len(gameStatePickle))

            for _, socket in self.connections.values():
                socket.sendall(prefix + gameStatePickle.encode())

            with open("logs1.txt", "w") as logs:
                accounts_json = json.dumps(self.accounts)
                powerups_json = json.dumps(self.powerUps)
                logs.write(accounts_json + '\n' + powerups_json)


    def RenderPowerUps(self):
        types = ["money", "speed", "food"]
        weights = (0.2, 0.5, 0.3)

        while True:
            time.sleep(2)
            if len(self.powerUps) <= 30:
                self.powerUps.append({
                    "type": random.choices(types, weights)[0],
                    "x": random.randrange(50, 1230),
                    "y": random.randrange(30, 690)
                })

    def HandlePowerUpCollision(self, clientSocket, user, type, x, y):
        
        currPowerUp = {
            "type": type,
            "x": int(x),
            "y": int(y)
        }
        # handle types of powerups
        if type == "money":
            # update score?
            self.accounts[user]["score"] += 10
        
        elif type == "speed" and self.accounts[user]["speed"] <= 17:
            self.accounts[user]["speed"] += 3

        elif type == "food":
            self.accounts[user]["size"] += 1

        self.powerUps = list(filter(lambda x: x != currPowerUp, self.powerUps))


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
                
                if opCode == "2":
                    self.HandlePowerUpCollision(clientSocket, clientRequest[1], clientRequest[2], clientRequest[3], clientRequest[4])

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