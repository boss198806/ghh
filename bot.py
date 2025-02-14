import os
import logging
import openai
import requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

# Настройте ваш API ключ от OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Включите логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния разговора
START, BIRTHDATE, QUESTION = range(3)

# Функция для генерации текста с помощью OpenAI
def generate_text(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    data = {
        "model": "gpt-4o-mini",
        "store": True,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response_data = response.json()
    return response_data['choices'][0]['message']['content'].strip()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Расчет числа жизненного пути', 'Задать вопрос']]
    await update.message.reply_text(
        'Привет! Я ваш бот-нумеролог. Что вы хотите сделать?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return START

# Обработчик для расчета числа жизненного пути
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
    life_path_number = calculate_life_path_number(birthdate)
    await update.message.reply_text(f'Ваше число жизненного пути: {life_path_number}')

    keyboard = [[InlineKeyboardButton("Связаться с @MininaKsuisha", url="https://t.me/MininaKsuisha")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Если у вас есть дополнительные вопросы, вы можете связаться со мной:', reply_markup=reply_markup)

    return ConversationHandler.END

# Обработчик входящих сообщений
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
    # Получение токена из переменных окружения
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_bot_token:
        logger.error("Telegram bot token is not set.")
        return

    # Вставьте ваш токен от BotFather
    application = ApplicationBuilder().token(telegram_bot_token).build()

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

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
