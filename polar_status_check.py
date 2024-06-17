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

    def closeAllOpenSessions(self):
        '''Change the status of all trading sessions to "CLOSED" where the status is "OPEN"'''

        # Open a cursor to perform database operations
        cur = self.conn.cursor()
        try:
            # Execute the command: update records to set trade_status to 'CLOSED' for all open sessions
            cur.execute("""
                UPDATE trading_session
                SET trade_status = 'CLOSED'
                WHERE trade_status = 'OPEN'
            """)
            # Commit the transaction
            self.conn.commit()
        except Exception as e:
            # Rollback in case of any error
            self.conn.rollback()
            print(f"An error occurred: {e}")
        finally:
            # Close the cursor
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
    chat_id = "-1002001136974" # Test Group
    # chat_id = "-1002238594821"
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
    # driver.get("https://www.tradingview.com/chart")
    driver.maximize_window()


def getCurrencyMeters(driver):
    '''Get The Currency Pairs and their Respective Meter Rating'''

    element_locator = (By.CLASS_NAME, "str-container")
    all_currency_elements = getElement(driver,30,element_locator,"multiple")
    currency_meter_list = []
    for i in all_currency_elements:
        element_data = {}
        element_data['currency'] = i.find_element(By.CLASS_NAME, 'title').text
        element_data['currency_level'] = int(i.find_element(By.CLASS_NAME, 'level').get_attribute('style').split(':')[1].replace("%;", ""))
        
        currency_meter_list.append(element_data)
    return currency_meter_list


def sort_pair(pair):
    '''Sort the Currency Pair to meet FX Standard'''

    currency_pairs = ["GBPUSD", "GBPJPY", "EURGBP", "GBPNZD", "GBPAUD", "GBPCAD", "GBPCHF", "EURUSD", "EURJPY", "EURCHF", "EURNZD", "EURAUD", "USDCAD", "USDJPY", "USDCHF", "NZDUSD", "AUDUSD", "NZDCHF", "AUDNZD", "NZDCAD", "NZDJPY", "AUDCAD", "AUDJPY", "AUDCHF", "CHFJPY", "CADCHF", "CADJPY", "EURCAD"]

    not_existing = True
    sell = False
    option=None
    while not_existing:
        if pair in currency_pairs:
            not_existing = False
        else:
            pair = pair[3:]+pair[:3]
            sell=True
    if sell:
        option = "SELL"
    else:
        option = "BUY"
    return pair, option



def pair_currencies(currency_list):
    '''Generate the currency pair from highest level and lowest level'''

    highest_level_currencies = [currency['currency'] for currency in currency_list if currency['currency_level'] == 100]
    lowest_level = min(currency_list, key=lambda x: x['currency_level'])['currency_level']

    lowest_level_currencies = [currency['currency'] for currency in currency_list if currency['currency_level'] == lowest_level]

    pairs = []
    db_data=[]
    for highest_currency in highest_level_currencies:
        for lowest_currency in lowest_level_currencies:
            pair = (highest_currency, lowest_currency)
            pair_data = sort_pair(''.join(pair))
            pairs.append(pair_data[0])
            pair_trade_option = pair_data[1]
            db_data.append([pair_data[0], pair_trade_option])
    print(pairs)
    return pairs, db_data


def DBPairValidation(pair_list):
    '''Checks open trades, then closes trades that don't meet requirements any longer and saves new Trades'''

    db = DB_Plug()
    all_open_sessions = db.getAllOpenSessions()
    filtered_pair_list = []
    print("All Open Sessions : ", all_open_sessions)
    print("Pair List : ", pair_list)

    # Iterate through all open sessions to find sessions that need to be closed
    for session in all_open_sessions:
        session_currency = session[1]
        session_trade_option = session[2]

        # Check if the session exists in the new pair list with the same trade option
        session_exists_in_pair_list = any(pair[0] == session_currency and pair[1] == session_trade_option for pair in pair_list)

        # If the session does not exist in the new pair list, close it
        if not session_exists_in_pair_list:
            db.closeSession(session_currency)
            sendTelegramSignal(f"NON POLAR ALERT!!! \n\n{session_currency} \n Close All Trades on this Pair\n\nNO LONGER POLAR!")

    # Filter out pairs that already exist in the open sessions with the same trade option
    for pair in pair_list:
        pair_currency = pair[0]
        pair_trade_option = pair[1]

        # Check if the pair exists in the open sessions with the same trade option
        pair_exists_in_open_sessions = any(session[1] == pair_currency and session[2] == pair_trade_option for session in all_open_sessions)

        # If the pair does not exist in the open sessions with the same trade option, add it to the filtered pair list
        if not pair_exists_in_open_sessions:
            filtered_pair_list.append(pair)

    print("Filtered Pair List: ", filtered_pair_list)
    for pair in filtered_pair_list:
        print("Trade Option: ", pair[1])
        db.insertNewSession(pair[0], pair[1], "OPEN")
        sendTelegramSignal(f"{pair[0]} [Added to DB] \n\n")


def polarStatusCheck():
    '''Checks if the polar status for opened pairs is still open'''
    driver = startDriver()
    driver.quit()
    driver = startDriver()

    openSite(driver)
    currency_list = getCurrencyMeters(driver)
    pairs_data = pair_currencies(currency_list)
    
    DBPairValidation(pairs_data[1])
    driver.quit()


polarStatusCheck()