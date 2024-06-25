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
        cur.execute("DELETE FROM trade_orders WHERE symbol LIKE %s;", (symbol,))
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
        cur.execute("DELETE FROM close_orders WHERE symbol LIKE %s;", (close_order_symbol,))
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






# Your login credentials
#login = 51829318
#password = '4n$Q1XNJqonzTV'
#server = 'ICMarketsSC-Demo'

login = 154765604
password = '#u4A73CRYix1'
server = 'Exness-MT5Trial9'

# Function to initialize and login to MetaTrader 5
def initialize_and_login():
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return False

    if not mt5.login(login, password, server):
        print("login() failed, error code =", mt5.last_error())
        mt5.shutdown()
        return False

    print("Connected to account:", login)
    return True

# Function to determine the lot size based on the balance
def determine_lot_size():
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info")
        return 0.01
    
    balance = account_info.balance
    lot_size = min(max(int(balance / 100) * 0.01, 0.01), 0.1)  # Ensure lot size is at least 0.01 and at most 0.1
    return lot_size

#function to get full symbol with any suffix
def get_full_symbol(base_symbol):
    symbols = mt5.symbols_get()
    for symbol in symbols:
        if symbol.name.startswith(base_symbol):
            print(symbol.name)
            return symbol.name
    return None

# Function to open a trade
def open_trade(base_symbol, action):
    if not initialize_and_login():
        return
    
    lot_size = determine_lot_size()
    symbol = get_full_symbol(base_symbol)
    if symbol is None:
        print("SYmbol with suffix not found")
        mt5.shutdown()
        return
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print("Failed to get symbol info for", base_symbol)
        mt5.shutdown()
        return

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print("Failed to select symbol:", base_symbol)
            mt5.shutdown()
            return
    
    symbol_tick = mt5.symbol_info_tick(symbol)
    if symbol_tick is None:
        print("Failed to get symbol tick for", base_symbol)
        mt5.shutdown()
        return

    price = symbol_tick.ask if action == mt5.ORDER_TYPE_BUY else symbol_tick.bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": action,
        "price": price,
        "deviation": 20,
        "magic": 123456,
        "comment": "Opened by Python script",
        "type_filling": mt5.ORDER_FILLING_IOC  # Trying IOC filling mode
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Failed to open trade:", result.comment)
    else:
        print("Trade opened successfully")
        # Mark trade as executed in the database
        # Initialize TradeDatabase instance
        db = TradeDatabase()
        db.delete_trade(base_symbol)

    mt5.shutdown()

# Function to close all trades for a symbol
def close_trades(base_symbol):
    if not initialize_and_login():
        return

    symbol = get_full_symbol(base_symbol)
    if symbol is None:
        print("SYmbol with suffix not found")
        mt5.shutdown()
        return
    
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        print("No positions found for symbol:", base_symbol)
        # Initialize TradeDatabase instance
        db = TradeDatabase()
        db.delete_close_order(base_symbol)
        mt5.shutdown()
        return

    for position in positions:
        price = mt5.symbol_info_tick(symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price": price,
            "deviation": 20,
            "magic": 123456,
            "comment": "Closed by Python script",
            "type_filling": mt5.ORDER_FILLING_IOC  # Trying IOC filling mode for closing trades
        }
        
        print("Sending close request:", request)
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("Failed to close trade:", result.comment)
        else:
            print("Trade closed successfully")
            db.delete_close_order(base_symbol)
    
    db.delete_close_order(base_symbol)
    mt5.shutdown()

# Example usage:
# Replace 'NZDUSD' with the symbol you want to trade
# symbol = 'NZDUSD'

# Open a sell trade
# open_trade(symbol, mt5.ORDER_TYPE_SELL)

# close_trades(symbol)

# Function to check database for pending trades and close orders
def check_database():
    # Initialize TradeDatabase instance
    db = TradeDatabase()
    pending_trades = db.get_pending_trades()
    if pending_trades:
        for trade in pending_trades:
            option = mt5.ORDER_TYPE_SELL
            if trade[2] == "BUY":
                option = mt5.ORDER_TYPE_BUY

            open_trade(trade[1], option)
    
    pending_closes = db.get_pending_closes()
    if pending_closes:
        for close_order in pending_closes:
            close_trades(close_order[1])

# Example usage:
if __name__ == "__main__":
    # db.insert_trade_order('EURUSD', 'BUY')
    # db.insert_trade_order('GBPUSD', 'SELL')
    while True:
        try:
            check_database()
        except Exception as e:
            print("Exception Occured : ", e)
        time.sleep(20)  # Check every 20 seconds

