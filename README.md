# Hapoel Beer Sheva Trivia Game 

## Description
This project implements a trivia game server focused on Hapoel Beer Sheva FC. The server interacts with clients over both TCP and UDP protocols, offering a multiplayer trivia experience where players answer questions about the football club Hapoel Beer Sheva.

## Features
- Supports multiple players connecting simultaneously.
- Utilizes TCP and UDP sockets for communication.
- Randomly generates trivia questions about Hapoel Beer Sheva FC.
- Tracks players' answers and determines the winner based on the number of correct answers.
- Can be configured to include bot players in the game lobby.

## Usage
1. Clone the repository to your local machine.
2. Ensure you have Python installed (version 3.6 or higher).
3. Open a terminal or command prompt and navigate to the project directory.
4. Run the server using the following command:
    ```
    python server.py
    ```
5. Players can connect to the server using the provided IP address and port number.
6. Enjoy playing the trivia game!

## Requirements
- Python 3.6 or higher

## Configuration
You can modify the following parameters in the `server.py` file:
- `magic_cookie`: The magic cookie value used for communication.
- `message_type`: The message type used for communication.
- `client_port`: The port number used for client connections.
- `server_name`: The name of the server.
- `bot_number`: The number of bot players to include in the game lobby.

## Additional Information (Client Module)

### Client Module Description
The client module includes functionality for connecting clients to the trivia game server. It provides classes and methods for finding the server, establishing a TCP connection, sending and receiving messages, and running the client application.

### Client Class
- `Client`: Represents a client connecting to the trivia game server. It includes methods for finding the server, connecting via TCP, sending answers, and running the client application.

### RealClient Class
- `RealClient`: Inherits from the `Client` class and represents a real player client. It includes additional methods for sending answers, handling game logic, and managing connections.

### BotClient Class
- `BotClient`: Inherits from the `Client` class and represents a bot player client. It includes methods for sending random answers and simulating game interactions.

### Usage
1. Import the `BotClient` class from the `client.py` module.
2. Create instances of the `BotClient` class for each bot player.
3. Run the bot client applications using separate threads.

