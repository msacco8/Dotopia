import socket
import pygame
import pygame.freetype
import sys
import time
import struct
import math
import threading
import json
import re

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

            gameStateResponse = message.decode().strip().split("~")
            # print(gameStateResponse)

            # Use regular expressions to extract user information and power-ups
            user_regex = r"(\w+)\|([\d.]+):([\d.]+):([\d.]+):([\d.]+)"
            powerup_regex = r"(\w+)\|([0-9\.]+)\|([0-9\.]+)"
            user_matches = re.findall(user_regex, gameStateResponse[0])
            powerup_matches = re.findall(powerup_regex, gameStateResponse[1])

            self.accounts = {}
            self.powerUps = []

            for match in user_matches:
                user, x, y, score, size = match
                self.accounts[user] = {
                    "x": x,
                    "y": y,
                    "score": score,
                    "size": size
                }

            for match in powerup_matches:
                powerup_type, x, y = match
                self.powerUps.append({
                    "type": powerup_type,
                    "x": x,
                    "y": y
                })

        except:
            print("Error receiving game state")
    
    # def UpdateGameState(self):
    #     try:
    #         prefix = b""
    #         while len(prefix) == 0:
    #             prefix = self.sock.recv(4)
    #         messageLength = struct.unpack(PREFIX_FORMAT, prefix)[0]

    #         message = b""
    #         while len(message) < messageLength:
    #             chunk = self.sock.recv(messageLength - len(message))
    #             if not chunk:
    #                 raise RuntimeError("socket connection broken")
    #             message += chunk

    #         gameStateResponse = message.decode().strip()
    #         # print(gameStateResponse)
    #         split = gameStateResponse.split("~")
    #         userInfo, powerUps = split[0].split("|"), split[1].split("|")
    #         self.accounts = {}
    #         self.powerUps = []

    #         for i in range(0, len(userInfo) - 1, 2):
    #             user = userInfo[i]
    #             vals = userInfo[i + 1].split(":")
    #             self.accounts[user] = {
    #                 "x": vals[0],
    #                 "y": vals[1],
    #                 "score": vals[2],
    #                 "size": vals[3]
    #             }
            
    #         for i in range(0, len(powerUps) - 2, 3):
    #             self.powerUps.append({
    #                 "type": powerUps[i],
    #                 "x": powerUps[i+1],
    #                 "y": powerUps[i+2]
    #             })
                
    #     except:
    #         print("Error receiving game state")

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
        # print("here")
        powerUpRequest = (opCode + "|" + self.username + "|" + powerUp["type"] + "|" + powerUp["x"] + "|" + powerUp["y"]).encode()

        # print(powerUpRequest)

        try:
            self.sock.send(powerUpRequest)
        except:
            print("Error sending powerup request")


    def Run(self):

        self.CreateUser()
        time.sleep(2)

        # pygame setup
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        clock = pygame.time.Clock()
        GAME_FONT = pygame.freetype.Font('freesansbold.ttf', 12)
        SCORE_FONT = pygame.freetype.Font('freesansbold.ttf', 48)
        END_FONT = pygame.freetype.Font('freesansbold.ttf', 128)
        dt = 0

        # get username from user
        screen.fill("black")

        while True:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit
            stateStartTime = time.time()
            self.UpdateGameState()
            stateEndTime = time.time()

            # fill the screen with a color to wipe away anything from last frame
            screen.fill("black")

            playerStartTime = time.time()
            # render each player
            for user in self.accounts.keys():
                
                if int(self.accounts[user]["size"]) > 10:
                    if user != self.username:
                        END_FONT.render_to(screen, (340, 300), "YOU LOST.", (255, 0, 0))
                    else:
                        END_FONT.render_to(screen, (340, 300), "YOU WIN!", (0, 255, 0))

                    pygame.display.update()
                    pygame.time.delay(10000)
                    pygame.quit()
                    sys.exit


                currSize = 5 * math.log(float(self.accounts[user]["size"]))
                userPos = pygame.Vector2(float(self.accounts[user]["x"]), float(self.accounts[user]["y"]))
                # print(userPos)
                pygame.draw.circle(screen, "white", userPos, currSize)
                GAME_FONT.render_to(screen, (userPos.x - 12, userPos.y + currSize + 12), user, (255, 255, 255))
                if user == self.username:
                    SCORE_FONT.render_to(screen, (10, 10), "$" + self.accounts[user]["score"], (0, 255, 0))
                # END_FONT.render_to(screen, (340, 300), "YOU WIN!", (0, 255, 0))

            playerEndTime = time.time()

            powerUpStartTime = time.time()
            # handle powerups
            for powerUp in self.powerUps:

                # draw powerups on screen
                powerUpPos = pygame.Vector2(float(powerUp["x"]), float(powerUp["y"]))

                if powerUp["type"] == "money":
                    color = "green"
                elif powerUp["type"] == "speed":
                    color = "blue"
                elif powerUp["type"] == "food":
                    color = "brown"

                pygame.draw.circle(screen, color, powerUpPos, 6)

                try:
                    x1 = float(self.accounts[self.username]["x"])
                    y1 = float(self.accounts[self.username]["y"])

                    x2 = float(powerUp["x"])
                    y2 = float(powerUp["y"])
                    
                    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                    currSize = 5 * math.log(float(self.accounts[self.username]["size"]))

                    if distance < currSize + 6:
                        self.ObtainPowerUp(powerUp)
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

            with open("timingLog2.txt", "a") as logs:
                timingObj = {
                    "updateGameState" : stateEndTime - stateStartTime,
                    "renderPlayers" : playerEndTime - playerStartTime,
                    "renderPowerUps" : powerUpEndTime - powerUpStartTime,
                    "handleMovement" : moveEndTime - moveStartTime
                }
                logs.write(json.dumps(timingObj) + "\n")

            # flip() the display to put your work on screen
            pygame.display.flip()

if __name__ == '__main__':
    try:
        serverAddress = sys.argv[1]
        username = input("Enter a username: ")
        client = GameClient(username)
        client.Connect(serverAddress)
        client.Run()
    except:
        print("Please try again and enter the server IP address as an argument.")


