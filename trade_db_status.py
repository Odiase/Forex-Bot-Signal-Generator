import time
from urllib.parse import urlparse, parse_qs, unquote

import MetaTrader5 as mt5
import psycopg2


################## DATABASE STUFF

class TradeDatabase:
    def __init__(self):
        '''Initialize Database Connection'''
        # Parse the connection URL
        config = self.parse_db_url("postgresql://forex_signal_bot_user:cXCwDrnAO9oZFiEI0ob0LZiLpYO3WsY6@dpg-cpri553qf0us738fs13g-a.oregon-postgres.render.com/forex_signal_bot", ssl_require=True)
        
        # Establish the connection
        self.conn = psycopg2.connect(
            database=config["NAME"],
            user=config["USER"],
            password=config["PASSWORD"],
            host=config["HOST"],
            port=config["PORT"],
            sslmode=config.get("sslmode", "")
        )
    
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

    def close(self):
        '''Close the database connection'''
        self.conn.close()


db = TradeDatabase()
# db.insert_close_order('NZDJPY')
# db.insert_close_order('EURCAD')


# db.insert_trade_order("NZDJPY", "BUY")
# db.insert_trade_order("EURUSD", "SELL")

print(db.get_pending_closes())
print(db.get_pending_trades())