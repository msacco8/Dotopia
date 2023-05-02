import socket
import pygame
import pygame.freetype
import sys

MSG_SIZE = 1024

class GameClient:

    def __init__(self, username):

        self.username = username

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.dt = 0

        self.pos = {
            "x": 0,
            "y": 0
        }

        self.accounts = []

        self.players = []

    def Connect(self, serverAddress):

        # connect to server from system arguments
        self.sock.connect((serverAddress, 6000))

    def CreateUser(self):
        opCode = "0"

        createUserPickle = (opCode + "|" + self.username).encode()

        # send message request to server and get response
        try:
            print("hello")
            self.sock.send(createUserPickle)
        except:
            print("Error creating user")

        return
    
    def UpdateGameState(self):

        try:
            gameStateResponse = self.sock.recv(MSG_SIZE).decode().strip().split("|")
            for i in range(0, len(gameStateResponse) - 1):
                user = gameStateResponse[i]
                pos = gameStateResponse[i + 1].split(":")
                self.accounts[user] = {
                    "x" : pos[0],
                    "y" : pos[1]
                }
        except:
            print("Error receiving game state")


    def Move(self, movementArray):
        opCode = "1"

        movementPickle = "".join(["1" if b else "0" for b in movementArray])
        print(movementPickle)
        # dtPickle = "{:.2f}".format(dt)

        # moveRequest = (opCode + "|"  + movementPickle + "|" + dtPickle).encode()
        moveRequest = (opCode + "|"  + self.username + "|" + movementPickle).encode()

        # send message request to server and get response
        try:
            self.sock.send(moveRequest)
        except:
            print("Error sending move request")

        try:
            moveResponse = self.sock.recv(MSG_SIZE).decode().strip().split("|")
        except:
            print("Error receiving move response")

        print(moveResponse)
        # reflect success status to client
        if moveResponse[0] == "1":
            # print(int(moveResponse[1]))
            try:
                self.pos["y"] = moveResponse[1]
                self.pos["x"] = moveResponse[2]
                # print(self.pos["x"])
            except:
                print(self.pos['x'])
                print("exception")

            # print("move success")
        else:
            print("move fail")

        # print("got here")
        return
    
    def Run(self):

        # pygame setup
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        clock = pygame.time.Clock()
        GAME_FONT = pygame.freetype.Font('freesansbold.ttf', 12)
        running = True
        dt = 0

        # player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
        # self.pos["x"] = player_pos.x
        # self.pos["y"] = player_pos.y

        # Send username to server
        self.CreateUser()

        while running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # GET OTHER PLAYERS POSITIONS
            # for player in self.players:
            #     pygame.draw.circle(screen, "white", )
            self.UpdateGameState()

            # fill the screen with a color to wipe away anything from last frame
            screen.fill("black")

            for user in self.accounts:
                userPos = pygame.Vector2(float(user["x"]), float(user["y"]))
                pygame.draw.circle(screen, "white", userPos, 5)
                GAME_FONT.render_to(screen, (userPos.x - 10, userPos.y + 20), user, (255, 255, 255))

            keys = pygame.key.get_pressed()
            movementArray = [keys[pygame.K_w], keys[pygame.K_s], keys[pygame.K_a], keys[pygame.K_d]]
            if True in movementArray:
                # self.Move(movementArray, self.dt)
                # print("here")
                self.Move(movementArray)
                # player_pos.x = float(self.pos["x"])
                # player_pos.y = float(self.pos["y"])

            
            print(player_pos.x)

            # text_surface, rect = GAME_FONT.render("Hello World!", (0, 0, 0))
            # screen.blit(text_surface, (40, 250))
            # GAME_FONT.render_to(screen, (player_pos.x - 10, player_pos.y + 20), username, (255, 255, 255))

            # flip() the display to put your work on screen
            pygame.display.flip()
            # print("hey")

            # limits FPS to 60
            # dt is delta time in seconds since last frame, used for framerate-
            # independent physics.
            # self.dt = clock.tick(60) / 1000

        pygame.quit()

if __name__ == '__main__':
    try:
        serverAddress = sys.argv[1]
        username = input("please enter a username: ")
        client = GameClient(username)
        client.Connect(serverAddress)
        client.Run()
    except:
        print("Please try again and enter the server IP address as an argument.")


