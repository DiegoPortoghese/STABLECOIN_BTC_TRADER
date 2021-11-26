import requests
import time
import json
import os
import datetime
from subprocess import Popen, PIPE

from termcolor import colored # package: termcolor
from tabulate import tabulate # package: tabulate
from websocket import create_connection # package: websocket-client2

## UPGRADES LIST
"""
1.5:
-Add configuration for MAX tradable ammount
-- INFO: for use it in program , set this config: BTC_TRADE_QTY="MAX"

1.4:
-Fix Ticker last trade price
1.3:
-Added checker for last trade with no value
-Added clear status multiplatform compatibility , windows and linux
-Updater fix 
"""
VERSION = "1.5"

## CONFIG
API_SECRET = ""
VERBOSE = False
STRATEGY="MINMAX"
CHECK_EXCHANGE_TIME_SECONDS=5
BTC_TRADE_QTY=0.00051
BTC_TRADE_MODE=False
BUY_VALUE=8000
SELL_VALUE=9000
GIT_URL=""
GITHUB_PERSONAL_TOKEN=""

# internal declaration
options = {}
options['origin'] = 'https://exchange.blockchain.com'
url = "wss://ws.prod.blockchain.info/mercury-gateway/v1/ws"
out_strings=[]
checker_config=None

def clear():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

## Utils ##
def verbose_print(message):
    now = datetime.datetime.now()
    date_time = now.strftime("%m/%d/%Y %H:%M:%S")
    with open("main.log","a") as f:
        f.write("["+date_time+"]: "+message+"\n")
    if VERBOSE:
        Lprint(message)

def Lprint(message):
    now = datetime.datetime.now()
    date_time = now.strftime("%m/%d/%Y %H:%M:%S")
    out_strings.append("["+date_time+"]: "+message)

def log_render():
    print("")
    print("-----------------------------------------------LOGS-----------------------------------------------")
    for message in out_strings[-15:]:
        print(message)
    print("--------------------------------------------------------------------------------------------------")    

def exchange_log(json):
    with open("exchange.log",'a') as f:
        f.write(json+"\n")

def load_config():
    global checker_config
    global API_SECRET
    global VERBOSE
    global BTC_TRADE_QTY
    global BTC_TRADE_MODE
    global STRATEGY
    global CHECK_EXCHANGE_TIME_SECONDS
    global BUY_VALUE
    global SELL_VALUE
    global GIT_URL
    global GITHUB_PERSONAL_TOKEN
    try:
        checker_config = os.stat("config.ini").st_mtime
        lines=[]
        with open("config.ini","r") as f:
            lines=f.readlines()
        for line in lines:
            if line.startswith("API_SECRET"):
                API_SECRET=line.replace("API_SECRET=","").replace('"',"").replace("\n","")
            if line.startswith("VERBOSE"):
                if line.split("=")[1].replace("\n","") == "True":
                    VERBOSE = True
                else:
                    VERBOSE = False
            if line.startswith("BTC_TRADE_QTY"):
                try:
                    if BTC_TRADE_QTY == line.replace("BTC_TRADE_QTY=","").replace('"',"").replace("\n","") == "MAX":
                        BTC_TRADE_MODE = True
                    else:
                        BTC_TRADE_MODE = False
                except:
                    pass
                if BTC_TRADE_MODE == False:
                    BTC_TRADE_QTY=float(line.split("=")[1])
            if line.startswith("STRATEGY"):
                STRATEGY=line.split("=")[1].replace('"',"").replace("\n","")
            if line.startswith("CHECK_EXCHANGE_TIME_SECONDS"):
                CHECK_EXCHANGE_TIME_SECONDS=int(line.split("=")[1])
            if line.startswith("BUY_VALUE"):
                BUY_VALUE=float(line.split("=")[1])
            if line.startswith("SELL_VALUE"):
                SELL_VALUE=float(line.split("=")[1])
            if line.startswith("GIT_URL"):
                GIT_URL=line.replace("GIT_URL=","").replace('"',"").replace("\n","")
            if line.startswith("GITHUB_PERSONAL_TOKEN"):
                GITHUB_PERSONAL_TOKEN=line.replace("GITHUB_PERSONAL_TOKEN=","").replace('"',"").replace("\n","")
    except:
        Lprint(colored("Error configuration file ! check your config.ini","red"))
        print(colored("Error configuration file ! check your config.ini","red"))
        exit()
    if (len(API_SECRET) < 200):
        Lprint(colored("API_SECRET CONFIG IS WRONG! check it in the config.ini","red"))
        print(colored("API_SECRET CONFIG IS WRONG! check it in the config.ini","red"))
        print(colored("Error configuration file ! check your config.ini","red"))
        exit()

