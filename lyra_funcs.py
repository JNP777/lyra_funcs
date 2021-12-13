
from web3 import Web3
import requests
import pandas as pd
from datetime import datetime

from config import web3_provider,  lyra_deployment


w3 = Web3(Web3.HTTPProvider(web3_provider))
w3.isConnected()

# Get all prices for active strikes and board for a specific market (i.e "sETH", "sBTC")
def get_prices(market):

    # Getting deployment info for lyra smart contracts from github
    deployment = requests.get(lyra_deployment).json()
    market_data =deployment["targets"]["markets"][market]
    
    # Option market contract for ethereum (give us the active board)
    OptionMarket_addy=Web3.toChecksumAddress(market_data["OptionMarket"]["address"])
    ABI_market=deployment["sources"]["OptionMarket"]["abi"]
    OptionMarket = w3.eth.contract(OptionMarket_addy, abi=ABI_market)
    # fetching live boards (each expiry date is a board)
    boards=OptionMarket.functions.getLiveBoards().call()

    # Contract for getting the listing and prices on every board
    OptionMarketViewer_addy=Web3.toChecksumAddress(market_data["OptionMarketViewer"]["address"])
    ABI_viewer=deployment["sources"]["OptionMarketViewer"]["abi"]
    OptionMarketViewer = w3.eth.contract(OptionMarketViewer_addy, abi=ABI_viewer)

    # fetching prices for every strike in every board
    options_price={}
    for board in boards:
        
        # Get board listing information (strikes)
        listing = OptionMarketViewer.functions.getListingsForBoard(board).call()

        # Iterate in each strike of the listing
        for option in listing:
            name=market +"-"+ str(int(option[2]/10**18)) +"-"+ str(datetime.fromtimestamp(option[3]))[0:10]
            options_price[name]={
                                        "id": option[0],
                                        "boardId": option[1] ,
                                        "strike": option[2]/10**18,
                                        "expiry":option[3] ,
                                        "iv":option[4]/10**18 ,
                                        "skew":option[5]/10**18 ,
                                        "callPrice":option[6]/10**18 ,
                                        "putPrice": option[7]/10**18,
                                        "callDelta":option[8]/10**18 ,
                                        "putDelta":option[9]/10**18 ,
                                        "longCall":option[10]/10**18 ,
                                        "shortCall":option[11]/10**18 ,
                                        "longPut":option[12]/10**18 ,
                                        "shortPut":option[13]/10**18 ,
                            }
    
    # Creating a df
    options_price_df = pd.DataFrame.from_dict(options_price, orient="index")
    options_price_df["expiry_date"] = pd.to_datetime(options_price_df["expiry"], unit = 's')

    return {"dict":options_price,"df":options_price_df}







