import telebot 
from telebot import types
from db import get_product, get_products_by_category, add_to_favourite, get_user_data
import logging

# Set up logging for better error handling
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = ''
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

    if call.data == "big_button":
        if call.message.text:
            # If the message has text, edit it
            bot.edit_message_text("Выберите категорию:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=second_buttons())
        else:
            # If the message has no text (like a photo), use edit_message_caption instead
            bot.edit_message_caption(caption="Выберите категорию:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=second_buttons())

    elif call.data.startswith("category_"):
        category = call.data.split('_')[1]
        products = get_products_by_category(category)
        
        if products:
            user_product_data[user_id] = {'category': category, 'products': products, 'index': 0}
            show_product_details(call.message, products[0])

    elif call.data == "view_cart":
        favourites = get_user_data(user_id)
        if favourites:
            for fav in favourites:
                product = get_product(fav['product_id'])
                if product:
                    show_product_details(call.message, product)
                else:
                    bot.edit_message_text("Несколько товаров из вашей корзины недоступны", chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            bot.edit_message_text("Ваша корзина пуста", chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data == "back":
        if 'photo' in call.message.json:
            media = types.InputMediaPhoto(call.message.photo[-1].file_id, caption="Welcome")
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=first_buttons())
        else:
            bot.edit_message_text("Добро пожаловать", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=first_buttons())

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
    caption = f"""
    Название: {product['name']}
    Размеры: {product['dimensions']}
    Цена: {product['price']}
    Сылка: {product['link']}
    """

    try:
        if image_path.lower().startswith(('http://', 'https://')):
            bot.send_photo(message.chat.id, image_path, caption=caption, reply_markup=markup)
        else:
            with open(image_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup)
    except FileNotFoundError:
        bot.edit_message_text(f"Image file not found: {image_path}\n\n{caption}", chat_id=message.chat.id, message_id=message.message_id, reply_markup=markup)
        logging.error(f"Image file not found: {image_path}")
    except Exception as e:
        bot.edit_message_text(f"Error with image: {e}\n\n{caption}", chat_id=message.chat.id, message_id=message.message_id, reply_markup=markup)
        logging.error(f"Error with image for product {product['id']}: {e}")

if __name__ == '__main__':
    bot.polling()
