import unittest
from unittest.mock import Mock, patch, MagicMock
from portfolio_manager import PortfolioManager
from datetime import datetime

class TestPortfolioManager(unittest.TestCase):
    def setUp(self):
        self.portfolio_manager = PortfolioManager()
        self.portfolio_manager.asset_db.update_portfolio = MagicMock()
        self.portfolio_manager.market_data.get_current_market_data = MagicMock(return_value={'AAPL': 150, 'GOOGL': 2800})
        self.test_user_id = "test_user"
        self.test_portfolio = {
            'name': 'Test Portfolio',
            'assets': {
                'AAPL': {
                    'quantity': 10,
                    'purchase_price': 150.00,
                    'purchase_date': datetime.now().isoformat()
                }
            }
        }

    def test_portfolio_creation(self):
        """Test portfolio creation"""
        portfolio_id = self.portfolio_manager.create_portfolio(
            self.test_user_id,
            self.test_portfolio['name']
        )
        self.assertIsNotNone(portfolio_id)
        self.assertIn(self.test_user_id, self.portfolio_manager.portfolios)
        self.assertIn(portfolio_id, self.portfolio_manager.portfolios[self.test_user_id])
        self.assertEqual(self.portfolio_manager.portfolios[self.test_user_id][portfolio_id]['name'], self.test_portfolio['name'])

    def test_asset_management(self):
        """Test asset management operations"""
        portfolio_id = self.portfolio_manager.create_portfolio(
            self.test_user_id,
            self.test_portfolio['name']
        )
        
       
        asset_id = self.portfolio_manager.add_asset(
            self.test_user_id,
            portfolio_id,
            {
                'symbol': 'MSFT',
                'quantity': 5,
                'purchase_price': 280.00
            }
        )
        self.assertTrue(asset_id)
        
        
        success = self.portfolio_manager.update_asset(
            self.test_user_id,
            portfolio_id,
            asset_id,
            {'quantity': 10}
        )
        self.assertTrue(success)
        
        
        success = self.portfolio_manager.remove_asset(
            self.test_user_id,
            portfolio_id,
            asset_id
        )
        self.assertTrue(success)

    @patch('market_data.MarketDataService')
    def test_portfolio_valuation(self, mock_market_data):
        """Test portfolio valuation"""
        mock_market_data.return_value.get_current_market_data.return_value = {
            'AAPL': {'price': 160.00}
        }
        
        portfolio_id = self.portfolio_manager.create_portfolio(
            self.test_user_id,
            self.test_portfolio['name']
        )
        
        self.portfolio_manager.add_asset(
            self.test_user_id,
            portfolio_id,
            {
                'symbol': 'AAPL',
                'quantity': 10,
                'purchase_price': 150.00
            }
        )
        
        value = self.portfolio_manager.get_portfolio_value(
            self.test_user_id,
            portfolio_id,
            {'AAPL': {'price': 160.00}}
        )
        
        self.assertEqual(value, 1600.00)  

    def test_portfolio_performance(self):
        """Test portfolio performance calculation"""
        portfolio_id = self.portfolio_manager.create_portfolio(
            self.test_user_id,
            self.test_portfolio['name']
        )
        
        initial_value = 1500.00 
        current_value = 1600.00 
        
        performance = self.portfolio_manager.calculate_performance(
            initial_value,
            current_value
        )
        
        self.assertIsInstance(performance, dict)
        self.assertIn('return_percentage', performance)
        self.assertIn('profit_loss', performance)

    def test_error_handling(self):
        """Test error handling"""
        
        with self.assertRaises(ValueError):
            self.portfolio_manager.get_portfolio_value(
                self.test_user_id,
                'invalid_id',
                {}
            )
        
        
        with self.assertRaises(ValueError):
            self.portfolio_manager.create_portfolio(
                '',
                'Test Portfolio'
            )

    def test_create_portfolio(self):
        user_id = 'user1'
        portfolio_name = 'Tech Stocks'
        portfolio_id = self.portfolio_manager.create_portfolio(user_id, portfolio_name)
        
        self.assertIn(user_id, self.portfolio_manager.portfolios)
        self.assertIn(portfolio_id, self.portfolio_manager.portfolios[user_id])
        self.assertEqual(self.portfolio_manager.portfolios[user_id][portfolio_id]['name'], portfolio_name)

    def test_add_asset(self):
        user_id = 'user1'
        portfolio_id = self.portfolio_manager.create_portfolio(user_id, 'Tech Stocks')
        asset_data = {'symbol': 'AAPL', 'quantity': 10}
        
        asset_id = self.portfolio_manager.add_asset(user_id, portfolio_id, asset_data)
        
        self.assertIn(asset_id, self.portfolio_manager.portfolios[user_id][portfolio_id]['assets'])
        self.assertEqual(self.portfolio_manager.portfolios[user_id][portfolio_id]['assets'][asset_id]['symbol'], 'AAPL')

    def test_update_asset(self):
        user_id = 'user1'
        portfolio_id = self.portfolio_manager.create_portfolio(user_id, 'Tech Stocks')
        asset_data = {'symbol': 'AAPL', 'quantity': 10}
        asset_id = self.portfolio_manager.add_asset(user_id, portfolio_id, asset_data)
        
        updates = {'quantity': 15}
        result = self.portfolio_manager.update_asset(user_id, portfolio_id, asset_id, updates)
        
        self.assertTrue(result)
        self.assertEqual(self.portfolio_manager.portfolios[user_id][portfolio_id]['assets'][asset_id]['quantity'], 15)

    def test_remove_asset(self):
        user_id = 'user1'
        portfolio_id = self.portfolio_manager.create_portfolio(user_id, 'Tech Stocks')
        asset_data = {'symbol': 'AAPL', 'quantity': 10}
        asset_id = self.portfolio_manager.add_asset(user_id, portfolio_id, asset_data)
        
        result = self.portfolio_manager.remove_asset(user_id, portfolio_id, asset_id)
        
        self.assertTrue(result)
        self.assertNotIn(asset_id, self.portfolio_manager.portfolios[user_id][portfolio_id]['assets'])

    def test_get_portfolio_value(self):
        user_id = 'user1'
        portfolio_id = self.portfolio_manager.create_portfolio(user_id, 'Tech Stocks')
        asset_data = {'symbol': 'AAPL', 'quantity': 10}
        self.portfolio_manager.add_asset(user_id, portfolio_id, asset_data)
        
        current_prices = {'AAPL': 150}
        total_value = self.portfolio_manager.get_portfolio_value(user_id, portfolio_id, current_prices)
        
        self.assertEqual(total_value, 1500)

    def test_display_portfolio(self):
        user_id = 'user1'
        portfolio_id = self.portfolio_manager.create_portfolio(user_id, 'Tech Stocks')
        asset_data = {'symbol': 'AAPL', 'quantity': 10}
        self.portfolio_manager.add_asset(user_id, portfolio_id, asset_data)
        
        display_data = self.portfolio_manager.display_portfolio(user_id, portfolio_id)
        
        self.assertIn('portfolio', display_data)
        self.assertIn('total_value', display_data)
        self.assertEqual(display_data['total_value'], 1500)

if __name__ == '__main__':
    unittest.main() 
