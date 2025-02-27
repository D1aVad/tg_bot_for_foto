from random import choice

import telebot
from PIL import Image, ImageOps
import io
from telebot import types

TOKEN = ''
bot = telebot.TeleBot(TOKEN)

user_states = {}  # Здесь будем хранить информацию о действиях пользователя

# Набор символов для ASCII-арта
ASCII_CHARS = '@%#*+=-:. '

JOKES = [
    "Почему программисты не умеют рассказывать анекдоты? Потому что они всегда начинают с 'Давайте вернемся к первому принципу...'",

    'Как программисты развлекают себя в отпуске? Они делают "кэш" на пляже!',

    'Почему программисту не надо много времени на свидание?Он просто копирует и вставляет!',

    'Программист на свидании: "Вы не можете вызывать меня, если не передадите мне параметры!"',

    'Почему программисты любят природу?Потому что в ней много айтишников и вьюверов!',

    'Вот что значит для программиста "выходные": Это когда ты оставляешь одну “interfaced” переменную на столе!',

    'Почему программист не может быть летчиком? Потому что он всегда смотрит на облака как на cloud storage.',

    'Почему программист не верит в любовь с первого взгляда? Он всегда забывает проверить: "Есть ли переменные?"',

    'Что делает программист, когда его девушка говорит "Мне нужно пространство"? Он создает новый проект с именем "девушка-space"!',

    'Какой любимый напиток программиста? Java, конечно!'
]

COMPLIMENTS = [
    "Ты действительно мастер своего дела!",
    "Твои навыки программирования впечатляют.",
    "У тебя потрясающее логическое мышление.",
    "Ты создаёшь потрясающие решения!",
    "Твои коды всегда чистые и понятные.",
    "Ты способен решать сложные задачи с лёгкостью.",
    "Твои идеи всегда вдохновляют команду.",
    "Ты отлично справляешься с многозадачностью.",
    "Ты — настоящий лидер в разработке.",
    "Твои усилия делают проект успешным!"
]


def resize_image(image, new_width=100):
    """Изменяет размер изображения, сохраняя соотношение сторон.

    Args:
        image (PIL.Image): Входное изображение.
        new_width (int): Ширина для изменения размера.

    Returns:
        PIL.Image: Измененное изображение.
    """
    width, height = image.size
    ratio = height / width
    new_height = int(new_width * ratio)
    return image.resize((new_width, new_height))


def grayify(image):
    """Переводит изображение в оттенки серого.

    Args:
        image (PIL.Image): Входное изображение.

    Returns:
        PIL.Image: Изображение в оттенках серого.
    """
    return image.convert("L")


def image_to_ascii(image_stream, new_width=40):
    """Преобразует изображение в ASCII-арт.

    Args:
        image_stream (io.BytesIO): Бинарное представление изображения.
        new_width (int): Ширина итогового ASCII-арта.

    Returns:
        str: Строка, представляющая ASCII-арт.
    """
    image = Image.open(image_stream).convert('L')

    width, height = image.size
    aspect_ratio = height / float(width)
    new_height = int(aspect_ratio * new_width * 0.55)
    img_resized = image.resize((new_width, new_height))

    img_str = pixels_to_ascii(img_resized)
    img_width = img_resized.width

    max_characters = 4000 - (new_width + 1)
    max_rows = max_characters // (new_width + 1)

    ascii_art = ""
    for i in range(0, min(max_rows * img_width, len(img_str)), img_width):
        ascii_art += img_str[i:i + img_width] + "\n"

    return ascii_art


