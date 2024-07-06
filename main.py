import telebot
from telebot import types
import json

API_TOKEN = '7273948604:AAHXupP-jUpo_A3eV92emZz5VKDIkeE2JII'

bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения токенов пользователей и результатов тестов
user_tokens = {}
user_results = {}


# Функция для загрузки лекций
def load_lecture(lecture_number):
    with open(f'lectures/lecture{lecture_number}.txt', 'r', encoding='utf-8') as file:
        return file.read()


# Функция для загрузки тестов
def load_test(test_number):
    with open(f'tests/test{test_number}.json', 'r', encoding='utf-8') as file:
        return json.load(file)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Пожалуйста, введите свой токен:")
    bot.register_next_step_handler(message, get_user_token)


# Обработчик получения токена пользователя
def get_user_token(message):
    user_tokens[message.chat.id] = message.text
    user_results[message.chat.id] = {}
    send_main_menu(message)


# Функция для отображения главного меню
def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    lectures_btn = types.KeyboardButton('Лекции')
    tests_btn = types.KeyboardButton('Тесты')
    markup.add(lectures_btn, tests_btn)

    # Добавляем кнопку "Меню" в главное меню
    menu_btn = types.KeyboardButton('Меню')
    markup.add(menu_btn)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == 'Меню':
        send_main_menu(message)
    elif message.text == 'Лекции':
        send_lectures_menu(message)
    elif message.text.startswith('Лекция'):
        lecture_number = message.text.split()[-1]
        send_lecture(message, lecture_number)
    elif message.text == 'Тесты':
        send_tests_menu(message)
    elif message.text.startswith('Тест'):
        test_number = message.text.split()[-1]
        if has_passed_test(message.chat.id, test_number):
            bot.reply_to(message, "Вы уже прошли этот тест.")
        else:
            send_test(message, test_number)
    else:
        bot.reply_to(message, "Я не понимаю эту команду. Пожалуйста, выберите действие из меню.")


# Функция для проверки прохождения теста
def has_passed_test(chat_id, test_number):
    return user_results.get(chat_id, {}).get(test_number, False)


# Функция для отображения меню лекций
def send_lectures_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for i in range(1, 6):
        btn = types.KeyboardButton(f'Лекция {i}')
        markup.add(btn)

    # Кнопка "Меню" в меню лекций
    menu_btn = types.KeyboardButton('Меню')
    markup.add(menu_btn)

    bot.send_message(message.chat.id, "Выберите лекцию:", reply_markup=markup)


# Функция для отправки текста лекции и кнопки "Пройти тест"
def send_lecture(message, lecture_number):
    lecture_text = load_lecture(lecture_number)
    markup = types.ReplyKeyboardMarkup(row_width=1)
    btn = types.KeyboardButton(f'Пройти тест {lecture_number}')
    markup.add(btn)

    menu_btn = types.KeyboardButton('Меню')
    markup.add(menu_btn)

    bot.send_message(message.chat.id, lecture_text, reply_markup=markup)
    bot.register_next_step_handler(message, handle_after_lecture, lecture_number)


# Обработчик после просмотра лекции
def handle_after_lecture(message, lecture_number):
    if message.text.startswith('Пройти тест'):
        test_number = message.text.split()[-1]
        if has_passed_test(message.chat.id, test_number):
            bot.reply_to(message, "Вы уже прошли этот тест.")
        else:
            send_test(message, test_number)
    else:
        send_main_menu(message)


# Функция для отображения меню тестов
def send_tests_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for i in range(1, 6):
        test_status = " (Пройден)" if has_passed_test(message.chat.id, str(i)) else ""
        btn = types.KeyboardButton(f'Тест {i}{test_status}')
        markup.add(btn)

    menu_btn = types.KeyboardButton('Меню')
    markup.add(menu_btn)

    bot.send_message(message.chat.id, "Выберите тест:", reply_markup=markup)


# Функция для проведения теста
def send_test(message, test_number):
    test = load_test(test_number)
    question_number = 0
    send_question(message, test, question_number, [], test_number)


# Функция для отправки вопроса
def send_question(message, test, question_number, user_answers, test_number):
    if question_number < len(test):
        question = test[question_number]
        markup = types.ReplyKeyboardMarkup(row_width=2)
        for option in question['options']:
            btn = types.KeyboardButton(option)
            markup.add(btn)
        msg = bot.send_message(message.chat.id, question['question'], reply_markup=markup)
        bot.register_next_step_handler(msg, handle_answer, test, question_number, user_answers, test_number)
    else:
        send_test_result(message, test, user_answers, test_number)


# Функция для обработки ответа
def handle_answer(message, test, question_number, user_answers, test_number):
    user_answers.append(message.text)
    send_question(message, test, question_number + 1, user_answers, test_number)


# Функция для отправки результата теста
def send_test_result(message, test, user_answers, test_number):
    score = 0
    for i, answer in enumerate(user_answers):
        if answer == test[i]['answer']:
            score += 1
    total_questions = len(test)
    percentage = (score / total_questions) * 100
    user_results[message.chat.id][test_number] = percentage
    result_text = f"Вы ответили правильно на {score} из {total_questions} вопросов ({percentage:.2f}%)."
    bot.send_message(message.chat.id, result_text)
    send_main_menu(message)


bot.polling()
