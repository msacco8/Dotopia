import socket
import pygame
import pygame.freetype
import sys
import time
import struct
import math
import re


# global constants
MSG_SIZE = 1024
PREFIX_FORMAT = "!I"
WINNING_SIZE = 10


class GameClient:
    '''
    Client side code for Dotopia
    '''
    def __init__(self, username):
        # current user
        self.username = username

        # client side socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # client side recreation of the accounts from global game state
        self.accounts = {}

        # client side recreation of the power ups from global game state
        self.powerUps = []
        

    def Connect(self, serverAddress):
        # connect to server from system arguments
        self.sock.connect((serverAddress, 6000))

    
    def UpdateGameState(self):
        try:
            # receive prefix packed by server side which tells the client how long the message is
            prefix = b""
            while len(prefix) == 0:
                prefix = self.sock.recv(4)
            messageLength = struct.unpack(PREFIX_FORMAT, prefix)[0]

            # use info from prefix to receive exactly the length of the message
            message = b""
            while len(message) < messageLength:
                chunk = self.sock.recv(messageLength - len(message))
                if not chunk:
                    raise RuntimeError("socket connection broken")
                message += chunk

            # split game state string into accounts portion and power ups portion
            gameStateResponse = message.decode().strip().split("~")

            # use regular expressions to extract user information and power-ups
            user_regex = r"(\w+)\|([\d.]+):([\d.]+):([\d.]+):([\d.]+)"
            powerup_regex = r"(\w+)\|([0-9\.]+)\|([0-9\.]+)"
            user_matches = re.findall(user_regex, gameStateResponse[0])
            powerup_matches = re.findall(powerup_regex, gameStateResponse[1])

            # clear previous game state before continuing
            self.accounts = {}
            self.powerUps = []

            # updating state of all players currently in arena
            for match in user_matches:
                user, x, y, score, size = match
                self.accounts[user] = {
                    "x": x,
                    "y": y,
                    "score": score,
                    "size": size
                }

            # updating state of all power ups which should be rendered
            for match in powerup_matches:
                powerup_type, x, y = match
                self.powerUps.append({
                    "type": powerup_type,
                    "x": x,
                    "y": y
                })
        except:
            print("Error receiving game state")


    def CreateUser(self):
        # encode new user request with an opcode so server knows what to do with it
        opCode = "0"
        createUserPickle = (opCode + "|" + self.username).encode()

        # send message request to server and get response
        try:
            self.sock.send(createUserPickle)
        except:
            print("Error creating user")


    def Move(self, movementArray):
        # encode the True/False array for key pressing into 0s and 1s so it can be sent as bytes
        opCode = "1"
        movementPickle = "".join(["1" if b else "0" for b in movementArray])
        moveRequest = (opCode + "|"  + self.username + "|" + movementPickle).encode()

        try:
            self.sock.send(moveRequest)
        except:
            print("Error sending move request")


    def ObtainPowerUp(self, powerUp):
        # if collision with powerup is detected, send collision to server to apply and remove from game
        opCode = "2"
        powerUpRequest = (opCode + "|" + self.username + "|" + powerUp["type"] + "|" + powerUp["x"] + "|" + powerUp["y"]).encode()

        try:
            self.sock.send(powerUpRequest)
        except:
            print("Error sending powerup request")


    def Run(self):
        # give server time to register new user
        self.CreateUser()
        time.sleep(2)

        # general pygame setup -- screen size and color, default fonts
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        GAME_FONT = pygame.freetype.Font('freesansbold.ttf', 12)
        SCORE_FONT = pygame.freetype.Font('freesansbold.ttf', 48)
        END_FONT = pygame.freetype.Font('freesansbold.ttf', 128)
        screen.fill("black")

        while True:
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit

            stateStartTime = time.time()
            # always be updating from local game state on each new frame
            self.UpdateGameState()
            stateEndTime = time.time()

            # clears last frame
            screen.fill("black")

            playerStartTime = time.time()
            for user in self.accounts.keys():
                # check to see if any user, specifically the current user, is over the winning size
                if int(self.accounts[user]["size"]) > WINNING_SIZE:
                    if user != self.username:
                        END_FONT.render_to(screen, (340, 300), "YOU LOST.", (255, 0, 0))
                    else:
                        END_FONT.render_to(screen, (340, 300), "YOU WIN!", (0, 255, 0))

                    # display end-game text and exit after 10 seconds
                    pygame.display.update()
                    pygame.time.delay(10000)
                    pygame.quit()
                    sys.exit

                # drawing the users at their current size with nametag under circle
                currSize = 5 * math.log(float(self.accounts[user]["size"]))
                userPos = pygame.Vector2(float(self.accounts[user]["x"]), float(self.accounts[user]["y"]))
                pygame.draw.circle(screen, "white", userPos, currSize)
                GAME_FONT.render_to(screen, (userPos.x - 12, userPos.y + currSize + 12), user, (255, 255, 255))
                
                # display money counter in top left corner
                if user == self.username:
                    SCORE_FONT.render_to(screen, (10, 10), "$" + self.accounts[user]["score"], (0, 255, 0))

            playerEndTime = time.time()
            powerUpStartTime = time.time()

            for powerUp in self.powerUps:
                # draw powerups on screen with correct color
                powerUpPos = pygame.Vector2(float(powerUp["x"]), float(powerUp["y"]))
                if powerUp["type"] == "money":
                    color = "green"
                elif powerUp["type"] == "speed":
                    color = "blue"
                elif powerUp["type"] == "food":
                    color = "brown"
                pygame.draw.circle(screen, color, powerUpPos, 6)

                # handling collisions between player and power up
                try:
                    x1 = float(self.accounts[self.username]["x"])
                    y1 = float(self.accounts[self.username]["y"])
                    x2 = float(powerUp["x"])
                    y2 = float(powerUp["y"])
                    
                    # math for box detection
                    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    currSize = 5 * math.log(float(self.accounts[self.username]["size"]))
                    if distance < currSize + 6:
                        self.ObtainPowerUp(powerUp)

                # occasionally will get floating point errors which we dont want to break the game
                except:
                    pass
                
            powerUpEndTime = time.time()

            # get dict of all pressed keys
            keys = pygame.key.get_pressed()

            moveStartTime = time.time()

            # handle client movement
            movementArray = [keys[pygame.K_w], keys[pygame.K_s], keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_SPACE]]
            if True in movementArray:
                self.Move(movementArray)

            moveEndTime = time.time()

            # uncomment for timing game loop processes
            '''
            with open("./logs/timingLog2.txt", "a") as logs:
                timingObj = {
                    "updateGameState" : stateEndTime - stateStartTime,
                    "renderPlayers" : playerEndTime - playerStartTime,
                    "renderPowerUps" : powerUpEndTime - powerUpStartTime,
                    "handleMovement" : moveEndTime - moveStartTime
                }
                logs.write(json.dumps(timingObj) + "\n")
            '''

            # flip() the display to put your work on screen
            pygame.display.flip()


if __name__ == '__main__':
    try:
        # make sure that the user enters the correct IP address as an arg to the command line
        serverAddress = sys.argv[1]
        username = input("Enter a username: ")
        client = GameClient(username)
        client.Connect(serverAddress)
        client.Run()
    except:
        print("Please try again and enter the server IP address as an argument.")


