from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import os
import logging
import openai
import os
from aiogram.dispatcher import filters
import sys

# Установка ключа API OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
BOT_TOKEN = os.environ.get('BOT_TOKEN', None)
MODE = os.environ.get('MODE', 'DEV')
MESSAGES_HISTORY_LEN = 15
DEBUG = os.environ.get('DEBUG', 'True')

if OPENAI_API_KEY is None:
    sys.exit("OPENAI_API_KEY not setted ")

if BOT_TOKEN is None:
    sys.exit("BOT_TOKEN not setted ")

openai.api_key = OPENAI_API_KEY
DEFAULT_CONTEXT = """The following is a conversation with an AI-powered bot.
The bot occasionally uses emojis, and sometimes makes small talk.
Here is example of how the bot might respond to a customer's question:

Here's example:
Human: I am having trouble with my order.
AI: Oh no! What seems to be the problem? I want to help.
Human: The item I ordered is not what I expected.
AI: Well that's not good. I'm sorry to hear that. Let me see I can do to make things right.
AI: Okay, I see the problem. I can get the correct item shipped out to you right away. I'll personally send you a tracking number when it ships.
Human: Thank you so much!
"""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
users = {}


def get_cached_info(message: types.Message):
    username = message["from"]["username"]
    if username not in users.keys():
        users[username] = {}
    return users.get(username, {}), username

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply(f"""Привет!
Я чат бот. Я запоминаю твои последние {MESSAGES_HISTORY_LEN} сообщений
Команды:
  /r - очистить историю сообщений
  /c - задать контекст (то что должно определять базовое поведение бота)""")

@dp.message_handler(commands=['u'])
async def process_help_command(message: types.Message):
    cached_info = get_cached_info(message)
    
    logging.debug(f"users:{users.keys()}")
    print(f"users:{users.keys()}")

@dp.message_handler(commands=['r'])
async def process_help_command(message: types.Message):
    cached_info, username = get_cached_info(message)
    users[username]["previous_messages"] = []
    print(f"история запросов для {username} очищена")

@dp.message_handler(commands=['c'])
async def process_help_command(message: types.Message):
    cached_info, username = get_cached_info(message)
    context = message.text[2:]
    users[username]["context"] = context
    print(f"контекст для {username}:\n{context}")

def enrichUserPromptWithContext(context, prompt, previous_messages):
    previous_messages_str = "\n".join(previous_messages)
    enriched_prompt = f"""{context}
Here's our current chat, continue answer in this context:
{previous_messages_str}

Human: {prompt}
AI:"""
    return enriched_prompt

@dp.message_handler(filters.Text)
async def process_default_message(message: types.Message):
    message_text = message.text

    cached_info, username = get_cached_info(message)
    previous_messages = cached_info.get("previous_messages", [])
    context = cached_info.get("context", DEFAULT_CONTEXT)
    if len(context) < 5:
        context = DEFAULT_CONTEXT
    
    previous_messages.append("Human: " + message_text)
    promt = enrichUserPromptWithContext(message_text, previous_messages, context)
    if DEBUG == "True":
        print(cached_info)
        print(len(previous_messages))
        print(promt)
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt = promt,
        max_tokens = 1000
    )
    answer = response.choices[0].text
    previous_messages.append("AI:" + answer)
    if len(answer) <= 1:
        answer = "[...hm...]"
    if len(previous_messages) > MESSAGES_HISTORY_LEN:
        previous_messages.pop(0)
        previous_messages.pop(1)
    users[username]["previous_messages"] = previous_messages
    if DEBUG == "True":
        print(len(answer))
        print(users[username])
    logging.info(f"\nmessage_text:{message_text}\n answer: {answer}")
    await message.reply(answer)
    
if __name__ == '__main__':
    executor.start_polling(dp)