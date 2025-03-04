import unittest
from unittest.mock import patch, MagicMock
from recommendation_engine import RecommendationEngine

class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = RecommendationEngine()

    @patch('recommendation_engine.yf.Ticker')
    def test_get_sp500_tickers(self, mock_ticker):
        
        mock_ticker.return_value.info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'marketCap': 2000000000000,
            'forwardPE': 30,
            'dividendYield': 0.01,
            'beta': 1.2
        }
        tickers = self.engine._get_sp500_tickers()
        self.assertIn('AAPL', tickers)
        self.assertEqual(tickers['AAPL']['name'], 'Apple Inc.')

    def test_get_recommendations(self):
        recommendations = self.engine.get_recommendations('conservative')
        self.assertIn('description', recommendations)
        self.assertIn('allocation', recommendations)
        self.assertIn('stock_recommendations', recommendations)

    @patch('recommendation_engine.NewsApiClient.get_everything')
    def test_fetch_news(self, mock_get_everything):
        mock_get_everything.return_value = {
            'articles': [
                {
                    'title': 'Apple stock rises',
                    'description': 'Apple stock sees a significant rise.',
                    'publishedAt': '2023-10-01T12:00:00Z',
                    'url': 'http://example.com/article1'
                }
            ]
        }
        news = self.engine.fetch_news('AAPL')
        self.assertEqual(len(news), 1)
        self.assertEqual(news[0]['title'], 'Apple stock rises')

    def test_generate_recommendations(self):
        risk_profile = {'profile': 'moderate', 'score': 50}
        market_data = {
            'AAPL': {'volatility': 0.2},
            'GOOGL': {'volatility': 0.4},
            'TSLA': {'volatility': 0.6}
        }
        recommendations = self.engine.generate_recommendations(risk_profile, market_data)
        self.assertIn('allocations', recommendations)
        self.assertIn('specific_recommendations', recommendations)

if __name__ == '__main__':
    unittest.main()
