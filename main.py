import logging
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
import pytz
import re

# ========== ИМПОРТ НАСТРОЕК ==========
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
    exit(1)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Часовой пояс для отображения
DISPLAY_TZ = pytz.timezone(config.DISPLAY_TIMEZONE)

# Глобальная переменная для хранения ID сообщения
current_message_id = config.MESSAGE_ID_TO_EDIT

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


# ========== ФУНКЦИИ ДЛЯ ЭКРАНИРОВАНИЯ MARKDOWNV2 ==========
def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы для MarkdownV2.
    Список символов: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)


def format_code_with_markdown(code: str) -> str:
    """Форматирует код жирным шрифтом в MarkdownV2"""
    return f'*{code}*'


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


def get_current_time_for_offset(offset_hours: int) -> str:
    """Возвращает текущее время для указанного смещения UTC в формате ЧЧ:ММ"""
    utc_now = datetime.now(pytz.UTC)
    local_time = utc_now + timedelta(hours=offset_hours)
    return local_time.strftime("%H:%M")


def generate_all_timezone_data() -> list:
    """
    Генерирует данные для всех часовых поясов:
    возвращает список кортежей (название пояса, текущее время, код)
    """
    data = []
    utc_now = datetime.now(pytz.UTC)

    for tz_info in TIMEZONES:
        local_time = utc_now + timedelta(hours=tz_info["offset"])
        current_time = local_time.strftime("%H:%M")
        code = generate_code_for_time(local_time)
        data.append({
            "name": tz_info["name"],
            "time": current_time,
            "code": code
        })

    # Сортируем по offset
    return sorted(data, key=lambda x: TIMEZONES[[t["name"] for t in TIMEZONES].index(x["name"])]["offset"])


def format_codes_table_markdown(data: list, update_time: datetime) -> str:
    """Форматирует коды в виде красивой таблицы с текущим временем (MarkdownV2)"""

    # Заголовок с компактной подписью (экранируем точки)
    date_str = escape_markdown(update_time.strftime('%d.%m.%Y'))
    time_str = escape_markdown(update_time.strftime('%H:%M:%S'))

    table = (
        f"🔄 Обновлено: 📅 {date_str} 🕒 {time_str} ({escape_markdown(config.DISPLAY_TIMEZONE)})\n\n"
        f"```\n"
        f"┌──────────────┬──────────┬─────────┐\n"
        f"│ Часовой пояс │  Время   │   Код   │\n"
        f"├──────────────┼──────────┼─────────┤\n"
    )

    # Строки таблицы
    for item in data:
        table += f"│ {item['name']:12} │  {item['time']}   │ {item['code']:7} │\n"

    # Нижняя граница и информация об обновлении
    table += (
        f"└──────────────┴──────────┴─────────┘\n"
        f"```\n"
        f"⏰ Следующее обновление через 1 час"
    )

    return table


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С СООБЩЕНИЕМ ==========
async def get_or_create_message() -> int:
    """
    Возвращает ID сообщения для редактирования.
    Если сообщение не задано в конфиге - создает новое.
    """
    global current_message_id

    if current_message_id:
        try:
            await bot.get_chat(config.GROUP_CHAT_ID)
            return current_message_id
        except:
            logger.warning(f"⚠️ Сообщение {current_message_id} не найдено, создаю новое")
            current_message_id = None

    try:
        data = generate_all_timezone_data()
        now_local = get_local_time()
        text = format_codes_table_markdown(data, now_local)

        msg = await bot.send_message(
            chat_id=config.GROUP_CHAT_ID,
            message_thread_id=config.TARGET_THREAD_ID,
            text=text,
            parse_mode="MarkdownV2"
        )

        current_message_id = msg.message_id
        logger.info(f"✅ Создано новое сообщение с ID: {current_message_id}")

        if config.PIN_MESSAGE:
            try:
                await bot.pin_chat_message(
                    chat_id=config.GROUP_CHAT_ID,
                    message_id=current_message_id,
                    disable_notification=True
                )
                logger.info("📌 Сообщение закреплено")
            except Exception as e:
                logger.error(f"❌ Не удалось закрепить сообщение: {e}")

        return current_message_id

    except Exception as e:
        logger.error(f"❌ Ошибка при создании сообщения: {e}")
        raise


async def update_codes_message():
    """Обновляет существующее сообщение с кодами"""
    global current_message_id

    try:
        if not current_message_id:
            current_message_id = await get_or_create_message()

        data = generate_all_timezone_data()
        now_local = get_local_time()
        new_text = format_codes_table_markdown(data, now_local)

        await bot.edit_message_text(
            chat_id=config.GROUP_CHAT_ID,
            message_id=current_message_id,
            text=new_text,
            parse_mode="MarkdownV2"
        )

        logger.info(f"✅ Сообщение {current_message_id} обновлено в {now_local.strftime('%H:%M')}")

    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.debug("Сообщение не изменилось")
        else:
            logger.error(f"❌ Ошибка при редактировании: {e}")
            current_message_id = None
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении: {e}")
        current_message_id = None


# ========== КОМАНДЫ ==========
@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    """Приветственное сообщение"""
    text = (
        "👋 Привет\\! Я бот для генерации кодов в инженерное меню\\.\n\n"
        "📌 *Доступные команды:*\n"
        "/table — таблица кодов для всех часовых поясов\n"
        "/code\\_utc \\[смещение\\] — код для конкретного UTC \\(например: /code_utc 3\\)\n"
        "/now — текущее время\n"
        "/timezones — список поддерживаемых поясов\n"
        "/config — показать текущие настройки\n\n"
        "🤖 Бот автоматически обновляет коды каждый час"
    )
    await message.answer(text, parse_mode="MarkdownV2")


