from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import MetaTrader5 as mt5

account = 154507996
server = "Exness-MT5Trial9"
password = "Iamfearless@123"

def account_login(login = account, password=password, server= server):
    if mt5.login(login,password,server):
        print("logged in succesffully")
    else: 
        print("login failed, error code: {}".format(mt5.last_error()))

def initialize(login = account, server=server, password=password):
    
    if not mt5.initialize():
        print("initialize() failed, error code {}", mt5.last_error())
    else:
        account_login(login, password, server)

def initialize_mt5(account, password, server, path=None):
    # Display data on the MetaTrader 5 package
    print("MetaTrader5 package author: ", mt5.__author__)
    print("MetaTrader5 package version: ", mt5.__version__)
    print(mt5.terminal_info())

    # Initialize MetaTrader 5
    if path:
        if not mt5.initialize(path):
            print("initialize() with path failed")
            mt5.shutdown()
            return False
    else:
        if not mt5.initialize():
            print("initialize() failed")
            mt5.shutdown()
            return False

    print("Initialized!")

    # Login to the account
    if not mt5.login(account, password, server):
        print(f"Server : {server} : Account = {account}, : Server = {server}")
        print("Failed to login, error code =", mt5.last_error())
        mt5.shutdown()
        return False
    else:
        print("Logged in")

    print(f"Successfully logged in to account {account}")
    return True

# Example usage:
# If you know the path to your terminal64.exe, you can specify it here
# path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
# If not, just call the function without the path argument
# path = None

initialize(account, password, server)
