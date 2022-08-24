"""
Get token from a pair address on DEX (uniswap, pancakeswap) with web3
Put secrets in .env and run this script
Requirement: python3, web3, python-dotenv
"""

import os
import requests
from web3 import Web3
from dotenv import load_dotenv
load_dotenv(verbose=True)

# constants
DECIMAL = 10 ** 18
API_URLS = {
    'uniswap': os.getenv("INFURA_API_URL"),
    'pancakeswap': 'https://bsc-dataseed1.binance.org'
}
ADDRESSES = {
    'uniswap': {
        'orai': {
            'token0': ['orai', '0x4c11249814f11b9346808179cf06e71ac328c1b5'],
            'token1': ['weth', '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'],
            'pair': '0x9081b50bad8beefac48cc616694c26b027c559bb'        # ORAI/WETH
        }
    },
    'pancakeswap': {
        'orai': {
            'token0': ['orai', '0xa325ad6d9c92b55a3fc5ad7e412b1518f96441c0'],
            'token1': ['wbnb', '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'],
            'pair': '0xf7697db76fbf4ba5d22c0c72ab986cf751fba3af'        # ORAI/WBNB
        }
    }
}
ABIS = {
    'uniswap': {
        'pair_abi_string': '[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"}]'
    },
    'pancakeswap': {
        'pair_abi_string': '[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"}]'
    },
    'chainlink': {
        'abi_string': '[{"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"}]'
    }
}

# ==== util funcs ====
def initialize_contract(w3, address, abi):
  checksummed_address = w3.toChecksumAddress(address)
  contract = w3.eth.contract(address=checksummed_address, abi=abi)
  return contract


# Used to find decimals value for a token
def get_decimals(token):
    decimals = 18
    if (token == 'wbtc'):
        decimals = 8
    elif (token == 'usdc' or token == 'usdt'):
        decimals = 6
    return decimals


# ==== main funcs ====
def get_chainlink_price(token='weth'):
    # token: 'weth' or 'wbnb'
    assert token == 'weth' or token == 'wbnb'
    contract_address = '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419' if token == 'weth' else '0x14e613ac84a31f709eadbdf89c6cc390fdc9540a'
    web3 = Web3(Web3.HTTPProvider(API_URLS['uniswap']))
    contract = initialize_contract(web3, contract_address, ABIS['chainlink']['abi_string'])
    ret = contract.functions.latestRoundData().call()
    return ret[1]/ (10**8)

def get_volume_price(dex_id,token_id):
    headers = {
    'accept': 'application/json',
            }
    params = {
        'coin_ids': token_id 
             }
    response = requests.get('https://api.coingecko.com/api/v3/exchanges/'+dex_id+'/tickers', params=params, headers=headers)
    return response.json()['tickers'][0]['converted_volume']['usd']


def get_token_price(dex='uniswap', token='orai'):
    # Setup web3
    web3 = Web3(Web3.HTTPProvider(API_URLS[dex]))
    contract = initialize_contract(web3, ADDRESSES[dex][token]['pair'], ABIS[dex]['pair_abi_string'])
    reserves = contract.functions.getReserves().call()
    # proper way
    # reserve0 = reserves[0] / get_decimals(ADDRESSES[dex][token]['token0'][0])
    # reserve1 = reserves[1] / get_decimals(ADDRESSES[dex][token]['token1'][0])
    # price01 = reserves[1] / reserves[0]
    # but if decimals are the same as in this case ORAI pairs
    price01 = reserves[1] / reserves[0]

    # get token1 price via api (USD)
    real_price1 =  get_chainlink_price(ADDRESSES[dex][token]['token1'][0])

    return price01 * real_price1



def get_uniswap_price(token):
    token = token.lower()
    avg = {
        'source' : 'UNISWAP',
        'price' : get_token_price(dex='uniswap', token=token),
        'volume24h' : get_volume_price(dex_id='uniswap_v2',token_id='oraichain-token')
    }
    return avg

def get_pancakeswap_price(token):
    token = token.lower()
    avg = {
        'source' : 'PANCAKESWAP',
        'price' : get_token_price(dex='pancakeswap', token=token),
        'volume24h' : get_volume_price(dex_id='pancakeswap_new',token_id='oraichain-token')
    }
    return avg

# KUCOIN 

# Doc: https://docs.kucoin.com/#get-24hr-stats

# Ex:
    # API: https://api.kucoin.com/api/v1/market/stats?symbol=BTC-USDT
    # DEX: https://www.kucoin.com/trade/BTC-USDT

# Note: 
    # Volume24h: USDT(*)
    # Pair: USDT
    # Timestamp: (1-2s)
def get_kucoin_price(token):
    response = requests.get('https://api.kucoin.com/api/v1/market/stats?symbol='+token+'-USDT')
    avg = {
        'source': 'KUCOIN',
        'price': float(response.json()['data']['last']),
        'volume24h': float(response.json()['data']['volValue']),
    }
    return avg
    
    
    
    
# COINMARKETCAP

# Doc: https://coinmarketcap.com/api/documentation/v1/#operation/getV1CryptocurrencyQuotesLatest

# Ex:
    # API: https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest
    # DEX: https://coinmarketcap.com/currencies/bitcoin/

# Note: 
    # Volume24h: USD
    # Pair: USD
    # Timestamp: (100-1000s)
 

def get_coinmarketcap_price(token):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {
        'symbol' : token
    }
    header = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY' : os.getenv('API_KEY_COINMARKETCAP')}
    response = requests.get(url=url,params=parameters,headers=header)
    avg = {
        'source': 'COINMARKERTCAP',
        'price': response.json()['data'][token]['quote']['USD']['price'],
        'volume24h': response.json()['data'][token]['quote']['USD']['volume_24h'],
    }
    return avg
    

# COINGECKO

# Docs: https://www.coingecko.com/en/api/documentation
#       https://github.com/man-c/pycoingecko

# Ex:
    # API: https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_vol=true&include_last_updated_at=true
    # DEX: https://www.coingecko.com/en/coins/bitcoin

# Note: 
    # Volume24h: USD
    # Pair: USD
    # Timestamp: (30-60s)

TOKEN_IDS_COINGECKO = {'ORAI': 'oraichain-token'}



def get_coingecko_price(token) :
    symbol = TOKEN_IDS_COINGECKO[token]
    url = "https://api.coingecko.com/api/v3/simple/price?ids="+symbol+"&vs_currencies=usd&include_24hr_vol=true&include_last_updated_at=true"
    response = requests.get(url)
    avg = {
        'source': 'COINGECKO',
        'price': response.json()[symbol]['usd'],
        'volume24h': response.json()[symbol]['usd_24h_vol'],
    }
    return avg
    

def get_oraidex_price(token):
    url = "https://backend-info.oraidex.io/tokens/v2/"+token
    response = requests.get(url)
    avg = {
        'source' : 'ORAIDEX',
        'price' : response.json()['price'],
        'volume24h' : response.json()['tradeVolume']

    }
    return avg 