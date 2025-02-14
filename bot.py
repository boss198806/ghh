import os
import openai
import logging
import re
import requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

# Получаем токены из переменных окружения (секреты Railway)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Настройка API ключа OpenAI
openai.api_key = OPENAI_API_KEY

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния разговора
START, BIRTHDATE, QUESTION = range(3)

# Функция для проверки корректности даты
def is_valid_date(date_string):
    # Проверяем, соответствует ли строка формату ДД.ММ.ГГГГ
    date_pattern = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
    return bool(date_pattern.match(date_string))

# Функция для генерации текста с помощью OpenAI
def generate_text(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating text: {e}")
        return "Извините, произошла ошибка при обработке вашего запроса."

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    image_url = "https://github.com/boss198806/ghh/blob/main/IMG_9235.JPG?raw=true"
    await update.message.reply_photo(photo=image_url)

    reply_keyboard = [['Расчет числа жизненного пути', 'Задать вопрос']]
    await update.message.reply_text(
        'Привет! Я ваш бот-нумеролог. Что вы хотите сделать?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return START

def calculate_life_path_number(birthdate):
    digits = [int(char) for char in birthdate if char.isdigit()]
    total = sum(digits)
    life_path_number = (total - 1) % 9 + 1
    return life_path_number

async def ask_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Пожалуйста, введите вашу дату рождения в формате ДД.ММ.ГГГГ')
    return BIRTHDATE

async def handle_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    birthdate = update.message.text
    if not is_valid_date(birthdate):
        await update.message.reply_text('Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.')
        return BIRTHDATE

    life_path_number = calculate_life_path_number(birthdate)
    await update.message.reply_text(f'Ваше число жизненного пути: {life_path_number}')

    keyboard = [[InlineKeyboardButton("Связаться с @MininaKsuisha", url="https://t.me/MininaKsuisha")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Если у вас есть дополнительные вопросы, вы можете связаться со мной:', reply_markup=reply_markup)

    return ConversationHandler.END

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Пожалуйста, задайте ваш вопрос.')
    return QUESTION

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text
    response_text = generate_text(user_message)
    await update.message.reply_text(response_text)

    keyboard = [[InlineKeyboardButton("Связаться с @MininaKsuisha", url="https://t.me/MininaKsuisha")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Если у вас есть дополнительные вопросы, вы можете связаться со мной:', reply_markup=reply_markup)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('До свидания! Если у вас возникнут вопросы, не стесняйтесь обращаться.')
    return ConversationHandler.END

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [MessageHandler(filters.Regex('^Расчет числа жизненного пути$'), ask_birthdate),
                    MessageHandler(filters.Regex('^Задать вопрос$'), handle_question)],
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_birthdate)],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    # Установите вебхук
    webhook_url = 'https://your-domain.com/webhook'  # Замените на ваш URL вебхука
    await application.bot.set_webhook(url=webhook_url)

    # Запустите приложение
    application.run_webhook(listen='0.0.0.0', port=8443, webhook_url=webhook_url)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
