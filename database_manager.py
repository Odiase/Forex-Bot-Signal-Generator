import psycopg2
from datetime import date
from urllib.parse import urlparse, parse_qs, unquote



class DB_Plug():
    '''Handles Database Connections'''

    def __init__(self):
        '''Initialize Database Connection'''
        # Parse the connection URL
        config = parse_db_url("postgres://forex_tradfing_bot_db_user:884Oc6Dxk8nqykNgI4K87cSClMb7f1Ga@dpg-cp7kus7sc6pc73ac33i0-a.oregon-postgres.render.com/forex_tradfing_bot_db", ssl_require=True)
        
        # Establish the connection
        self.conn = psycopg2.connect(
            database=config["NAME"],
            user=config["USER"],
            password=config["PASSWORD"],
            host=config["HOST"],
            port=config["PORT"],
            sslmode=config.get("sslmode", "")
        )


    def createTable(self):
        '''Create Database Table'''

        # Open a cursor to perform database operations
        cur = self.conn.cursor()
        # Execute a command: create trading_session table
        cur.execute("""
            CREATE TABLE trading_session(
                trading_session_id SERIAL PRIMARY KEY,
                currency_pair VARCHAR(8) NOT NULL,
                trade_option VARCHAR(6) NOT NULL,
                date_created DATE NOT NULL,
                trade_status VARCHAR(8) NOT NULL
            );
        """)
        self.conn.commit()
        # Close cursor and communication with the database
        cur.close()
        self.conn.close()
    

    def createTable2(self):
        '''Create the Table that holds record for Trade orders'''
        cur = self.conn.cursor()
        cur.execute("""
        
            CREATE TABLE trade_orders (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                action VARCHAR(10) NOT NULL,
                status VARCHAR(10) DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def insertNewSession(self, currency_pairs, trade_option, trade_status):
        '''Insert a new record into the trading_session table'''

        # Open a cursor to perform database operations
        cur = self.conn.cursor()
        # Get the current date
        date_created = date.today()
        # Execute a command: insert new record
        cur.execute("""
            INSERT INTO trading_session (currency_pair, trade_option, date_created, trade_status)
            VALUES (%s, %s, %s, %s)
            """, (currency_pairs, trade_option, date_created, trade_status))
        self.conn.commit()
        # Close cursor
        cur.close()

    def getOpenSession(self, currency_pair):
        '''Get trading sessions with status "OPEN" for a specific currency pair'''

        # Open a cursor to perform database operations
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM trading_session
            WHERE currency_pair = %s AND trade_status = 'OPEN'
            """, (currency_pair,))
        # Fetch all the matching records
        records = cur.fetchall()
        # Close cursor
        cur.close()
        return records
    
    def getAllOpenSessions(self):
        '''Get trading sessions with status "OPEN" for a specific currency pair'''

        # Open a cursor to perform database operations
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM trading_session
            WHERE trade_status = 'OPEN'
            """)
        # Fetch all the matching records
        records = cur.fetchall()
        # Close cursor
        cur.close()
        return records

    def closeSession(self, currency_pair):
        '''Change the status of trading sessions to "CLOSED" for a specific currency pair'''

        # Open a cursor to perform database operations
        cur = self.conn.cursor()
        # Execute a command: update records to set trade_status to 'CLOSED' for the specified currency pair
        cur.execute("""
            UPDATE trading_session
            SET trade_status = 'CLOSED'
            WHERE currency_pair = %s AND trade_status = 'OPEN'
            """, (currency_pair,))
        self.conn.commit()
        # Close cursor
        cur.close()

    def close(self):
        '''Close the database connection'''
        self.conn.close()





def parse_db_url(url, ssl_require=False):
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



# Example usage:
db = DB_Plug()
# db.createTable()
