import logging
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import pytz

# ========== НАСТРОЙКИ ==========
API_TOKEN = os.getenv('BOT_TOKEN')

# ID группы и ветки (замените на свои!)
GROUP_CHAT_ID = -1001234567890
TARGET_THREAD_ID = 12345

# Часовой пояс для отображения (можно оставить Europe/Moscow)
DISPLAY_TIMEZONE = pytz.timezone('Europe/Moscow')

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ========== ДАННЫЕ О ЧАСОВЫХ ПОЯСАХ ==========
TIMEZONES = [
    {"name": "UTC−11", "offset": -11, "code_suffix": "830"},   # 00:40
    {"name": "UTC−10", "offset": -10, "code_suffix": "831"},   # 01:40
    {"name": "UTC−9",  "offset": -9,  "code_suffix": "8210"},  # 02:40? уточнить
    {"name": "UTC−8",  "offset": -8,  "code_suffix": "8211"},  # 03:40
    {"name": "UTC−7",  "offset": -7,  "code_suffix": "8212"},  # 04:40
    {"name": "UTC−6",  "offset": -6,  "code_suffix": "8213"},  # 05:40
    {"name": "UTC−5",  "offset": -5,  "code_suffix": "8214"},  # 06:40
    {"name": "UTC−4",  "offset": -4,  "code_suffix": "8215"},  # 07:40
    {"name": "UTC−3",  "offset": -3,  "code_suffix": "8216"},  # 08:40
    {"name": "UTC−2",  "offset": -2,  "code_suffix": "8217"},  # 09:40
    {"name": "UTC−1",  "offset": -1,  "code_suffix": "8218"},  # 10:40
    {"name": "UTC+0",  "offset": 0,   "code_suffix": "8219"},  # 11:40? уточнить
    {"name": "UTC+1",  "offset": 1,   "code_suffix": "822"},   # 12:40
    {"name": "UTC+2",  "offset": 2,   "code_suffix": "823"},   # 13:40
    {"name": "UTC+3",  "offset": 3,   "code_suffix": "824"},   # 14:40
    {"name": "UTC+4",  "offset": 4,   "code_suffix": "825"},   # 15:40
    {"name": "UTC+5",  "offset": 5,   "code_suffix": "826"},   # 16:40
    {"name": "UTC+6",  "offset": 6,   "code_suffix": "827"},   # 17:40
    {"name": "UTC+7",  "offset": 7,   "code_suffix": "828"},   # 18:40
    {"name": "UTC+8",  "offset": 8,   "code_suffix": "829"},   # 19:40
    {"name": "UTC+9",  "offset": 9,   "code_suffix": "8210"},  # 20:40
    {"name": "UTC+10", "offset": 10,  "code_suffix": "8211"},  # 21:40
    {"name": "UTC+11", "offset": 11,  "code_suffix": "830"},   # 22:40
    {"name": "UTC+12", "offset": 12,  "code_suffix": "831"},   # 23:40
]

# ========== ФУНКЦИИ ГЕНЕРАЦИИ КОДОВ ==========
def get_local_time(timezone_name: str = 'Europe/Moscow') -> datetime:
    """Возвращает текущее время в указанном часовом поясе"""
    tz = pytz.timezone(timezone_name)
    return datetime.now(tz)

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

def generate_code_for_offset(offset_hours: int) -> str:
    """
    Генерирует код для указанного смещения UTC
    Использует время UTC + смещение
    """
    utc_now = datetime.now(pytz.UTC)
    local_time = utc_now + timedelta(hours=offset_hours)
    return generate_code_for_time(local_time)

def generate_all_timezone_codes() -> dict:
    """
    Генерирует коды для всех часовых поясов
    Возвращает словарь: название пояса -> код
    """
    codes = {}
    utc_now = datetime.now(pytz.UTC)
    
    for tz_info in TIMEZONES:
        local_time = utc_now + timedelta(hours=tz_info["offset"])
        code = generate_code_for_time(local_time)
        codes[tz_info["name"]] = code
    
    return codes

