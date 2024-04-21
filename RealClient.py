import multiprocessing
import os
import random
import socket
import struct
import sys
import threading
import signal
import time
import json
from time import sleep
import socket
import Client
from Client import *
from multiprocessing import *
import keyboard
from select import *


ANSI_RED = "\u001b[31m"
ANSI_GREEN = "\u001b[32m"
ANSI_YELLOW = "\u001b[33m"
ANSI_RESET = "\u001b[0m"
ANSI_BLUE = "\u001b[34m"
ANSI_BOLD = "\u001b[1m"



import re


def remove_ansi_escape_codes(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class RealClient(Client):

    def __init__(self, num_of_bots=0):
        super().__init__()
        self.getting_answer_process = None
        self.num_of_bots = num_of_bots
        self.answer = None
        self.conn_failed = False

    def send_answer(self, q=None):
        answer_value = ''
        while True:
            try:
                # Receiving an answer from the user and stores it in the process queue
                self.answer = None
                self.answer = keyboard.read_key().upper()
                q.put(self.answer)
                # Checks if the client entered any input or is he still in the input step
                self.answer_entered = True
                # Converting the answer
                if self.answer in ['Y', 'T', '1']:
                    answer_value = 'True'
                    break
                elif self.answer in ['N', 'F', '0']:
                    answer_value = 'False'
                    break
                else:
                    print(ANSI_RED + "Invalid input. Please enter Y/T/1 for True or N/F/0 for False." + ANSI_RESET)
            except Exception:
                print(ANSI_RED + f'Player {self.Player_name} was disconnected.' + ANSI_RESET)
                break
        # Sending the answer to the server
        if self.answer_entered:
            self.TCP_socket.send(bytes(answer_value, 'utf8'))

    # Printing game statistic for the client
    def game_summary(self, round_played, streak):
        if (streak / round_played) == 1:
            summary_msg = f'{ANSI_GREEN}{ANSI_BOLD}Well done, you are a true fan{ANSI_RESET}'
        elif 0.5 <= (streak / round_played) < 1:
            summary_msg = f'{ANSI_BLUE}{ANSI_BOLD}Nice job, but im sure you could do better'
        else:
            summary_msg = f'{ANSI_RED}{ANSI_BOLD}Are you sure you are a fan of Hapoel Beer Sheva FC, maybe you should practice a bit more{ANSI_RESET}'
        print(f'{ANSI_GREEN}{ANSI_BOLD}Game summary: \n{ANSI_RESET}' + f'You got{ANSI_BOLD} {streak}/{round_played} \n{ANSI_RESET}' + f'{summary_msg}')

    # Resets the Parameters for the client for a new game
    def new_game_initialization(self):
        self.connected = False
        self.answer_entered = False
        self.lost = False
        self.conn_failed = False
        self.correct_answers_counter = 0

    # A thread that checks each time that during the input function if the client and the server are still connected
    def check_conn(self):
        while not self.conn_failed:
            try:
                self.TCP_socket.send(b'')
            except (ConnectionResetError,BrokenPipeError):
                # If we lost connection between the client and the server we will terminate the process
                self.getting_answer_process.terminate()
                break

    def run_client(self):
        round_played = 0
        while True:
            try:
                # Finding and connecting to a server
                if not self.connected:
                    self.find_server()
                    success = self.connect_server()
                    if not success:
                        continue
                    else:
                        self.lost = False
                        self.connected = True
                        round_played = 1
                # Receiving a message from the server and converts it to the right format
                msg = self.receive_message()
                msg_without_ansi = remove_ansi_escape_codes(msg)
                # Checks if the message is a question and the client didn't lose
                if "true or false" in msg_without_ansi.lower() and not self.lost:
                    print(msg)
                    # Check within it's the first question in the game or beyond
                    if 'round' in msg_without_ansi.lower():
                        round_played += 1
                        # Checks if the player is still in the game
                        if self.Player_name not in msg_without_ansi:
                            self.lost = True
                            continue
                        else:
                            self.lost = False
                    if not self.lost:
                        try:
                            # Creating a process for getting an answer
                            self.conn_failed = False
                            queue = multiprocessing.Queue()
                            self.getting_answer_process = multiprocessing.Process(target=self.send_answer, args=(queue,))
                            # A thread that suppose to check the connection during the running of the process
                            conn_thread = threading.Thread(target=self.check_conn)
                            conn_thread.start()
                            # self.getting_answer_thread = threading.Thread(target=self.send_answer)
                            # Setting a 10 seconds timeout for the process
                            self.getting_answer_process.start()
                            self.getting_answer_process.join(10)
                            # Checks after 10 seconds if we got an input from the client, if we got we will kill the
                            # thread that suppose to check the connection
                            if not queue.empty():
                                self.answer = queue.get()
                                self.conn_failed = True

                            # Checks if we lost connection with the server
                            elif not conn_thread.is_alive():
                                raise ConnectionResetError
                            else:
                                self.conn_failed = True

                            # If we didn't get an input and the connection is still stable it means that the client is still
                            # in the 'entering input' step but his 10 seconds are over so we want to interrupt this step
                            if self.answer is None:
                                raise KeyboardInterrupt
                            else:
                                self.answer = None
                        # Catches the interrupt and printing an informative message to the client
                        except KeyboardInterrupt:
                            print(f'{ANSI_RED}{ANSI_BOLD}Sorry, but you didnt answer in time{ANSI_RESET}')
                # Checks if the client answered correctly
                elif self.Player_name in msg_without_ansi and 'correct!' in msg_without_ansi.lower() and 'in' not in msg_without_ansi.lower():
                    self.correct_answers_counter += 1
                    print(msg)
                # Checks if the client answered incorrectly
                elif self.Player_name in msg_without_ansi and 'incorrect!' in msg_without_ansi.lower():
                    # self.lost = True
                    print(msg)
                # Checks if the game is over
                elif "game over" in msg_without_ansi.lower() or "all players left the game" in msg_without_ansi.lower():
                    print(msg)
                    self.game_summary(round_played, self.correct_answers_counter)
                    self.new_game_initialization()
                    sleep(4)
                else:
                    print(msg)
            # Catches any exception if our server been closed or terminated
            except (ConnectionResetError, KeyboardInterrupt) as e:
                if type(e) == ConnectionResetError:
                    print(f"{ANSI_RED}{ANSI_BOLD}Connection with the server was lost, trying to find a new lobby...{ANSI_RESET}")
                    self.new_game_initialization()
                else:
                    break
        sleep(2)


if __name__ == '__main__':
    client = RealClient()
    client.run_client()
