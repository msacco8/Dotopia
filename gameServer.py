import socket
import threading

MSG_SIZE = 1024
PORT = 6000

class Server():

    def __init__(self):

        # store mapping from username to messages
        self.accounts = {}

        # store mapping from username to address and port
        self.connections = {}

        self.pos = {
            "x": 640,
            "y": 360
        }

        # initialize server socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def Move(self, clientSocket, movementString):
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
            self.pos["y"] -= 1
        if movementArray[1]:
            self.pos["y"] += 1
        if movementArray[2]:
            self.pos["x"] -= 1
        if movementArray[3]:
            self.pos["x"] += 1


        moveResponse = "1" + "|" + str(self.pos["y"]) + "|" + str(self.pos["x"])

        print(moveResponse)
        try:
            clientSocket.send(moveResponse.encode())
        except:
            print("Error sending move response")
        return


    # def DeleteAccount(self, clientSocket, username):
    #     deleteAccountResponse = ''

    #     # deletes mapping from accounts to messages and returns success
    #     if username in self.accounts:
    #         del self.accounts[username]
    #         deleteAccountResponse = "1|" + username
    #         print("User " + username + " deleted.")
    #     # returns failure response in case that user does not exist
    #     else:
    #         deleteAccountResponse = "0|" + username
    #         print("Error deleting user " + username + ".")

    #     try:
    #         clientSocket.send(deleteAccountResponse.encode())
    #     except:
    #         print("Error sending delete account response")
    #     return

    # def ListAccounts(self, clientSocket, wildcard):
    #     listAccountsResponse = '1|'

    #     # adds each account that contains wildcard substring to response
    #     for account in self.accounts.keys():
    #         if wildcard in account:
    #             listAccountsResponse += account + "|"

    #     try:
    #         clientSocket.send(listAccountsResponse[:-1].encode())
    #     except:
    #         print("Error sending list accounts response")
    #     return

    # def LogIn(self, clientSocket, clientAddress, username):
    #     logInResponse = ''

    #     # checks if username exists and is not currently logged in
    #     if username in self.accounts and username not in self.connections:
    #         self.connections[username] = clientAddress
    #         logInResponse = "1|" + username
    #     # returns failure response otherwise
    #     else:
    #         logInResponse = "0|" + username

    #     try:
    #         clientSocket.send(logInResponse.encode())
    #     except:
    #         print("Error sending log in response")
    #     return

    # def CreateAccount(self, clientSocket, clientAddress, username):
    #     createAccountResponse = ''

    #     # verifies that user doesn't already exist
    #     if username not in self.accounts:
    #         # adds to both mappings from username to messages and addr/port
    #         self.connections[username] = clientAddress
    #         self.accounts[username] = []
    #         createAccountResponse = "1|" + username
    #     # returns failure response if user already exists
    #     else:
    #         createAccountResponse = "0|" + username
        
    #     clientSocket.send(createAccountResponse.encode())
    #     return

    # def GetMessages(self, clientSocket, username):

    #     # initialize response and number of MSG_SIZE messages to send
    #     responseBuilder = ''
    #     numMessages = 1

    #     # verify that user exists and that they have unread messages
    #     if username in self.accounts and self.accounts[username]:

    #         # add each message with pipe delimiter to response
    #         for sender, message in self.accounts[username]:
    #             responseBuilder += "|" + sender + "|" + message

    #         # calculate number of different MSG_SIZE chunks to send based on total message length
    #         numMessages = ((len(responseBuilder) + 2) // MSG_SIZE) + 1

    #         # append to front of message for client side to receive
    #         getMessagesResponse = str(numMessages) + responseBuilder

    #         # clear user's inbox
    #         self.accounts[username] = []

    #     else:
    #         getMessagesResponse = "0|"
        
    #     # initialize sent data counter
    #     totalSent = 0

    #     # send MSG_SIZE while there is data to be sent
    #     while totalSent < (numMessages * MSG_SIZE):
    #         toSend = ''

    #         # prepare remaining data if on last message
    #         if totalSent + MSG_SIZE > len(getMessagesResponse[totalSent:]):
    #             toSend = getMessagesResponse[totalSent:]

    #         # prepare MSG_SIZE chunk if not
    #         else:
    #             toSend = getMessagesResponse[totalSent:(totalSent + MSG_SIZE)]

    #         # send current chunk and increment sent counter
    #         try:
    #             sent = clientSocket.send(toSend.encode())
    #         except:
    #             print("Error sending chunk.")
    #         totalSent += MSG_SIZE
    #     return 

    # def SendMessage(self, clientSocket, sender, recipient, message):
    #     sendMessageResponse = ''

    #     # verify that recipient exists
    #     if recipient in self.accounts:
    #         # add message to messages list and return success response
    #         self.accounts[recipient].append([sender, message])
    #         sendMessageResponse = "1|" + recipient
    #     else:
    #         # return failure response if recipient doesn't exist
    #         sendMessageResponse = "0|" + recipient
    #     try:
    #         clientSocket.send(sendMessageResponse.encode())
    #     except:
    #         print("Error sending send message response")
    #     return

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

            clientThread= threading.Thread(target=self.ClientThread, args=(clientSocket, clientAddress))
            clientThread.start()

        self.sock.close()

    def ClientThread(self, clientSocket, clientAddress):

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
                    self.Move(clientSocket, clientRequest[1])
                #     self.LogIn(clientSocket, clientAddress, clientRequest[1])

                # elif opCode == "1":
                #     self.CreateAccount(clientSocket, clientAddress, clientRequest[1])
                
                # elif opCode == "2":
                #     self.SendMessage(clientSocket, clientRequest[1], clientRequest[2], clientRequest[3])

                # elif opCode == "3":
                #     self.GetMessages(clientSocket, clientRequest[1])

                # elif opCode == "4":
                #     self.ListAccounts(clientSocket, clientRequest[1])

                # elif opCode == "5":
                #     self.DeleteAccount(clientSocket, clientRequest[1])
                    
        # remove client from connection list when they send 0 bytes
        for user, (addr, port) in self.connections.items():
            if addr == clientAddress[0] and port == clientAddress[1]:
                print("User " + user + " at " + addr + ":" + str(port) + " disconnected")
                del self.connections[user]
                break
        clientSocket.close()   

if __name__ == '__main__':
    server = Server()
    server.Listen()