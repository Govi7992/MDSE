import unittest
from datetime import datetime
from portfolio_manager import PortfolioManager

class TestPortfolioManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.manager = PortfolioManager()
        self.test_user_id = "user1"
        self.test_portfolio_name = "Test Portfolio"
        
    def test_create_portfolio(self):
        """Test portfolio creation"""
        # Test creating first portfolio
        portfolio_id = self.manager.create_portfolio(self.test_user_id, self.test_portfolio_name)
        self.assertEqual(portfolio_id, 1)
        
        # Verify portfolio was created correctly
        self.assertIn(self.test_user_id, self.manager.portfolios)
        self.assertIn(portfolio_id, self.manager.portfolios[self.test_user_id])
        portfolio = self.manager.portfolios[self.test_user_id][portfolio_id]
        
        self.assertEqual(portfolio['name'], self.test_portfolio_name)
        self.assertEqual(len(portfolio['assets']), 0)
        self.assertIsInstance(portfolio['created_at'], datetime)
        self.assertIsInstance(portfolio['last_updated'], datetime)

    def test_add_asset(self):
        """Test adding assets to portfolio"""
        portfolio_id = self.manager.create_portfolio(self.test_user_id, self.test_portfolio_name)
        
        # Test adding valid asset
        asset_data = {
            'symbol': 'AAPL',
            'quantity': 10,
            'purchase_price': 150.0
        }
        asset_id = self.manager.add_asset(self.test_user_id, portfolio_id, asset_data)
        
        self.assertEqual(asset_id, 1)
        portfolio = self.manager.portfolios[self.test_user_id][portfolio_id]
        self.assertIn(asset_id, portfolio['assets'])
        
        # Verify asset data
        stored_asset = portfolio['assets'][asset_id]
        self.assertEqual(stored_asset['symbol'], 'AAPL')
        self.assertEqual(stored_asset['quantity'], 10)
        self.assertEqual(stored_asset['purchase_price'], 150.0)
        self.assertIsInstance(stored_asset['added_at'], datetime)
        self.assertIsInstance(stored_asset['last_updated'], datetime)

        # Test adding asset to non-existent portfolio
        result = self.manager.add_asset(self.test_user_id, 999, asset_data)
        self.assertFalse(result)

        # Test adding asset to non-existent user
        result = self.manager.add_asset("nonexistent_user", portfolio_id, asset_data)
        self.assertFalse(result)

    def test_update_asset(self):
        """Test updating assets in portfolio"""
        portfolio_id = self.manager.create_portfolio(self.test_user_id, self.test_portfolio_name)
        asset_data = {
            'symbol': 'AAPL',
            'quantity': 10,
            'purchase_price': 150.0
        }
        asset_id = self.manager.add_asset(self.test_user_id, portfolio_id, asset_data)
        
        # Test valid update
        updates = {'quantity': 15, 'purchase_price': 160.0}
        result = self.manager.update_asset(self.test_user_id, portfolio_id, asset_id, updates)
        self.assertTrue(result)
        
        # Verify updates
        updated_asset = self.manager.portfolios[self.test_user_id][portfolio_id]['assets'][asset_id]
        self.assertEqual(updated_asset['quantity'], 15)
        self.assertEqual(updated_asset['purchase_price'], 160.0)
        
        # Test updating non-existent asset
        result = self.manager.update_asset(self.test_user_id, portfolio_id, 999, updates)
        self.assertFalse(result)

    def test_remove_asset(self):
        """Test removing assets from portfolio"""
        portfolio_id = self.manager.create_portfolio(self.test_user_id, self.test_portfolio_name)
        asset_data = {
            'symbol': 'AAPL',
            'quantity': 10,
            'purchase_price': 150.0
        }
        asset_id = self.manager.add_asset(self.test_user_id, portfolio_id, asset_data)
        
        # Test valid removal
        result = self.manager.remove_asset(self.test_user_id, portfolio_id, asset_id)
        self.assertTrue(result)
        self.assertNotIn(asset_id, self.manager.portfolios[self.test_user_id][portfolio_id]['assets'])
        
        # Test removing non-existent asset
        result = self.manager.remove_asset(self.test_user_id, portfolio_id, 999)
        self.assertFalse(result)

    def test_validate_portfolio_access(self):
        """Test portfolio access validation"""
        portfolio_id = self.manager.create_portfolio(self.test_user_id, self.test_portfolio_name)
        
        # Test valid access
        self.assertTrue(self.manager._validate_portfolio_access(self.test_user_id, portfolio_id))
        
        # Test invalid user
        self.assertFalse(self.manager._validate_portfolio_access("nonexistent_user", portfolio_id))
        
        # Test invalid portfolio
        self.assertFalse(self.manager._validate_portfolio_access(self.test_user_id, 999))

    def test_get_portfolio_value(self):
        """Test portfolio value calculation"""
        portfolio_id = self.manager.create_portfolio(self.test_user_id, self.test_portfolio_name)
        
        # Add multiple assets
        assets = [
            {'symbol': 'AAPL', 'quantity': 10, 'purchase_price': 150.0},
            {'symbol': 'GOOGL', 'quantity': 5, 'purchase_price': 2500.0},
            {'symbol': 'MSFT', 'quantity': 15, 'purchase_price': 300.0}
        ]
        
        for asset in assets:
            self.manager.add_asset(self.test_user_id, portfolio_id, asset)
        
        # Test portfolio value calculation
        current_prices = {
            'AAPL': 170.0,
            'GOOGL': 2600.0,
            'MSFT': 310.0
        }
        
        expected_value = (10 * 170.0) + (5 * 2600.0) + (15 * 310.0)
        actual_value = self.manager.get_portfolio_value(self.test_user_id, portfolio_id, current_prices)
        self.assertEqual(actual_value, expected_value)
        
        # Test with missing price data
        incomplete_prices = {'AAPL': 170.0}  # Missing some symbols
        partial_value = self.manager.get_portfolio_value(self.test_user_id, portfolio_id, incomplete_prices)
        self.assertEqual(partial_value, 10 * 170.0)  # Should only count AAPL value
        
        # Test with non-existent portfolio
        value = self.manager.get_portfolio_value(self.test_user_id, 999, current_prices)
        self.assertEqual(value, 0)

if __name__ == '__main__':
    unittest.main() 