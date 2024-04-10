import socket
import struct
import threading
import time
import concurrent.futures
import random
import multiprocessing
import scapy.all
from struct import pack
import random
import sys
global send_offer_checker
send_offer_checker = True
global questions
from scapy.arch import get_if_addr

questions = [("q1", "T"), ("q2", "F"), ("q3", "T"), ("q4", "T"), ("q5", "F"), ("q6", "T"), ("q7", "F"), ("q8", "T"), ("q9", "T"), ("q10", "F"), ("q11", "T"), ("q12", "F"), ("q13", "T"), ("q14", "F"), ("q15", "T"), ("q16", "T"), ("q17", "F"), ("q18", "T"), ("q19", "F"), ("q20", "F")]
class Server:
    def __init__(self, magic_cookie, message_type, server_port, client_port):
        self.MAGIC_COOKIE = magic_cookie
        self.MESSAGE_TYPE = message_type
        self.server_port = server_port
        self.client_port = client_port
        #TODO: check ip adress
        self.ip_address = get_if_addr('eth1')
        # self.ip_address = "172.1.0.4"
        self.players = {}
        self.active_players = {}
        self.bot_number = 0
        self.bot_list = []
        try:
            self.TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.TCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.TCP.bind(('', self.server_port))
        except socket.error:
            print("")
            exit()

    def send_offers(self):
        messege = pack('IbH', self.MAGIC_COOKIE, self.MESSAGE_TYPE, self.server_port)
        print(f"Server started,listening on IP address {self.ip_address}")
        last_player_time = 0
        while send_offer_checker:
            UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            UDP_socket.bind(('',5000))
            UDP_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            UDP_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            UDP_socket.sendto(msg, ("<broadcast>", self.client_port))
            sleep(1)

    def Client_connect(self):
        self.TCP.listen()
        last_player_time = 0
        while last_player_time < 10:
            time_start = time.time()
            try:
                # TODO: DUPLICATE FOR BOTS
                client_socket, (client_ip, client_port) = self.tcp_socket.accept()
                player_name = str(client_socket.recv(1024), 'utf8')
                self.players[client_socket]= (player_name,client_ip, client_port)
                last_player_time = time.time() - time_start
                if last_player_time < 10:
                    send_offer_checker = False
                else:
                    print(f"Player {player_name} connected.\n")
            except Exception as e:
                #TODO: CHECK THE EXCEPT
                print(f'Unable to connect to client.' + str(e))
        self.bot_number = random.randint(1, sys.maxsize)

    def send_to_player(self, player_socket, msg,question=True):
        try:
            player_socket.sendall(bytes(msg, 'utf-8'))
            if question:
                player_socket.settimeout(10)
        except Exception as e:
            print(f"Error occurred while sending to player: {e}")

    def send_to_all_players(self, msg,question=True):
        threads = []
        for player_socket in self.players.keys():
            thread = threading.Thread(target=self.send_to_player, args=(player_socket, msg,question))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
    def get_answer(self, player_socket,true_answer):
        try:
            answer = player_socket.recv(1024).decode('utf-8')
            # Process the answer received from the player
            if answer == true_answer:
                self.active_players[player_socket] = self.players[player_socket]
                print(f"{self.players[player_socket][0]} is correct!")
            else:
                print(f"{self.players[player_socket][0]} is incorrect!")
        except socket.timeout:
            print(f"{self.players[player_socket][0]} is incorrect!")

    def ask_questions(self,question,answer):
        msg = f"True or false :{question[0]} "
        self.send_to_all_players(msg,True)
        answer_threads = []
        self.active_players = {}
        for player_socket in self.players.keys():
            thread = threading.Thread(target=self.get_answer, args=(player_socket,answer))
            answer_threads.append(thread)
            thread.start()

        for thread in answer_threads:
            thread.join()

    def start_game(self):
        welcome_message = "Welcome to the HBS Trivia Game server, where we are answering trivia questions about Hapoel Beer Sheva FC.\n"
        player_number = 1
        for player in self.players.items():
            welcome_message += f"Player {player_number}: {player[0]}\n"
            player_number += 1
        welcome_message += "==\n"
        send_to_all_players(welcome_message,False)
        copy_questions = copy.deepcopy(questions)
        # self.active_players = copy.deepcopy(self.players)
        available_player_counter = len(self.players)
        question_counter = 1
        while available_player_counter > 1:
            if question_counter != 1:
                msg = f"Round {question_counter}, played by"
                for player in self.active_players.items():
                    msg += f" {player[0]} and"
                msg = msg[:-4] + ":"
                print(msg)
            question, answer = random.choice(copy_questions)
            copy_questions.remove((question,answer))
            self.ask_questions(question,answer)
            available_player_counter = len(self.active_players)
            question_counter += 1
        # print(f"{self.players[player_socket][0]} Wins!")
        msg = "Game over!\n" + f"Congratulations to the winner: {next(iter(self.active_players.values()))[0]}"
        send_to_all_players(msg,False)
        print(msg)

    def active_server(self):

        while True:
            t1 = threading.Thread(target=self.send_offers)
            t2 = threading.Thread(target=self.Client_connect)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            self.start_game()
            sleep(2)

if __name__ == '__main__':
    # TODO: check what is the real server port !
    server = Server(magic_cookie=0xabcddcba, message_type=0x02, server_port=4567, client_port=1337)
    server.active_server()

