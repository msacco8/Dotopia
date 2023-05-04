# Design Documentation and Engineering Notebook

Project done by John Minicus and Michael Sacco

## Dotopia: A Distributed Online Multiplayer Game

Dotopia uses the Python standard library and the pygame library.

To run the client and server. make sure that the two terminals are on the same network and that you have are in the root directory of 'Dotopia'. Then, run:

```bash
python3 gameServer.py
```

This will display the IP address and port that the server is listening on in the terminal. Use the IP address as a command line argument when running the client to connect to the server.

```bash
python3 client.py <server IP address>
```

Once connected, the client will prompt the user for a username and then open the game window.

To run the Client and Server tests enter the following commands in the root directory.

Client:
```bash
python3 gameClientTests.py
```

Server:
```bash
python3 gameServerTests.py
```

To aggregate the client timing logs enter the following command in the root directory.

```bash
python3 timing.py
```

## Gameplay Design

Each player is comprised of a circle of variable size and a text element for their username. Each powerup is a circle of fixed size and color based on the type of power up. Red powerups represent food, which increases the radius of the player logarithmically. Green powerups increase the amount of money you have, which is denoted by a green text element in the top left corner. Money can be used by holding the space bar, which will linearly increase the player's speed for each dollar spent. Blue powerups increase the player speed by a constant amount, to a certain ceiling limit. Players can move around the map using the W, A, S, D keys. Players must race to increase their size to a defined value by collecting powerups, in which the game ends. When the game ends, players will be notified of their status and the window will exit after a short duration.

## Client Architecture

The client-side of the online multiplayer game system is responsible for handling user inputs, sending requests to update the game state, and rendering the game. The architecture of the client application can be divided into four main components: network communication, game state management, rendering, and user input.

Network Communication:
The network communication component of the client application is responsible for establishing a connection with the server and exchanging messages between the client and the server. The client uses a socket object to connect to the server using the TCP protocol and sends and receives messages using the send() and recv() methods, respectively.

The client uses a message format that includes an opcode and arguments separated by a delimiter (“|”). The opcode indicates the type of message, such as creating a user, moving the player, or obtaining a powerup. The arguments include the username, movement array, powerup type, and coordinates.

Game State Management:
The game state management component of the client application is responsible for storing and updating the game state received from the server. The game state includes information about each player's position, size, and score, as well as the location of powerups. The client uses a 4 byte prefix in order to determine the message length of the incoming game state from the server. Once obtained, the client socket receives bytes until the entire length of the message has been received. This was an improvement over our messaging center wire protocol as it allows for messages to be sent in quick succession, without clogging the socket and receiving partial information. This is absolutely necessary for the game as messages are broadcasted from the server to all clients every 0.05 seconds. The client receives the game state as a string of concatenated messages and uses regular expressions to parse the user information and powerup information.

The parsed information is stored in two dictionaries, accounts, and powerUps. The accounts dictionary stores information about each player, and the powerUps dictionary stores information about each powerup's location and type. The two objects are delimited by a '~' character and then parsed separately based on their format. The powerups object contains the fields type, and coordinates each delimited by '|'. Since each powerup is guaranteed to have three fields, this is the only delimiter necessary. The player object contains user information in the form 'user|x:y:score:size'.

Rendering:
The rendering component of the client application is responsible for displaying the game graphics on the user's screen. The client uses the Pygame library to create and update the game's graphics. The graphics include the player's circles, powerup icons, and player score. The Pygame freetype module is used to render fonts for the game. Additionally, the rendering loop checks the position of the user against the positions of the powerups to handle collisions. When a collision is detected, an event is dispatched to the server to update the state of the player and the powerups, which is then broadcasted to all clients.

User Input:
The user input component of the client application is responsible for handling user input, such as moving the player's circle. The client uses the Pygame event module to poll for user input, and the movement array is updated based on the user's input. If thee movement array reflects the pressing of any allowed keys, a move operation will be dispatched to the server to update the game state and broadcast to all clients.

