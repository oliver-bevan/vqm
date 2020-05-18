import tkinter as tk
import threading
import queue
import os
import datetime
import time
from integration import TwitchChat
from quiz import Player
from google.cloud import firestore
from python_twitch_irc import TwitchIrc

class Show:
    def __init__(self, quiz, chat_integration, otkey_file):
        self.quiz = quiz
        
        self.players = []

        self.messages_queue = queue.Queue()

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\obeva\Documents\Projects\vp-service-credentials.json"

        self.db = firestore.Client()

        self.chat_integration = chat_integration
        self.ot_keyfile = otkey_file

        self.current_question = 0

    def begin_show(self, master):
        self.show_gui = ShowGUI(master, len(self.quiz.questions[0].answers))
        #begin method to constantly update donated amount - do with after() so its constantly updating

    def connect_chat(self):
        self.chat_integration.connect()

        chat_thread = threading.Thread(target=self.chat_integration.handle_forever)
        chat_thread.setDaemon(True)

        chat_thread.start()

    def create_players(self):
        keys_ref = self.db.collection("otkeys").document(self.ot_keyfile).collection("keys") #Get location of keyfiles
        active_keys_ref = keys_ref.where("valid", "==", True) #Only get active keyfiles

        keyfiles = active_keys_ref.stream() #Get keyfiles

        keys = []

        for document in keyfiles: #Extract key from keyfile
            keys.append(document.id)

        messages = self.chat_integration.messages_queue.dump_to_list()

        for message in messages:
            if message.message in keys:
                self.players.append(Player(message.username, message.message))
                keys.remove(message.message)
        #todo - deactivate keys

        
    def present_next_question(self):
        self.show_gui.label_1.configure(text= self.quiz.questions[self.current_question].question)

        for index, answer in enumerate(self.quiz.questions[self.current_question].answers):
            self.show_gui.answer_labels[index].configure(text= str(index + 1) + ". " + answer)

        self.countdown(1, self.quiz.questions[self.current_question].interval)

    def countdown(self, interval, remaining):
        if remaining > 0:
            self.show_gui.label_4.configure(text= str(remaining))
            remaining = remaining - 1
            self.show_gui.after(interval*1000, lambda: self.countdown(interval, remaining))
        else:
            self.show_gui.label_4.configure(text= "")
            self.mark_current_question()

    def mark_current_question(self):
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(seconds=(self.quiz.questions[self.current_question].interval))

        responses = self.chat_integration.messages_queue.dump_to_list()
        valid_responses = list(filter(lambda response: end_time > response.timestamp > start_time, responses))
        if valid_responses:
            for player in list(self.players): #Iterate over copy to allow removal
                player_responses = list(filter(lambda response: response.username == player.username, valid_responses))
                if player_responses:
                    player_responses.sort(key= lambda response: response.timestamp)

                    player_response = player_responses[0]

                    if player_response.message == str(self.quiz.questions[self.current_question].correct_answer):
                        time_taken = int((start_time - player_response.timestamp).total_seconds()*1000)
                        
                        player.scores.append((self.quiz.questions[self.current_question].interval*1000) - time_taken)
                    else:
                        self.players.remove(player)
                else:
                    self.players.remove(player)
        else:
            self.show_gui.label_1.configure(text= "No valid answers!")

        if self.players:
            players_by_speed = list(sorted(self.players, key= lambda player: player.scores[self.current_question]))
        else:
            self.show_gui.label_1.configure(text= "No valid answers!")
        if players_by_speed:
            self.show_gui.label_1.configure(text="Fastest responder: " + players_by_speed[0].username)

            self.show_gui.label_4.configure(text="")

            for label in self.show_gui.answer_labels:
                label.configure(text="")
        else:
            self.show_gui.label_1.configure(text= "No correct answers!")

        self.current_question = self.current_question + 1
    
    def present_results(self):
        if self.players:
            players_by_score = list(sorted(self.players, key= lambda player: sum(player.scores)))
            if players_by_score and sum(players_by_score[0].scores) > 0:
                self.show_gui.label_1.configure(text="Winning Player!")
                self.show_gui.label_4.configure(text=players_by_score[0].username)
            else:
                self.show_gui.label_1.configure(text="No Winner.")
        else:
                self.show_gui.label_1.configure(text="No Winner.")


class ShowGUI(tk.Toplevel):
    def __init__(self, master, number_of_answers):
        super().__init__(master)
        self.title("VQ")

        self.geometry("800x600")

        self.label_1 = tk.Label(self)
        self.label_4 = tk.Label(self)

        self.answer_labels = []

        for answer in range(number_of_answers):
            self.answer_labels.append(tk.Label(self))
            self.answer_labels[answer].grid(row=1, column=answer)        
        self.label_1.grid(row=0, column=0)
        self.label_4.grid(row=2, column=2)


class OperatorGUI(tk.Frame):
    def __init__(self, master, show):
        super().__init__(master)

        self.show = show

        self.button_connect_chat = tk.Button(self, text="Connect to chat", command=self.show.connect_chat)
        self.button_create_players = tk.Button(self, text="Create players, authenticating payment", command=self.show.create_players)

        self.button_begin_show = tk.Button(self, text="Begin Show", command= lambda:self.show.begin_show(self))

        self.button_next_question = tk.Button(self, text="Next Question", command= self.show.present_next_question)

        self.button_present_results = tk.Button(self, text="Present Results", command= self.show.present_results)

        self.button_connect_chat.grid(row=0, column=0)
        self.button_create_players.grid(row=0, column=1)

        self.button_begin_show.grid(row=1, column=0)
        self.button_next_question.grid(row=1, column=1)
        self.button_present_results.grid(row=2, column=1)
