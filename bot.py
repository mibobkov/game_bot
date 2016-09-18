import logging
import threading
from asyncio import async

import telegram.ext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater
from telegram.ext.dispatcher import run_async

from User import User
from config import token
from consts import normal_attack_text, shout_text, fight_text, love_text, eat_text, go_text, drink_text, inventory_text, \
    trade_text, pray_text, sit_text, escape_text, count_text, leaderboard_text, transitions, transitions_text, \
    custom_keyboard, fight_keyboard
import consts

updater = Updater(token)

dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

podvohs = 0

def escape(user, text):
    user.reply("Вы попытались выбраться, но не получилось. Нужно постороннее вмешательство.\n")
    user.send_message()


def sit(user, text):
    user.reply("Вы сели и сидите. Ничего не происходит и вряд ли произойдёт.\n")
    user.send_message()


def pray(user, text):
    user.reply("Вы кому-то помолились. Кто-то оставил вашу молитву без внимания.\n")
    user.send_message()


def count(user, text):
    user.reply("Вы решили посчитать селёдок. Вы видете, что их: 0. Вряд ли это число изменится.\n")
    user.send_message()


def inventory(user, text):
    if len(user.inventory) == 0:
        user.reply("Пусто.\n")
    else:
        for item in user.inventory:
            user.reply(item.name + ' - ' + str(user.inventory[item]) + ' шт.\n')
    user.send_message()


def go(user, text):
    if user.status == 'going':
        for location in transitions[user.location]:
            if text.find(location) != -1:
                user.status = 'normal'
                user.reply(transitions_text[user.location + "," + location])
                user.location = location
                if user.location == 'Ебеня':
                    intervention_countdown(user)
                user.send_message()
    else:
        go_keyboard = []
        for dest in transitions[user.location]:
            go_keyboard.append([dest])
        user.reply("Куда вы хотите пойти?\n")
        user.status = 'going'
        user.send_message(keyboard=go_keyboard)


def intervention_countdown(user):
    threading.Timer(60, lambda: intervention(user)).start()


def intervention(user):
    user.reply("Произошло постороннее вмешательство.\n")
    user.location = 'Замок'


def multiply():
    global podvohs
    if podvohs < consts.podvohs_limit:
        podvohs += 1
    threading.Timer(20/consts.spawn_mod, multiply).start()


multiply()

users = {}


def register_user(bot, update):
    user = User()
    users[update.message.chat_id] = user
    user.set(bot, update.message.chat_id)
    user.status = 'name'
    user.reply("Добро пожаловать. Как вас зовут?\n")
    user.send_message(keyboard=[])


def name_user(user, text):
    user.name = text
    user.reply("Хорошо. Я буду звать вас Кирилл.\n")
    user.status = 'normal'
    user.send_message()

@run_async
def message(bot, update):
    global users
    if update.message.chat_id not in users:
        register_user(bot, update)
        return
    text = update.message.text
    user = users[update.message.chat_id]
    user.set(bot, update.message.chat_id)
    if user.status == 'name':
        name_user(user, text)
    elif user.status == 'fight':
        fight(user, text)
    elif user.status == 'going':
        go(user, text)
    elif user.status == 'trading':
        trade(user, text)
    else:
        if text == pray_text and user.location == 'Ебеня':
            pray(user, text)
        elif text == sit_text and user.location == 'Ебеня':
            sit(user, text)
        elif text == count_text and user.location == 'Ебеня':
            count(user, text)
        elif text == escape_text and user.location == 'Ебеня':
            escape(user, text)
        elif text == fight_text:
            fight(user, text)
        elif text == trade_text and user.location == 'Кузнец':
            trade(user, text)
        elif text == inventory_text:
            inventory(user, text)
        elif text == love_text:
            love(user, text)
        elif text == eat_text:
            eat(user, text)
        elif text == go_text:
            go(user, text)
        elif text == leaderboard_text:
            leaderboard(user, text)
        elif text == drink_text and (user.location == 'Бар' or user.location == 'Поляна'):
            drink(user, text)


def leaderboard(user, text):
    user.reply("Лидерборд:\n\n")
    for p in users:
        player = users[p]
        user.reply(player.name + " -  " + " Уровень: " + str(player.level) + "\n" +
                   "   Золото: " + str(player.gold) + "  Убито подвохов: " + str(player.kill_count))
    user.reply("\nЭто псевдолидерборд. Просто показывает всех Кириллов.\n")
    user.send_message()


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Я Кирилл",
                    reply_markup=telegram.ReplyKeyboardMarkup(custom_keyboard))


def fight(user, text):
    global podvohs
    if user.status == 'fight':
        if text == shout_text:
            shout(user, text)
        elif text == normal_attack_text:
            normal_attack(user, text)
        else:
            user.status = 'normal'
            user.send_message()
    else:
        if podvohs <= 0:
            user.reply("Вы убили всех подвохов. Но они ещё вернутся!\n")
            user.send_message()
        else:
            user.reply("Вы бьётесь с полчищами подвохов.\n")
            user.reply("Осталось " + str(podvohs) + " подвохов\n")
            user.reply("Вы должны контроллировать их численность чтобы предотвратить захват мира подвохами.\n")
            user.reply("Выберите атаку: \n")
            user.status = 'fight'
            user.send_message(keyboard=fight_keyboard)


