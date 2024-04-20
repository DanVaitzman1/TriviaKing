import copy
import socket
import struct
import threading
import time
from time import sleep
from struct import pack
import multiprocessing
import random
import sys
import concurrent
import concurrent.futures
import Client
from Client import *
from BotClient import *
from enum import Enum

ANSI_RED = "\u001b[31m"
ANSI_GREEN = "\u001b[32m"
ANSI_YELLOW = "\u001b[33m"
ANSI_RESET = "\u001b[0m"
ANSI_BOLD = "\u001b[1m"
ANSI_BLUE = "\u001b[34m"

questions = [
    ('Alona Barkat is the owner of Hapoel Beer Sheva', "True"),
    ('Hapoel Beer Sheva has 11 state cups', "False"),
    ("Hapoel Beer Sheva's first championship was in 1967", "False"),
    ('Hapoel Beer Sheva has 5 championships', "True"),
    ('Hapoel Beer Sheva participated in the group stage of the Champions League', "False"),
    ('The coach of Hapoel Beer Sheva is Eliniv Barda', "True"),
    ('In the past, Hapoel Beer Sheva played against Barcelona', "True"),
    ("The Hapoel Beer Sheva fan organization is called Ultra South", "True"),
    ('Hapoel Beer Sheva plays at Vasermil Stadium', "False"),
    ('Uri Malmilian played for Hapoel Beer Sheva', "True"),
    ('Eli Lahav purchased Hapoel Beer Sheva from Alona Barkat', "False"),
    ('Hapoel Beer Sheva won 3 consecutive championships', "True"),
    ('Hapoel Beer Sheva has never won the Toto Cup of the Leomit League', "False"),
    ('Hapoel Beer Sheva holds 5 state cups', "True"),
    ('Hapoel Beer Sheva was established in 1949', "True"),
    ('Hapoel Beer Sheva are called "the monkeys"', "False"),
    ('Hapoel Beer Sheva played in an enterprise called the UEFA Intertoto Cup', "True"),
    ("Hapoel Beer Sheva's record of home victories per season stands at 16 games", "True"),
    ("Hapoel Beer Sheva's biggest loss of all time was to Barcelona and the result was 7-0", "False"),
    ('The greatest conqueror in the history of Hapoel Beer Sheva is Shalom Avitan', "True")]

player_names = [
    "dan vaitzman",
    "gila mida",
    "nir damti",
    "eli kopter",
    "meri dol",
    "shira haron",
    "eti paron",
    "beni vdal",
    "sami saviv",
    "micha napo",
    "beti pool",
    "lea ki",
    "avi ron",
    "simha rif",
    "beri tzakala",
    "beki tzur",
    "guy biton",
    "ido dai",
    "yafa lula",
    "ezra hut",
    "udi ber",
    "uzi mer",
    "beni mus",
    "alma nedaber",
    "micha far",
    "adi j",
    "tim sorli",
    "miki drer",
    "beni huta",
    "simon ne",
    "lora zita",
    "micha tampo"
]

def get_ip_address():
    # Get the IP address of the machine where the server is running
    try:
        # Create a temporary socket to get the IP address
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))  # Connect to Google's DNS server
        ip_address = temp_socket.getsockname()[0]
        temp_socket.close()
        return ip_address
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "127.0.0.1"  # Default to localhost if unable to retrieve IP address


def formatted_answer(answer):
    if answer in ['t', 'y', '1']:
        answer = 'true'
    elif answer in ['n', 'f', '0']:
        answer = 'false'
    return answer


