import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

API_TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def generate_code_for_time(target_time: datetime) -> str:
    """Генерирует код для конкретного времени"""
    month_part = target_time.month + 5
    day_part = target_time.day
    hour_12 = target_time.hour % 12
    if hour_12 == 0:
        hour_12 = 12
    hour_part = hour_12
    
    return f"#*{month_part}{day_part}{hour_part}"

def generate_codes_for_day() -> list:
    """Генерирует коды на все часы текущего дня"""
    now = datetime.now()
    codes = []
    
    # Генерируем для каждого часа с 00:00 до 23:00
    for hour in range(24):
        time_point = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        # Пропускаем прошедшие часы (опционально)
        # if time_point < now:
        #     continue
            
        code = generate_code_for_time(time_point)
        time_str = time_point.strftime("%H:%M")
        codes.append((time_str, code))
    
    return codes

@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    await message.answer(
        "👋 Привет! Я бот для генерации кода в инженерное меню.\n\n"
        "📌 Доступные команды:\n"
        "/code — код на текущее время\n"
        "/daycodes — все коды на сегодня (по часам)\n"
        "/now — показать текущее время\n\n"
        "🤖 Я работаю в группах и личных сообщениях"
    )

@dp.message(Command("now"))
async def send_current_time(message: Message):
    now = datetime.now()
    await message.answer(
        f"🕒 Текущее время: {now.strftime('%d.%m.%Y %H:%M')}"
    )

@dp.message(Command("code"))
async def send_code(message: Message):
    try:
        code = generate_code_for_time(datetime.now())
        now = datetime.now()
        
        await message.answer(
            f"📅 {now.strftime('%d.%m.%Y')}\n"
            f"🕒 {now.strftime('%H:%M')}\n"
            f"🔑 <b>{code}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer("❌ Ошибка при генерации кода")
        logger.error(f"Error in /code: {e}")

@dp.message(Command("daycodes"))
async def send_day_codes(message: Message):
    try:
        codes = generate_codes_for_day()
        now = datetime.now()
        
        # Формируем красивое сообщение
        response = f"📅 <b>Коды на {now.strftime('%d.%m.%Y')}</b>\n\n"
        
        # Разбиваем на блоки по 6 часов для читаемости
        blocks = [codes[i:i+6] for i in range(0, len(codes), 6)]
        
        for block in blocks:
            for time_str, code in block:
                response += f"{time_str}  <b>{code}</b>\n"
            response += "\n"
        
        response += "⏰ Коды указаны для каждого часа"
        
        await message.answer(response, parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Ошибка при генерации кодов")
        logger.error(f"Error in /daycodes: {e}")

async def main():
    logger.info("Bot started")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
