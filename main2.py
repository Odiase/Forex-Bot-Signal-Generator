import requests

def sendTelegramSignal(message):
    message = str(message)
    TOKEN = "7258721074:AAHDu-Ckm6k_0l8wp1z6B47LDP-p8iTjuhs"
    # chat_id = "-1002001136974" # test group
    chat_id = "-1002238594821"
    parameters = {
        "chat_id" : chat_id,
        "text" : message
    }

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"#?chat_id={chat_id}&text={message}"
    request = requests.get(url, data=parameters)


sendTelegramSignal("Hello Everyone! I am TradyFx, and i'll be sending Forex Trading Signals Onward, Let's all have fun shall we!")