Overall, the client-side architecture is designed to be scalable, flexible, and fault-tolerant. The client sends and receives messages using a well-defined message format, which makes it easy to extend the functionality of the client and server. The use of regular expressions to parse the game state information and dictionaries to store the information makes it easy and more efficient to update the game state. The Pygame library provides a powerful and flexible graphics engine for rendering the game, and the event module makes it easy to handle user input. The client application is fault-tolerant in the sense that it can handle errors when sending and receiving messages and when parsing the game state information.

## Server Architecture

The server is designed to handle multiple clients simultaneously. It communicates with clients using a TCP socket.

The server creates a socket object and listens to a port for incoming connections. When a client connects to the server, the server accepts the connection and creates a thread to handle the client. The thread is responsible for receiving messages from the client and calling appropriate methods on the server to handle the request. The server is constantly receiving bytes from each client until a message is received, and the message is deconstructed into its operation code and arguments. The server then calls methods to update the game state based on the following operation codes that are received.

"0" - CreateUser(clientSocket, clientAddress, username) - updates game state by creating a new user
"1" - Move(clientSocket, username, movementString) - updates game state based on user and the keys that they are currently pressing
"2" - HandlePowerUpCollision(clientSocket, user, type, x, y) - updates game state based on user, and the type and position of the powerup they collided with

The server stores the user data in a dictionary named "accounts". This dictionary contains information about each user such as their username, current position, score, speed, and size. When a new user is created, the server adds a new key-value pair to the "accounts" dictionary. Additionally, powerups are stored in a list for rendering each powerup to each client's game window.

The server has a "BroadcastGameState" method that sends the current state of the game to all connected clients. This method runs in a separate thread and is responsible for sending updates to clients every 50 milliseconds. The current state of the game includes the position, score, speed, and size of each user as well as the location of all power-ups on the game board.

The server also has a "RenderPowerUps" method that runs in a separate thread and is responsible for creating new power-ups at random locations on the game board. The method checks the number of power-ups present on the game board and creates new power-ups if the number is less than or equal to 30.

The server has a method named "HandlePowerUpCollision" that is dispatched by the client when a user collides with a power-up. This method updates the user's score, speed, or size based on the type of power-up and removes the power-up from the game board.

The "Move" method takes into account an array based on the keys pressed and either alters the position of the player or increases their speed in the case that the space bar is pressed.

"RenderPowerUps", "Move" and "HandlePowerUpCollision" handle thread safety by acquiring locks before they update their respective objects. Even though it was a rare occurrence, through testing we found that occasionally when broadcasting the game state we would receive an error indicating that a dictionary was modified while being accessed. The acquiring of locks prior to modifying the game state objects resolves this issue by causing the functions that attempt to read objects being modified to sleep until the lock is released. This created a more robust gaming environment that can handle edge cases like this.

The server logs the current state of the game every 50 milliseconds to a file named "logs1.txt". The log file contains the current state of the "accounts" dictionary and the "powerUps" list. Overall, the server is designed to handle multiple clients and maintain the state of the game. It provides methods to create new users, move users, handle power-up collisions, and broadcast the current state of the game to all connected clients.

## Extra
Overview:

Brief discussion of:
What we built
Client/server architecture
Wire protocol
Distributed computing concepts that we focused on

Game Mechanics:

Client:

Dispatch events (discuss wire protocol for each):
CreateUser
Move
ObtainPowerUp
UpdateGameState
Wire protocol discussion
Receive 4 byte header to get message length
Receiving bytes until message is length described in header
Split message into the two objects that make up the game state
Split each object into fields based on object type
Update local objects to reflect new game state
Main game loop
Renders each element of game state to client screen
Checks conditions to dispatch events
Powerup collision - ObtainPowerUp
State of pressed keys - Move

Server:
Broadcast thread
Powerup thread
Thread for each client
