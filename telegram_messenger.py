import requests


def sendTelegramSignal(message):
    message = str(message)
    TOKEN = "7258721074:AAHDu-Ckm6k_0l8wp1z6B47LDP-p8iTjuhs"
    #oduwa, #dima group
    # chat_ids = ["1614557200", "-1002238594821"]
    chat_id = "1196997302" # mafii
    # for chat_id in chat_ids:
    #     try:
    #         parameters = {
    #             "chat_id" : chat_id,
    #             "text" : message
    #         }
    #         url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"#?chat_id={chat_id}&text={message}"
    #         request = requests.get(url, data=parameters)
    parameters = {
                "chat_id" : chat_id,
                "text" : message
            }
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"#?chat_id={chat_id}&text={message}"
    request = requests.get(url, data=parameters)
        # except:
        #     pass
        

# sendTelegramSignal("Bro Mafss!! \n\n Welcome!, I am TradyFx, and my duty is to send you Forex Signals and Updates on major Pairs")