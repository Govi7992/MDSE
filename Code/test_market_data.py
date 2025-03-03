import unittest
from unittest.mock import patch
from market_data import MarketDataService

class TestMarketDataService(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.market_service = MarketDataService()

    @patch('requests.get')
    def test_fetch_market_data_success(self, mock_get):
        """Test successful market data fetch"""
        mock_response = {
            'Global Quote': {
                '05. price': '150.25'
            }
        }
        mock_get.return_value.json.return_value = mock_response

        result = self.market_service.fetch_market_data('AAPL')
        self.assertEqual(result['price'], 150.25)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_fetch_market_data_invalid_response(self, mock_get):
        """Test market data fetch with invalid response"""
        mock_response = {'Invalid': 'Response'}
        mock_get.return_value.json.return_value = mock_response

        result = self.market_service.fetch_market_data('AAPL')
        self.assertIsNone(result['price'])

    @patch('requests.get')
    def test_fetch_market_data_exception(self, mock_get):
        """Test market data fetch with exception"""
        mock_get.side_effect = Exception('API Error')

        result = self.market_service.fetch_market_data('AAPL')
        self.assertIsNone(result['price'])

    @patch('market_data.MarketDataService.fetch_market_data')
    def test_get_current_market_data(self, mock_fetch):
        """Test getting current market data for all symbols"""
        mock_fetch.return_value = {'price': 100.0}

        result = self.market_service.get_current_market_data()
        
        expected_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'BTC']
        self.assertEqual(set(result.keys()), set(expected_symbols))
        
   
        self.assertEqual(mock_fetch.call_count, len(expected_symbols))
        
     
        for symbol in expected_symbols:
            self.assertIn(symbol, result)
            self.assertEqual(result[symbol], {'price': 100.0})

    @patch('market_data.MarketDataService.fetch_market_data')
    def test_get_asset_price(self, mock_fetch):
        """Test getting price for a specific asset"""
        mock_fetch.return_value = {'price': 200.0}

        result = self.market_service.get_asset_price('TSLA')
        self.assertEqual(result['price'], 200.0)
        mock_fetch.assert_called_once_with('TSLA')

    def test_api_key_exists(self):
        """Test that API key is set"""
        self.assertIsNotNone(self.market_service.api_key)
        self.assertIsInstance(self.market_service.api_key, str)
        self.assertTrue(len(self.market_service.api_key) > 0)

if __name__ == '__main__':
    unittest.main() 