def format_codes_message(codes: dict, update_time: datetime) -> str:
    """Форматирует сообщение со всеми кодами"""
    # Сортируем пояса по offset
    sorted_timezones = sorted(TIMEZONES, key=lambda x: x["offset"])
    
    response = (
        f"🔄 <b>Коды обновлены</b>\n"
        f"📅 {update_time.strftime('%d.%m.%Y')}\n"
        f"🕒 {update_time.strftime('%H:%M:%S')} (МСК)\n\n"
    )
    
    # Группируем по 4 пояса в строке для компактности
    for i in range(0, len(sorted_timezones), 4):
        row = sorted_timezones[i:i+4]
        line = ""
        for tz in row:
            code = codes.get(tz["name"], "N/A")
            # Форматируем: "UTC+3  #*824"
            line += f"{tz['name']:8} <b>{code}</b>    "
        response += line + "\n"
    
    response += "\n⏰ Коды актуальны на текущее время UTC"
    return response

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    """Приветственное сообщение"""
    await message.answer(
        "👋 Привет! Я бот для генерации кодов в инженерное меню.\n\n"
        "📌 <b>Доступные команды:</b>\n"
        "/codes — все коды для всех часовых поясов\n"
        "/code_utc [смещение] — код для конкретного UTC (например: /code_utc 3)\n"
        "/now — текущее время\n"
        "/timezones — список поддерживаемых поясов\n\n"
        "🤖 Бот автоматически обновляет коды каждый час"
    )

@dp.message(Command("timezones"))
async def list_timezones(message: Message):
    """Показывает все поддерживаемые часовые пояса"""
    response = "🌍 <b>Поддерживаемые часовые пояса:</b>\n\n"
    
    for tz in TIMEZONES:
        response += f"• {tz['name']} (смещение {tz['offset']:+d})\n"
    
    await message.answer(response, parse_mode="HTML")

@dp.message(Command("now"))
async def send_current_time(message: Message):
    """Показывает текущее время в разных поясах"""
    utc_now = datetime.now(pytz.UTC)
    msk_now = utc_now + timedelta(hours=3)
    
    await message.answer(
        f"🕐 <b>Текущее время</b>\n\n"
        f"UTC: {utc_now.strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"МСК: {msk_now.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        f"Для кода используй /codes",
        parse_mode="HTML"
    )

@dp.message(Command("code_utc"))
async def code_for_utc(message: Message):
    """Генерирует код для указанного смещения UTC"""
    try:
        # Парсим аргумент (число после команды)
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Укажите смещение: /code_utc 3")
            return
        
        offset = int(args[1])
        code = generate_code_for_offset(offset)
        
        await message.answer(
            f"🌍 UTC{offset:+d}\n"
            f"🔑 <b>{code}</b>",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Неверный формат. Используйте число, например: /code_utc 3")
    except Exception as e:
        await message.answer("❌ Ошибка")
        logger.error(f"Error in /code_utc: {e}")

@dp.message(Command("codes"))
async def send_all_codes(message: Message):
    """Отправляет коды для всех часовых поясов"""
    try:
        codes = generate_all_timezone_codes()
        now_local = get_local_time()  # для отображения
        
        response = format_codes_message(codes, now_local)
        await message.answer(response, parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Ошибка при генерации кодов")
        logger.error(f"Error in /codes: {e}")

# ========== АВТОМАТИЧЕСКАЯ ОТПРАВКА КАЖДЫЙ ЧАС ==========
async def hourly_update_job():
    """
    Фоновая задача, которая запускается каждый час
    и отправляет обновленные коды в заданную ветку
    """
    while True:
        try:
            # Ждем до следующего часа ровно
            now = datetime.now(pytz.UTC)
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            sleep_seconds = (next_hour - now).total_seconds()
            
            logger.info(f"⏳ Следующее обновление через {sleep_seconds/60:.0f} минут")
            await asyncio.sleep(sleep_seconds)
            
            # Генерируем и отправляем коды
            codes = generate_all_timezone_codes()
            now_local = get_local_time()
            response = format_codes_message(codes, now_local)
            
            await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=TARGET_THREAD_ID,
                text=response,
                parse_mode="HTML"
            )
            logger.info(f"✅ Коды обновлены и отправлены в {now_local.strftime('%H:%M')}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в hourly_update_job: {e}")
            await asyncio.sleep(300)  # ждем 5 минут при ошибке

# ========== ЗАПУСК БОТА ==========
async def main():
    """Главная функция запуска бота"""
    if not API_TOKEN:
        logger.error("❌ Не задан BOT_TOKEN!")
        return
    
    logger.info("🚀 Бот запускается...")
    logger.info(f"📢 Будет отправлять коды каждый час в ветку {TARGET_THREAD_ID}")
    
    # Запускаем фоновую задачу
    asyncio.create_task(hourly_update_job())
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
