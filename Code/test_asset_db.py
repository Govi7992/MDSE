import unittest
from unittest.mock import Mock, patch
from asset_db import AssetDB
from datetime import datetime

class TestAssetDB(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.asset_db = AssetDB()
        
        # Sample test data
        self.test_user_id = "test_user"
        self.test_portfolio = {
            'name': 'Test Portfolio',
            'assets': {
                'AAPL': {
                    'quantity': 10,
                    'purchase_price': 150.00,
                    'purchase_date': datetime.now().isoformat()
                }
            },
            'created_at': datetime.now().isoformat()
        }
        
        self.test_risk_profile = {
            'profile': 'moderate',
            'score': 55,
            'timestamp': datetime.now().isoformat()
        }

    def test_user_data_operations(self):
        """Test user data storage and retrieval"""
        # Store user data
        self.asset_db.user_data[self.test_user_id] = {
            'portfolio': self.test_portfolio,
            'risk_profile': self.test_risk_profile
        }
        
        # Test fetching user data
        user_data = self.asset_db.fetch_userdata(self.test_user_id)
        self.assertIsNotNone(user_data)
        self.assertIn('portfolio', user_data)
        self.assertIn('risk_profile', user_data)

    def test_portfolio_operations(self):
        """Test portfolio operations"""
        # Test storing portfolio
        result = self.asset_db.update_portfolio(
            self.test_user_id,
            self.test_portfolio
        )
        self.assertTrue(result)
        
        # Test fetching portfolio
        portfolio = self.asset_db.fetch_portfolio(self.test_user_id)
        self.assertEqual(portfolio['name'], self.test_portfolio['name'])
        self.assertEqual(
            portfolio['assets']['AAPL']['quantity'],
            self.test_portfolio['assets']['AAPL']['quantity']
        )

    def test_risk_profile_operations(self):
        """Test risk profile operations"""
        # Store risk profile
        self.asset_db.user_data[self.test_user_id] = {
            'risk_profile': self.test_risk_profile
        }
        
        # Test fetching risk profile
        risk_profile = self.asset_db.fetch_riskprofile(self.test_user_id)
        self.assertEqual(risk_profile['profile'], 'moderate')
        self.assertEqual(risk_profile['score'], 55)

    def test_asset_data_operations(self):
        """Test asset data operations"""
        test_asset_data = {
            'symbol': 'AAPL',
            'current_price': 160.00,
            'volume': 1000000,
            'last_updated': datetime.now().isoformat()
        }
        
        # Test updating asset data
        result = self.asset_db.update_assetdata('AAPL', test_asset_data)
        self.assertTrue(result)
        
        # Test fetching asset data
        asset_data = self.asset_db.fetch_assetdata('AAPL')
        self.assertEqual(asset_data['symbol'], 'AAPL')
        self.assertEqual(asset_data['current_price'], 160.00)

    def test_nonexistent_data(self):
        """Test handling of non-existent data"""
        # Test non-existent user
        self.assertIsNone(self.asset_db.fetch_userdata("nonexistent_user"))
        
        # Test non-existent portfolio
        self.assertIsNone(self.asset_db.fetch_portfolio("nonexistent_user"))
        
        # Test non-existent risk profile
        self.assertIsNone(self.asset_db.fetch_riskprofile("nonexistent_user"))
        
        # Test non-existent asset
        self.assertIsNone(self.asset_db.fetch_assetdata("INVALID"))

    def test_data_validation(self):
        """Test data validation"""
        # Test invalid portfolio data
        invalid_portfolio = {'name': 'Invalid'}  # Missing required fields
        result = self.asset_db.update_portfolio(self.test_user_id, invalid_portfolio)
        self.assertFalse(result)
        
        # Test invalid asset data
        invalid_asset = {'symbol': 'AAPL'}  # Missing required fields
        result = self.asset_db.update_assetdata('AAPL', invalid_asset)
        self.assertFalse(result)

    def test_data_consistency(self):
        """Test data consistency across operations"""
        # Store portfolio
        self.asset_db.update_portfolio(self.test_user_id, self.test_portfolio)
        
        # Update portfolio
        updated_portfolio = self.test_portfolio.copy()
        updated_portfolio['assets']['AAPL']['quantity'] = 15
        self.asset_db.update_portfolio(self.test_user_id, updated_portfolio)
        
        # Verify consistency
        stored_portfolio = self.asset_db.fetch_portfolio(self.test_user_id)
        self.assertEqual(
            stored_portfolio['assets']['AAPL']['quantity'],
            updated_portfolio['assets']['AAPL']['quantity']
        )

if __name__ == '__main__':
    unittest.main() 