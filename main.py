import logging
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import pytz  # Новая библиотека для работы с часовыми поясами

# ========== НАСТРОЙКИ ==========
API_TOKEN = os.getenv('BOT_TOKEN')  # Токен бота из переменных окружения

# ⚠️ ВАЖНО: Укажите ID группы и ветки, куда отправлять коды
GROUP_CHAT_ID = -1001234567890  # ID группы (отрицательное число для супергрупп)
TARGET_THREAD_ID = 12345        # ID ветки (узнать через @GetIDsBot)

# ========== НАСТРОЙКА ЧАСОВОГО ПОЯСА ==========
# Список популярных поясов: Europe/Moscow, Europe/Kiev, Europe/Minsk, Asia/Yekaterinburg, etc.
TIMEZONE = pytz.timezone('Europe/Moscow')  # <-- ИЗМЕНИТЕ НА ВАШ ПОЯС!

# Время автоматической отправки (часы:минуты) в МЕСТНОМ времени
SCHEDULE_HOUR = 0    # Час (0-23) по местному времени
SCHEDULE_MINUTE = 1  # Минута (0-59) по местному времени

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
def get_local_time() -> datetime:
    """Возвращает текущее время в заданном часовом поясе"""
    return datetime.now(TIMEZONE)

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
    """Генерирует коды на все часы текущего дня (00:00 - 23:00) по местному времени"""
    now_local = get_local_time()
    codes = []
    
    for hour in range(24):
        # Создаем время для каждого часа сегодня
        time_point = now_local.replace(hour=hour, minute=0, second=0, microsecond=0)
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
    
    response += f"⏰ Коды указаны для каждого часа (по местному времени {TIMEZONE})"
    return response

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    """Приветственное сообщение"""
    await message.answer(
        "👋 Привет! Я бот для генерации кода в инженерное меню.\n\n"
        f"🌍 Часовой пояс: {TIMEZONE}\n\n"
        "📌 Доступные команды:\n"
        "/code — код на текущее время\n"
        "/daycodes — все коды на сегодня\n"
        "/now — показать текущее время\n"
        "/send_to_topic — принудительно отправить коды в заданную ветку\n\n"
        "/timezone — показать текущий часовой пояс\n\n"
        "🤖 Я работаю в группах и личных сообщениях"
    )

@dp.message(Command("timezone"))
async def show_timezone(message: Message):
    """Показывает текущий часовой пояс"""
    now_local = get_local_time()
    now_utc = datetime.now(pytz.UTC)
    
    await message.answer(
        f"🌍 Часовой пояс бота: <b>{TIMEZONE}</b>\n"
        f"🕒 Местное время: {now_local.strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"🕐 UTC время: {now_utc.strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"📊 Разница с UTC: {(now_local.utcoffset().total_seconds() / 3600):+.0f} часов",
        parse_mode="HTML"
    )

@dp.message(Command("now"))
async def send_current_time(message: Message):
    """Показывает текущее время"""
    now_local = get_local_time()
    await message.answer(
        f"📅 {now_local.strftime('%d.%m.%Y')}\n"
        f"🕒 {now_local.strftime('%H:%M:%S')}\n"
        f"🌍 Часовой пояс: {TIMEZONE}"
    )

@dp.message(Command("code"))
async def send_code(message: Message):
    """Отправляет код на текущее время"""
    try:
        now_local = get_local_time()
        code = generate_code_for_time(now_local)
        
        await message.answer(
            f"📅 {now_local.strftime('%d.%m.%Y')}\n"
            f"🕒 {now_local.strftime('%H:%M')}\n"
            f"🔑 <b>{code}</b>\n"
            f"🌍 {TIMEZONE}",
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
        now_local = get_local_time()
        response = format_codes_message(codes, now_local)
        
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
        now_local = get_local_time()
        response = format_codes_message(codes, now_local)
        
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
    (по местному времени) и отправляет коды в заданную ветку.
    """
    while True:
        try:
            now_local = get_local_time()
            
            # Вычисляем время следующего запуска в МЕСТНОМ времени
            next_run_local = now_local.replace(
                hour=SCHEDULE_HOUR, 
                minute=SCHEDULE_MINUTE, 
                second=0, 
                microsecond=0
            )
            
            # Если время сегодня уже прошло, переносим на завтра
            if now_local >= next_run_local:
                next_run_local += timedelta(days=1)
            
            # Переводим время следующего запуска в UTC для ожидания
            # (asyncio.sleep использует системное время, которое на сервере UTC)
            next_run_utc = next_run_local.astimezone(pytz.UTC)
            now_utc = datetime.now(pytz.UTC)
            
            # Ждем до следующего запуска
            sleep_seconds = (next_run_utc - now_utc).total_seconds()
            
            logger.info(f"📅 Следующая отправка запланирована на {next_run_local.strftime('%d.%m.%Y %H:%M')} (местное время)")
            logger.info(f"⏰ Это соответствует {next_run_utc.strftime('%d.%m.%Y %H:%M')} UTC")
            
            await asyncio.sleep(max(0, sleep_seconds))
            
            # Генерируем и отправляем коды
            codes = generate_codes_for_day()
            now_local = get_local_time()
            response = format_codes_message(codes, now_local)
            
            await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=TARGET_THREAD_ID,
                text=response,
                parse_mode="HTML"
            )
            logger.info(f"✅ Коды успешно отправлены в ветку {TARGET_THREAD_ID} в {now_local.strftime('%H:%M')}")
            
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
    logger.info(f"🌍 Часовой пояс: {TIMEZONE}")
    logger.info(f"📢 Будет отправлять коды в группу {GROUP_CHAT_ID}, ветка {TARGET_THREAD_ID}")
    logger.info(f"⏰ Ежедневная отправка в {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} по местному времени")
    
    # Запускаем фоновую задачу для автоматической отправки
    asyncio.create_task(scheduled_job())
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
