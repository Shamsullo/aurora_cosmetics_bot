import random, re
import cv2
from asgiref.sync import sync_to_async
from django.db.models import Q, Sum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CallbackContext, CallbackQueryHandler, CommandHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)

from .nalog_request import NalogRuPython
from .models import BotContent, BotUser, Draw, Prize, QRCheck


@sync_to_async
def get_last_bot_content():
    return BotContent.objects.last()


@sync_to_async
def get_or_create_or_update_bot_user(telegram_id, username=None, first_name=None, last_name=None):
    """
    Retrieves an existing BotUser by telegram_id, or creates a new one.
    If the user exists and any of the fields (first_name, last_name) differ,
    they are updated.
    """

    # Try to get the existing user or create a new one
    user, created = BotUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name
        }
    )

    # If the user already existed, check if the first_name or last_name need to be updated
    if not created:
        has_changes = False  # Track whether any changes are needed

        # Check if first_name needs updating
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            has_changes = True

        # Check if last_name needs updating
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            has_changes = True

        # Check if username needs updating
        if username and user.username != username:
            user.username = username
            has_changes = True

        # Save the user only if changes were detected
        if has_changes:
            user.save()

    return user


@sync_to_async
def insert_qr_check(data):
    QRCheck.objects.create(**data)


@sync_to_async
def insert_draw(data):
    draw = Draw.objects.create(**data)
    return draw.id


@sync_to_async
def insert_player_info_draw(id, info):
    Draw.objects.filter(id=id).update(player_info=info)


@sync_to_async
def get_playing_prize_type(telegram_id):
    last_played_date = Draw.objects.filter(telegram_id=telegram_id).last()
    playing_sum = QRCheck.objects.filter(telegram_id=telegram_id)
    if last_played_date:
        playing_sum = playing_sum.filter(created_at__gt=last_played_date.created_at)
    playing_sum = playing_sum.aggregate(playing_sum=Sum('purchase_amount'))
    return playing_sum['playing_sum']


@sync_to_async
def get_prizes(premium=False):
    return list(Prize.objects.filter(Q(available__gt=0) | Q(available__isnull=True)))


INSTRUCTION_REQUEST, VIDEO_INSTRUCTION_REQUEST, PHONE_REQUEST, CODE_REQUEST, PHOTO_REQUEST, CONTACT_DATA, WIN_PRIZE, FINAL_REQUEST = range(8)
nalog_ru: NalogRuPython = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    db_user = await get_or_create_or_update_bot_user(
        telegram_id=update.message.from_user.id,
        username=update.message.from_user.username,
        first_name=update.message.from_user.first_name,
        last_name=update.message.from_user.last_name
    )
    context.bot_data.setdefault('custom_timeout', 20)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VIDEO_NOTE)

    bot_content: BotContent = await get_last_bot_content()
    if bot_content.intro_circle_video:
        await update.message.reply_video_note(bot_content.intro_circle_video, read_timeout=context.bot_data['custom_timeout'])

    if bot_content.intro_text:
        await update.message.reply_text(bot_content.intro_text)

    # Сообщение с инструкцией
    instruction_message = bot_content.instruction_text or None
    keyboard = [
        [InlineKeyboardButton("Купить на OZON", callback_data='buy_ozon')],
        [InlineKeyboardButton("Купить на Wildberries", callback_data='buy_wb')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                       action=ChatAction.TYPING)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                       action=ChatAction.UPLOAD_PHOTO)
    await update.message.reply_photo(
        photo=bot_content.intro_image,
        caption=instruction_message,
        reply_markup=reply_markup
    )
    return (VIDEO_INSTRUCTION_REQUEST)