def check_config():
    checker_config_buff = os.stat("config.ini").st_mtime
    if checker_config_buff != checker_config:
        Lprint(colored("New configuration detected!","blue"))
        load_config()
        Lprint(colored("New Configuration Loaded Successfully!","green"))
        Lprint("NEW CONFIGURATION")
        Lprint("VERBOSE: "+str(VERBOSE))
        Lprint("BTC_TRADE_QTY: "+str(BTC_TRADE_QTY))
        Lprint("STRATEGY: "+STRATEGY)
        Lprint("CHECK_EXCHANGE_TIME_SECONDS: "+str(CHECK_EXCHANGE_TIME_SECONDS))
        Lprint("BUY_VALUE: "+str(BUY_VALUE))
        Lprint("SELL_VALUE: "+str(SELL_VALUE))

def get_profit():
    exchanges=[]
    with open("exchange.log") as f:
        lines = f.readlines()
    for line in lines:
        exchanges.append(json.loads(line))
    profit=0
    for exchange in exchanges:
        orderQty = exchange["orderQty"]
        avgPx = exchange["avgPx"]
        if exchange["side"] == "sell":
            profit= profit+(orderQty*avgPx)
        elif exchange["side"] == "buy":
            profit= profit-(orderQty*avgPx)
    return profit

def table_exchange():
    exchanges=[]
    with open("exchange.log") as f:
        lines = f.readlines()
    for line in lines:
        exchanges.append(json.loads(line))
    table_exchanges = []
    for exchange in exchanges:
        bf_exchange = []
        bf_exchange.append(exchange["orderID"])
        if exchange["side"] == "sell":
            bf_exchange.append(colored(exchange["side"],"green"))
        else:
            bf_exchange.append(colored(exchange["side"],"red"))
        bf_exchange.append(exchange["orderQty"])
        bf_exchange.append(exchange["avgPx"])
        bf_exchange.append(exchange["ordStatus"])
        bf_exchange.append(exchange["transactTime"])
        bf_exchange.append(exchange["tradeId"])

        table_exchanges.append(bf_exchange)
        
    print(tabulate(table_exchanges, headers=["orderID","side","orderQty","avgPx","ordStatus","transactTime","tradeId"]))


def check_update():
    verbose_print("Checking for Updates")
    try:
        pipe = Popen("curl -s https://"+GITHUB_PERSONAL_TOKEN+"@"+GIT_URL+'/master/version_controller.txt'+"", shell=True,stdout=PIPE) # curl call 
        version_buff = pipe.communicate()[0].decode("utf-8")
        verbose_print(str(version_buff))
        if float(version_buff) > float(VERSION):
            Lprint("New version available , Version "+version_buff)
            Lprint("UPDATING PLEASE WAIT..")

            time.sleep(5)
            Popen("python3 ./reloader.py", shell=True) # start reloader
            exit("exit for updating")
    except Exception as e:
        verbose_print(e)
        pass

## BLOCKCHAIN WEBSOCKET API FUNCTIONS ##

def get_btcpax():
    ws = create_connection(url, **options)
    msg = '{"action": "subscribe", "channel": "ticker", "symbol": "BTC-PAX"}'
    ws.send(msg)
    result = ws.recv()
    verbose_print(result)
    result = ws.recv()
    verbose_print(result)
    ws.close()
    return json.loads(result)["last_trade_price"]#{'seqnum': 1, 'event': 'snapshot', 'channel': 'ticker', 'symbol': 'BTC-PAX', 'price_24h': 879me_24h":4.80918,"last_trade_price":8721.7}7.4, 'volume_24h': 4.80918, 'last_trade_price': 8721.7

