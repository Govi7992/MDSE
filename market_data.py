import requests
from datetime import datetime

class MarketDataService:
    def __init__(self):
        self.api_key = "5ZRTU7NJS6J9VB5Y"
        self.market_data = {}
        self.last_update = datetime.now()

    def fetch_market_data(self, symbol: str) -> dict:
        """
        Fetch market data for a given symbol.
        Returns a dictionary with price information.
        """
        try:
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}'
            response = requests.get(url)
            data = response.json()

            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                price = float(data['Global Quote']['05. price'])
                return {'price': price}
            else:
                return {'price': None}
                
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return {'price': None}

    def get_current_market_data(self) -> dict:
        """Get current market data for all tracked symbols."""
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'BTC']
        current_data = {}
        
        for symbol in symbols:
            current_data[symbol] = self.fetch_market_data(symbol)
            
        return current_data

    def get_asset_price(self, symbol: str) -> dict:
        """Get current price for a specific asset."""
        return self.fetch_market_data(symbol)
