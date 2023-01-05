# /setup.py file
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# dependencies
import telebot
import os
from functools import wraps
import codecs
import common.tg_analytics as tga
import schedule

from time import sleep
from threading import Thread

from jinja2 import Template
from services.country_service import CountryService
from services.statistics_service import StatisticsService
from services.history_service import HistoryService
from services.coin_service import CoinService
from services.chat_gpt_service import ChatGPTservice
from telebot import types
from flask import Flask, request

# bot initialization
token = os.getenv('API_BOT_TOKEN')
bot = telebot.TeleBot(token)
user_steps = {}
known_users = []
stats_service = StatisticsService()
country_service = CountryService()
history_service = HistoryService()
coin_service = CoinService()
chat_gpt_service = ChatGPTservice()
commands = {'start': 'Start using this bot',
            'country': 'Please, write a country name',
            'statistics': 'Statistics by users queries',
            'history': 'Please, write a country name',
            'help': 'Useful information about this bot',
            'contacts': 'Developer contacts',
            'top': 'bar chart for top 20 country deaths or top 20 daily cases',
            'COIN QUOTES':'COIN QUOTES',
            'coin': 'Please write a coin and currency, default: TONCOIN:RUB',
            'chat': 'chatGDP: type any questions'
            }

def get_user_step(uid):
    if uid in user_steps:
        return user_steps[uid]
    else:
        known_users.append(uid)
        user_steps[uid] = 0
        return user_steps[uid]


# decorator for bot actions
def send_action(action):

    def decorator(func):
        @wraps(func)
        def command_func(message, *args, **kwargs):
            bot.send_chat_action(chat_id=message.chat.id, action=action)
            return func(message, *args, **kwargs)
        return command_func
    return decorator
# auto run job
def autorun_job():
    country='russia'
    cid='-608476246'
    try:
        statistics = stats_service.get_statistics_by_country_name(country, 'auto run')
    except Exception as e:
        raise e
    bot.send_message(cid,statistics, parse_mode='HTML')
    sleep(1)
    try:
        history_service.get_history_by_country_name(country, 'auto run')
    except Exception as e:
        raise e

    user_steps[cid] = 0
    bot.send_photo(chat_id=cid, photo=open('viz_hist.png', 'rb'))

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

# decorator for save user activity
def save_user_activity():

    def decorator(func):
        @wraps(func)
        def command_func(message, *args, **kwargs):
            response = tga.statistics(message.chat.id, message.text)
            if response == 'true':
                return func(message, *args, **kwargs)
            else:
                message.text='error'
                return func(message,*args, **kwargs)
        return command_func
    return decorator


# start command handler
@bot.message_handler(commands=['start'])
@send_action('typing')
@save_user_activity()
def start_command_handler(message):
    cid = message.chat.id
    menu1 = telebot.types.InlineKeyboardMarkup()
    menu1.add(telebot.types.InlineKeyboardButton(text = 'COVID 19: country', callback_data ='country'))
    menu1.add(telebot.types.InlineKeyboardButton(text = 'COVID 19: history', callback_data ='history'))
    menu1.add(telebot.types.InlineKeyboardButton(text = 'COVID 19: top', callback_data ='top'))
    menu1.add(telebot.types.InlineKeyboardButton(text = 'COIN QUOTES: coin', callback_data ='coin'))
    menu1.add(telebot.types.InlineKeyboardButton(text = 'ChatGPT', callback_data ='chatgpt'))
    menu1.add(telebot.types.InlineKeyboardButton(text = 'Statistics by users queries', callback_data ='statistics'))
    menu1.add(telebot.types.InlineKeyboardButton(text = 'Contacts', callback_data ='contacts'))
    menu1.add(telebot.types.InlineKeyboardButton(text = 'Help', callback_data ='help'))
    # markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    # button_geo = types.KeyboardButton(text='send location', request_location=True)
    # markup.add(button_geo)
    bot.send_message(cid, '{0}, please choose command from the menu'.format(message.from_user.first_name + ' ' + message.from_user.last_name),
                     reply_markup=menu1)
                 
    # help_command_handler(message)

@bot.callback_query_handler(func=lambda call: True)
def step2(call):
    if call.data == 'country':
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
        country_command_handler(call.message)
        # bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='country')
    elif call.data == 'statistics':
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
        statistics_command_handler(call.message)
    elif call.data == 'help':
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
        help_command_handler(call.message)
    elif call.data == 'chatgpt':
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
        chat_command_handler(call.message)
    elif call.data == 'history':
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
        history_command_handler(call.message)
    elif call.data == 'top':
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
        top_20_country_command_handler(call.message)
    elif call.data == 'coin':
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
        coin_command_handler(call.message)
    elif call.data == 'contacts':
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
        contacts_command_handler(call.message)
    # elif call.data == 'covid-deaths':
    #     call.message.chat.id = 4
    #     call.message.from_user.first_name=call.from_user.first_name
    #     call.message.from_user.last_name=call.from_user.last_name
    #     stats_service.get_top_20_country('1',call.message.from_user.first_name + ' ' + call.message.from_user.last_name)
    #     # top_20_country_death_command_handler(call.message)
    # elif call.data == 'covid-daily-cases':
    #     call.message.chat.id = 4
    #     call.message.from_user.first_name=call.from_user.first_name
    #     call.message.from_user.last_name=call.from_user.last_name
    #     call.message.text='2'
    #     top_20_country_death_command_handler(call.message)

