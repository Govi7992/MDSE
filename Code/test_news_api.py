import unittest
from unittest.mock import patch, MagicMock
from news_service import NewsService

class TestNewsService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.news_service = NewsService()

    def test_init(self):
        """Test NewsService initialization."""
        self.assertEqual(self.news_service.base_url, "https://newsapi.org/v2")
        self.assertIsNotNone(self.news_service.api_key)
        self.assertIsNotNone(self.news_service.news_api)

    @patch('newsapi.NewsApiClient.get_top_headlines')
    def test_get_financial_news_success(self, mock_get_top_headlines):
        """Test successful retrieval of financial news."""
        # Mock response data
        mock_response = {
            'articles': [
                {
                    'title': 'Test Article',
                    'url': 'http://test.com',
                    'description': 'Test Description',
                    'publishedAt': '2024-03-20',
                    'source': {'name': 'Test Source'}
                }
            ]
        }
        mock_get_top_headlines.return_value = mock_response

        # Call the method
        result = self.news_service.get_financial_news('test query')

        # Verify the mock was called with correct parameters
        mock_get_top_headlines.assert_called_once_with(
            q='test query',
            language='en'
        )

        # Assert the response is formatted correctly
        self.assertEqual(len(result), 1)
        article = result[0]
        self.assertEqual(article['title'], 'Test Article')
        self.assertEqual(article['url'], 'http://test.com')
        self.assertEqual(article['description'], 'Test Description')
        self.assertEqual(article['published_at'], '2024-03-20')
        self.assertEqual(article['source'], 'Test Source')

    @patch('newsapi.NewsApiClient.get_top_headlines')
    def test_get_financial_news_empty_response(self, mock_get_top_headlines):
        """Test handling of empty response."""
        mock_get_top_headlines.return_value = {'articles': []}
        result = self.news_service.get_financial_news()
        self.assertEqual(result, [])

    @patch('newsapi.NewsApiClient.get_top_headlines')
    def test_get_financial_news_missing_fields(self, mock_get_top_headlines):
        """Test handling of response with missing fields."""
        mock_response = {
            'articles': [
                {
                    'title': None,
                    'url': None,
                    'description': None,
                    'publishedAt': None,
                    'source': None
                }
            ]
        }
        mock_get_top_headlines.return_value = mock_response

        result = self.news_service.get_financial_news()
        self.assertEqual(len(result), 1)
        article = result[0]
        self.assertEqual(article['title'], '')
        self.assertEqual(article['url'], '')
        self.assertEqual(article['description'], '')
        self.assertEqual(article['published_at'], '')
        self.assertEqual(article['source'], '')

    @patch('newsapi.NewsApiClient.get_top_headlines')
    def test_get_financial_news_api_error(self, mock_get_top_headlines):
        """Test handling of API errors."""
        mock_get_top_headlines.side_effect = Exception("API Error")
        
        with self.assertRaises(Exception) as context:
            self.news_service.get_financial_news()
        
        self.assertTrue("Error fetching news: API Error" in str(context.exception))

if __name__ == '__main__':
    unittest.main() 
