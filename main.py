import logging
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import pytz

# ========== ИМПОРТ НАСТРОЕК ==========
# Подключаем настройки из отдельного файла
import config

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
API_TOKEN = os.getenv('BOT_TOKEN')
if not API_TOKEN:
    logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
    logger.error("Создайте файл .env с строкой: BOT_TOKEN=ваш_токен")
    exit(1)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Часовой пояс для отображения
DISPLAY_TZ = pytz.timezone(config.DISPLAY_TIMEZONE)

# ========== ДАННЫЕ О ЧАСОВЫХ ПОЯСАХ ==========
TIMEZONES = [
    {"name": "UTC−11", "offset": -11, "code_suffix": "830"},
    {"name": "UTC−10", "offset": -10, "code_suffix": "831"},
    {"name": "UTC−9", "offset": -9, "code_suffix": "8210"},
    {"name": "UTC−8", "offset": -8, "code_suffix": "8211"},
    {"name": "UTC−7", "offset": -7, "code_suffix": "8212"},
    {"name": "UTC−6", "offset": -6, "code_suffix": "8213"},
    {"name": "UTC−5", "offset": -5, "code_suffix": "8214"},
    {"name": "UTC−4", "offset": -4, "code_suffix": "8215"},
    {"name": "UTC−3", "offset": -3, "code_suffix": "8216"},
    {"name": "UTC−2", "offset": -2, "code_suffix": "8217"},
    {"name": "UTC−1", "offset": -1, "code_suffix": "8218"},
    {"name": "UTC+0", "offset": 0, "code_suffix": "8219"},
    {"name": "UTC+1", "offset": 1, "code_suffix": "822"},
    {"name": "UTC+2", "offset": 2, "code_suffix": "823"},
    {"name": "UTC+3", "offset": 3, "code_suffix": "824"},
    {"name": "UTC+4", "offset": 4, "code_suffix": "825"},
    {"name": "UTC+5", "offset": 5, "code_suffix": "826"},
    {"name": "UTC+6", "offset": 6, "code_suffix": "827"},
    {"name": "UTC+7", "offset": 7, "code_suffix": "828"},
    {"name": "UTC+8", "offset": 8, "code_suffix": "829"},
    {"name": "UTC+9", "offset": 9, "code_suffix": "8210"},
    {"name": "UTC+10", "offset": 10, "code_suffix": "8211"},
    {"name": "UTC+11", "offset": 11, "code_suffix": "830"},
    {"name": "UTC+12", "offset": 12, "code_suffix": "831"},
]


# ========== ФУНКЦИИ ГЕНЕРАЦИИ КОДОВ ==========
def get_local_time(timezone_name: str = None) -> datetime:
    """Возвращает текущее время в указанном часовом поясе"""
    if timezone_name is None:
        tz = DISPLAY_TZ
    else:
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
    """Генерирует код для указанного смещения UTC"""
    utc_now = datetime.now(pytz.UTC)
    local_time = utc_now + timedelta(hours=offset_hours)
    return generate_code_for_time(local_time)


def generate_all_timezone_codes() -> dict:
    """Генерирует коды для всех часовых поясов"""
    codes = {}
    utc_now = datetime.now(pytz.UTC)

    for tz_info in TIMEZONES:
        local_time = utc_now + timedelta(hours=tz_info["offset"])
        code = generate_code_for_time(local_time)
        codes[tz_info["name"]] = code

    return codes


def format_codes_table(codes: dict, update_time: datetime) -> str:
    """Форматирует коды в виде красивой таблицы"""
    sorted_timezones = sorted(TIMEZONES, key=lambda x: x["offset"])

    table = (
        f"┌──────────────┬─────────┐\n"
        f"│ Часовой пояс │   Код   │\n"
        f"├──────────────┼─────────┤\n"
    )

    for tz in sorted_timezones:
        code = codes.get(tz["name"], "N/A")
        table += f"│ {tz['name']:12} │ {code:7} │\n"

    table += f"└──────────────┴─────────┘\n"
    table += (
        f"\n📅 {update_time.strftime('%d.%m.%Y')}\n"
        f"🕒 {update_time.strftime('%H:%M:%S')} ({config.DISPLAY_TIMEZONE})\n"
        f"🔄 Коды обновляются каждый час"
    )

    return table


# ========== ОБРАБОТЧИКИ КОМАНД ==========
@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    """Приветственное сообщение"""
    await message.answer(
        "👋 Привет! Я бот для генерации кодов в инженерное меню.\n\n"
        "📌 <b>Доступные команды:</b>\n"
        "/table — таблица кодов для всех часовых поясов\n"
        "/code_utc [смещение] — код для конкретного UTC (например: /code_utc 3)\n"
        "/now — текущее время\n"
        "/timezones — список поддерживаемых поясов\n"
        "/config — показать текущие настройки\n\n"
        "🤖 Бот автоматически обновляет коды каждый час"
    )


