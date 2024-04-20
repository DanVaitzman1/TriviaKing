
import Client
from Client import *

ANSI_RED = "\u001b[31m"
ANSI_GREEN = "\u001b[32m"
ANSI_YELLOW = "\u001b[33m"
ANSI_RESET = "\u001b[0m"
import re

def remove_ansi_escape_codes(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class BotClient(Client):

    def __init__(self, is_bot, name):
        super().__init__(is_bot=is_bot, Player_name=name)
        self.game_over = False

    def send_answer(self, q=None):
        try:
            answer_value = random.choice(["True", "False"])
            sleep(2.5)
            self.TCP_socket.send(bytes(answer_value, 'utf8'))
        except KeyboardInterrupt:
             print(ANSI_RED + "Bots were terminated by the host" + ANSI_RESET)

    # Run function for the bot
    def run_client(self):
        while True:
            self.find_server()
            success = self.connect_server()
            if not success:
                continue
            else:
                break
        while not self.game_over:
            try:
                msg = self.receive_message()
                msg_without_ansi = remove_ansi_escape_codes(msg)

                if "true or false" in msg_without_ansi.lower():
                    if 'round' in msg_without_ansi.lower():
                        if self.Player_name not in msg_without_ansi:
                            self.lost = True
                            continue
                        else:
                            self.lost = False
                    if not self.lost:
                        self.send_answer()

                # elif self.Player_name in msg_without_ansi.lower() and 'correct!' in msg_without_ansi.lower() and 'in' not in msg_without_ansi.lower():
                #     self.correct_answers_counter += 1
                #     # print(msg)
                #
                # elif self.Player_name in msg_without_ansi.lower() and 'incorrect!' in msg_without_ansi.lower():
                #     # print(msg)
                #     # self.lost = True

                elif "game over" in msg_without_ansi.lower() or "All players left the game" in msg_without_ansi.lower():
                    # print(msg)
                    self.TCP_socket.close()
                    self.game_over = True
                    self.lost = False
                    sleep(4)

            except ConnectionResetError:
                print("Connection with the server was lost, trying to find a new lobby...")
                self.game_over = True
                self.lost = False



if __name__ == '__main__':
        bot_number = 2
        bots = []
        for i in range(bot_number):
            bot = BotClient(is_bot=True)
            thread = threading.Thread(target=bot.run_client)
            thread.start()
            bots.append(thread)

        for bot in bots:
            bot.join()

