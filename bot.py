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
OPENAI_ENGINE = os.environ.get('OPENAI_ENGINE', 'gpt-3.5-turbo')

if OPENAI_API_KEY is None:
    sys.exit("OPENAI_API_KEY not setted ")

if BOT_TOKEN is None:
    sys.exit("BOT_TOKEN not setted ")

openai.api_key = OPENAI_API_KEY
DEFAULT_CONTEXT = """Следующий диалог - разговор с AI-ботом помощником.
Бот может использовать эмоджи и иногда вести small talk.
Далее несколько примеров как бот может отвечать на пользовательские вопросы:

Вот пример:
Human: У меня проблемы с моим заказом.
AI: О нет, что произошло? Я хочу вам помочь. 
AI: Ну это жалко. Давайте посмотрим, что я могу сделать, чтобы уладить ситуацию. 
AI: Хорошо, я вижу проблему. Я могу немедленно отправить правильный товар вам. Когда он отправится, я пришлю вам лично номер отслеживания. 
Human: Большое спасибо!
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
Далее наш текущий чат, продолжай отвечать в этом контексте:
{previous_messages_str}
user: {prompt}
assistant:"""
    return enriched_prompt

@dp.message_handler(filters.Text)
async def process_default_message(message: types.Message):
    message_text = message.text

    cached_info, username = get_cached_info(message)
    previous_messages = cached_info.get("previous_messages", [])
    context = cached_info.get("context", DEFAULT_CONTEXT)
    if len(context) < 5:
        context = DEFAULT_CONTEXT
    
    previous_messages.append({"role": "user", "content": message_text})
    promt = enrichUserPromptWithContext(message_text, previous_messages, context)
    if DEBUG == "True":
        print(cached_info)
        print(len(previous_messages))
        print(promt)
    response = openai.ChatCompletion.create(
        model = OPENAI_ENGINE,
        #prompt = promt,
        #max_tokens = 1000,
        messages = previous_messages
    )
    answer = response.choices[0]["message"]["content"]
    previous_messages.append({"role": "assistant", "content": answer})
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