import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
import asyncio

API_TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def generate_code() -> str:
    """Генерирует код по формуле: #*[месяц+5][день][час в 12-ч формате]"""
    now = datetime.now()
    
    month_part = now.month + 5
    day_part = now.day
    hour_12 = now.hour % 12
    if hour_12 == 0:
        hour_12 = 12
    hour_part = hour_12
    
    return f"#*{month_part}{day_part}{hour_part}"

@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    await message.answer(
        "Привет! Я бот для генерации кода в инженерное меню.\n"
        "Отправь команду /code"
    )

@dp.message(Command("code"))
async def send_code(message: Message):
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

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
