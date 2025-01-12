import sqlite3
import logging

def get_db_connection():
    conn = sqlite3.connect('goods.db')
    return conn

def get_products_by_category(category):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, dimensions, image, link FROM goods WHERE category=?", (category,))
    rows = cursor.fetchall()
    conn.close()

    products = []
    for row in rows:
        product = {
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'dimensions': row[3],
            'image': row[4],
            'link': row[5],
        }
        products.append(product)
    
    logging.info(f"Found {len(products)} products for category: {category}")
    return products

def get_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, dimensions, image, link FROM goods WHERE id=?", (product_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'dimensions': row[3],
                'image': row[4],
                'link': row[5],
            }
        logging.error(f"Product with ID {product_id} not found.")
    except Exception as e:
        logging.error(f"Error retrieving product {product_id}: {e}")
    return None

def add_to_favourite(user_id, product_id):
    try:
        conn = sqlite3.connect('favourite.db')
        cursor = conn.cursor()

        
        cursor.execute("SELECT * FROM favourites WHERE user_id=? AND product_id=?", (user_id, product_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO favourites (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
            conn.commit()
            logging.info(f"Product {product_id} added to user {user_id}'s favorites.")
        else:
            logging.info(f"Product {product_id} is already in user {user_id}'s favorites.")
        conn.close()
    except Exception as e:
        logging.error(f"Error adding product {product_id} to user {user_id}'s favorites: {e}")

def get_user_data(user_id):
    conn = sqlite3.connect('favourite.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favourites WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    favourites = []
    for row in rows:
        favourites.append({'user_id': row[0], 'product_id': row[1]})
    return favourites
