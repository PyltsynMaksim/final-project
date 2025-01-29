import telebot 
from telebot import types
from db import get_product, get_products_by_category, add_to_favourite, get_user_data
import logging

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = '8191675436:AAErE5Rq6IeUPbcF90BrVJ87CEbXH2TmKQU'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Store product list and user data to handle "Next" button
user_product_data = {}

def first_buttons():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Каталог", callback_data="big_button")
    btn2 = types.InlineKeyboardButton("Корзина", callback_data="view_cart")
    btn3 = types.InlineKeyboardButton(text="Связь с менеджером", url='tg://user?id=5078469186')
    btn4 = types.InlineKeyboardButton(text="Перейти на наш сайт", url='https://mrmattress.ru')
    markup.add(btn1)
    markup.add(btn2, btn3, btn4)
    return markup

def second_buttons():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Кровати", callback_data="category_Кровати")
    btn2 = types.InlineKeyboardButton("Подушки", callback_data="category_Подушки")
    btn3 = types.InlineKeyboardButton("Матрасы", callback_data="category_Матрасы")
    btn4 = types.InlineKeyboardButton("Одеяла", callback_data="category_Одеяла")
    btn_back = types.InlineKeyboardButton("Назад", callback_data="back")
    markup.add(btn1, btn2, btn3, btn4, btn_back)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    photo_url = 'https://img1.wsimg.com/isteam/ip/6e5d5951-63a5-43bd-889a-8ab684a4f9e1/blob-0003.png/:/cr=t:0%25,l:0%25,w:100%25,h:100%25/rs=w:792,h:500,cg:true'
    bot.send_photo(message.chat.id, photo_url, "Добро пожаловать", reply_markup=first_buttons())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id

    if call.data == "big_button" or call.data == "back":
        if call.data == "back":
            photo_url = 'https://img1.wsimg.com/isteam/ip/6e5d5951-63a5-43bd-889a-8ab684a4f9e1/blob-0003.png/:/cr=t:0%25,l:0%25,w:100%25,h:100%25/rs=w:792,h:500,cg:true'
            bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   media=types.InputMediaPhoto(photo_url, caption="Добро пожаловать"),
                                   reply_markup=first_buttons())
        elif call.data == "big_button":
            bot.edit_message_caption(caption="Выберите категорию:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=second_buttons())

    elif call.data.startswith("category_"):
        category = call.data.split('_')[1]
        products = get_products_by_category(category)
        
        if products:
            user_product_data[user_id] = {'category': category, 'products': products, 'index': 0}
            show_product_details(call.message, products[0])

    elif call.data == "view_cart":
        favourites = get_user_data(user_id)
        cart_message = "Ваша корзина:\n\n"
        if favourites:
            for fav in favourites:
                product = get_product(fav['product_id'])
                if product:
                    cart_message += f"{product['name']} - {product['price']}\n"
                else:
                    cart_message += "Товар недоступен\n"
            bot.edit_message_text(cart_message, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=first_buttons())
        else:
            bot.edit_message_text("Ваша корзина пуста", chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data.startswith("product_"):
        product_id = int(call.data.split('_')[1])
        product = get_product(product_id)
        show_product_details(call.message, product)

    elif call.data.startswith("add_favourite_"):
        product_id = int(call.data.split('_')[2])
        add_to_favourite(user_id, product_id)
        bot.answer_callback_query(call.id, text="Добавлено в корзину!")

    elif call.data.startswith("next_"):
        current_product_id = int(call.data.split('_')[1])
        category = user_product_data[user_id]['category']
        products = user_product_data[user_id]['products']
        index = user_product_data[user_id]['index']

        # Find next product in the list
        next_index = (index + 1) % len(products)
        user_product_data[user_id]['index'] = next_index
        next_product = products[next_index]
        show_product_details(call.message, next_product)

def show_product_details(message, product):
    if not product:
        bot.edit_message_text("Product not found", chat_id=message.chat.id, message_id=message.message_id)
        return

    logging.info(f"Product details: {product}")
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton("Назад", callback_data="back")
    fav_btn = types.InlineKeyboardButton("Добавить в корзину", callback_data=f"add_favourite_{product['id']}")
    forward_btn = types.InlineKeyboardButton("Следующее", callback_data=f"next_{product['id']}")
    markup.add(back_btn, fav_btn, forward_btn)

    image_path = product['image']
    caption = f"Название: {product['name']}\nРазмеры: {product['dimensions']}\nЦена: {product['price']}\nСсылка: {product['link']}"

    try:
        if image_path and image_path.lower().startswith(('http://', 'https://')):
            bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=message.message_id,
                media=types.InputMediaPhoto(image_path, caption=caption),
                reply_markup=markup)
        else:
            with open(image_path, 'rb') as photo:
                bot.edit_message_media(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    media=types.InputMediaPhoto(photo.read(), caption=caption),
                    reply_markup=markup)
    except Exception as e:
        logging.error(f"Error showing product details: {e}")
        bot.edit_message_text("Error loading product image", chat_id=message.chat.id, message_id=message.message_id)

if __name__ == '__main__':
    bot.polling()

