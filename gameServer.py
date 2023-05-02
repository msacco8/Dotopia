import socket
import threading
import random

MSG_SIZE = 1024
PORT = 6000

class Server():

    def __init__(self):

        # accounts[username][connection] = ip address
        # accounts[username][pos] = position
        # store mapping from username to game data
        self.accounts = {}

        self.connections = {}

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
                "y": random.randrange(30, 690)
            }
            self.connections[username] = (clientAddress, clientSocket)


    def Move(self, clientSocket, username, movementString):
        moveResponse = ''

        # dt = float(dtString)

        print(movementString)
        movementArray = [True if x == "1" else False for x in movementString]
        print(movementArray)

        # if movementArray[0]:
        #     self.pos["y"] -= 300 *dt
        # if movementArray[1]:
        #     self.pos["y"] += 300 *dt
        # if movementArray[2]:
        #     self.pos["x"] -= 300 *dt
        # if movementArray[3]:
        #     self.pos["x"] += 300 *dt
        if movementArray[0]:
            self.accounts[username]["y"] -= 1
        if movementArray[1]:
            self.accounts[username]["y"] += 1
        if movementArray[2]:
            self.accounts[username]["x"] -= 1
        if movementArray[3]:
            self.accounts[username]["x"] += 1


        moveResponse = "1" + "|" + str(self.accounts[username]["y"]) + "|" + str(self.accounts[username]["x"])

        print(moveResponse)
        print(self.accounts)
        print(self.connections)
        try:
            clientSocket.send(moveResponse.encode())
        except:
            print("Error sending move response")
        return
    
    
    def BroadcastGameState(self):
        # "user1|x:y|user2|x:y"
        gameStatePickle = ''
        for user in self.accounts.keys():
            gameStatePickle += user + "|" + str(self.accounts[user]["x"]) + ":" + str(self.accounts[user]["y"]) + "|"

        gameStatePickle = gameStatePickle[:-1]
        print(gameStatePickle)

        self.sock.send(gameStatePickle.encode())


    def Listen(self):

        # bind socket to host address and port
        ADDR = socket.gethostbyname(socket.gethostname())
        self.sock.bind((ADDR, PORT))

        # become a server socket
        self.sock.listen(5)
        print("Listening on " + ADDR + ":" + str(PORT))

        while True:
            # accept connections from outside
            (clientSocket, clientAddress) = self.sock.accept()
            print(clientAddress[0] + ":" + str(clientAddress[1]) + ' connected!')

            clientThread = threading.Thread(target=self.ClientThread, args=(clientSocket, clientAddress))
            clientThread.start()

            self.BroadcastGameState()

        self.sock.close()

    def ClientThread(self, clientSocket, clientAddress):

        # Store mapping from user to address and port
        # Store mapping from user to attributes (pos for now) 

        # receive MSG_SIZE until 0 bytes are received and exit control loop
        while True:
            clientRequest = clientSocket.recv(MSG_SIZE).decode()
            if not clientRequest:
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