def get_balances():
    """
    FUNCTION FOR GET CURRENT BALANCES. 
    Out: Balance in json
    """
    ws = create_connection(url, **options)
    msg = '{"token": "'+API_SECRET+'", "action": "subscribe", "channel": "auth"}'
    ws.send(msg)
    result =  ws.recv()
    verbose_print(result)
    msg = '{"action": "subscribe", "channel": "balances"}'
    ws.send(msg)
    result = ws.recv()
    verbose_print(result)
    result = ws.recv()
    ws.close()
    verbose_print(result)
    json_balances = json.loads(result)
    for x in json_balances["balances"]:
        if x["currency"] == "BTC":
            btc_balance = x["balance"]
        if x["currency"] == "PAX":
            pax_balance = x["balance"]
    print("Account Balance: "+colored(str(btc_balance)+" BTC","yellow")+" | "+colored(str(pax_balance)+" PAX","green"))

def get_balances_currency(currency=""):
    """
    FUNCTION FOR GET CURRENT BALANCES specific currency. 
    in: "BTC" or "PAX"
    Out: Balance in float
    """
    ws = create_connection(url, **options)
    msg = '{"token": "'+API_SECRET+'", "action": "subscribe", "channel": "auth"}'
    ws.send(msg)
    result =  ws.recv()
    verbose_print(result)
    msg = '{"action": "subscribe", "channel": "balances"}'
    ws.send(msg)
    result = ws.recv()
    verbose_print(result)
    result = ws.recv()
    ws.close()
    verbose_print(result)
    json_balances = json.loads(result)
    for x in json_balances["balances"]:
        if x["currency"] == "BTC":
            btc_balance = x["balance"]
        if x["currency"] == "PAX":
            pax_balance = x["balance"]
    if currency == "BTC":
        return btc_balance
    if currency == "PAX":
        return pax_balance
    return 0


def sell_btc(value):
    """
    SELL btc function. give value of BTC to sell. return srv json response
    """
    ws = create_connection(url, **options)
    msg = '{"token": "'+API_SECRET+'", "action": "subscribe", "channel": "auth"}'
    ws.send(msg)
    result =  ws.recv()
    verbose_print(result)
    msg = '{"action": "subscribe", "channel": "trading"}'
    ws.send(msg)
    result =  ws.recv()
    verbose_print(result)
    result =  ws.recv()
    verbose_print(result)
    msg = '{ "action": "NewOrderSingle", "channel": "trading", "clOrdID": "def SELL", "symbol": "BTC-PAX", "ordType": "market", "timeInForce": "GTC", "side": "sell", "orderQty": '+str(value)+' }'
    ws.send(msg)
    result = ws.recv()
    verbose_print(result)
    exchange_log(result)
    ##OUT
    sell_return = json.loads(result)
    if sell_return["text"] == "Fill":
        Lprint(colored("Sell of "+str(value) +" BTC Completed successfully","green"))
    else:
        Lprint(colored("Sell of "+str(value) +" BTC Error occurred",'red'))
        Lprint(colored("API say: "+sell_return["text"],"red"))

def buy_btc(value):
    """
    SELL btc function. give value of BTC to buy. return srv json response
    """
    ws = create_connection(url, **options)
    msg = '{"token": "'+API_SECRET+'", "action": "subscribe", "channel": "auth"}'
    ws.send(msg)
    result =  ws.recv()
    verbose_print(result)
    msg = '{"action": "subscribe", "channel": "trading"}'
    ws.send(msg)
    result =  ws.recv()
    verbose_print(result)
    result =  ws.recv()
    verbose_print(result)
    msg = '{ "action": "NewOrderSingle", "channel": "trading", "clOrdID": "def BUY", "symbol": "BTC-PAX", "ordType": "market", "timeInForce": "GTC", "side": "buy", "orderQty": '+str(value)+' }'
    ws.send(msg)
    result = ws.recv()
    verbose_print(result)
    exchange_log(result)
    buy_return = json.loads(result)
    if buy_return["text"] == "Fill":
        Lprint(colored("Buy of "+str(value) +" BTC Completed successfully","green"))
    else:
        Lprint(colored("Buy of "+str(value) +" BTC Error occurred",'red'))
        Lprint(colored("API say: "+buy_return["text"],"red")) 


