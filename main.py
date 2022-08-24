from get_price_dex import *
import threading
from fastapi import FastAPI
import time



def price(token):
    data = []
    thread = []
    def thread1(token):
        data.append(get_oraidex_price(token))
    def thread2(token):
        data.append(get_coingecko_price(token))
    def thread3(token):
        data.append(get_coinmarketcap_price(token))
    def thread4(token):
        data.append(get_kucoin_price(token))
    def thread5(token):
        data.append(get_uniswap_price(token))
    def thread6(token):
        data.append(get_pancakeswap_price(token))
        
    thread.append(threading.Thread(target=thread1,args={token,}))
    thread.append(threading.Thread(target=thread2,args={token,}))
    thread.append(threading.Thread(target=thread3,args={token,}))
    thread.append(threading.Thread(target=thread4,args={token,}))
    thread.append(threading.Thread(target=thread5,args={token,}))
    thread.append(threading.Thread(target=thread6,args={token,}))
    for _thread in thread:
        _thread.start()
    for _thread in thread:
        _thread.join()
    avg = {
        'data' : data,
        'timestamp' : time.time()
    }
    return avg

app = FastAPI() 
@app.get("/{token}")
async def get_price(token):
    return price(token.upper())
