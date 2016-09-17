import telegram
import math

from consts import drink_text, trade_text, pray_text, sit_text, escape_text, count_text, custom_keyboard, start


class User:
    def __init__(self):
        self.inventory = {}
        self.name = 'None'
        self.bot = None
        self.chat_id = None
        self.hp = 100
        self.max_hp = 100
        self.dmg = 5
        self.drunk = 6
        self.gold = 10
        self.max_drunk = 10
        self.location = start
        self.text = ''
        self.status = 'normal'
        self.inventory = {}
        self.kill_count = 0
        self.level = 1
        self.exp = 0

    def level_up(self):
        self.dmg += int(math.pow(1.2, self.level))
        self.max_hp += int(math.pow(1.2, self.level) * 5)
        self.hp = self.max_hp
        self.level += 1
        self.reply("Вы перешли на следующий уровень!")

    def get_next_level(self):
        return int(100 * math.pow(1.3, self.level-1))

    def get_exp(self, amount):
        self.exp += amount
        while self.exp > self.get_next_level():
            self.level_up()

    def set(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id

    def heal(self, amount, text=True):
        if (self.hp + amount) > self.max_hp:
            healed = self.max_hp - self.hp
            self.hp = self.max_hp
        else:
            healed = amount
            self.hp = self.hp + amount
        if text:
            self.reply("Вам прибавилось " + str(healed) + " здоровья.")

    def damage(self, amount, text=True):
        if (self.hp - amount) < 0:
            self.hp = 0
        else:
            self.hp = self.hp - amount
        if text:
            self.reply("Вы получили " + str(amount) + " урона.\n")

    def add(self, item, amount):
        if item not in self.inventory:
            self.inventory[item] = amount
        else:
            self.inventory[item] += amount

    def has(self, item, amount):
        if item not in self.inventory:
            return False
        else:
            return amount <= self.inventory[item]

    def remove(self, item, amount):
        if item in self.inventory:
            if self.inventory[item] > amount:
                self.inventory[item] -= amount
            else:
                del self.inventory[item]

    def reply(self, message):
        self.text += message + '\n'

    def reset(self):
        self.hp = self.max_hp
        self.drunk = 6
        self.location = 'Ваш дом'
        self.status = 'normal'

    def die(self):
        dead_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        self.reply("Вы умерли. И возродились у себя дома.\n")
        self.reset()
        self.gold = int(self.gold / 2)
        self.exp -= 10 * int(math.pow(1.3, self.level))
        self.bot.send_message(chat_id=self.chat_id, text=self.stats_text() + self.text,
                              reply_markup=dead_markup)

    def send_message(self, keyboard=custom_keyboard, additional=[]):
        if self.hp == 0:
            self.die()
        else:
            if self.status == 'normal':
                if self.location == 'Бар' or self.location == 'Поляна':
                    additional = [[drink_text]]
                elif self.location == 'Кузнец':
                    additional = [[trade_text]]
                if self.location == 'Ебеня':
                    additional = [[pray_text], [sit_text], [count_text], [escape_text]]
            reply_markup = telegram.ReplyKeyboardMarkup(keyboard + additional)
            self.bot.send_message(chat_id=self.chat_id, text=self.stats_text() + self.text,
                                  reply_markup=reply_markup)
        self.text = ''

    def get_damage(self):
        res = self.dmg
        max = 0
        for item in self.inventory:
            if item.damage > max:
                max = item.damage
        return res + max

    def stats_text(self):
        if self.drunk == 6:
            drunk_text = "У вас ваша дефолтная шестёрка. \n"
        elif self.drunk >= 8:
            drunk_text = "Вы бухой в жопу. Как селёдка.\n"
        elif self.drunk == 7:
            drunk_text = "Вы слегка tipsy\n"
        else:
            drunk_text = "Вы необычайно трезвы\n"
        damage_text = ''
        if self.dmg != self.get_damage():
            damage_text = '+' + str(self.get_damage() - self.dmg)
        return ("Уровень:   " + str(self.level) + "\n" +
                "Опыт:         " + str(self.exp) + '/' + str(self.get_next_level()) + '\n' +
                "Местонах: " + self.location + "\n" +
                "Здоровье: " + str(self.hp) + "\n" +
                "Урон:         " + str(self.dmg) + damage_text + "\n" +
                "Золото:     " + str(self.gold) + "\n" +
                "Шкала бухости: " + str(self.drunk) + "/" + str(self.max_drunk) + "\n" +
                drunk_text + '\n')