def pixels_to_ascii(image):
    """Преобразует пиксели изображения в строку ASCII-символов.

    Args:
        image (PIL.Image): Входное изображение.

    Returns:
        str: Строка, представляющая символы ASCII.
    """
    pixels = image.getdata()
    characters = ""
    for pixel in pixels:
        characters += ASCII_CHARS[pixel * len(ASCII_CHARS) // 256]
    return characters


def pixelate_image(image, pixel_size):
    """Пикселизирует изображение для создания эффекта грубого отображения.

    Args:
        image (PIL.Image): Входное изображение.
        pixel_size (int): Размер пикселя для группировки.

    Returns:
        PIL.Image: Пикселизированное изображение.
    """
    image = image.resize(
        (image.size[0] // pixel_size, image.size[1] // pixel_size),
        Image.NEAREST
    )
    image = image.resize(
        (image.size[0] * pixel_size, image.size[1] * pixel_size),
        Image.NEAREST
    )
    return image


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Отправляет приветственное сообщение при запуске бота.

    Args:
        message (telebot.types.Message): Сообщение, инициировавшее команду.
    """
    bot.reply_to(message, "Send me an image, and I'll provide options for you!")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Обрабатывает полученное изображение и запрашивает набор символов для ASCII-арта.

    Args:
        message (telebot.types.Message): Сообщение, содержащее изображение.
    """
    bot.reply_to(message,
                 "I got your photo! Please enter the characters you want to use for ASCII art. If you want to use a standard set of characters, copy @%#*+=-:. ")
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id, 'state': 'input_characters'}


@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id].get(
    'state') == 'input_characters')
def get_ascii_characters(message):
    """Получает пользовательские символы для создания ASCII-арта.

    Args:
        message (telebot.types.Message): Сообщение, содержащее пользовательский ввод символов.
    """
    global ASCII_CHARS
    ASCII_CHARS = message.text.strip()  # Сохраняем вводимые пользователем символы
    bot.reply_to(message,
                 f"Characters set to: `{ASCII_CHARS}`. Now, please choose what you'd like to do with the image.",
                 reply_markup=get_options_keyboard())

    # Очищаем состояние
    user_states[message.chat.id]['state'] = None


