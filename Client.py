import socket
import struct
import getch
import signal
import time


def play_best_game_ever():
    print("Client started, listening for offer requests...")
    UDP_PORT = 13117  # UDP_PORT
    flag = False
    getch_timeout = 10

    def handler(signum, frame):  # handler
        raise OSError()

    signal.signal(signal.SIGALRM, handler)


    while not flag:

        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp.bind(('', UDP_PORT))
        stop = False
        data = None
        while not stop:
            data, address = udp.recvfrom(1024)
            if data is None:
                continue
            try:
                unpacked_data = struct.unpack('ibh', data)  # unpacked_data

                if unpacked_data[0] == -1412571974 and unpacked_data[1] == 2:
                    # print(msg_rec[2])
                    stop = True
            except:
                continue
        udp.close()
        print("Received offer from " + str(address[0]) + " attempting to connect...")
        portnum = unpacked_data[2]
        try:
            tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp.connect((socket.gethostname(), portnum))
            flag = True
        except:
            tcp.close()
            continue
    team_name = 'Team 1\n'
    tcp.sendall(bytes(team_name, "utf-8"))

    print(tcp.recv(1024).decode("utf-8"))

    start = time.time()
    send_flag = False
    try:
        signal.alarm(getch_timeout)
        char = getch.getch()
        signal.alarm(0)
        send_flag = True
    except:
        pass

    if send_flag:
        message = char
        tcp.sendall(bytes(f'{message}', "utf-8"))

    server_message = tcp.recv(1024)

    print(server_message.decode("utf-8"))
    tcp.close()


if __name__ == '__main__':

    play = True
    while play:
        play_best_game_ever()

