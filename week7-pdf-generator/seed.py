import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "report.db"

def seed_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS orders;")
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    
    products = ["Laptop Pro", "Wireless Mouse", "USB-C Hub", "Mechanical Keyboard", "27-inch Monitor", "Gaming Headset"]
    customers = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace"]
    
    orders = []
    now = datetime.now()
    for _ in range(200):
        customer = random.choice(customers)
        product = random.choice(products)
        amount = round(random.uniform(15.0, 350.0), 2)
        days_ago = random.randint(0, 30)
        date_str = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        orders.append((customer, product, amount, date_str))
        
    cursor.executemany(
        "INSERT INTO orders (customer, product, amount, created_at) VALUES (?, ?, ?, ?);",
        orders
    )
    conn.commit()
    conn.close()
    print("Database seeded with 200 orders.")

if __name__ == "__main__":
    seed_db()