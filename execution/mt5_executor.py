import MetaTrader5 as mt5

def connect():

    mt5.initialize()


def place_trade(symbol, action, lot=0.01):

    price = mt5.symbol_info_tick(symbol).ask

    if action == "SELL":
        price = mt5.symbol_info_tick(symbol).bid

    order_type = mt5.ORDER_TYPE_BUY if action=="BUY" else mt5.ORDER_TYPE_SELL

    request = {

        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 10,
        "magic": 100,
        "comment": "AI Gold Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    mt5.order_send(request)