def strategy_minmax():
    start_time = time.time()
    print(colored("STRATEGY MINMAX STARTED!","red"))
    last_price = get_btcpax()
    while True:
        now = datetime.datetime.now()
        date_time = now.strftime("%m/%d/%Y %H:%M:%S")
        time.sleep(CHECK_EXCHANGE_TIME_SECONDS)
        clear()
        check_config()
        check_update()
        later = time.time()
        difference = int(later - start_time)
        print(colored("BLOCKCHAIN TRADER BOT | STRATEGY MIN MAX | Execution Time: "+str(datetime.timedelta(seconds=difference)),"white"))
        print(colored("STATISTICS","blue"))
        get_balances()
        profit=get_profit()
        print(colored("Current Profit: ","white")+colored(str(profit)+" PAX","green"))
        print(colored("Trade Quantity: ","white")+colored(str(BTC_TRADE_QTY)+" BTC","yellow"))
        price = get_btcpax()
        print(colored("TICKER","blue"))
        print(colored("BTC/PAX: ","white")+colored(str(price)+" PAX","blue"))
        print("")
        table_exchange()
        
        if last_price != price:
            last_price = price
            Lprint(colored("New Price Detected! BTC/PAX price: "+str(price),"blue"))        

        exchanges=[]
        with open("exchange.log") as f:
            lines = f.readlines()
        for line in lines:
            exchanges.append(json.loads(line))
        last_valid_side=[]
        for exchange in exchanges:
            if exchange["text"] == "Fill":
                last_valid_side=exchange["side"]
        if BTC_TRADE_MODE == False:
            if len(last_valid_side) > 0:
                if last_valid_side=="sell":
                    if price <= BUY_VALUE:
                        buy_btc(BTC_TRADE_QTY)
                if last_valid_side=="buy":
                    if price >= SELL_VALUE:
                        sell_btc(BTC_TRADE_QTY)
            else:
                if price <= BUY_VALUE:
                    buy_btc(BTC_TRADE_QTY)
                if price >= SELL_VALUE:
                    sell_btc(BTC_TRADE_QTY)
        else:
            BUY_DYN_BTC_TRADE_QTY = (get_balances_currency("PAX")/get_btcpax())-((get_balances_currency("PAX")/get_btcpax())*0.03)
            SELL_DYN_BTC_TRADE_QTY = get_balances_currency("BTC")-(get_balances_currency("BTC")*0.03)
            if len(last_valid_side) > 0:
                if last_valid_side=="sell":
                    if price <= BUY_VALUE:
                        buy_btc(BUY_DYN_BTC_TRADE_QTY)
                if last_valid_side=="buy":
                    if price >= SELL_VALUE:
                        sell_btc(SELL_DYN_BTC_TRADE_QTY)
            else:
                if price <= BUY_VALUE:
                    buy_btc(BUY_DYN_BTC_TRADE_QTY)
                if price >= SELL_VALUE:
                    sell_btc(SELL_DYN_BTC_TRADE_QTY)            
        log_render()

if __name__ == "__main__":
    print(colored("Blockchain Trader BOT Starting...","blue"))
    load_config()
    print(colored("Configuration Loaded Successfully!","green"))
    print("CONFIGURATION")
    print("VERBOSE: "+str(VERBOSE))
    print("BTC_TRADE_QTY: "+str(BTC_TRADE_QTY))
    print("STRATEGY: "+STRATEGY)
    print("CHECK_EXCHANGE_TIME_SECONDS: "+str(CHECK_EXCHANGE_TIME_SECONDS))
    print("BUY_VALUE: "+str(BUY_VALUE))
    print("SELL_VALUE: "+str(SELL_VALUE))
    if STRATEGY == "MINMAX":
        strategy_minmax()
        #Simulator()
    pass
