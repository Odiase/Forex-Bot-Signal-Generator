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

##############DATABASES CONNECTIONS

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


db2 = TradeDatabase()


class DB_Plug():
    '''Handles Database Connections'''

    def __init__(self):
        '''Initialize Database Connection'''
        # Parse the connection URL
        config = parse_db_url("postgresql://forex_signal_bot_user:cXCwDrnAO9oZFiEI0ob0LZiLpYO3WsY6@dpg-cpri553qf0us738fs13g-a.oregon-postgres.render.com/forex_signal_bot", ssl_require=True)

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
    # chromedriver_autoinstaller.install()
    options = Options()
    # options.add_argument("--no-sandbox")
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
    # options.add_argument("--disable-software-rasterizer")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--remote-debugging-port=9222")


    # for option in options:
    #     chrome_options.add_argument(option)
    driver = webdriver.Chrome(options=options)

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
    TOKEN = "7258721074:AAHDu-Ckm6k_0l8wp1z6B47LDP-p8iTjuhs"
    # chat_id = "-1002001136974"
    #oduwa, #dima group
    chat_ids = ["1614557200", "-1002238594821"]
    # chat_id = "-1002238594821"
    for chat_id in chat_ids:
        try:
            parameters = {
                "chat_id" : chat_id,
                "text" : message
            }
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"#?chat_id={chat_id}&text={message}"
            request = requests.get(url, data=parameters)
        except:
            pass

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

def solveCaptcha():
    solver = TwoCaptcha("d1b123a6ba1e5655887c3d28dd3d3ea6")
    result = solver.recaptcha("6Lcqv24UAAAAAIvkElDvwPxD0R8scDnMpizaBcHQ","https://www.tradingview.com")
    time.sleep(60)
    print("Result : ", result)

def authenticateTradingView(driver):
    try:
        email_btn = getElement(driver, 20, (By.CLASS_NAME, "emailButton-nKAw8Hvt"), "single")
        email_btn.click()
        time.sleep(3)

        email_field = driver.switch_to.active_element
        email_field.send_keys("workwisehub.office@gmail.com")
        time.sleep(3)
        email_field.send_keys(Keys.TAB)
        password_field = driver.switch_to.active_element
        password_field.send_keys("dafflebag4eva")
        password_field.send_keys(Keys.ENTER)
        solver = TwoCaptcha("d1b123a6ba1e5655887c3d28dd3d3ea6")
        print("Solving Captcha")
        result = solver.recaptcha("6Lcqv24UAAAAAIvkElDvwPxD0R8scDnMpizaBcHQ","https://www.tradingview.com")

        recaptcha_response = driver.find_element(By.ID, 'g-recaptcha-response')
        driver.execute_script("arguments[0].style.display = 'block';", recaptcha_response)  # Make the element visible if necessary
        recaptcha_response.send_keys(result['code'])
        password_field.send_keys(Keys.ENTER)
        time.sleep(30)

        return True
    except:
        return False

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
        # if session_exists_in_pair_list:
            # remoce session from db1
            db.closeSession(session_currency)
            sendTelegramSignal(f"Watchlist Removal \n\n{session_currency} \n\n CLOSE TRADES on this Pair")
            #close open trades on this pair
            db2.insert_close_order(session_currency)

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
        sendTelegramSignal(f"Watchlist Addition \n\n{pair[0]}")


def getChartData(driver, trade_option_from_csm, currency_pair):
    '''Gets the entry Point From the Chart Based off pine code editor'''

    time_now = datetime.now()

    #get the latest buy/sell signal data
    signal_data_cells = getElement(driver, 30, (By.CSS_SELECTOR, ".ka-tr"), "multiple")
    latest_signal_cell = signal_data_cells[1]
    latest_trade_option_el = latest_signal_cell.find_elements(By.TAG_NAME, "td")[2]
    latest_trade_option = latest_trade_option_el.find_elements(By.CSS_SELECTOR, ".ka-cell")[1].text.lower()

    latest_trade_option_time_el = latest_signal_cell.find_elements(By.TAG_NAME, "td")[3]
    latest_trade_option_time = latest_trade_option_time_el.find_elements(By.CSS_SELECTOR, ".ka-cell")[1].text

    print(f"Latest Trade Option : {latest_trade_option.lower()} \nLatest Trade Time : {latest_trade_option_time}")
    print(f"Trade Option From CSM : {trade_option_from_csm.lower()}")

    # checking if the time between the last signal and current time is close enought to initiate a signal to MT4

    time_difference = time_now - datetime.strptime(latest_trade_option_time, "%Y-%m-%d %H:%M")
    print("TD : ", time_difference.total_seconds())
    if time_difference.total_seconds() / 3600 <= 1 and latest_trade_option == trade_option_from_csm.lower():
        print("Haha! its within the time frame.")
        telegram_signal = f'''OPEN TRADE \n\n{latest_trade_option} {currency_pair}'''
        sendTelegramSignal(telegram_signal)
        print("Signal Sent")
        #sendSignalToMT5()
        db2.insert_trade_order(currency_pair, trade_option_from_csm.upper())
        print("Sent Order TO Be Placed")
        pass
    else:
        sendTelegramSignal(f"{currency_pair} \n\nNo Signal Detected.")
        print("Its more than an Hour")
    return latest_trade_option




