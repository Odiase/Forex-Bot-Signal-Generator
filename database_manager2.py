import time
from urllib.parse import urlparse, parse_qs, unquote

import MetaTrader5 as mt5
import psycopg2


################## DATABASE STUFF

class TradeDatabase:
    def __init__(self, retries=5, delay=2):
        '''Initialize Database Connection with retry mechanism'''
        self.retries = retries
        self.delay = delay
        self.conn = self.connect_with_retry()

    def connect_with_retry(self):
        '''Attempt to establish a database connection with retries'''
        config = self.parse_db_url("postgresql://forex_signal_bot_user:cXCwDrnAO9oZFiEI0ob0LZiLpYO3WsY6@dpg-cpri553qf0us738fs13g-a.oregon-postgres.render.com/forex_signal_bot", ssl_require=True)

        attempts = 0
        while attempts < self.retries:
            try:
                conn = psycopg2.connect(
                    database=config["NAME"],
                    user=config["USER"],
                    password=config["PASSWORD"],
                    host=config["HOST"],
                    port=config["PORT"],
                    sslmode=config.get("sslmode", "")
                )
                print("Connected on Attempt ", attempts)
                return conn
            except psycopg2.OperationalError as e:
                attempts += 1
                print(f"Connection attempt {attempts} failed: {e}")
                if attempts < self.retries:
                    print(f"Retrying in {self.delay} seconds...")
                    time.sleep(self.delay)
                else:
                    print("All retry attempts failed.")
                    raise
    
    def parse_db_url(self, url, ssl_require=False):
        parsed_config = {}

        spliturl = urlparse(url)

        path = spliturl.path[1:]
        query = parse_qs(spliturl.query)

        hostname = spliturl.hostname or ""
        if "%" in hostname:
            hostname = spliturl.netloc
            if "@" in hostname:
                hostname = hostname.rsplit("@", 1)[1]
            hostname = unquote(hostname)

        port = spliturl.port

        parsed_config.update(
            {
                "NAME": unquote(path or ""),
                "USER": unquote(spliturl.username or ""),
                "PASSWORD": unquote(spliturl.password or ""),
                "HOST": hostname,
                "PORT": port or 5432,
            }
        )

        if ssl_require:
            parsed_config["sslmode"] = "require"

        return parsed_config

    def create_table_trade_orders(self):
        '''Create the Table that holds record for Trade orders'''
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trade_orders (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                action VARCHAR(10) NOT NULL,
                status VARCHAR(10) DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
        cur.close()

    def create_table_close_orders(self):
        '''Create the Table that holds record for Close orders'''
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS close_orders (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                status VARCHAR(10) DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
        cur.close()

    def get_pending_trades(self):
        '''Fetch trades with status 'PENDING' from trade_orders table'''
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM trade_orders WHERE status = 'PENDING';")
        trades = cur.fetchall()
        cur.close()
        return trades

    def delete_trade(self, symbol):
        '''Delete a trade from trade_orders table by trade SYMBOL'''
        cur = self.conn.cursor()
        cur.execute("DELETE FROM trade_orders WHERE symbol = %s;", (symbol,))
        self.conn.commit()
        cur.close()

    def get_pending_closes(self):
        '''Fetch trades with status 'PENDING' from close_orders table'''
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM close_orders WHERE status = 'PENDING';")
        trades = cur.fetchall()
        cur.close()
        return trades

    def delete_close_order(self, close_order_symbol):
        '''Delete a close order from close_orders table by order SYMBOL'''
        cur = self.conn.cursor()
        cur.execute("DELETE FROM close_orders WHERE symbol= %s;", (close_order_symbol,))
        self.conn.commit()
        cur.close()

    def insert_trade_order(self, symbol, action):
        '''Insert a new trade order into trade_orders table'''
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO trade_orders (symbol, action)
            VALUES (%s, %s);
        """, (symbol, action))
        self.conn.commit()
        cur.close()

    def insert_close_order(self, symbol):
        '''Insert a new close order into close_orders table'''
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO close_orders (symbol)
            VALUES (%s);
        """, (symbol,))
        self.conn.commit()
        cur.close()
    
    def update_trade_status_to_open(self, symbol):
        '''Update the status of a trade from PENDING to OPEN by trade ID'''
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE trade_orders
            SET status = 'OPEN'
            WHERE symbol = %s;
        """, (symbol,))
        self.conn.commit()
        cur.close()

    def get_open_trades(self):
        '''Fetch trades with status 'OPEN' from trade_orders table'''
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM trade_orders WHERE status = 'OPEN';")
        trades = cur.fetchall()
        cur.close()
        return trades
    
    def insert_close_orders_for_open_trades(self):
        '''Insert close orders for all open trades'''
        open_trades = self.get_open_trades()
        print("Open Trades : ", open_trades)
        for trade in open_trades:
            symbol = trade[1]  # Assuming 'symbol' is the second column in the trade_orders table
            self.insert_close_order(symbol)

    def close(self):
        '''Close the database connection'''
        self.conn.close()


db = TradeDatabase()
# db.insert_close_order('EURUSD')
# db.insert_close_order('GBPUSD')

# print(db.get_pending_closes)
print("Placing Trades")
db.insert_trade_order('EURJPY', 'BUY')
db.insert_trade_order('GBPCHF', 'BUY')
print('Placed Trades')
time.sleep(30)
print("CLosing all Open Trades.")
db.insert_close_orders_for_open_trades()

# db.insert_close_order('EURJPY')
# db.insert_close_order('GBPCHF')