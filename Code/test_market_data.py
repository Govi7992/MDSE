import unittest
from unittest.mock import patch, Mock
from market_data import MarketDataService
from datetime import datetime, timedelta

class TestMarketDataService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.market_data = MarketDataService()

    def test_initialization(self):
        """Test proper initialization of MarketDataService"""
        self.assertEqual(self.market_data.api_key, "5ZRTU7NJS6J9VB5Y")
        self.assertEqual(self.market_data.market_data, {})
        self.assertIsInstance(self.market_data.last_update, datetime)

    @patch('requests.get')
    def test_fetch_market_data_success(self, mock_get):
        """Test successful market data fetch"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Global Quote': {
                '05. price': '150.25'
            }
        }
        mock_get.return_value = mock_response

        result = self.market_data.fetch_market_data('AAPL')
        
        # Verify API call
        expected_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={self.market_data.api_key}'
        mock_get.assert_called_once_with(expected_url)
        
        # Verify result
        self.assertEqual(result, {'price': 150.25})

    @patch('requests.get')
    def test_fetch_market_data_failure(self, mock_get):
        """Test market data fetch with invalid response"""
        mock_response = Mock()
        mock_response.json.return_value = {}  # Empty response
        mock_get.return_value = mock_response

        result = self.market_data.fetch_market_data('INVALID')
        self.assertEqual(result, {'price': None})

    @patch('requests.get')
    def test_get_current_market_data(self, mock_get):
        """Test getting current market data for all symbols"""
        # Mock response for each symbol
        mock_response = Mock()
        mock_response.json.return_value = {
            'Global Quote': {
                '05. price': '100.00'
            }
        }
        mock_get.return_value = mock_response

        result = self.market_data.get_current_market_data()
        
        # Verify API calls for each symbol
        self.assertEqual(mock_get.call_count, 5)  # Should be called for each symbol
        
        # Verify results
        expected_result = {
            'AAPL': {'price': 100.0},
            'GOOGL': {'price': 100.0},
            'MSFT': {'price': 100.0},
            'AMZN': {'price': 100.0},
            'BTC': {'price': 100.0}
        }
        self.assertEqual(result, expected_result)

    @patch('requests.get')
    def test_get_asset_price(self, mock_get):
        """Test getting price for a specific asset"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Global Quote': {
                '05. price': '150.25'
            }
        }
        mock_get.return_value = mock_response

        result = self.market_data.get_asset_price('AAPL')
        
        # Verify API call
        expected_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={self.market_data.api_key}'
        mock_get.assert_called_once_with(expected_url)
        
        # Verify result
        self.assertEqual(result, {'price': 150.25})

    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        """Test handling of API errors"""
        mock_get.side_effect = Exception("API Error")

        result = self.market_data.fetch_market_data('AAPL')
        self.assertEqual(result, {'price': None})

    @patch('requests.get')
    def test_malformed_response_handling(self, mock_get):
        """Test handling of malformed API responses"""
        test_cases = [
            # Missing Global Quote
            {'response': {}, 'expected': {'price': None}},
            # Missing price
            {'response': {'Global Quote': {}}, 'expected': {'price': None}},
            # Invalid price format
            {'response': {'Global Quote': {'05. price': 'invalid'}}, 'expected': {'price': None}}
        ]

        for case in test_cases:
            mock_response = Mock()
            mock_response.json.return_value = case['response']
            mock_get.return_value = mock_response

            result = self.market_data.fetch_market_data('AAPL')
            self.assertEqual(result, case['expected'])

if __name__ == '__main__':
    unittest.main() 