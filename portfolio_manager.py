from datetime import datetime
from typing import Dict, Optional
from recommendation_engine import RecommendationEngine
from asset_db import AssetDB
from market_data import MarketDataService

class PortfolioManager:
    def __init__(self):
        """Initialize portfolio manager with dashboard capabilities"""
        self.portfolios = {}
        self.recommendation_engine = RecommendationEngine()
        self.market_data = MarketDataService()
        self.asset_db = AssetDB()
        
    def create_portfolio(self, user_id, name):
        """Create a new portfolio"""
        if not user_id:
            raise ValueError("User ID cannot be empty")
            
        if user_id not in self.portfolios:
            self.portfolios[user_id] = {}
            
        portfolio_id = len(self.portfolios[user_id]) + 1
        portfolio = {
            'name': name,
            'assets': {},
            'created_at': datetime.now(),
            'last_updated': datetime.now()
        }
        
        self.portfolios[user_id][portfolio_id] = portfolio

        try:
            self.asset_db.update_portfolio(user_id, portfolio)
        except:
            pass
        
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
            raise ValueError("Invalid portfolio access")

        portfolio = self.portfolios[user_id][portfolio_id]
        total_value = 0

        for asset in portfolio['assets'].values():
            symbol = asset['symbol']
            if symbol not in current_prices:
                continue
                
            price_data = current_prices[symbol]
            current_price = price_data['price'] if isinstance(price_data, dict) else price_data
            total_value += current_price * asset['quantity']

        return total_value

    def get_recommendations(self, user_id: str, portfolio_id: str) -> Dict:
        """Get investment recommendations for portfolio"""
        risk_profile = self.get_risk_profile(user_id)
        market_data = self.market_data.get_current_market_data()
        return self.recommendation_engine.generate_recommendations(risk_profile, market_data)
        
    def display_portfolio(self, user_id: str, portfolio_id: str) -> Dict:
        """Get portfolio display data"""
        if not self._validate_portfolio_access(user_id, portfolio_id):
            return {}
            
        portfolio = self.portfolios[user_id][portfolio_id]
        current_prices = self.market_data.get_current_market_data()
        return {
            'portfolio': portfolio,
            'total_value': self.get_portfolio_value(user_id, portfolio_id, current_prices),
            'last_updated': portfolio['last_updated']
        }
        
    def generate_alert(self, user_id: str, portfolio_id: str) -> Optional[str]:
        """Generate portfolio alerts based on market conditions"""
        if not self._validate_portfolio_access(user_id, portfolio_id):
            return None
            
        portfolio = self.portfolios[user_id][portfolio_id]
        return None

    def calculate_performance(self, initial_value: float, current_value: float) -> Dict:
        """Calculate portfolio performance metrics"""
        if initial_value <= 0:
            raise ValueError("Initial value must be greater than 0")
            
        profit_loss = current_value - initial_value
        return_percentage = (profit_loss / initial_value) * 100
        
        return {
            'return_percentage': return_percentage,
            'profit_loss': profit_loss
        }