def get_options_keyboard():
    """Создает клавиатуру с вариантами для действий с изображением.

    Returns:
        telebot.types.InlineKeyboardMarkup: Клавиатура с кнопками.
    """
    keyboard = types.InlineKeyboardMarkup()
    pixelate_btn = types.InlineKeyboardButton("Pixelate", callback_data="pixelate")
    ascii_btn = types.InlineKeyboardButton("ASCII Art", callback_data="ascii")
    negative_btn = types.InlineKeyboardButton('Negative', callback_data='negative')
    vertical_reflection_btn = types.InlineKeyboardButton("Vertical reflection", callback_data="vert_ref")
    horizontal_reflection_btn = types.InlineKeyboardButton("Horizontal reflection", callback_data="horizont_ref")
    heat_map_btn = types.InlineKeyboardButton('Heat map', callback_data='heat_map')
    resize_for_stiker_btn = types.InlineKeyboardButton('Resize for stiker', callback_data='stiker')
    random_joke_btn = types.InlineKeyboardButton('Random joke', callback_data='r_joke')
    random_compliment_btn = types.InlineKeyboardButton('Random compliment', callback_data='r_compliment')

    keyboard.add(pixelate_btn, ascii_btn, negative_btn, vertical_reflection_btn, horizontal_reflection_btn,
                 heat_map_btn, resize_for_stiker_btn, random_joke_btn, random_compliment_btn)
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Обрабатывает нажатия кнопок в клавиатуре.

    Args:
        call (telebot.types.CallbackQuery): Запрос, содержащий информацию о нажатой кнопке.
    """
    if call.data == "pixelate":
        bot.answer_callback_query(call.id, "Pixelating your image...")
        pixelate_and_send(call.message)
    elif call.data == "ascii":
        bot.answer_callback_query(call.id, "Converting your image to ASCII art...")
        ascii_and_send(call.message)
    elif call.data == 'negative':
        bot.answer_callback_query(call.id, "Converting your image to negative")
        negative_and_save(call.message)
    elif call.data == 'vert_ref':
        bot.answer_callback_query(call.id, "Reflecting your image vertically")
        vert_reflection_image_and_save(call.message)
    elif call.data == 'horizont_ref':
        bot.answer_callback_query(call.id, "Reflecting your image horizontally")
        horizont_reflection_image_and_save(call.message)
    elif call.data == 'heat_map':
        bot.answer_callback_query(call.id, 'Converting your image to a heat map')
        convert_to_heat_map_and_save(call.message)
    elif call.data == 'stiker':
        bot.answer_callback_query(call.id, 'Converting your image to a stiker')
        resize_for_sticker_and_save(call.message)
    elif call.data == 'r_joke':
        bot.send_message(call.message.chat.id, choice(JOKES))
    elif call.data == 'r_compliment':
        bot.send_message(call.message.chat.id, choice(COMPLIMENTS))


def pixelate_and_send(message):
    """Пикселизирует изображение и отправляет его обратно пользователю.

    Args:
        message (telebot.types.Message): Сообщение, инициировавшее запрос пикселизации.
    """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    pixelated = pixelate_image(image, 20)

    output_stream = io.BytesIO()
    pixelated.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def ascii_and_send(message):
    """Генерирует ASCII-арт из изображения и отправляет его обратно пользователю.

    Args:
        message (telebot.types.Message): Сообщение, инициировавшее запрос на создание ASCII-арта.
    """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    ascii_art = image_to_ascii(image_stream)
    bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")


def negative_and_save(message):
    """
        Создает негатив изображения и отправляет его пользователю.

        Эта функция получает изображение от пользователя, инвертирует его цвета с помощью
        метода ImageOps.invert из библиотеки PIL, и затем отправляет инвертированное
        изображение обратно пользователю в формате JPEG.

        Args:
            message (telebot.types.Message): Объект сообщения от пользователя,
            содержащий информацию о фото.
        """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    inverted_image = ImageOps.invert(image)

    output_stream = io.BytesIO()
    inverted_image.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def vert_reflection_image_and_save(message):
    """
        Отражает изображение по вертикали и отправляет его пользователю.

        Эта функция получает изображение от пользователя, отражает его по вертикали с помощью
        метода Image.FLIP_TOP_BOTTOM из библиотеки PIL, и затем отправляет изображение обратно пользователю
        в формате JPEG.

        Args:
            message (telebot.types.Message): Объект сообщения от пользователя,
            содержащий информацию о фото.
        """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    reflection_image = image.transpose(Image.FLIP_TOP_BOTTOM)

    output_stream = io.BytesIO()
    reflection_image.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def horizont_reflection_image_and_save(message):
    """
        Отражает изображение по горизонтали и отправляет его пользователю.

        Эта функция получает изображение от пользователя, отражает его по горизонтали с помощью
        метода Image.FLIP_LEFT_RIGHT из библиотеки PIL, и затем отправляет изображение обратно пользователю
        в формате JPEG.

        Args:
            message (telebot.types.Message): Объект сообщения от пользователя,
            содержащий информацию о фото.
        """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    reflection_image = image.transpose(Image.FLIP_LEFT_RIGHT)

    output_stream = io.BytesIO()
    reflection_image.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def convert_to_heat_map_and_save(message):
    """
        Делает из изображения тепловую карту

        Эта функция получает изображение от пользователя, переводит его в серые тона
        с помощью функции grayify и создает из него тепловую карту,
        устанавлива границы цветов от синего до красного с помощью ImageOps.colorize из библиотеки PIL
        Затем отправляет изображение обратно пользователю в формате JPEG.

        Args:
            message (telebot.types.Message): Объект сообщения от пользователя,
            содержащий информацию о фото.
        """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    image = grayify(image)
    heat_map = ImageOps.colorize(image, black='blue', white='red')

    output_stream = io.BytesIO()
    heat_map.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def resize_for_sticker_and_save(message, max_dimension=512):
    """
    Изменяет размер изображения, сохраняя пропорции, чтобы его максимальная сторона не превышала указанный максимум.

    Args:
        image (PIL.Image): Входное изображение.
        max_dimension (int): Максимальное значение для любой из сторон.

    Returns:
        PIL.Image: Измененное изображение.
    """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)

    width, height = image.size

    if width > max_dimension or height > max_dimension:
        if width > height:
            ratio = max_dimension / float(width)
        else:
            ratio = max_dimension / float(height)

        new_width = int(width * ratio)
        new_height = int(height * ratio)

        output_stream = io.BytesIO()
        image = image.resize((new_width, new_height),
                             Image.LANCZOS)  # .LANCZOS - Этот фильтр обеспечивает высокое качество снижения размера изображения, уменьшая артефакты и предполагая более гладкие переходы между пикселями.
        image.save(output_stream, format="JPEG")
        output_stream.seek(0)
        bot.send_photo(message.chat.id, output_stream)


bot.polling(none_stop=True)
