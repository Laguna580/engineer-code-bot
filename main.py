import logging
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F

# ========== НАСТРОЙКИ ==========
API_TOKEN = os.getenv('BOT_TOKEN')  # Токен бота из переменных окружения

# ⚠️ ВАЖНО: Укажите ID группы и ветки, куда отправлять коды
GROUP_CHAT_ID = -1002828047738  # ID группы (отрицательное число для супергрупп)
TARGET_THREAD_ID = 1743        # ID ветки (узнать через @GetIDsBot)

# Время автоматической отправки (часы:минуты)
SCHEDULE_HOUR = 19    # Час (0-23)
SCHEDULE_MINUTE = 3  # Минута (0-59)

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ========== ФУНКЦИИ ГЕНЕРАЦИИ КОДОВ ==========
def generate_code_for_time(target_time: datetime) -> str:
    """
    Генерирует код для конкретного времени по формуле:
    #*[месяц+5][день][час в 12-ч формате]
    """
    month_part = target_time.month + 5
    day_part = target_time.day
    hour_12 = target_time.hour % 12
    if hour_12 == 0:
        hour_12 = 12
    hour_part = hour_12
    
    return f"#*{month_part}{day_part}{hour_part}"

def generate_codes_for_day() -> list:
    """Генерирует коды на все часы текущего дня (00:00 - 23:00)"""
    now = datetime.now()
    codes = []
    
    for hour in range(24):
        time_point = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        code = generate_code_for_time(time_point)
        time_str = time_point.strftime("%H:%M")
        codes.append((time_str, code))
    
    return codes

def format_codes_message(codes: list, date: datetime) -> str:
    """Форматирует список кодов в красивое сообщение"""
    response = f"📅 <b>Коды на {date.strftime('%d.%m.%Y')}</b>\n\n"
    
    # Разбиваем на блоки по 6 часов для читаемости
    blocks = [codes[i:i+6] for i in range(0, len(codes), 6)]
    
    for block in blocks:
        for time_str, code in block:
            response += f"{time_str}  <b>{code}</b>\n"
        response += "\n"
    
    response += "⏰ Коды указаны для каждого часа"
    return response

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    """Приветственное сообщение"""
    await message.answer(
        "👋 Привет! Я бот для генерации кода в инженерное меню.\n\n"
        "📌 Доступные команды:\n"
        "/code — код на текущее время\n"
        "/daycodes — все коды на сегодня\n"
        "/now — показать текущее время\n"
        "/send_to_topic — принудительно отправить коды в заданную ветку\n\n"
        "🤖 Я работаю в группах и личных сообщениях"
    )

@dp.message(Command("now"))
async def send_current_time(message: Message):
    """Показывает текущее время"""
    now = datetime.now()
    await message.answer(
        f"🕒 Текущее время: {now.strftime('%d.%m.%Y %H:%M')}"
    )

@dp.message(Command("code"))
async def send_code(message: Message):
    """Отправляет код на текущее время"""
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
    """Отправляет все коды на сегодня"""
    try:
        codes = generate_codes_for_day()
        now = datetime.now()
        response = format_codes_message(codes, now)
        
        await message.answer(response, parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Ошибка при генерации кодов")
        logger.error(f"Error in /daycodes: {e}")

@dp.message(Command("send_to_topic"))
async def send_to_specific_topic(message: Message):
    """
    Принудительно отправляет коды в заданную ветку.
    Полезно для тестирования или ручной отправки.
    """
    try:
        codes = generate_codes_for_day()
        now = datetime.now()
        response = format_codes_message(codes, now)
        
        # Отправляем в конкретную ветку
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=TARGET_THREAD_ID,
            text=response,
            parse_mode="HTML"
        )
        
        await message.reply(f"✅ Сообщение отправлено в ветку {TARGET_THREAD_ID}")
        
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")
        logger.error(f"Error in /send_to_topic: {e}")

# ========== АВТОМАТИЧЕСКАЯ ОТПРАВКА ПО РАСПИСАНИЮ ==========
async def scheduled_job():
    """
    Фоновая задача, которая запускается каждый день в указанное время
    и отправляет коды в заданную ветку.
    """
    while True:
        try:
            now = datetime.now()
            
            # Вычисляем время следующего запуска
            next_run = now.replace(
                hour=SCHEDULE_HOUR, 
                minute=SCHEDULE_MINUTE, 
                second=0, 
                microsecond=0
            )
            
            # Если время сегодня уже прошло, переносим на завтра
            if now >= next_run:
                next_run += timedelta(days=1)
            
            # Ждем до следующего запуска
            sleep_seconds = (next_run - now).total_seconds()
            logger.info(f"Следующая отправка запланирована на {next_run.strftime('%d.%m.%Y %H:%M')}")
            await asyncio.sleep(sleep_seconds)
            
            # Генерируем и отправляем коды
            codes = generate_codes_for_day()
            now = datetime.now()
            response = format_codes_message(codes, now)
            
            await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=TARGET_THREAD_ID,
                text=response,
                parse_mode="HTML"
            )
            logger.info(f"✅ Коды успешно отправлены в ветку {TARGET_THREAD_ID}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в scheduled_job: {e}")
            # В случае ошибки ждем час и пробуем снова
            await asyncio.sleep(3600)

# ========== ЗАПУСК БОТА ==========
async def main():
    """Главная функция запуска бота"""
    # Проверяем наличие токена
    if not API_TOKEN:
        logger.error("❌ Не задан BOT_TOKEN в переменных окружения!")
        return
    
    logger.info(f"🚀 Бот запускается...")
    logger.info(f"📢 Будет отправлять коды в группу {GROUP_CHAT_ID}, ветка {TARGET_THREAD_ID}")
    logger.info(f"⏰ Ежедневная отправка в {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")
    
    # Запускаем фоновую задачу для автоматической отправки
    asyncio.create_task(scheduled_job())
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())




