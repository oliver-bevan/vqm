from quiz import Quiz
from quiz import Question
from integration import TwitchChat
from show import Show
from show import ShowGUI
from show import OperatorGUI
import tkinter as tk
#display menu - option to run show or create quiz
#setup show then handoff to gui

def present_menu_get_response(options):
    for index, option  in enumerate(options):
        print(str(index + 1) + ". " + str(option))

    input_valid = False
    while not input_valid:
        print("Make a choice: ", "")
        raw_input = input()
        try:
            choice = int(raw_input)
        except ValueError:
            continue
        if not 0 < choice <= len (options):
            continue

        return choice

def begin_show(quiz):
    print("Please choose live stream chat provider: ")

    if present_menu_get_response(["Twitch"]) == 1:
        username = input("Enter username: ")
        key = input("Enter Oauth key: ")

        question_regex = quiz.question_regex

        key_regex = input("Please enter user one-time-key regex (usually 10 digits): ")
        
        chat_provider = TwitchChat(username, key, "#" + username, question_regex, key_regex)

    key_path = input("Please enter the Cloud Firestore document path for this show\'s keys: ")

    show = Show(quiz, chat_provider, key_path)
    
    master_gui = tk.Tk()

    master_gui.title("VQM")
    master_gui.geometry("800x600")

    gui = OperatorGUI(master_gui, show)
    gui.pack()

    master_gui.mainloop()
    
print("--Volani Quiz Master: Main Menu--")
quizzes = []
quizzes.append(Quiz("Test Quiz", [Question("Test Question, B is Correct?", ["Incorrect", "Correct", "Inccorect"], 2, 10)], r"^[1-3]$"))
while True:
    

    choice = present_menu_get_response(["Create Quiz", "Run Show"])

    if choice == 1:
        print("Enter quiz title: ")
        title = input()
        print("Enter answer regex: ")
        answer_regex = input()

        input_valid = False

        questions = []

        while not input_valid:
            print("How many questions: ")
            raw_input = input()
            try:
                number_of_questions = int(raw_input)
            except ValueError:
                continue
            if not 0 < number_of_questions:
                continue
            input_valid = True
        for question_number in range(number_of_questions):
            print("Question " + str(question_number + 1))
            question = input("Enter question: ")

            correct_index = input("Enter number of correct answer: ")
            answers = []
            input_valid = False
            while not input_valid:
                print("Enter, in seconds, amount of time for answer: ")
                raw_input = input()
                try:
                    interval = int(raw_input)
                except ValueError:
                    continue
                if not 0 < interval:
                    continue
                input_valid = True
            input_valid = False
            while not input_valid:
                print("How many answers: ")
                raw_input = input()
                try:
                    number_of_questions = int(raw_input)
                except ValueError:
                    continue
                if not 0 < number_of_questions:
                    continue
                input_valid = True
            for question_number in range(number_of_questions):
                print("Answer " + str(question_number + 1))
                answers.append(input("Enter answer: "))

            questions.append(Question(question, answers, correct_index, interval))
        quizzes.append(Quiz(title, questions, answer_regex))
    elif choice == 2:
        print("Choose a Quiz")
        begin_show(quizzes[present_menu_get_response(quizzes) - 1])
