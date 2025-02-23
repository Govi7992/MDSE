import unittest
from unittest.mock import patch, MagicMock
from recommendation_engine import RecommendationEngine
from datetime import datetime

class TestRecommendationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RecommendationEngine()
        
        # Mock SP500 data for testing
        self.mock_sp500_data = {
            'AAPL': {
                'name': 'Apple Inc.',
                'sector': 'Technology',
                'market_cap': 2000000000000,  # 2T
                'pe_ratio': 25,
                'dividend_yield': 0.005,
                'beta': 1.2
            },
            'JNJ': {
                'name': 'Johnson & Johnson',
                'sector': 'Healthcare',
                'market_cap': 400000000000,  # 400B
                'pe_ratio': 15,
                'dividend_yield': 0.025,
                'beta': 0.8
            }
        }

    @patch('yfinance.Ticker')
    def test_get_sp500_tickers(self, mock_ticker):
        # Configure mock
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = self.mock_sp500_data['AAPL']
        mock_ticker.return_value = mock_ticker_instance

        # Test the method
        result = self.engine._get_sp500_tickers()
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0)

    def test_get_recommendations_conservative(self):
        self.engine.sp500_tickers = self.mock_sp500_data
        result = self.engine.get_recommendations('conservative')
        
        self.assertIsInstance(result, dict)
        self.assertIn('description', result)
        self.assertIn('allocation', result)
        self.assertIn('stock_recommendations', result)
        self.assertIn('explanation', result)
        
        # Verify conservative allocation
        self.assertEqual(result['allocation']['bonds'], 50)
        self.assertGreaterEqual(sum(result['allocation'].values()), 100)

    def test_get_recommendations_aggressive(self):
        self.engine.sp500_tickers = self.mock_sp500_data
        result = self.engine.get_recommendations('aggressive')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['allocation']['bonds'], 10)
        self.assertEqual(result['allocation']['cash'], 10)

    def test_filter_stocks(self):
        self.engine.sp500_tickers = self.mock_sp500_data
        
        # Test conservative filter
        conservative_stocks = self.engine._filter_stocks(
            min_market_cap=100e9,
            max_beta=1.0,
            min_dividend_yield=0.02
        )
        self.assertTrue(any(stock['ticker'] == 'JNJ' for stock in conservative_stocks))
        self.assertFalse(any(stock['ticker'] == 'AAPL' for stock in conservative_stocks))

        # Test aggressive filter
        aggressive_stocks = self.engine._filter_stocks(
            min_market_cap=10e9,
            min_beta=1.0
        )
        self.assertTrue(any(stock['ticker'] == 'AAPL' for stock in aggressive_stocks))

    def test_calculate_allocation(self):
        stock_data = self.mock_sp500_data['AAPL']
        allocation = self.engine._calculate_allocation(stock_data, 0)
        
        self.assertIsInstance(allocation, float)
        self.assertLessEqual(allocation, 15.0)  # Should not exceed cap
        self.assertGreater(allocation, 0)

    @patch('newsapi.NewsApiClient')
    def test_fetch_news(self, mock_newsapi):
        # Mock news API response
        mock_newsapi.return_value.get_everything.return_value = {
            'articles': [
                {
                    'title': 'Positive News About Stock',
                    'description': 'This is very good news',
                    'url': 'http://example.com',
                    'publishedAt': '2024-01-01T12:00:00Z'
                }
            ]
        }

        news = self.engine.fetch_news('AAPL')
        
        self.assertIsInstance(news, list)
        if news:
            self.assertIn('sentiment', news[0])
            self.assertIn('sentiment_score', news[0])
            self.assertIn('title', news[0])

    def test_get_recommendations_with_news(self):
        self.engine.sp500_tickers = self.mock_sp500_data
        
        # Mock fetch_news to avoid API calls
        with patch.object(self.engine, 'fetch_news', return_value=[{
            'title': 'Test News',
            'sentiment_score': 0.5,
            'url': 'http://example.com',
            'date': 'Jan 01, 2024'
        }]):
            result = self.engine.get_recommendations_with_news('moderate')
            
            self.assertIn('market_sentiment', result)
            self.assertIn('stock_recommendations', result)
            if result['stock_recommendations']:
                self.assertIn('news', result['stock_recommendations'][0])

    def test_get_sentiment_analysis(self):
        # Test different sentiment scenarios
        very_positive = self.engine._get_sentiment_analysis(0.4)
        self.assertIn('very positive', very_positive.lower())
        
        neutral = self.engine._get_sentiment_analysis(0)
        self.assertIn('neutral', neutral.lower())
        
        negative = self.engine._get_sentiment_analysis(-0.2)
        self.assertIn('negative', negative.lower())

    def test_get_default_recommendations(self):
        result = self.engine._get_default_recommendations()
        
        self.assertIsInstance(result, dict)
        self.assertIn('allocation', result)
        self.assertEqual(sum(result['allocation'].values()), 100)
        self.assertIn('explanation', result)

    def test_error_handling(self):
        # Test with invalid risk profile
        result = self.engine.get_recommendations('invalid_profile')
        self.assertIsInstance(result, dict)
        self.assertIn('allocation', result)
        
        # Test with empty SP500 data
        self.engine.sp500_tickers = {}
        result = self.engine.get_recommendations('conservative')
        self.assertIsInstance(result, dict)
        self.assertIn('explanation', result)

if __name__ == '__main__':
    unittest.main() 