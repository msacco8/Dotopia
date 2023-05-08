import socket
import threading
import random
import time
import struct
import json


# global constants
MSG_SIZE = 1024
PORT = 6000
PREFIX_FORMAT = "!I"
MOVE_SPEED = 3.
MAX_SPEED = 20
SPEED_JUMP = 3
START_SIZE = 3
WIDTH = 1280
HEIGHT = 720


class Server():
    '''
    Server side code for Dotopia
    '''
    def __init__(self):
        # store mapping from username to game data
        # stores each users x and y coordinates, score, and size
        self.accounts = {}

        # list of clients and respective sockets
        self.connections = {}

        # list of power ups which should be rendered
        self.powerUps = []

        # locks for multithreading support
        self.powerUpsLock = threading.Lock()
        self.accountsLock = threading.Lock()

        # server side socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def CreateUser(self, clientSocket, clientAddress, username):
        # deny users who are already signed in 
        if username in self.accounts:
            print("Error creating user -- username already taken.")
            clientSocket.close()
        # store relevant user data in the accounts dictionary and connections, random start position
        else:
            self.accounts[username] = {
                "x": random.randrange(50, 1230),
                "y": random.randrange(30, 690),
                "score": 0,
                "speed": MOVE_SPEED,
                "size": START_SIZE
            }
            self.connections[username] = (clientAddress, clientSocket)


    def Move(self, username, movementString):
        # array where indexes represent pressing down W A S D SPACE, in order
        movementArray = [True if x == "1" else False for x in movementString]
        currMoveSpeed = self.accounts[username]["speed"]

        xPos = self.accounts[username]["x"]
        yPos = self.accounts[username]["y"]

        # lock to handle multithreading
        # update x and y coordinates based on which of W A S D are pressed
        self.accountsLock.acquire()
        try:
            if movementArray[0] and yPos > 0:
                self.accounts[username]["y"] = round(yPos - currMoveSpeed, 2)
            if movementArray[1] and yPos < HEIGHT:
                self.accounts[username]["y"] = round(yPos + currMoveSpeed, 2)
            if movementArray[2] and xPos > 0:
                self.accounts[username]["x"] = round(xPos - currMoveSpeed, 2)
            if movementArray[3] and xPos < WIDTH:
                self.accounts[username]["x"] = round(xPos + currMoveSpeed, 2)
            # for user speeding up when money is spent
            # cap speed at 20 and make sure that the user has money to spend and money is decremented appropriately
            if movementArray[4]:
                if currMoveSpeed <= MAX_SPEED and self.accounts[username]["score"] > 0:
                    self.accounts[username]["speed"] = round(currMoveSpeed + 0.3, 2)
                    self.accounts[username]["score"] -= 1
        finally:
            self.accountsLock.release()

    
    def BroadcastGameState(self):
        # operating on its own thread, consistently broadcasting game thread
        while True:
            gameStatePickle = ''

            for user in self.accounts.keys():
                # if players have recently had a speed power up in any form, they should
                # be slowly decreasing back down towards the base speed
                if self.accounts[user]["speed"] > MOVE_SPEED:
                    self.accountsLock.acquire()
                    try:
                        self.accounts[user]["speed"] = round(self.accounts[user]["speed"] - 0.05, 2)
                    finally:
                        self.accountsLock.release()
                
                # accounts portion of the game state string
                # each user delimited by | and x, y, score, and size of user delimited by :
                gameStatePickle += (user + "|" + str(self.accounts[user]["x"]) + ":" + 
                                    str(self.accounts[user]["y"]) + ":" + str(self.accounts[user]["score"]) + ":" +
                                    str(self.accounts[user]["size"]) + "|")

            # sleed as to not clog the socket
            time.sleep(0.05)

            # power up portion of the game state string
            # power ups and their x and y coords are delimited by |
            gameStatePickle = gameStatePickle[:-1] + "~"
            for powerUp in self.powerUps:
                gameStatePickle += (powerUp["type"] + "|" + str(powerUp["x"]) + "|" + str(powerUp["y"]) + "|")

            # prefix the game state with the length of the message encoding so client can read
            # the appropriate amount of bytes
            gameStatePickle = gameStatePickle[:-1]
            prefix = struct.pack(PREFIX_FORMAT, len(gameStatePickle))

            # send the game state to all clients currently connected
            for _, socket in self.connections.values():
                socket.sendall(prefix + gameStatePickle.encode())

            # logs game states as json strings for debugging/visualization purposes
            with open("logs1.txt", "w") as logs:
                accounts_json = json.dumps(self.accounts)
                powerups_json = json.dumps(self.powerUps)
                logs.write(accounts_json + '\n' + powerups_json)


    def RenderPowerUps(self):
        # weighted probablities for each type of power up
        types = ["money", "speed", "food"]
        weights = (0.2, 0.5, 0.3)

        while True:
            # only render a new power up every 2 seconds, max of 30 on screen
            time.sleep(2)
            if len(self.powerUps) <= 30:
                self.powerUpsLock.acquire()
                try:
                    self.powerUps.append({
                        "type": random.choices(types, weights)[0],
                        "x": random.randrange(50, 1230),
                        "y": random.randrange(30, 690)
                    })
                finally:
                    self.powerUpsLock.release()


    def HandlePowerUpCollision(self, user, type, x, y):
        currPowerUp = {
            "type": type,
            "x": int(x),
            "y": int(y)
        }

        # lock for multithreading purposes
        self.powerUpsLock.acquire()
        try:
            # if player collided with a money power up, increase their score by 10
            if type == "money":
                self.accounts[user]["score"] += 10
            # increase user speed by 3 while adhering the current max speed limit
            elif type == "speed" and self.accounts[user]["speed"] <= MAX_SPEED - SPEED_JUMP:
                self.accounts[user]["speed"] += SPEED_JUMP
            # colliding with food increases size by 1
            elif type == "food":
                self.accounts[user]["size"] += 1

            # delete the current power up from the field by filtering it out of power ups list
            self.powerUps = list(filter(lambda x: x != currPowerUp, self.powerUps))

        finally:
            self.powerUpsLock.release()


    def ClientThread(self, clientSocket, clientAddress):
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
                    self.Move(clientRequest[1], clientRequest[2])
                if opCode == "2":
                    self.HandlePowerUpCollision(clientRequest[1], clientRequest[2], clientRequest[3], clientRequest[4])

        # remove client from accounts and connection list when they send 0 bytes
        for user, ((addr, port), _) in self.connections.items():
            if addr == clientAddress[0] and port == clientAddress[1]:
                print("User " + user + " at " + addr + ":" + str(port) + " disconnected")
                del self.accounts[user]
                del self.connections[user]
                break
        
        # clean up socket
        clientSocket.close()   


    def Listen(self):
        # bind socket to host address and port
        ADDR = socket.gethostbyname(socket.gethostname())
        self.sock.bind((ADDR, PORT))

        # become a server socket
        self.sock.listen(5)
        print("Listening on " + ADDR + ":" + str(PORT))

        # always be broadcasting game state separately from other processes
        gameStateThread = threading.Thread(target=self.BroadcastGameState)
        gameStateThread.start()

        # always be rendering power ups on screen separately from other processes
        powerUpThread = threading.Thread(target=self.RenderPowerUps)
        powerUpThread.start()

        while True:
            # accept connections from outside
            (clientSocket, clientAddress) = self.sock.accept()
            print(clientAddress[0] + ":" + str(clientAddress[1]) + ' connected!')

            # always be handling client user input separately from other processes
            clientThread = threading.Thread(target=self.ClientThread, args=(clientSocket, clientAddress))
            clientThread.start()


if __name__ == '__main__':
    # create new server object and run main control flow
    server = Server()
    server.Listen()