# New user handles
@bot.message_handler(content_types=['new_chat_members'])
@send_action('typing')
@save_user_activity()
def new_chat_user_command_handler(message):
    cid = message.chat.id
    try:
        for user in message.new_chat_members:
            if user.last_name is not None:
                bot.send_message(cid, 'Hello, {0}, please choose command from the menu'.format(user.first_name + ' ' + user.last_name))
            else:
                bot.send_message(cid, 'Hello, {0}, please choose command from the menu'.format(user.first_name))
        help_command_handler(message)
    except Exception as e:
            raise e

# country command handler
@bot.message_handler(commands=['country'])
@send_action('typing')
@save_user_activity()
def country_command_handler(message):
    cid = message.chat.id
    user_steps[cid] = 1
    bot.send_message(cid, '{0}, please write name of country (started from / if you use groups)'.format(message.from_user.first_name + ' ' + message.from_user.last_name))
    
# history command handler
@bot.message_handler(commands=['history'])
@send_action('typing')
@save_user_activity()
def history_command_handler(message):
    cid = message.chat.id
    user_steps[cid] = 2
    bot.send_message(cid, '{0}, please write name of country (started from / if you use groups)'.format(message.from_user.first_name + ' ' + message.from_user.last_name))

# top 20 countries command handler
@bot.message_handler(commands=['top'])
@send_action('typing')
@save_user_activity()
def top_20_country_command_handler(message):
    # menu2 = telebot.types.InlineKeyboardMarkup()
    # menu2.add(telebot.types.InlineKeyboardButton(text = 'COVID 19: view top 20 country deaths', callback_data ='covid-deaths'))
    # menu2.add(telebot.types.InlineKeyboardButton(text = 'COVID 19: view top 20 country daily cases', callback_data ='covid-daily-cases'))
    cid = message.chat.id
    user_steps[cid] = 4
    bot.send_message(cid, '{0}, please select /1 to view top 20 country deaths or /2 to view top 20 country daily cases'.format(message.from_user.first_name + ' ' + message.from_user.last_name))
    # bot.send_message(cid, '{0}, please select'.format(message.from_user.first_name + ' ' + message.from_user.last_name), reply_markup=menu2)

# top 20 countriy deaths command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 4)
@send_action('typing')
@save_user_activity()
def top_20_country_death_command_handler(message):
    cid = message.chat.id
    try:
        txt=message.text.strip().replace('/','')
        if txt[:1]=='1':
            stats_service.get_top_20_country('1',message.from_user.first_name + ' ' + message.from_user.last_name)
        elif txt[:1]=='2':
            stats_service.get_top_20_country('2',message.from_user.first_name + ' ' + message.from_user.last_name)
    except Exception as e:
            raise e
    
    user_steps[cid] = 0
    bot.send_photo(chat_id=cid, photo=open('viz_stat.png', 'rb'))
    start_command_handler(message)

# query coin command handler
@bot.message_handler(commands=['coin'])
@send_action('typing')
@save_user_activity()
def coin_command_handler(message):
    cid = message.chat.id
    user_steps[cid] = 5
    bot.send_message(cid, '{0}, Please write a coin and a currency, /default: TONCOIN:RUB (started from / if you use groups)'.format(message.from_user.first_name + ' ' + message.from_user.last_name))

# coin command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 5)
@send_action('typing')
@save_user_activity()
def coin_currency_command_handler(message):
    cid = message.chat.id
    coin_currency=message.text.strip().replace('/','').split(':')
    
    try:
        if len(coin_currency)==0 or 'default' in coin_currency[0]:
            coin = 'TON'
            currency = 'RUB'
        else:
            coin = coin_currency[0]
            currency = coin_currency[1]
        statistics = coin_service.get_coin_quotes_by_coin_currency(coin,currency, message.from_user.first_name + ' ' + message.from_user.last_name)
    except Exception as e:
        raise e

    user_steps[cid] = 0
    bot.send_message(cid, statistics, parse_mode='HTML')
    start_command_handler(message)

# query chatGPT command handler
@bot.message_handler(commands=['chat'])
@send_action('typing')
@save_user_activity()
def chat_command_handler(message):
    cid = message.chat.id
    user_steps[cid] = 6
    bot.send_message(cid, '{0}, Please write any question for AI'.format(message.from_user.first_name + ' ' + message.from_user.last_name))

# chatGPT command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 6)
@send_action('typing')
@save_user_activity()
def chat_message_command_handler(message):
    cid = message.chat.id
    user_input = message.text
    response_ai = chat_gpt_service.get_response_from_openai(user_input, message.from_user.first_name + ' ' + message.from_user.last_name)
    
    user_steps[cid] = 0
    bot.send_message(chat_id=cid, text=response_ai)
    start_command_handler(message)