class Server:

    def __init__(self, magic_cookie, message_type, client_port, server_name, bot_number=0):
        self.MAGIC_COOKIE = magic_cookie
        self.MESSAGE_TYPE = message_type
        self.client_port = client_port
        self.server_name = server_name.ljust(32)[:32]
        self.server_port = random.randint(1024, 49151)
        self.players = {}
        self.active_players = {}
        self.player_answers = {}
        self.connected_players = []
        if bot_number == 0:
            self.bot_number = random.randint(1, 3)
        else:
            self.bot_number = bot_number
        self.num_of_left_clients = 0
        self.still_receiving_offers = True
        self.at_least_one_correct = False
        self.enough_players_to_start = False
        self.game_round = 1
        self.non_conn_issue_players = 0
        self.current_record = None
        try:
            # Defines the TCP socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.ip_address = get_ip_address()
            self.tcp_socket.bind(('', self.server_port))
        except socket.error:
            print("")
            exit()

    def send_offers(self):
        msg = pack('IbH32s', self.MAGIC_COOKIE, self.MESSAGE_TYPE, self.server_port, self.server_name.encode('utf-8'))
        print(ANSI_GREEN+f"Server started, listening on IP address {ANSI_BLUE+ANSI_BOLD+self.ip_address}" + ANSI_RESET)
        while self.still_receiving_offers or not self.enough_players_to_start:
            # Create UDP socket
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Allows the socket to send broadcast messages. it will send the message to all the clients in the network.
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Allows the socket to reuse a local address and port combination that is already in use by another socket.
            # We are using that to bind multiple sockets to the same address and port.
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Bind the client with the server address
            udp_socket.bind((self.ip_address, self.client_port))
            # Sends the message in broadcast
            udp_socket.sendto(msg, ("<broadcast>", self.client_port))
            sleep(1)

    def client_connect(self):
        self.tcp_socket.listen()
        while True:
            try:
                client_socket, (client_ip, client_port) = self.tcp_socket.accept()
                self.tcp_socket.settimeout(10)
                player_name = str(client_socket.recv(1024), 'utf8')
                self.players[client_socket] = (player_name, client_ip, client_port)
                self.active_players[client_socket] = (player_name, client_ip, client_port)
                self.connected_players.append(client_socket)
                print(ANSI_GREEN+f"{ANSI_BOLD+player_name} connected."+ANSI_RESET)
            except socket.timeout:
                # Resembles that 10 seconds were past since our last player who joined
                self.still_receiving_offers = False
                # Checks at the end of the waiting time that the players who joined are still connected to the server
                for player_socket in self.connected_players:
                        self.send_message_to_player(player_socket, '')
                self.non_conn_issue_players = len(self.players)
                # Checks if all the real clients who joined in the first wave left at the end of the first wave,
                # or at the end of the second wave we have at least more than one real client in the lobby
                if len(self.players) == 0 or len(self.connected_players) - self.num_of_left_clients == self.bot_number:
                    self.tcp_socket.settimeout(None)
                    print(ANSI_GREEN+f"Not enough players, Keep looking for players to start a lobby..." + ANSI_RESET)
                    continue
                # Checks if we have enough players to start a game
                elif len(self.players) > 1:
                    self.enough_players_to_start = True
                    break
                else:
                    break
            except Exception as e:
                # TODO: CHECK THE EXCEPT
                print(ANSI_RED+f"Player is unable to connect.\n"+ANSI_RESET)

    def send_message_to_player(self, player_socket, msg):
        try:
            player_socket.sendall(bytes(msg, 'utf-8'))
        except (ConnectionResetError, BrokenPipeError):
            # If we lost connection with one of the clients we will remove him from the game
            if self.players.get(player_socket) is not None:
                print(ANSI_RED + f'{ANSI_BOLD + self.players[player_socket][0]} left the lobby.' + ANSI_RESET)
                self.players.pop(player_socket, 0)
                self.active_players.pop(player_socket, 0)
                self.num_of_left_clients += 1

    def send_question_to_player(self, player_socket, question):
        try:
            player_socket.sendall(bytes(question, 'utf-8'))
        except Exception as e:
            if self.active_players.get(player_socket) is not None:
                # If we lost connection with one of the clients we will remove him from the game
                print(ANSI_RED+f"{ANSI_BOLD+self.players[player_socket][0]}  failed to receive question. \n"+ANSI_RESET)
                self.players.pop(player_socket, 0)
                self.active_players.pop(player_socket, 0)


    def send_to_all_players(self, msg, function):
        threads = []
        for player_socket in self.players.keys():
            thread = threading.Thread(target=function, args=(player_socket, msg))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def get_answer(self, player_socket, correct_answer):
        sum_correct_answers = 0
        try:
            answer = player_socket.recv(1024).decode('utf-8').lower()
            answer = formatted_answer(answer)
            if self.player_answers.get(player_socket) is not None:
                sum_correct_answers = self.player_answers[player_socket][1]
            else:
                sum_correct_answers = 0
            # Process the answer received from the player
            if answer == correct_answer.lower():
                msg = ANSI_GREEN+ANSI_BOLD+f"{ANSI_BOLD+self.players[player_socket][0]} is correct!"+ANSI_RESET              
                self.player_answers[player_socket] = (True, sum_correct_answers + 1)
                self.at_least_one_correct = True
            else:
                msg = ANSI_RED+f"{ANSI_BOLD+self.players[player_socket][0]} is incorrect!"+ANSI_RESET
                self.player_answers[player_socket] = (False, sum_correct_answers)
        except (socket.timeout, ConnectionResetError) as e:
            if type(e) == socket.timeout:
                msg = ANSI_RED+f"{ANSI_BOLD+self.players[player_socket][0]} is incorrect!"+ANSI_RESET
                self.player_answers[player_socket] = (False, sum_correct_answers)
            else:
                msg = ANSI_RED+f'{ANSI_BOLD+self.players[player_socket][0]} left the game.'+ANSI_RESET
                self.active_players.pop(player_socket, 0)
                self.players.pop(player_socket, 0)
                self.non_conn_issue_players -= 1
        sleep(0.2)
        print(msg)
        self.send_message_to_player(player_socket, msg)

    def ask_questions(self, question, answer, rnd_msg):
        q = f"{ANSI_GREEN}True{ANSI_RESET} {ANSI_BOLD}or{ANSI_RESET}{ANSI_RESET} {ANSI_RED}false{ANSI_RESET}:{question} "
        round_i_q = rnd_msg + q
        print(round_i_q + '\n')
        sleep(0.05)
        self.send_to_all_players(round_i_q, self.send_question_to_player)
        answer_threads = []
        for player_socket in self.active_players.keys():
            player_socket.settimeout(10)  # Setting a timeout here

        for player_socket in self.active_players.keys():
            thread = threading.Thread(target=self.get_answer, args=(player_socket, answer))
            answer_threads.append(thread)

        for thread in answer_threads:
            thread.start()

        for thread in answer_threads:
            thread.join()

    def remove_player(self):
        if self.at_least_one_correct:
            for player, game_info in self.player_answers.items():
                if not game_info[0]:
                    self.active_players.pop(player, 0)

    def clean_game(self):
        self.players = {}
        self.active_players = {}
        self.player_answers = {}
        self.still_receiving_offers = True
        self.enough_players_to_start = False
        self.at_least_one_correct = False
        self.tcp_socket.settimeout(None)
        self.game_round = 1
        self.connected_players = []
        self.num_of_left_clients = 0

    def send_welcome_message(self):
        sleep(1)
        players_in_lobby_message = ANSI_BOLD + f"Welcome to the {self.server_name.rstrip()} Trivia Game server, where we are answering trivia questions about{ANSI_RED} Hapoel Beer Sheva FC.{ANSI_RESET} \n"
        player_number = 1
        for player in self.active_players.values():
            players_in_lobby_message += f"{ANSI_BLUE}Player {player_number}: {player[0]} \n"
            player_number += 1
        players_in_lobby_message += "== \n"
        # sleep(0.05)
        return players_in_lobby_message

    def send_round_starts_message(self):
        player_counter = 0
        if self.game_round != 1:
            msg = f"{ANSI_BLUE}Round {ANSI_BOLD}{self.game_round}{ANSI_RESET},{ANSI_BLUE} played by {ANSI_RESET}"
            for player in self.active_players.values():
                player_counter += 1
                if player_counter < len(self.active_players):
                    msg += f"{ANSI_BLUE} {player[0]} and {ANSI_RESET}"
                else:
                    msg += f"{ANSI_BLUE}{player[0]}{ANSI_RESET}:"
            msg += "\n"
            # sleep(0.05)
            return msg
        else:
            return self.send_welcome_message()

    def send_end_game_message(self):
        end_game_message = ''
        player_socket = ""
        player_info = ""
        # Checks if we have any player in the game and try to extract his info
        if len(self.active_players) > 0:
            player_socket, player_info = next(iter(self.active_players.items()))
        # Scenario where all the players left during the game
        if len(self.active_players) == 0:
            end_game_message = f"{ANSI_RED}All players left the game. No winner for this Game."
            sleep(0.05)
        # Scenario where all the players left during the game except from one player
        elif self.non_conn_issue_players == 1:
            end_game_message = f"{ANSI_GREEN}{ANSI_BOLD}Game over!\n{ANSI_RESET}" + f"{ANSI_RED} Unfortunately all the players left the game except {ANSI_RESET}{ANSI_YELLOW}{player_info[0]}{ANSI_RESET}, {ANSI_GREEN}Congratulations to the winner: {ANSI_BOLD}{next(iter(self.active_players.values()))[0]}{ANSI_RESET}\n"
            sleep(0.05)
        # Checks if at least one of the two last players was right
        elif self.at_least_one_correct and len(self.active_players) == 1:
            end_game_message = f"{ANSI_GREEN}{ANSI_BOLD}Game over!\n" + f"Congratulations to the winner: {player_info[0]}{ANSI_RESET} \n"
            sleep(0.05)
        # Checks if the winner is a real player and then compares his current score to the server record and updates
        # the record if needed
        if player_info[0] in player_names:
            if self.current_record is None:
                self.current_record = (player_info[0], self.player_answers[player_socket][1])
                end_game_message += f"{ANSI_GREEN}{ANSI_BOLD}" + f"Congrats {player_info[0]} just broke the server record!!{ANSI_RESET} \n"
            elif self.current_record[1] < self.player_answers[player_socket][1]:
                self.current_record = (player_info[0], self.player_answers[player_socket][1])
                end_game_message += f"{ANSI_GREEN}{ANSI_BOLD}" + f"Congrats {player_info[0]} just broke the server record!!{ANSI_RESET} \n"
        self.send_to_all_players(end_game_message, self.send_message_to_player)
        print(end_game_message)
        if len(self.active_players) != 0 and self.current_record is not None:
            print(ANSI_YELLOW + f'This server all time record belongs to {ANSI_BOLD}{self.current_record[0]}{ANSI_RESET}{ANSI_YELLOW} with {ANSI_BOLD}{self.current_record[1]}{ANSI_RESET}{ANSI_YELLOW} correct answers in a single game {ANSI_RESET} \n')

    def start_game(self):
        try:
            copy_questions = copy.deepcopy(questions)
            while len(self.active_players) > 1:
                self.at_least_one_correct = False
                # sleep(0.5)
                # getting the right message to send to the players
                intro_msg = self.send_round_starts_message()
                if len(copy_questions) == 0:
                    copy_questions = copy.deepcopy(questions)
                # Randomly choosing a question to ask the players
                question, answer = random.choice(copy_questions)
                # Removing the chosen question, so it couldn't be picked again in this game
                copy_questions.remove((question, answer))
                # sleep(0.5)
                self.ask_questions(question, answer, intro_msg)
                self.game_round += 1
                # removing the incorrect players from the active players list (if needed)
                self.remove_player()
            sleep(0.5)
            self.send_end_game_message()
            # Resets some of the server data to start a new game
            self.clean_game()
        except KeyboardInterrupt:
            print(ANSI_RED + "Server was terminated by the host" + ANSI_RESET)
    ###########################################################
    # Our other option of the structure of the code
    # The run server function without including the bots inside
    ###########################################################
    # def run_server(self):
    #     try:
    #         while True:
    #             t1 = threading.Thread(target=self.send_offers)
    #             t2 = threading.Thread(target=self.client_connect)
    #             t1.start()
    #             t2.start()
    #             t1.join()
    #             t2.join()
    #             self.start_game()
    #             sleep(2)
    #     except KeyboardInterrupt:
    #         print(ANSI_RED + "Server was terminated by the host" + ANSI_RESET)

    def run_server(self):
        try:
            bots = []
            while True:
                # real clients connecting server
                sending_offers_thread = threading.Thread(target=self.send_offers)
                connecting_real_clients_thread = threading.Thread(target=self.client_connect)
                sending_offers_thread.start()
                connecting_real_clients_thread.start()
                connecting_real_clients_thread.join()

                # checks if the server's lobby contains one real player
                if len(self.players) == 1:

                    # starting to connect bots to the client's lobby
                    connecting_bots_thread = threading.Thread(target=self.client_connect)
                    connecting_bots_thread.start()

                    for i in range(self.bot_number):
                        name = f'BOT {i + 1}'
                        bot = BotClient(is_bot=True, name=name)
                        thread = threading.Thread(target=bot.run_client)
                        thread.start()
                        bots.append(thread)

                    # sending_offers_bots_thread.join()
                    sending_offers_thread.join()
                    connecting_bots_thread.join()

                    # starting the game
                    game_thread = threading.Thread(target=self.start_game)
                    game_thread.start()

                    # game ends
                    game_thread.join()

                    for bot in bots:
                        bot.join()

                    sleep(2)
                else:
                    sending_offers_thread.join()
                    self.start_game()
                    sleep(2)

        except KeyboardInterrupt:
            print(ANSI_RED + "Server was terminated by the host" + ANSI_RESET)


if __name__ == "__main__":
    port = random.randint(1024, 49151)
    server = Server(magic_cookie=0xabcddcba, message_type=0x02, client_port=13117, server_name="HBS", bot_number=4)
    server.run_server()