@dp.message(Command("config"))
async def show_config(message: Message):
    """Показывает текущие настройки бота"""
    await message.answer(
        f"⚙️ <b>Текущие настройки</b>\n\n"
        f"📢 Группа ID: <code>{config.GROUP_CHAT_ID}</code>\n"
        f"📌 Ветка ID: <code>{config.TARGET_THREAD_ID}</code>\n"
        f"🌍 Часовой пояс: {config.DISPLAY_TIMEZONE}\n"
        f"🔄 Автообновление: {'включено' if config.ENABLE_HOURLY_UPDATES else 'выключено'}\n"
        f"⏰ Отправка в: {config.SEND_AT_MINUTE:02d} минут каждого часа",
        parse_mode="HTML"
    )


@dp.message(Command("timezones"))
async def list_timezones(message: Message):
    """Показывает все поддерживаемые часовые пояса"""
    response = "🌍 <b>Поддерживаемые часовые пояса:</b>\n\n"
    response += "┌──────────┬────────┐\n"
    response += "│   Пояс   │ Смещ.  │\n"
    response += "├──────────┼────────┤\n"

    for tz in TIMEZONES:
        response += f"│ {tz['name']:8} │ {tz['offset']:+4d}   │\n"

    response += "└──────────┴────────┘"

    await message.answer(response, parse_mode="HTML")


@dp.message(Command("now"))
async def send_current_time(message: Message):
    """Показывает текущее время в разных поясах"""
    utc_now = datetime.now(pytz.UTC)
    local_now = get_local_time()

    await message.answer(
        f"🕐 <b>Текущее время</b>\n\n"
        f"UTC: {utc_now.strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"Локальное: {local_now.strftime('%d.%m.%Y %H:%M:%S')} ({config.DISPLAY_TIMEZONE})\n\n"
        f"Для таблицы кодов используй /table",
        parse_mode="HTML"
    )


@dp.message(Command("code_utc"))
async def code_for_utc(message: Message):
    """Генерирует код для указанного смещения UTC"""
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Укажите смещение: /code_utc 3")
            return

        offset = int(args[1])
        code = generate_code_for_offset(offset)

        await message.answer(
            f"┌──────────────┬─────────┐\n"
            f"│   UTC{offset:+3d}    │ {code:7} │\n"
            f"└──────────────┴─────────┘",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Неверный формат. Используйте число, например: /code_utc 3")
    except Exception as e:
        await message.answer("❌ Ошибка")
        logger.error(f"Error in /code_utc: {e}")


@dp.message(Command("table", "codes"))
async def send_codes_table(message: Message):
    """Отправляет таблицу кодов для всех часовых поясов"""
    try:
        codes = generate_all_timezone_codes()
        now_local = get_local_time()
        response = format_codes_table(codes, now_local)
        await message.answer(f"<pre>{response}</pre>", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Ошибка при генерации кодов")
        logger.error(f"Error in /table: {e}")


# ========== АВТОМАТИЧЕСКАЯ ОТПРАВКА ==========
async def hourly_update_job():
    """Фоновая задача для автоматической отправки"""
    if not config.ENABLE_HOURLY_UPDATES:
        logger.info("⏸ Автоматическая отправка отключена в настройках")
        return

    while True:
        try:
            # Ждем до следующего часа в указанную минуту
            now = datetime.now(pytz.UTC)
            next_run = (now + timedelta(hours=1)).replace(
                minute=config.SEND_AT_MINUTE,
                second=0,
                microsecond=0
            )
            sleep_seconds = (next_run - now).total_seconds()

            logger.info(f"⏳ Следующая отправка через {sleep_seconds / 60:.1f} минут")
            await asyncio.sleep(sleep_seconds)

            # Генерируем и отправляем коды
            codes = generate_all_timezone_codes()
            now_local = get_local_time()
            response = format_codes_table(codes, now_local)

            await bot.send_message(
                chat_id=config.GROUP_CHAT_ID,
                message_thread_id=config.TARGET_THREAD_ID,
                text=f"<pre>{response}</pre>",
                parse_mode="HTML"
            )
            logger.info(f"✅ Таблица отправлена в {now_local.strftime('%H:%M')}")

        except Exception as e:
            logger.error(f"❌ Ошибка в hourly_update_job: {e}")
            await asyncio.sleep(300)


# ========== ЗАПУСК БОТА ==========
async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Бот запускается...")
    logger.info(f"📢 Группа: {config.GROUP_CHAT_ID}, Ветка: {config.TARGET_THREAD_ID}")
    logger.info(f"🌍 Часовой пояс: {config.DISPLAY_TIMEZONE}")
    logger.info(f"🔄 Автоотправка: {'вкл' if config.ENABLE_HOURLY_UPDATES else 'выкл'}")

    # Запускаем фоновую задачу
    asyncio.create_task(hourly_update_job())

    # Запускаем поллинг
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())