import configparser
import hashlib
import multiprocessing
import re
import uuid
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
import abc
import select

ANSI_RED = "\u001b[31m"
ANSI_GREEN = "\u001b[32m"
ANSI_YELLOW = "\u001b[33m"
ANSI_RESET = "\u001b[0m"
ANSI_BLUE = "\u001b[34m"
ANSI_BOLD = "\u001b[1m"

def get_mac():
    mac = uuid.getnode()
    mac_str = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])
    mac = mac_str.replace(':', '')
    # Remove any non-hexadecimal characters from the MAC address
    formatted_mac = re.sub(r'[^a-fA-F0-9]', '', mac)
    return formatted_mac


def load(filename, config):
    config.read(filename)


def save(filename, config):
    with open(filename, 'w') as configfile:
        config.write(configfile)


def set_client_name(config, client_id, name):
    if not config.has_section('Clients'):
        config.add_section('Clients')
    if not config.has_option('Clients', client_id):
        config.set('Clients', client_id, name)


def get_client_name(config, client_id):
    if config.has_section('Clients') and client_id in config['Clients']:
        return config.get('Clients', client_id)
    else:
        return None


class Client(abc.ABC):

    def __init__(self, magic_cookie=0xabcddcba, message_type=0x02, client_port=13117, is_bot=False, Player_name=None):
        self.MAGIC_COOKIE = magic_cookie
        self.MESSAGE_TYPE = message_type
        self.server_ip = None
        self.server_port = None
        self.server_name = None
        self.TCP_socket = None
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.client_identifier = get_mac()
        self.is_bot = is_bot
        # Check if the type of the player is a bot
        if self.is_bot:
            self.Player_name = Player_name
        else:
            # If not, we are looking for the MAC address of the client in the configuration file
            load('clients.ini', self.config)
            # If this MAC address isn't there we are adding a new pair of MAC address and a name, and removing the chosen
            # name from the available names in the name list in the configuration file
            if get_client_name(self.config, self.client_identifier) is None:
                self.Player_name = random.choice(list(self.config['Names']))
                name = str(self.Player_name)
                set_client_name(self.config, self.client_identifier, name)
                self.config['Names'].pop(name)
                save('clients.ini', self.config)
            else:
                self.Player_name = get_client_name(self.config, self.client_identifier)
        self.client_port = client_port
        self.connected = False
        self.answer_entered = False
        self.lost = False
        self.correct_answers_counter = 0

    def find_server(self):
        if not self.is_bot:
            print(ANSI_GREEN + "Client started, Listening for offer requests..." + ANSI_RESET)
        # create the udp socket
        # Defines the UDP socket of the client
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket_client.bind(('', self.client_port))
        find_server = True
        # Listening for Offer Requests
        while find_server:
            # Receiving
            data, address = socket_client.recvfrom(1024)
            # Parsing Received Data
            try:
                magic_cookie, message_type, port, server_name_bytes = struct.unpack('IbH32s', data)
                self.server_name = server_name_bytes.decode('utf-8').rstrip()
                magic_cookie, message_type = int(hex(magic_cookie), 16), int(hex(message_type), 16)
            except Exception as e:
                if not self.is_bot:
                    print("Failed while trying to connect to the server " + str(e))
                continue
            # Validating Magic Cookie and Message Type
            if magic_cookie != self.MAGIC_COOKIE or message_type != self.MESSAGE_TYPE:
                if not self.is_bot:
                    print(
                    "Failed while trying to connect to the server, you have problems with MESSAGE TYPE or MAGIC_COOKIE.")
                continue
            # Extracting Server IP and Port
            self.server_ip = address[0]
            try:
                self.server_port = int(port)
            except ValueError as e:
                if not self.is_bot:
                    print("Failed while trying to connect to the server,problems with server port" + str(e))
                self.server_ip = None
                continue
            socket_client.close()
            break

    def connect_server(self):
        self.TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if not self.is_bot:
            print(f"{ANSI_BLUE}Received offer from server {ANSI_BOLD}{self.server_name}{ANSI_RESET} {ANSI_BLUE}at address {self.server_ip}, attempting to connect...{ANSI_RESET} ")
        # the client try to connecct to the server
        try:
            self.TCP_socket.connect((self.server_ip, self.server_port))
        except socket.error as e:
            # if the client falied while trying to connect to the server
            if not self.is_bot:
                print(f"{ANSI_RED}Failed while trying to connect to the server using TCP" + str(e))
            self.TCP_socket.close()
            return False
        # the client connect to the server
        if not self.is_bot:
            print(f"{ANSI_GREEN}The connection to the server {self.server_name} was made successfully")
        self.TCP_socket.sendall(bytes(str(self.Player_name), 'utf8'))
        return True

    def receive_message(self):
        try:
            msg = self.TCP_socket.recv(1024).decode('utf-8')
            return msg
        except (KeyboardInterrupt, ConnectionResetError) as e:
            if type(e) == ConnectionResetError:
                self.TCP_socket.close()
                raise ConnectionResetError
            else:
                print(f"{self.Player_name} left the game")

    def send_answer(self, q=None):
        pass

    def run_client(self):
        pass


if __name__ == '__main__':
    client = Client(magic_cookie=0xabcddcba, message_type=0x02, client_port=13117)
    client.run_client()
