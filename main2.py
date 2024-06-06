import time
from datetime import datetime
import schedule

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType
import chromedriver_autoinstaller

from twocaptcha import TwoCaptcha

import psycopg2
from datetime import date
from urllib.parse import urlparse, parse_qs, unquote


class DB_Plug:
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
        '''Return trading session with status "OPEN" for a specific currency pair'''

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
        '''Returns All trading sessions with status "OPEN" '''

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


PINE_EDITOR_SCRIPT = """
//@version=5
strategy("MACD and EMA Strategy with Position Tool", overlay=true)

// MACD Settings
fastLength = 12
slowLength = 26
signalLength = 9
macdSource = close

[macdLine, signalLine, _] = ta.macd(macdSource, fastLength, slowLength, signalLength)
macdColor = macdLine > signalLine ? color.green : color.red
signalColor = color.red

// EMA Settings
emaLength = 200
emaSource = close
emaOffset = 0
emaMethod = ta.ema(emaSource, emaLength)
emaColor = close > emaMethod ? color.green : color.red

// Plot MACD and Signal lines
plot(macdLine, color=macdColor, title="MACD Line")
plot(signalLine, color=signalColor, title="Signal Line")

// Plot EMA line
plot(emaMethod, color=emaColor, title="EMA Line")

// Strategy logic
buySignal = ta.crossover(macdLine, signalLine) and close > emaMethod
sellSignal = ta.crossunder(macdLine, signalLine) and close < emaMethod

bgcolor(buySignal ? color.green : na, transp=90)
bgcolor(sellSignal ? color.red : na, transp=90)

// Plot Buy and Sell signals on the chart
plotshape(series=buySignal, title="Buy Signal", color=color.green, style=shape.triangleup, location=location.belowbar)
plotshape(series=sellSignal, title="Sell Signal", color=color.red, style=shape.triangledown, location=location.abovebar)

// Position tool
stopLossPips = 20 // Maximum 100 pips
takeProfitPips = stopLossPips * 2

strategy.entry("Buy", strategy.long, when=buySignal)
strategy.exit("Take Profit/Stop Loss", from_entry="Buy", loss=stopLossPips, profit=takeProfitPips)

strategy.entry("Sell", strategy.short, when=sellSignal)
strategy.exit("Take Profit/Stop Loss", from_entry="Sell", loss=stopLossPips, profit=takeProfitPips)
"""


def startDriver():
    chromedriver_autoinstaller.install() 
    chrome_options = webdriver.ChromeOptions()
    options = [
    # Define window size here
    #    "--window-size=1200,1200",
        # "--ignore-certificate-errors"
    
        # "--headless",
        
        # "--disable-gpu",
        # # "--window-size=1920,1200",
        # "--ignore-certificate-errors",
        # "--disable-extensions",
        # "--no-sandbox",
        # "--disable-dev-shm-usage",
        #'--remote-debugging-port=9222'
    ]
    for option in options:
        chrome_options.add_argument(option)
    driver = webdriver.Chrome(options=chrome_options)

    return driver

def getElement(driver, wait_time, element_locator, quantity_type):
    '''Gets an element or list of Elements from a page'''
    try:
        wait = WebDriverWait(driver, wait_time)

        if quantity_type == "single":
            element = wait.until(EC.presence_of_element_located(element_locator))
            return element
        elif quantity_type == "multiple":
            elements = wait.until(EC.presence_of_all_elements_located(element_locator))
            return elements
    except Exception as e:
        print(e)

def sendTelegramSignal(message):
    message = str(message)
    TOKEN = "6592918138:AAEWmvPEgFAJ4-dctj0-XM1xmzkauN3L8sA"
    chat_id = "-1002001136974"
    # chat_id = "-1002049858126"
    parameters = {
        "chat_id" : chat_id,
        "text" : message
    }

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"#?chat_id={chat_id}&text={message}"
    request = requests.get(url, data=parameters)

def openSite(driver):
    '''Opens Currency Strength Meter'''

    # uniben = "https://waeup.uniben.edu"
    driver.get("https://currencystrengthmeter.org/")
    # driver.get("https://www.tradingview.com/")
    time.sleep(2)

