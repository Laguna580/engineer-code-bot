import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types

# Токен будет браться из переменных окружения Railway
API_TOKEN = os.getenv('BOT_TOKEN')

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def generate_code() -> str:
    """Генерирует код по формуле: #*[месяц+5][день][час в 12-ч формате]"""
    now = datetime.now()

    # 1. Месяц (1-12) + 5
    month_part = now.month + 5

    # 2. Текущий день месяца
    day_part = now.day

    # 3. Час в 12-часовом формате (1-12)
    hour_12 = now.hour % 12
    if hour_12 == 0:
        hour_12 = 12
    hour_part = hour_12

    return f"#*{month_part}{day_part}{hour_part}"


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Привет! Я бот для генерации кода в инженерное меню.\n"
        "Отправь команду /code"
    )


@dp.message_handler(commands=['code'])
async def send_code(message: types.Message):
    try:
        code = generate_code()
        now = datetime.now()

        await message.answer(
            f"📅 Дата: {now.strftime('%d.%m.%Y')}\n"
            f"🕒 Время: {now.strftime('%H:%M')}\n"
            f"🔑 Код для входа: <b>{code}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer("❌ Ошибка при генерации кода")
        logging.error(f"Error: {e}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)