# geo command handler
@bot.message_handler(content_types=['location'])
@send_action('typing')
@save_user_activity()
def geo_command_handler(message):
    cid = message.chat.id
    geo_result = country_service.get_country_information(message.location.latitude, message.location.longitude)
    statistics = stats_service.get_statistics_by_country_name(geo_result['countryName'], message.from_user.first_name + ' ' + message.from_user.last_name)
    user_steps[cid] = 0
    bot.send_message(cid, statistics, parse_mode='HTML')

# history statistics command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 2)
@send_action('typing')
@save_user_activity()
def history_statistics_command_handler(message):
    cid = message.chat.id
    country_name = message.text.strip().replace('/','')

    try:
        history_service.get_history_by_country_name(country_name, message.from_user.first_name + ' ' + message.from_user.last_name)
    except Exception as e:
        raise e

    user_steps[cid] = 0
    bot.send_photo(chat_id=cid, photo=open('viz_hist.png', 'rb'))
    start_command_handler(message)

# country statistics command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
@send_action('typing')
@save_user_activity()
def country_statistics_command_handler(message):
    cid = message.chat.id
    country_name = message.text.strip().replace('/','')

    try:
        statistics = stats_service.get_statistics_by_country_name(country_name, message.from_user.first_name + ' ' + message.from_user.last_name)
    except Exception as e:
        raise e

    user_steps[cid] = 0
    bot.send_message(cid, statistics, parse_mode='HTML')
    start_command_handler(message)


# query statistics command handler
@bot.message_handler(commands=['statistics'])
@send_action('typing')
@save_user_activity()
def statistics_command_handler(message):
    cid = message.chat.id
    bot.send_message(cid, stats_service.get_statistics_of_users_queries(), parse_mode='HTML')
    start_command_handler(message)

# contacts command handler
@bot.message_handler(commands=['contacts'])
@send_action('typing')
@save_user_activity()
def contacts_command_handler(message):
    cid = message.chat.id
    with codecs.open('templates/contacts.html', 'r', encoding='UTF-8') as file:
        template = Template(file.read())
        bot.send_message(cid, template.render(user_name=message.from_user.first_name + ' ' + message.from_user.last_name), parse_mode='HTML')
        start_command_handler(message)

# help command handler
@bot.message_handler(commands=['help'])
@send_action('typing')
@save_user_activity()
def help_command_handler(message):
    cid = message.chat.id
    help_text = 'The following commands are available \n*COVID19*:\n'
    for key in commands:
        if key == 'COIN QUOTES':
            help_text += '*COIN QUOTES*:\n'
        else:
            help_text += '/' + key + ': '
            help_text += commands[key] + '\n'
    help_text += '\nZZZBOT speaks english (except of for AI - you can use any language), be careful and take care'
    bot.send_message(cid, help_text)


# hi command handler
@bot.message_handler(func=lambda message: message.text == 'hi')
@send_action('typing')
@save_user_activity()
def hi_command_handler(message):
    cid = message.chat.id
    with codecs.open('templates/himydear.html', 'r', encoding='UTF-8') as file:
        template = Template(file.read())
        bot.send_message(cid, template.render(user_name=message.from_user.first_name + ' ' + message.from_user.last_name), parse_mode='HTML')


# default text messages and hidden statistics command handler
@bot.message_handler(func=lambda message: True, content_types=['text'])
@send_action('typing')
@save_user_activity()
def default_command_handler(message):
    cid = message.chat.id
    if message.text[:int(os.getenv('PASS_CHAR_COUNT'))] == os.getenv('STAT_KEY'):
        try:
            st = message.text.split(' ')
            if 'txt' in st:
                tga.analysis(st, cid)
                with codecs.open('%s.txt' % cid, 'r', encoding='UTF-8') as file:
                    bot.send_document(cid, file)
                    file.close()
                    tga.remove(cid)
            else:
                messages = tga.analysis(st, cid)
                bot.send_message(cid, messages)
        except Exception as e:
            raise e
    else:
        with codecs.open('templates/idunnocommand.html', 'r', encoding='UTF-8') as file:
            template = Template(file.read())
            bot.send_message(cid, template.render(text_command=message.text), parse_mode='HTML')

if os.getenv('local') == 'true':
    # application entry point
    if __name__ == '__main__':
        # Create the job in schedule.
        schedule.every().day.at("10:30").do(autorun_job)
        Thread(target=schedule_checker).start() 
        bot.polling(none_stop=True, interval=0)
else:
    # set web hook
    server = Flask(__name__)

    @server.route('/' + token, methods=['POST'])
    def get_messages():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode('utf-8'))])
        return '!', 200

    @server.route('/')
    def web_hook():
        bot.remove_webhook()
        bot.set_webhook(url=os.getenv('HEROKU_URL') + token)
        return '!', 200

    # application entry point
    if __name__ == '__main__':
        # Create the job in schedule.
        schedule.every().day.at("10:30").do(autorun_job)
        Thread(target=schedule_checker).start() 
        server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8443)))