def acceptCookies(driver):
    '''Accepts cookies on the Currency Strength Meter'''

    accept_cookies_locator = (By.ID, "cookie_action_close_header")
    element = getElement(driver, 10, accept_cookies_locator, "single")

    element.click()
    time.sleep(2)


def getCurrencyStrength(driver):
    '''Get the Strength of a Currency'''

    try:
        openSite(driver)
        acceptCookies(driver)

        currency_row_locator = (By.CLASS_NAME, "currency-row")
        currencies = getElement(driver, 20, currency_row_locator, "multiple")
        
        currency_data = {}

        for currency in currencies:
            currency_name = currency.find_element(By.CLASS_NAME, "currency-label").text.strip()
            currency_strength = int(currency.find_element(By.CLASS_NAME, "currency-value").text.strip())
            currency_data[currency_name] = currency_strength

        return currency_data
    except Exception as e:
        print(f"Error in getCurrencyStrength: {e}")
        return {}

def determinePairs(currency_data):
    '''Determine Currency Pairs based on Strength'''

    # Sort currencies by strength
    sorted_currencies = sorted(currency_data, key=currency_data.get, reverse=True)
    
    # Pair the strongest with the weakest
    strongest_currency = sorted_currencies[0]
    weakest_currency = sorted_currencies[-1]

    currency_pair = f"{strongest_currency}/{weakest_currency}"

    return currency_pair

def openTradingView():
    '''Automates TradingView to send Signals based on a Strategy'''

    driver = startDriver()
    driver.get("https://www.tradingview.com/chart/")

    # Code to interact with TradingView and apply Pine Script
    # ... Your TradingView interaction logic here ...

    time.sleep(10)  # Time to allow TradingView page to load
    # Insert Pine Editor Script
    # Interact with elements to insert and run the Pine script
    # ...

    # Close the driver after completing interactions
    driver.quit()

def validateDBPairs():
    '''Validates Currency Pairs from the Database'''

    try:
        db = DB_Plug()
        open_sessions = db.getAllOpenSessions()

        if not open_sessions:
            return

        driver = startDriver()
        currency_strength = getCurrencyStrength(driver)
        driver.quit()

        for session in open_sessions:
            session_id, currency_pair, trade_option, date_created, trade_status = session
            base_currency, quote_currency = currency_pair.split('/')

            base_currency_strength = currency_strength.get(base_currency, 0)
            quote_currency_strength = currency_strength.get(quote_currency, 0)

            if trade_option == "BUY" and base_currency_strength < quote_currency_strength:
                db.closeSession(currency_pair)
                sendTelegramSignal(f"Closed session for {currency_pair} as BUY option is no longer valid.")
            elif trade_option == "SELL" and base_currency_strength > quote_currency_strength:
                db.closeSession(currency_pair)
                sendTelegramSignal(f"Closed session for {currency_pair} as SELL option is no longer valid.")
    except Exception as e:
        print(f"Error in validateDBPairs: {e}")

def run_tasks():
    try:
        # Perform tasks
        db = DB_Plug()
        driver = startDriver()
        currency_data = getCurrencyStrength(driver)
        driver.quit()
        
        currency_pair = determinePairs(currency_data)
        open_sessions = db.getAllOpenSessions()
        open_sessions_pairs = [session[1] for session in open_sessions]
        
        if currency_pair not in open_sessions_pairs:
            # Determine trade option
            strongest_currency, weakest_currency = currency_pair.split('/')
            trade_option = "BUY" if currency_data[strongest_currency] > currency_data[weakest_currency] else "SELL"
            db.insertNewSession(currency_pair, trade_option, "OPEN")
            sendTelegramSignal(f"New trading session for {currency_pair} as {trade_option}")

        # Validate DB pairs
        validateDBPairs()
    except Exception as e:
        print(f"Error in run_tasks: {e}")


def sub_main():
    driver = startDriver()
    openSite(driver)
    currency_list = getCurrencyStrength(driver)
    pairs_data = determinePairs(currency_list)
    
    validateDBPairs(pairs_data[1])
    openTradingView(driver, pairs_data[0], pairs_data[1])

def main():
    # Schedule tasks
    schedule.every(10).minutes.do(run_tasks)
    schedule.every().hour.do(sub_main)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
