from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import MetaTrader5 as mt5

login = 51819267
server = "ICMarketsSC-Demo"
password = "!R$$LjVJr0&IF2"

def verify_login():
    account_info = mt5.account_info()._asdict()
    if account_info:
        print("Account Info:", account_info)
        return True
    else:
        print("Failed to get account info, error code:", mt5.last_error())
        return False

def account_login(login, password, server):
    if mt5.login(login,password,server):
        print("logged in succesffully")
    else: 
        print("login failed, error code: {}".format(mt5.last_error()))

def check_initialization():
    # Terminal information
    terminal_info = mt5.terminal_info()
    if terminal_info:
        print("MT5 Terminal Info:", terminal_info)
    else:
        print("Failed to get terminal info, error code:", mt5.last_error())

    # Account information
    account_info = mt5.account_info()
    if account_info:
        print("MT5 Account Info:", account_info)
    else:
        print("Failed to get account info, error code:", mt5.last_error())

    # Total number of symbols
    symbols_total = mt5.symbols_total()
    if symbols_total != -1:
        print("Total number of symbols:", symbols_total)
    else:
        print("Failed to get symbols total, error code:", mt5.last_error())

    # Specific symbol information
    symbol_info = mt5.symbol_info("EURUSD")
    if symbol_info:
        print("Symbol Info for EURUSD:", symbol_info)
    else:
        print("Failed to get symbol info for EURUSD, error code:", mt5.last_error())

def initialize(login,password,server):
    # shuts down any initial connection or instance of mt5
    mt5.shutdown()
    
    if not mt5.initialize():
        print("initialize() failed, error code {}", mt5.last_error())
    else:
        print("MT5 Has Been Initialized.")
        check_initialization()
        time.sleep(5)
        account_login(login,password,server)
        verify_login()

# Example usage:
# If you know the path to your terminal64.exe, you can specify it here
# path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
# If not, just call the function without the path argument
# path = None

initialize(login,password,server)
# account_login(login,password,server)