def openTradingView(driver, pairs, pairs_trade_option):
    '''Opens Trading View and Pine Editor to Enter Trade Script'''

    for i in range(len(pairs)):
        if i != 0:
            url = f"https://www.tradingview.com/chart/?symbol=FX_IDC%3A{pairs[i]}"
            driver.execute_script(f"window.open('{url}', '_blank');")
        else:
            driver.get(f"https://www.tradingview.com/chart/?symbol=FX_IDC%3A{pairs[i]}")

        trade_option = pairs_trade_option[i][1]

        #changing chart timeframe
        if i == 0:
            print("Opened Chart")
            chart_body_el = getElement(driver, 20, (By.TAG_NAME, "body"), "single")
            chart_body_el.send_keys("1h")
            time.sleep(2)
            # Use JavaScript to trigger the Enter key event
            active_element = driver.switch_to.active_element
            active_element.send_keys(Keys.ENTER)
            print("CLicked Enter")
            time.sleep(10)

        #open pine editor
        pine_editor = getElement(driver, 30, (By.CLASS_NAME, "tab-jJ_D7IlA"), "multiple")
        pine_editor[1].click()
        time.sleep(6)

        # interaction with pine editor
        if i == 0:
            pine_editor = driver.switch_to.active_element
            pine_editor.send_keys(Keys.CONTROL + 'a')
            pine_editor.send_keys(Keys.BACKSPACE)
            pine_editor.send_keys(PINE_EDITOR_SCRIPT)
        time.sleep(6)
        add_to_chart_el = getElement(driver, 30, (By.CLASS_NAME, "addToChartButton-YIGGCRdR"), "single")
        add_to_chart_el.click()
        time.sleep(5)

        # runs the account authentication of trading view
        if i == 0:
            authenticateTradingView(driver)
            add_to_chart_el = getElement(driver, 30, (By.CLASS_NAME, "addToChartButton-YIGGCRdR"), "single")
            add_to_chart_el.click()

        #clicks on "list of trades" Tab
        list_of_trade_el = getElement(driver, 20, (By.ID, "List of Trades"), "single")
        list_of_trade_el.click()
        order_signal = getChartData(driver, trade_option, pairs[i])
        # Sending the pine script data to the editor


def polarStatusCheck():
    '''Checks if the polar status for opened pairs is still open'''
    driver = startDriver()
    driver.quit()
    driver = startDriver()
    print("driver : ", driver)
    openSite(driver)
    currency_list = getCurrencyMeters(driver)
    pairs_data = pair_currencies(currency_list)

    DBPairValidation(pairs_data[1])
    driver.quit()

def openTradingView2(driver, pair, pair_trade_option):
    '''Opens Trading View and Pine Editor to Enter Trade Script'''
    url = f"https://www.tradingview.com/chart/?symbol=FX_IDC%3A{pair}"
    driver.get(url)
    print("Opened Chart")

    #changing the chart time frame        
    chart_body_el = getElement(driver, 20, (By.TAG_NAME, "body"), "single")
    chart_body_el.send_keys("1h")
    time.sleep(2)

    # Use JavaScript to trigger the Enter key event for the chart time confirmation
    active_element = driver.switch_to.active_element
    active_element.send_keys(Keys.ENTER)
    print("CLicked Enter")
    time.sleep(5)

    #open pine editor
    pine_editor = getElement(driver, 30, (By.CLASS_NAME, "tab-jJ_D7IlA"), "multiple")
    pine_editor[1].click()
    time.sleep(15)

    # interaction with pine editor
    pine_editor = driver.switch_to.active_element
    pine_editor.send_keys(Keys.CONTROL + 'a')
    pine_editor.send_keys(Keys.BACKSPACE)
    pine_editor.send_keys(PINE_EDITOR_SCRIPT)
    time.sleep(6)

    #loading pine script indicator on chart
    add_to_chart_el = getElement(driver, 30, (By.CLASS_NAME, "addToChartButton-YIGGCRdR"), "single")
    add_to_chart_el.click()
    time.sleep(5)

    # runs the account authentication of trading view
    authenticateTradingView(driver)
    # add_to_chart_el = getElement(driver, 30, (By.CLASS_NAME, "addToChartButton-YIGGCRdR"), "single")
    add_to_chart_el.click()

    #clicks on "list of trades" Tab
    list_of_trade_el = getElement(driver, 20, (By.ID, "List of Trades"), "single")
    list_of_trade_el.click()
    order_signal = getChartData(driver, pair_trade_option, pair)


def runBot():
    '''Runs the Bot'''

    driver = startDriver()
    openSite(driver)
    currency_list = getCurrencyMeters(driver)
    pairs_data = pair_currencies(currency_list)

    DBPairValidation(pairs_data[1])
    print("Opening Trading View.")
    print("Pairs Data : ", pairs_data)
    # openTradingView(driver, pairs_data[0], pairs_data[1])
    for i in range(len(pairs_data)):
        if i > 0:
            driver = startDriver()
        print(f"Opening for chart {pairs_data[0][i]}")
        openTradingView2(driver, pairs_data[0][i], pairs_data[1][i][1])
        driver.quit()
    driver.quit()




# runBot()
def main():
    print(datetime.now())
    running = True
    count = 0
    while running:
        # Get the current day of the week and time
        now = datetime.now()
        current_day = now.weekday()   # Monday is 0 and Sunday is 6
        current_hour = now.hour
        current_minute = now.minute


        # Check if the current day is Monday to Friday (0-4) and time is between 12 PM and 6 PM
        # if current_day >= 0 and current_day <= 4 and current_hour >= 7 and (current_hour < 22 or (current_hour == 18 and current_minute == 0)):
        if True:
            print(now)
            try:
                runBot()
                running = False
            except Exception as e:
                if count == 2:
                    running = False
                print(e)
                count+=1
                sendTelegramSignal(f"Network Error Detected \n\n Retry In Progress")
                time.sleep(5)
        else:
            print("Outside of allowed run time (Monday to Friday, 12 PM to 6 PM)")
            running = False  # Exit the loop if it's outside the allowed run time

main()