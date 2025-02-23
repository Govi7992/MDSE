from datetime import datetime

class PortfolioManager:
    def __init__(self):
        self.portfolios = {}
        
    def create_portfolio(self, user_id, name):
        if user_id not in self.portfolios:
            self.portfolios[user_id] = {}
            
        portfolio_id = len(self.portfolios[user_id]) + 1
        self.portfolios[user_id][portfolio_id] = {
            'name': name,
            'assets': {},
            'created_at': datetime.now(),
            'last_updated': datetime.now()
        }
        return portfolio_id

    def add_asset(self, user_id, portfolio_id, asset_data):
        
        if not self._validate_portfolio_access(user_id, portfolio_id):
            return False

        portfolio = self.portfolios[user_id][portfolio_id]
        asset_id = len(portfolio['assets']) + 1
        
        portfolio['assets'][asset_id] = {
            **asset_data,
            'added_at': datetime.now(),
            'last_updated': datetime.now()
        }
        
        portfolio['last_updated'] = datetime.now()
        return asset_id

    def update_asset(self, user_id, portfolio_id, asset_id, updates):
        if not self._validate_portfolio_access(user_id, portfolio_id):
            return False

        portfolio = self.portfolios[user_id][portfolio_id]
        if asset_id not in portfolio['assets']:
            return False

        portfolio['assets'][asset_id].update(updates)
        portfolio['assets'][asset_id]['last_updated'] = datetime.now()
        portfolio['last_updated'] = datetime.now()
        return True

    def remove_asset(self, user_id, portfolio_id, asset_id):
        if not self._validate_portfolio_access(user_id, portfolio_id):
            return False

        portfolio = self.portfolios[user_id][portfolio_id]
        if asset_id not in portfolio['assets']:
            return False

        del portfolio['assets'][asset_id]
        portfolio['last_updated'] = datetime.now()
        return True

    def _validate_portfolio_access(self, user_id, portfolio_id):
        return (user_id in self.portfolios and 
                portfolio_id in self.portfolios[user_id])

    def get_portfolio_value(self, user_id, portfolio_id, current_prices):
        if not self._validate_portfolio_access(user_id, portfolio_id):
            return 0

        portfolio = self.portfolios[user_id][portfolio_id]
        total_value = 0

        for asset in portfolio['assets'].values():
            current_price = current_prices.get(asset['symbol'], 0)
            total_value += current_price * asset['quantity']

        return total_value