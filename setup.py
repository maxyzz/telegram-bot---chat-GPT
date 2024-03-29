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
            'chat_gpt_text': 'chatGDP: type any questions for text answer',
            'chat_gpt_image': 'chatGDP: type any questions for image answer'
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

#This will generate buttons for us in more elegant way
def generate_buttons(bts_names, markup):
    for button in bts_names:
        markup.add(telebot.types.InlineKeyboardButton(text = button[0], callback_data =button[1]))
    return markup

# start command handler
@bot.message_handler(commands=['start','menu'])
@send_action('typing')
@save_user_activity()
def start_command_handler(message):
    cid = message.chat.id
    menu1 = telebot.types.InlineKeyboardMarkup()
    btn11=telebot.types.InlineKeyboardButton(text = 'COVID-19', callback_data ='covid')
    # btn11=telebot.types.InlineKeyboardButton(text = 'COVID 19: country', callback_data ='country')
    # btn12=telebot.types.InlineKeyboardButton(text = 'COVID 19: history', callback_data ='history')
    # btn13=telebot.types.InlineKeyboardButton(text = 'COVID 19: top', callback_data ='top')
    menu1.row(btn11)
    btn21=telebot.types.InlineKeyboardButton(text = 'Chat GPT', callback_data ='chatgpt')
    # btn21=telebot.types.InlineKeyboardButton(text = 'ChatGPT: text', callback_data ='chatgpt-text')
    # btn22=telebot.types.InlineKeyboardButton(text = 'ChatGPT: image', callback_data ='chatgpt-image')
    menu1.row(btn21)
    btn31=telebot.types.InlineKeyboardButton(text = 'COIN QUOTES: coin', callback_data ='coin')
    btn32=telebot.types.InlineKeyboardButton(text = 'ADM: Stats', callback_data ='statistics')
    menu1.row(btn31,btn32)
    btn41=telebot.types.InlineKeyboardButton(text = 'Contacts', callback_data ='contacts')
    btn42=telebot.types.InlineKeyboardButton(text = 'Help', callback_data ='help')
    menu1.row(btn41,btn42)
    bot.send_message(cid, '{0}, please choose command from the menu'.format(message.from_user.first_name + ' ' + message.from_user.last_name),
                     reply_markup=menu1)
    # help_command_handler(message)

@bot.callback_query_handler(func=lambda call: True)
def step2(call):
    if hasattr(call, 'data'):
        call.message.from_user.first_name=call.from_user.first_name
        call.message.from_user.last_name=call.from_user.last_name
    if call.data == 'covid':
        #Generating keyboard markup
        markup = telebot.types.InlineKeyboardMarkup()
        markup = generate_buttons([['COVID 19: country','covid-country'],
                                ['COVID 19: history','covid-history'],
                                ['COVID 19: top','covid-top'],
                                ['back to main MENU','menu']], markup)
        bot.send_message(call.message.chat.id,
                                '{0}, please choose command from the menu'.format(call.from_user.first_name + ' ' + call.from_user.last_name),
                                reply_markup=markup)
    elif call.data == 'covid-country':
        country_command_handler(call.message)
    elif call.data == 'statistics':
        statistics_command_handler(call.message)
    elif call.data == 'help':
        help_command_handler(call.message)
    elif call.data == 'chatgpt':
        #Generating keyboard markup
        markup = telebot.types.InlineKeyboardMarkup()
        markup = generate_buttons([['ChatGPT: text','chatgpt-text'],
                                ['ChatGPT: image','chatgpt-image'],
                                ['back to main MENU','menu']], markup)
        bot.send_message(call.message.chat.id,
                                '{0}, please choose command from the menu'.format(call.from_user.first_name + ' ' + call.from_user.last_name),
                                reply_markup=markup)
    elif call.data == 'chatgpt-text':
        chat_command_handler(call.message)
    elif call.data == 'chatgpt-image':
        chat_command_image_handler(call.message)
    elif call.data == 'covid-history':
        history_command_handler(call.message)
    elif call.data == 'covid-top':
        #Generating keyboard markup
        markup = telebot.types.InlineKeyboardMarkup()
        markup = generate_buttons([['COVID 19: top 20 country deaths','covid-deaths'],
                                ['COVID 19: top 20 country daily cases','covid-daily-cases'],
                                ['back to main MENU','menu']], markup)
        bot.send_message(call.message.chat.id,
                                '{0}, please choose command from the menu'.format(call.from_user.first_name + ' ' + call.from_user.last_name),
                                reply_markup=markup)
        top_20_country_command_menu_handler(call.message)
    elif call.data == 'coin':
        coin_command_handler(call.message)
    elif call.data == 'contacts':
        contacts_command_handler(call.message)
    elif call.data == 'menu':
        start_command_handler(call.message)
    elif call.data == 'covid-deaths':
        call.message.text='1'
        top_20_country_death_command_handler(call.message)
    elif call.data == 'covid-daily-cases':
        call.message.text='2'
        top_20_country_death_command_handler(call.message)

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
    cid = message.chat.id
    user_steps[cid] = 4
    bot.send_message(cid, '{0}, please select /1 to view top 20 country deaths or /2 to view top 20 country daily cases'.format(message.from_user.first_name + ' ' + message.from_user.last_name))

# top 20 countries command menu handler
@bot.message_handler(commands=['top'])
@send_action('typing')
@save_user_activity()
def top_20_country_command_menu_handler(message):
    cid = message.chat.id
    user_steps[cid] = 4

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
    bot.send_photo(chat_id=cid, photo=open('images/viz_stat.png', 'rb'))
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

# query chatGPT text command handler
@bot.message_handler(commands=['chat_gpt_text'])
@send_action('typing')
@save_user_activity()
def chat_command_handler(message):
    cid = message.chat.id
    user_steps[cid] = 6
    bot.send_message(cid, '{0}, Please write any question for AI'.format(message.from_user.first_name + ' ' + message.from_user.last_name))

# chatGPT text command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 6)
@send_action('typing')
@save_user_activity()
def chat_message_command_handler(message):
    cid = message.chat.id
    user_input = message.text
    response_ai = chat_gpt_service.get_response_from_openai(user_input, message.from_user.first_name + ' ' + message.from_user.last_name)
    
    user_steps[cid] = 6
    bot.send_message(chat_id=cid, text=response_ai)
    # start_command_handler(message)

# query chatGPT image command handler
@bot.message_handler(commands=['chat_gpt_image'])
@send_action('typing')
@save_user_activity()
def chat_command_image_handler(message):
    cid = message.chat.id
    user_steps[cid] = 7
    bot.send_message(cid, '{0}, Please write any question for AI'.format(message.from_user.first_name + ' ' + message.from_user.last_name))

# chatGPT image command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 7)
@send_action('typing')
@save_user_activity()
def chat_message_command_image_handler(message):
    cid = message.chat.id
    user_input = message.text
    chat_gpt_service.get_image_response_from_openai(user_input, message.from_user.first_name + ' ' + message.from_user.last_name)

    user_steps[cid] = 7
    bot.send_photo(chat_id=cid, photo=open('images/viz_responseAI.png', 'rb'))
    # start_command_handler(message)

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
        # start_command_handler(message)

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

