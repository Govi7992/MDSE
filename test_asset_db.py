import unittest
from unittest.mock import Mock, patch
from asset_db import AssetDB
from datetime import datetime

class TestAssetDB(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.asset_db = AssetDB()
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
        self.asset_db.user_data[self.test_user_id] = {
            'portfolio': self.test_portfolio,
            'risk_profile': self.test_risk_profile
        }
        
        user_data = self.asset_db.fetch_userdata(self.test_user_id)
        self.assertIsNotNone(user_data)
        self.assertIn('portfolio', user_data)
        self.assertIn('risk_profile', user_data)

    def test_portfolio_operations(self):
        result = self.asset_db.update_portfolio(
            self.test_user_id,
            self.test_portfolio
        )
        self.assertTrue(result)
        
        portfolio = self.asset_db.fetch_portfolio(self.test_user_id)
        self.assertEqual(portfolio['name'], self.test_portfolio['name'])
        self.assertEqual(
            portfolio['assets']['AAPL']['quantity'],
            self.test_portfolio['assets']['AAPL']['quantity']
        )

    def test_risk_profile_operations(self):
        """Test risk profile operations"""
        self.asset_db.user_data[self.test_user_id] = {
            'risk_profile': self.test_risk_profile
        }
        
        risk_profile = self.asset_db.fetch_riskprofile(self.test_user_id)
        self.assertEqual(risk_profile['profile'], 'moderate')
        self.assertEqual(risk_profile['score'], 55)

    def test_asset_data_operations(self):
        test_asset_data = {
            'symbol': 'AAPL',
            'current_price': 160.00,
            'volume': 1000000,
            'last_updated': datetime.now().isoformat()
        }

        result = self.asset_db.update_assetdata('AAPL', test_asset_data)
        self.assertTrue(result)
        asset_data = self.asset_db.fetch_assetdata('AAPL')
        self.assertEqual(asset_data['symbol'], 'AAPL')
        self.assertEqual(asset_data['current_price'], 160.00)

    def test_nonexistent_data(self):
        """Test handling of non-existent data"""
        self.assertIsNone(self.asset_db.fetch_userdata("nonexistent_user"))
        self.assertIsNone(self.asset_db.fetch_portfolio("nonexistent_user"))
        self.assertIsNone(self.asset_db.fetch_riskprofile("nonexistent_user"))
        self.assertIsNone(self.asset_db.fetch_assetdata("INVALID"))

    def test_data_validation(self):
        invalid_portfolio = {'name': 'Invalid'}
        result = self.asset_db.update_portfolio(self.test_user_id, invalid_portfolio)
        self.assertFalse(result)
    
        invalid_asset = {'symbol': 'AAPL'} 
        result = self.asset_db.update_assetdata('AAPL', invalid_asset)
        self.assertFalse(result)

    def test_data_consistency(self):
        self.asset_db.update_portfolio(self.test_user_id, self.test_portfolio)
        updated_portfolio = self.test_portfolio.copy()
        updated_portfolio['assets']['AAPL']['quantity'] = 15
        self.asset_db.update_portfolio(self.test_user_id, updated_portfolio)
        stored_portfolio = self.asset_db.fetch_portfolio(self.test_user_id)
        self.assertEqual(
            stored_portfolio['assets']['AAPL']['quantity'],
            updated_portfolio['assets']['AAPL']['quantity']
        )

if __name__ == '__main__':
    unittest.main() 