@dp.message(Command("reset_message"))
async def reset_message(message: Message):
    """Сбрасывает ID сообщения и создает новое"""
    global current_message_id
    current_message_id = None
    await get_or_create_message()
    await message.reply("✅ Сообщение сброшено и создано заново")


@dp.message(Command("config"))
async def show_config(message: Message):
    """Показывает текущие настройки бота"""
    text = (
        f"⚙️ *Текущие настройки*\n\n"
        f"📢 Группа ID: `{config.GROUP_CHAT_ID}`\n"
        f"📌 Ветка ID: `{config.TARGET_THREAD_ID}`\n"
        f"📝 ID сообщения: `{current_message_id or 'не задано'}`\n"
        f"📌 Закреплено: {'да' if config.PIN_MESSAGE else 'нет'}\n"
        f"🌍 Часовой пояс: {escape_markdown(config.DISPLAY_TIMEZONE)}"
    )
    await message.answer(text, parse_mode="MarkdownV2")


@dp.message(Command("update"))
async def manual_update(message: Message):
    """Принудительное обновление таблицы"""
    try:
        await update_codes_message()
        await message.reply("✅ Таблица обновлена")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {escape_markdown(str(e))}")


@dp.message(Command("now"))
async def send_current_time(message: Message):
    """Показывает текущее время"""
    utc_now = datetime.now(pytz.UTC)
    local_now = get_local_time()

    text = (
        f"🕐 *Текущее время*\n\n"
        f"UTC: {escape_markdown(utc_now.strftime('%d.%m.%Y %H:%M:%S'))}\n"
        f"Локальное: {escape_markdown(local_now.strftime('%d.%m.%Y %H:%M:%S'))} ({escape_markdown(config.DISPLAY_TIMEZONE)})"
    )
    await message.answer(text, parse_mode="MarkdownV2")


@dp.message(Command("code_utc"))
async def code_for_utc(message: Message):
    """Генерирует код для указанного смещения UTC"""
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Укажите смещение: /code_utc 3", parse_mode="MarkdownV2")
            return

        offset = int(args[1])
        code = generate_code_for_offset(offset)
        current_time = get_current_time_for_offset(offset)

        text = (
            f"```\n"
            f"┌──────────────┬──────────┬─────────┐\n"
            f"│   UTC{offset:+3d}    │  {current_time}   │ {code:7} │\n"
            f"└──────────────┴──────────┴─────────┘\n"
            f"```"
        )
        await message.answer(text, parse_mode="MarkdownV2")
    except ValueError:
        await message.answer("❌ Неверный формат\\. Используйте число", parse_mode="MarkdownV2")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {escape_markdown(str(e))}", parse_mode="MarkdownV2")
        logger.error(f"Error in /code_utc: {e}")


@dp.message(Command("timezones"))
async def list_timezones(message: Message):
    """Показывает все поддерживаемые часовые пояса"""
    text = "🌍 *Поддерживаемые часовые пояса:*\n\n```\n"
    text += "┌──────────┬────────┐\n"
    text += "│   Пояс   │ Смещ.  │\n"
    text += "├──────────┼────────┤\n"

    for tz in TIMEZONES:
        text += f"│ {tz['name']:8} │ {tz['offset']:+4d}   │\n"

    text += "└──────────┴────────┘\n```"

    await message.answer(text, parse_mode="MarkdownV2")


@dp.message(Command("table", "codes"))
async def send_codes_table(message: Message):
    """Отправляет таблицу кодов для всех часовых поясов"""
    try:
        data = generate_all_timezone_data()
        now_local = get_local_time()
        response = format_codes_table_markdown(data, now_local)
        await message.answer(response, parse_mode="MarkdownV2")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {escape_markdown(str(e))}", parse_mode="MarkdownV2")
        logger.error(f"Error in /table: {e}")


# ========== АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ ==========
async def hourly_update_job():
    """Фоновая задача для автоматического обновления"""
    if not config.ENABLE_HOURLY_UPDATES:
        logger.info("⏸ Автоматическое обновление отключено")
        return

    await asyncio.sleep(5)

    try:
        await get_or_create_message()
    except Exception as e:
        logger.error(f"❌ Не удалось создать начальное сообщение: {e}")

    while True:
        try:
            now = datetime.now(pytz.UTC)
            next_run = (now + timedelta(hours=1)).replace(
                minute=config.SEND_AT_MINUTE,
                second=0,
                microsecond=0
            )
            sleep_seconds = (next_run - now).total_seconds()

            logger.info(f"⏳ Следующее обновление через {sleep_seconds / 60:.1f} минут")
            await asyncio.sleep(sleep_seconds)

            await update_codes_message()

        except Exception as e:
            logger.error(f"❌ Ошибка в hourly_update_job: {e}")
            await asyncio.sleep(300)


# ========== ЗАПУСК БОТА ==========
async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Бот запускается...")
    logger.info(f"📢 Группа: {config.GROUP_CHAT_ID}, Ветка: {config.TARGET_THREAD_ID}")

    asyncio.create_task(hourly_update_job())
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())