async def instruction_request(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.bot_data.setdefault('custom_timeout', 20)
    bot_content: BotContent = await get_last_bot_content()
    # Сообщение с инструкцией
    instruction_message = bot_content.instruction_text or None
    keyboard = [
        [InlineKeyboardButton("Купить на OZON", callback_data='buy_ozon')],
        [InlineKeyboardButton("Купить на Wildberries", callback_data='buy_wb')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    await update.message.reply_photo(
        photo=bot_content.intro_image,
        caption=instruction_message,
        reply_markup=reply_markup,
        read_timeout=context.bot_data['custom_timeout']
    )

    return (VIDEO_INSTRUCTION_REQUEST)


# Обработка выбора магазина
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    bot_content: BotContent = await get_last_bot_content()
    print(query)
    # Показать видео-инструкцию для выбранной платформы
    platform = "OZON" if query.data == 'buy_ozon' else "Wildberries"
    if platform == "OZON":
        video_path = bot_content.ozon_inst_video
    else:
        video_path = bot_content.wild_inst_video
    await query.message.reply_text(
        f"Смотри видео инструкцию: как сделать и отправить скрин чека о покупке на {platform} и участвовать в розыгрыше подарков ⤵️")
    await query.message.reply_video(video_path)

    await query.message.reply_text("Для участие в розыгрыше надо пройти верификацию, чтобы проходить это сделать ваш номер телефона в формате +7XXXXXXXXXX:")
    return (PHONE_REQUEST)


async def phone_handler(update: Update, context):
    phone = update.message.text

    # Пример для российских номеров: начинается с +, 11 цифр
    pattern = r"^\+\d{11}$"

    if re.match(pattern, phone):
        context.user_data['phone'] = phone
        # Здесь можно добавить сообщение об успешной валидации
        await update.message.reply_text("Номер телефона введен корректно!")

        # Создаем экземпляр NalogRuPython с переданным номером телефона
        global nalog_ru
        nalog_ru = NalogRuPython(phone)  # Код SMS будет запрошен здесь

        await update.message.reply_text("Введите код из SMS:")
        return CODE_REQUEST

    else:
        # Здесь можно добавить сообщение об ошибке
        await update.message.reply_text("Некорректный формат номера телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX")


def validate_code(code):
    return bool(re.match(r"^\d{4}$", code))


async def code_handler(update: Update, context):
    code = update.message.text

    # Используем код для авторизации
    global nalog_ru

    if True:
    # if validate_code(code):
    #     nalog_ru.set_session_id(code)  # Передаем только код
        context.user_data['is_authenticated'] = True
        await update.message.reply_text("Авторизация успешна!\n\nОтправьте, пожалуйтса, фотографии всех имеющихся QR-кодов одним сообщением.\n\nПри необходимости – вы можете перезапустить бот через /start и догрузить остальные QR-коды позже.")
        return PHOTO_REQUEST
    else:
        await update.message.reply_text("Неверный код. Пожалуйста, проверьте и попробуйте снова.")


@sync_to_async
def choose_random_prize(available_prizes, no_win_probability=0.5):
    weighted_prizes = []

    for prize in available_prizes:
        weight = prize.quantity  # Base weight on quantity

        # Check if this is a mega prize (min_purchase > 1500)
        if prize.min_purchase > 1500:
            weight = max(1, weight // 3)  # Reduce chances for mega prizes (1/3rd the normal weight)

        weighted_prizes.extend([prize] * weight)

    none_weight = int(no_win_probability * len(weighted_prizes))
    weighted_prizes.extend([None] * none_weight)

    random.shuffle(weighted_prizes)

    if weighted_prizes:
        selected_prize = random.choice(weighted_prizes)

        if selected_prize is not None:
            if not selected_prize.available:
                selected_prize.available = selected_prize.quantity - 1
            else:
                selected_prize.available -= 1
            selected_prize.save()

        return selected_prize


async def shuffle_handler(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Получаем ID пользователя
    user_id = update.effective_user.id
    tg_id = update.effective_user.id
    is_mega_prize = await get_playing_prize_type(tg_id)

    if is_mega_prize in (None, 0):
        keyboard_end = [
            [InlineKeyboardButton("Купить на OZON", url='https://www.ozon.ru/seller/aurora-cosmetics-1933716/products/?miniapp=seller_1933716')],
            [InlineKeyboardButton("Купить на Wildberries", url='https://www.wildberries.ru/brands/311342631-aurora-cosmetics')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard_end)

        await query.message.reply_text(
            text="К сожалению, на данный момент для вас нет доступных подарков.\nЧтобы получить шанс на выигрыш, просто совершите покупку детской уходовой косметики Aurora Cosmetics на Wildberries или Ozon.",
            reply_markup=reply_markup
        )

    #Розыгрыш стандартных призов
    prizes = await get_prizes(premium=is_mega_prize)
    if not prizes:
        await query.message.reply_text("К сожалению, на данный момент нет доступных гарантированных призов.")

    # Выбираем случайный приз
    prize = await choose_random_prize(prizes)
    user_data = context.user_data

    if prize is None:
        message = "Упс.. к сожалению, в этот раз тебе не повезло🥲\nНо не расстраивайся, мы благодарим тебя за участие и выбор Aurora Cosmetics❤️\n\nСкоро будут новые розыгрыши и подарки, следи за нашим каналом"
        await query.message.reply_text(text=message)

    elif prize:
        message = f"Поздравляем! Вы выиграли {prize.name} {f': {prize.description}' if prize.description else ''}!"
        reply_keyboard = [[InlineKeyboardButton("Заполнить контактные данные",callback_data='contact_request')]]
        markup = InlineKeyboardMarkup(reply_keyboard)
        id = await insert_draw({
            "telegram_id": tg_id,
            "phone_number": user_data.get("phone"),
            "total_sum": is_mega_prize,
            "prize": prize
        })
        context.user_data['play_id'] = id
        await query.message.reply_text(message, reply_markup=markup)
        return CONTACT_DATA

    id = await insert_draw(
        {
            "telegram_id": tg_id,
            "phone_number": user_data.get("phone"),
            "total_sum": is_mega_prize,
            "prize": prize or None,
        }
    )
    context.user_data['play_id'] = id
    return FINAL_REQUEST


async def handle_photo(update: Update, context):
    if not context.user_data.get('phone'):
        await update.message.reply_text("Вы не авторизованы. Пожалуйста, введите ваш код.")
        return CODE_REQUEST

    # Получаем недостающие данные
    tg_id = update.effective_user.id
    tg_user_name = update.effective_user.username
    # Получаем фотографию от пользователя
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    await file.download_to_drive("qr_code.jpg")

    # Распознаем QR-код
    try:
        image = cv2.imread("qr_code.jpg")
        detector = cv2.QRCodeDetector()
        qr_data, _, _ = detector.detectAndDecode(image)
        print("QR DATA:", qr_data)
        # Получаем данные чека
        try:
            # ticket = nalog_ru.get_ticket(qr_data)
            ticket = {'status': 2, 'statusReal': 2, 'id': '669025388d4db58808962bd8', 'kind': 'kkt', 'createdAt': '2024-10-19T14:42:52+03:00', 'statusDescription': {}, 'qr': 't=20240627T1556&s=1786.00&fn=7380440800792177&i=92555&fp=2059569348&n=1', 'operation': {'date': '2024-06-27T15:56', 'type': 1, 'sum': 178600}, 'process': [{'time': '2024-07-11T18:32:24+00:00', 'result': 21}, {'time': '2024-07-11T18:32:30+00:00', 'result': 2}], 'query': {'operationType': 1, 'sum': 178600, 'documentId': 92555, 'fsId': '7380440800792177', 'fiscalSign': '2059569348', 'date': '2024-06-27T15:56'}, 'ticket': {'document': {'receipt': {'dateTime': 1719492960, 'buyerPhoneOrAddress': 'allxndrva@list.ru', 'cashTotalSum': 0, 'code': 3, 'creditSum': 0, 'ecashTotalSum': 178600, 'fiscalDocumentFormatVer': 4, 'fiscalDocumentNumber': 92555, 'fiscalDriveNumber': '7380440800792177', 'fiscalSign': 2059569348, 'fnsUrl': 'www.nalog.gov.ru', 'items': [{'name': 'Шампунь детский для мытья волос и купания 300мл Aurora Cosmetics', 'nds': 6, 'paymentAgentByProductType': 16, 'paymentType': 4, 'price': 46400, 'productType': 1, 'providerInn': '072196655529', 'quantity': 1, 'sum': 46400}, {'name': 'Крем под подгузник детский для новорождённых 100мл Aurora Cosmetics', 'nds': 6, 'paymentAgentByProductType': 16, 'paymentType': 4, 'price': 54300, 'productType': 1, 'providerInn': '072196655529', 'quantity': 1, 'sum': 54300}, {'name': 'Крем для тела увлажняющий от растяжек 200мл Aurora Cosmetics', 'nds': 6, 'paymentAgentByProductType': 16, 'paymentType': 4, 'price': 77900, 'productType': 1, 'providerInn': '072196655529', 'quantity': 1, 'sum': 77900}], 'kktRegId': '0008009926025653    ', 'ndsNo': 178600, 'operationType': 1, 'operator': 'Автоматическое устройство', 'prepaidSum': 0, 'provisionSum': 0, 'requestNumber': 475, 'retailPlace': 'https://www.wildberries.ru/', 'retailPlaceAddress': '142181, ОБЛ.МОСКОВСКАЯ, г.о.ПОДОЛЬСК, г.ПОДОЛЬСК, д.КОЛЕДИНО, тер.ИНДУСТРИАЛЬНЫЙ ПАРК, д.6, стр.1', 'shiftNumber': 157, 'taxationType': 1, 'appliedTaxationType': 1, 'totalSum': 178600, 'user': 'ООО "Вайлдберриз"', 'userInn': '7721546864  '}}}, 'organization': {'name': 'ООО "Вайлдберриз"', 'inn': '7721546864'}, 'seller': {'name': 'ООО "Вайлдберриз"', 'inn': '7721546864'}}
            # print("TICKET:", ticket)
            order_number = ticket['id']

            # Список целевых товаров
            target_items = [
                "Крем для тела увлажняющий от растяжек 200мл Aurora Cosmetics",
                "Крем под подгузник детский для новорождённых 100мл Aurora Cosmetics",
                "Пена детская для ванны 250мл Aurora Cosmetics",
                "Детский крем увлажняющий 150мл Aurora Cosmetics",
                "Шампунь детский для мытья волос и купания 300мл Aurora Cosmetics",
                "Детский защитный крем под подгузник Aurora Cosmetics, 100 мл",
                "Детский увлажняющий крем для ежедневного ухода Aurora Cosmetics, 150 мл",
                "Детская пена для ванн Aurora Cosmetics, 250 мл",
                "Детский шампунь для мытья волос и купания 2в1, Aurora Cosmetics, 300 мл"
            ]

            # Фильтрация товаров и подсчет суммы
            found_items = []
            total_sum = 0
            for item in ticket['ticket']['document']['receipt']['items']:
                if item['name'] in target_items:
                    found_items.append(item['name'])
                    total_sum += item['sum']
                    result = total_sum / 100

            db_data = {
                "telegram_id": tg_id,
                "phone_number": nalog_ru.phone_number,
                "purchase_amount": result,
                "operation_date": ticket['operation']['date'],
                "order_number": order_number,
                "qr_data": qr_data,
                "buyer_phone_or_address": ticket['ticket']['document']['receipt']['buyerPhoneOrAddress'],
                "items": "\n\n".join(found_items),
                "organization": ticket['organization']['name']
            }
            await insert_qr_check(db_data)

            # Формирование сообщения
            if found_items:
                items_str = "\n\n".join(found_items)
                message = f"В чеке обнаружены следующие товары:\n\n{items_str}\n\nНа общую сумму: {result:.1f} руб."
                await update.message.reply_text(message)
                await update.message.reply_text(
                    f"Поздравляем! Вы стали участником {'розыгрыша' if total_sum < 900 else 'мега - розыгрыша'}.🔥\n Нажимай на кнопку 'Получить подарок' чтобы попытай удачу или загрузите ваши осталные чеки того чтобы поднять шанс на выиграть крутные прызи👇",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("Получить подарок", callback_data='WIN_PRIZE')]
                        ]
                    )
                )
                return WIN_PRIZE

            else:
                message = "В чеке не найдены товары из списка."
                await update.message.reply_text(message)

        except Exception as e:
            await update.message.reply_text(f"Ошибка при распознавании чека: {e}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при распознавании QR-кода: {e}")


async def final_message(update: Update, context: CallbackContext):

    # Получаем ID пользователя
    user_id = update.effective_user.id
    keyboard_end = [[InlineKeyboardButton("Канал с новостями", url="https://t.me/katyashkuro")]]
    reply_markup = InlineKeyboardMarkup(keyboard_end)

    await update.message.reply_text(text="Мы от всей души благодарим за доверие и то, что выбираете Aurora Cosmetics❤️\n\nВсе новые розыгрыши и акции будут в нашем телеграм канале, следите за новостями👇", reply_markup=reply_markup)
    return ConversationHandler.END


async def collect_contact_data(update: Update, context):
    query = update.callback_query
    user_data = context.user_data
    print('User data:', user_data)
    # text = query.message.text
    text = None
    print(context)
    if query:
        text = query.message.text
        print(text)
    if update.message:
        text = update.message.text
        context.user_data['user_info'] = text
        print("text", text)

    # Если мы не собираем ФИО, проверяем другие поля
    if 'user_info' not in user_data and query:
        await query.message.reply_text("Введите ваше контакиный дынные ФИО и ближайший адрес пункта выдачи заказов:")
        return CONTACT_DATA

    if text:
        await insert_player_info_draw(user_data.get('play_id', 0), text)
        await update.message.reply_text("Ваши контактные данные успешно собраны!")
        keyboard_end = [[InlineKeyboardButton("Канал с новостями", url="https://t.me/katyashkuro")]]
        reply_markup = InlineKeyboardMarkup(keyboard_end)

        await update.message.reply_text(
            text="Мы от всей души благодарим за доверие и то, что выбираете Aurora Cosmetics❤️\n\nВсе новые розыгрыши и акции будут в нашем телеграм канале, следите за новостями👇",
            reply_markup=reply_markup)
        return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await instruction_request(update, context)


def main():
    application = Application.builder().token("7849503177:AAF32VKmuc2iFOKmGlhxPMb0Y11MXIxy5aI").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INSTRUCTION_REQUEST: [
                CallbackQueryHandler(button),
                CallbackQueryHandler(shuffle_handler, pattern='^WIN_PRIZE$')
            ],
            VIDEO_INSTRUCTION_REQUEST: [
                CallbackQueryHandler(button),
                CallbackQueryHandler(shuffle_handler, pattern='^WIN_PRIZE$')
            ],
            PHONE_REQUEST: [
                CommandHandler("start", start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler),
                CallbackQueryHandler(button),
            ],
            CODE_REQUEST: [
                CommandHandler("start", start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, code_handler),
            ],
            PHOTO_REQUEST: [
                MessageHandler(filters.PHOTO, handle_photo),
                CallbackQueryHandler(shuffle_handler, pattern='^WIN_PRIZE$'),
                CallbackQueryHandler(button),
            ],
            WIN_PRIZE: [
                CallbackQueryHandler(shuffle_handler, pattern='^WIN_PRIZE$'),
                CallbackQueryHandler(button)
            ],
            CONTACT_DATA: [
                CallbackQueryHandler(collect_contact_data,pattern='^contact_request$'),
                CallbackQueryHandler(shuffle_handler, pattern='^WIN_PRIZE$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_contact_data)
            ],
            FINAL_REQUEST: [
                CommandHandler("restart", start),
                CommandHandler("start", start),
                CallbackQueryHandler(shuffle_handler, pattern='^WIN_PRIZE$'),
                CallbackQueryHandler(button),
                MessageHandler(filters.TEXT & ~filters.COMMAND, final_message)
            ]
        },
        fallbacks=[
            CommandHandler("help", help_command)
        ]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.run_polling()


if __name__ == '__main__':
    main()
