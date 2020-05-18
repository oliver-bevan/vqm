class Quiz():
    def __init__(self, title, questions, question_regex):
        self.questions = questions
        self.title = title
        self.question_regex = question_regex
    def __str__(self):
        return self.title

class Question():
    def __init__(self, question, answers, correct_answer, interval):
        self.question = question
        self.interval = interval
        self.answers = answers
        self.correct_answer = correct_answer


class Player:
    def __init__(self, username, key):
        self.username = username
        self.scores = []
        self.key = key
        