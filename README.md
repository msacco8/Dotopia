# Design Documentation and Engineering Notebook

Project done by John Minicus and Michael Sacco

## Dotopia: A Distributed Online Multiplayer Game

Dotopia uses only the Python standard library

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

## Gameplay Mechanics

## Client Architecture

## Server Architecture
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
