import requests
from datetime import datetime, timedelta

class MarketDataService:
    def __init__(self):
        self.api_key = "5ZRTU7NJS6J9VB5Y"
        self.market_data = {}
        self.last_update = datetime.now()

    def get_current_market_data(self):
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'BTC']
        for symbol in symbols:
            self.market_data[symbol] = self.fetch_market_data(symbol)
        return self.market_data

    def get_asset_price(self, symbol):
        return self.fetch_market_data(symbol)

    def fetch_market_data(self, symbol):
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}'
        response = requests.get(url)
        data = response.json()
        if 'Global Quote' in data:
            price = float(data['Global Quote']['05. price'])
            return {'price': price}
        return {'price': None}