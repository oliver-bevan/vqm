import socket
import re
import threading
import queue
import time
import datetime

class ListQueue(queue.Queue):
    def dump_to_list(self):
        with self.mutex:
            list_output = list(self.queue)
            self.queue.clear()
            return list_output

class Message():
    def __init__(self, timestamp, channel, username, message):
        self.timestamp = timestamp
        self.username = username
        self.message = message
    def __str__(self):
        return str(self.timestamp) + " - " + self.message + " - " + self.username
    def __repr__(self):
        return str(self.timestamp) + " - " + self.message + " - " + self.username

class TwitchChat:
    def __init__(self, nickname, key, channel, question_regex, key_regex):
        self.server = "irc.chat.twitch.tv"
        self.port = 6667
        self.nickname = nickname
        self.key = key
        self.channel = channel
        self.question_regex = question_regex
        self.key_regex = key_regex
        self.socket = socket.socket()
        self.messages_queue = ListQueue()

    def connect(self):
        self.socket.connect((self.server, self.port))

        self.socket.send(f"PASS {self.key}\n".encode("utf-8"))
        self.socket.send(f"NICK {self.nickname}\n".encode("utf-8"))
        self.socket.send(f"JOIN {self.channel}\n".encode("utf-8"))


    def handle_forever(self):
        while True:
            message = self.socket.recv(2048).decode("utf-8")

            if message.startswith("PING"):
                self.socket.send("PONG\n".encode("utf-8"))

            if "PRIVMSG" in message:
                username, channel, final_message = re.search(r":(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)", message).groups() #Parse output
                final_message = final_message[:-1] #Remove trailing newline and cr
                if (re.search(self.key_regex, final_message) or re.search(self.question_regex, final_message)): #and "WHIPSER" in message:
                    timestamp = datetime.datetime.now()
                    self.messages_queue.put(Message(timestamp, channel, username, final_message))