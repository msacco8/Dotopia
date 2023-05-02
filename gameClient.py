import socket
import pygame
import pygame.freetype
import sys
import time
import struct
import math

MSG_SIZE = 1024

PREFIX_FORMAT = "!I"

class GameClient:

    def __init__(self, username):

        self.username = username

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.dt = 0

        self.accounts = {}

        self.powerUps = []
        

    def Connect(self, serverAddress):
        # connect to server from system arguments
        self.sock.connect((serverAddress, 6000))


    def CreateUser(self):
        opCode = "0"

        createUserPickle = (opCode + "|" + self.username).encode()

        # send message request to server and get response
        try:
            self.sock.send(createUserPickle)
        except:
            print("Error creating user")

        return
    
    def UpdateGameState(self):
        try:
            prefix = b""
            while len(prefix) == 0:
                prefix = self.sock.recv(4)
            messageLength = struct.unpack(PREFIX_FORMAT, prefix)[0]

            message = b""
            while len(message) < messageLength:
                chunk = self.sock.recv(messageLength - len(message))
                if not chunk:
                    raise RuntimeError("socket connection broken")
                message += chunk

            gameStateResponse = message.decode().strip()
            print(gameStateResponse)
            split = gameStateResponse.split("~")
            userInfo, powerUps = split[0].split("|"), split[1].split("|")
            self.accounts = {}
            self.powerUps = []

            for i in range(0, len(userInfo) - 1, 2):
                user = userInfo[i]
                vals = userInfo[i + 1].split(":")
                self.accounts[user] = {
                    "x": vals[0],
                    "y": vals[1],
                    "score": vals[2]
                }
            
            for i in range(0, len(powerUps) - 2, 3):
                self.powerUps.append({
                    "type": powerUps[i],
                    "x": powerUps[i+1],
                    "y": powerUps[i+2]
                })
                
        except:
            print("Error receiving game state")

    def Move(self, movementArray):
        opCode = "1"

        movementPickle = "".join(["1" if b else "0" for b in movementArray])

        moveRequest = (opCode + "|"  + self.username + "|" + movementPickle).encode()

        # send message request to server and get response
        try:
            self.sock.send(moveRequest)
        except:
            print("Error sending move request")

    # If collision with powerup is detected, send collision to server to apply and remove from game
    def ObtainPowerUp(self, powerUp):
        opCode = "2"
        print("here")
        powerUpRequest = (opCode + "|" + self.username + "|" + powerUp["type"] + "|" + powerUp["x"] + "|" + powerUp["y"]).encode()

        print(powerUpRequest)

        try:
            self.sock.send(powerUpRequest)
        except:
            print("Error sending powerup request")


    def Run(self):

        # pygame setup
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        clock = pygame.time.Clock()
        GAME_FONT = pygame.freetype.Font('freesansbold.ttf', 12)
        SCORE_FONT = pygame.freetype.Font('freesansbold.ttf', 48)
        dt = 0

        # player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
        # self.pos["x"] = player_pos.x
        # self.pos["y"] = player_pos.y

        # Send username to server
        self.CreateUser()

        while True:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    break

            self.UpdateGameState()

            # fill the screen with a color to wipe away anything from last frame
            screen.fill("black")

            # render each player
            for user in self.accounts.keys():
                userPos = pygame.Vector2(float(self.accounts[user]["x"]), float(self.accounts[user]["y"]))
                # print(userPos)
                pygame.draw.circle(screen, "white", userPos, 12)
                GAME_FONT.render_to(screen, (userPos.x - 12, userPos.y + 25), user, (255, 255, 255))
                if user == self.username:
                    SCORE_FONT.render_to(screen, (10, 10), "$" + self.accounts[user]["score"], (0, 255, 0))

            # handle powerups
            for powerUp in self.powerUps:

                # draw powerups on screen
                powerUpPos = pygame.Vector2(float(powerUp["x"]), float(powerUp["y"]))
                color = "green" if powerUp["type"] == "money" else "blue"
                pygame.draw.circle(screen, color, powerUpPos, 6)

                # print("x", self.accounts[str(self.username)]["x"])
                x1 = float(self.accounts[str(self.username)]["x"])
                y1 = float(self.accounts[str(self.username)]["y"])

                x2 = float(powerUp["x"])
                y2 = float(powerUp["y"])
                
                distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                if distance < 12 + 6:
                    print("here?")
                    self.ObtainPowerUp(powerUp)

                # handle powerUp collision
                # print(powerUpPos.x)
                # withinX = int(powerUp["x"]) - 9 < int(self.accounts[self.username]["x"]) and int(powerUp["x"]) + 9 > int(self.accounts[self.username]["x"])
                # withinY = int(powerUp["y"]) - 9 < int(self.accounts[self.username]["y"]) and int(powerUp["y"]) + 9 > int(self.accounts[self.username]["y"])
                
                # if withinX and withinY:
                #     print("here?")
                #     self.ObtainPowerUp(powerUp)

            # get dict of all pressed keys
            keys = pygame.key.get_pressed()

            # handle client movement
            movementArray = [keys[pygame.K_w], keys[pygame.K_s], keys[pygame.K_a], keys[pygame.K_d]]
            if True in movementArray:
                self.Move(movementArray)

            # flip() the display to put your work on screen
            pygame.display.flip()

            # limits FPS to 60
            # dt is delta time in seconds since last frame, used for framerate-
            # independent physics.
            # self.dt = clock.tick(60) / 1000

        # pygame.quit()

if __name__ == '__main__':
    try:
        serverAddress = sys.argv[1]
        username = input("please enter a username: ")
        client = GameClient(username)
        client.Connect(serverAddress)
        client.Run()
    except:
        print("Please try again and enter the server IP address as an argument.")