def normal_attack(user, text):
    global podvohs
    if user.drunk < 8:
        killed = int(user.get_damage() / 5)
        if podvohs < killed:
            killed = podvohs
        podvohs -= killed
        user.reply("Вы использовали обычную атаку.\n")
        user.damage(int(podvohs / 10 + 1))
        user.reply("Вы убили " + str(killed) + " подвоха.\n")
        user.gold += killed
        user.get_exp(killed * 2)
        user.reply("Вы получили " + str(killed) + " золота\n")
        user.kill_count += killed
    else:
        user.reply("Вы попытались использовать обычную атаку.\n")
        user.reply("Но вы бухой в жопу.\n")
        user.damage(int(podvohs / 10 + 1))
        user.reply("Вы не убили ни одного подвоха.\n")
    user.status = 'normal'
    user.send_message()


def shout(user, text):
    global podvohs

    if user.drunk < 8:
        if podvohs < 3:
            killed = podvohs
        else:
            killed = 3
        podvohs -= killed
        user.gold += killed
        user.get_exp(killed * 2)
        user.reply("Вы орнули в голосину.\n")
        user.damage(int(podvohs / 10 + 1))
        user.reply("Вы убили " + str(killed) + " подвохов.\n")
        user.reply("Вы получили " + str(killed) + " золота")
        user.kill_count += killed
    else:
        user.reply("Вы орнули в голосину.\n" +
                   "Подвохи существа нежные и сильно восприимчивые к парам алкоголя. Волна алкопара накрыла бедных подвохов.\n" +
                   "Теперь им может помочь только брынза, ведь в ней так много солей, необходимых их организмам, когда они бухие.")
    user.status = 'normal'
    user.send_message()


class Item:
    def __init__(self, name, damage, cost):
        self.name = name
        self.damage = damage
        self.cost = cost

knife = Item('Ножичек', 5, 20)
dagger = Item('Кинжал', 15, 50)
sword = Item('Меч', 30, 100)
bfsword = Item('Большой, сука, меч', 50, 200)
dildo = Item('Черный дилдо', 0, 5)
cheese = Item('Брынза', 0, 0)

shop_items = [knife, dagger, sword, bfsword, dildo]

def trade(user, text):
    if user.status != 'trading':
        user.reply("Что вы хотите купить?\n")
        keyboard = []
        for item in shop_items:
            user.reply(item.name + ' - ' + str(item.cost) + ' золота.')
            keyboard += [[item.name]]
        keyboard += [['Ничего']]
        user.status = 'trading'
        user.send_message(keyboard=keyboard)
    else:
        for item in shop_items:
            if text == item.name:
                if user.gold >= item.cost:
                    user.gold -= item.cost
                    user.add(item, 1)
                    user.reply("Вы купили + " + item.name)
                else:
                    user.reply("Нужно больше золота.")
        if text == dildo.name:
            user.reply("Нахера? о_О")
        user.status = 'normal'
        user.send_message()


def love(user, text):
    if user.location == 'Ебеня':
        user.reply("В Ебенях нету баб\n")
        user.send_message()
        return

    if user.drunk < 8:
        user.heal(5)
        user.reply("Вы пошли лапать баб.\n" +
                   "Вам приятно.\n" +
                   "Здоровье пополняяяется!\n")
    else:
        if user.location == 'Кузнец':
            user.reply("Вы пошли лапать баб.\n" +
                       "Поскольку вы бухой в жопу, как селёдка, то вы промахнулись и облапали кузнеца.\n" +
                       "Он вас тоже обнял, от чего у вас хрустнули ребра. Кузнецу показалось, что вы ещё не уяснили, насколько сильно он вас любит, поэтому он взял молот и треснул вас по башке.\n" +
                       "Вам чуток поплохело.\n")
            user.damage(20)
        else:
            user.add(cheese, 1)
            if user.drunk > 0:
                user.drunk -= 1
            user.reply("Вы пошли лапать баб.\n" +
                       "Поскольку вы бухой в жопу, как селёдка, то вы промахнулись и облапали кусок брынзы.\n" +
                       "Вам стало легче, ведь в брынзе так много солей, которых не хватает вашему организму.\n" +
                       "Крутая вещь! - подумали вы и взяли себе ещё кусок.\n")
    user.send_message()


def drink(user, text):
    if user.drunk == 10:
        user.reply("Самолёёёётик, самолёёёёётик!\n")
    else:
        user.drunk += 1
        user.reply("Вы слегка бухнули. Но наверное не обязательно напиваться? Ведь завтра на работу...\n")
    user.send_message()


def eat(user, text):
    if user.has(cheese, 1):
        if user.drunk > 0:
            user.drunk -= 1
        user.remove(cheese, 1)
        user.reply("Вы съели кусок брынзы.\n\n" +
                   "Вам полегчало. Наверное потому, что там много солей, которых так не хватает организму, когда ты бухой.\n\n")
        user.heal(20)
    else:
        user.reply("А кушать то нечего...")
    user.send_message()


from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)

def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized:
        print("Unauthorised")
    except BadRequest:
        print("Bad request")
    except TimedOut:
        print("Timed out")
    except NetworkError:
        print("Network error")
    except ChatMigrated as e:
        print("Chat Migrated")
    except TelegramError:
        print("TelegramError")

dispatcher.add_error_handler(error_callback)

start_handler = CommandHandler('start', start)

message_handler = MessageHandler([Filters.text], message)

dispatcher.add_handler(message_handler)
dispatcher.add_handler(start_handler)

updater.start_polling()
