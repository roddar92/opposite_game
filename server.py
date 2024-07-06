# -*- coding: utf-8 -*-
import random
from collections import defaultdict


from flask import Flask, render_template, redirect
from flask import request


app = Flask(__name__, template_folder='templates', static_folder='static')
HOST = '0.0.0.0'
PORT = 8889


class OppositeGameException(Exception):
    def __init__(self, msg):
        self.msg = msg


class OppositesGame(object):
    def __init__(self):
        self.status = "unknown"
        self.__opposites_dictionary = defaultdict(list)
        self.__answers = ''
        self.__quessed_keys = list()
        self.__current_key = ''
        self.__current_vals = list()
        self.__current_candidates = list()
        self.__attempts = 1

        self.RIGHT_ANSWER = [
            "Да, всё правильно! :)",
            "Здорово! Так держать! :)",
            "Правильно. Молодец!"
        ]

        with open("resources/ru_opposites.txt", "r", encoding='utf-8') as f:
            for line in f:
                (word, opposites) = line.split()
                opposites = opposites.split(",")
                self.__opposites_dictionary[word].extend(list(opposites))
                for opposite in opposites:
                    if opposite not in self.__opposites_dictionary:
                        self.__opposites_dictionary[opposite] = list()
                    self.__opposites_dictionary[opposite].append(word)

                    # TODO refactoring links for synonyms
                    for w in self.__opposites_dictionary[opposite]:
                        if opposite not in self.__opposites_dictionary[w]:
                            self.__opposites_dictionary[w].append(opposite)

    def init_game(self):
        self.__answers = ''
        self.__quessed_keys = list()
        self.__current_key = ''
        self.__current_vals = list()
        self.__current_candidates = list()
        self.__attempts = 1
        self.__status = "init"

    def __synonyms(self, values):
        synonyms = list()
        for value in values:
            synonyms.extend(self.__opposites_dictionary[value])
        return set(synonyms)

    def clean(self):
        pass

    def move(self):
        word = random.choice(
            [key for key in self.__opposites_dictionary.keys() if key not in self.__quessed_keys]
        )
        self.__current_key = word
        self.__current_vals = self.__opposites_dictionary[word]
        return word

    def get_candidates(self):
        return self.__current_candidates

    def get_current_key(self):
        return self.__current_key

    def generate_candidates(self, word):
        curr_values = self.__opposites_dictionary[word]
        synonyms = set(w for w in self.__synonyms(curr_values) if w != word)

        candidates = [
            random.choice(curr_values) if len(curr_values) > 1 else curr_values[0],
            random.choice(list(self.__opposites_dictionary.keys()))
        ]

        if len(synonyms) > 1:
            candidates.append(random.choice(list(synonyms)))
        elif len(synonyms) == 1:
            candidates.append(synonyms.pop())
        self.__current_candidates = candidates

        random.shuffle(candidates)
        return candidates

    def check_answer(self, word):
        # print(word)
        if is_end_of_game(word):
            self.status = "over"
            ones, total = self.__answers.count('1'), len(self.__answers)
            self.__answers = ''
            return f"Тогда давай закончим игру! Мы правильно ответили на {ones} вопросов из {total}."
        elif word in self.__current_vals:
            self.__attempts = 1
            self.__quessed_keys.append(self.__current_key)
            self.__answers += '1'
            return random.choice(self.RIGHT_ANSWER)
        elif self.__attempts == 1 and (word == self.__current_key or word in self.__synonyms(self.__current_vals)):
            self.__attempts += 1
            raise OppositeGameException("Ты угадал синоним, но не противоположное слово.")
        else:
            if self.__attempts == 2:
                self.__attempts = 1
                self.__answers += '0'
                return "Увы, правильный ответ - " + random.choice(self.__current_vals)
            else:
                self.__attempts += 1
                raise OppositeGameException("Извини, но я не понял твоего ответа.")

    def set_status(self, status):
        self.status = status


def is_agree(string):
    return string in "да давай конечно разумеется yes ага".lower().split()


def is_disagree(string):
    return string.startswith("не") or string.lower().startswith("нет") or string.lower().startswith("no") or \
           string.startswith("конечно нет") or string.startswith("разумеется нет")


def is_end_of_game(string):
    return string in "конец стоп хватит end over".lower().split() or \
           "закончим" in string or string == "устал" or string == "устала"


@app.route("/game", methods=['POST', 'GET'])
def game():
    if request.method == 'POST':
        word = request.form['clicked_word'].strip().lower()
        try:
            if is_end_of_game(word):
                opp_game.set_status("over")
                # TODO redirect to home page with another text
                # greeting = 'Пока-пока! Хочешь сыграть ещё раз?'

                opp_game.clean()
                return redirect('/')
            else:
                text = opp_game.check_answer(word)
                guessed = opp_game.move()
                candidates = opp_game.generate_candidates(guessed)
                cls = 'n'
        except Exception as e:
            text = f"{e} Попробуешь ещё разок?"
            guessed = opp_game.get_current_key()
            candidates = opp_game.get_candidates()
            cls = 'e'

        return render_template('game.html', data={'value': text, 'cls': cls,
                                                  'guessed': guessed,
                                                  'candidates': candidates})
    else:
        guessed = opp_game.move()
        candidates = opp_game.get_candidates()
        if not candidates:
            candidates = opp_game.generate_candidates(guessed)
        cls = 'n'
        return render_template(
            'game.html',
            data={'value': 'Отлично! :) Я говорю слово, а ты подбираешь противоположное.',
                  'cls': cls,
                  'guessed': guessed,
                  'candidates': candidates})


@app.route("/")
def index():
    opp_game.init_game()
    greeting = 'Приветствую!'
    return render_template('index.html', data={'greeting': greeting})


if __name__ == "__main__":
    opp_game = OppositesGame()
    app.run(host=HOST, port=PORT)
