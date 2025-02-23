import unittest
from unittest.mock import Mock, patch
from news_service import NewsService

class TestNewsService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock for NewsApiClient
        self.mock_news_api = Mock()
        with patch('news_service.NewsApiClient', return_value=self.mock_news_api):
            self.news_service = NewsService()
        
        # Sample test data
        self.sample_article = {
            'title': 'Test Financial News',
            'url': 'http://example.com/news',
            'description': 'Test description',
            'publishedAt': '2024-03-14T10:00:00Z',
            'source': {'name': 'Test Source'}
        }

    def test_initialization(self):
        """Test proper initialization of NewsService"""
        with patch('news_service.NewsApiClient') as mock_news_api:
            news_service = NewsService()
            
            # Verify API key and base URL
            self.assertEqual(news_service.api_key, "dad6b10bc28a47f3b68db8b75b07a311")
            self.assertEqual(news_service.base_url, "https://newsapi.org/v2")
            
            # Verify NewsApiClient initialization
            mock_news_api.assert_called_once_with(api_key=news_service.api_key)

    def test_get_financial_news_success(self):
        """Test successful retrieval of financial news"""
        # Mock response from NewsAPI
        mock_response = {
            'articles': [self.sample_article]
        }
        
        # Configure mock
        self.mock_news_api.get_top_headlines.return_value = mock_response
        
        # Get news with default query
        articles = self.news_service.get_financial_news()
        
        # Verify API call parameters
        self.mock_news_api.get_top_headlines.assert_called_with(
            q='finance',
            language='en'
        )
        
        # Verify response formatting
        self.assertEqual(len(articles), 1)
        article = articles[0]
        self.assertEqual(article['title'], 'Test Financial News')
        self.assertEqual(article['url'], 'http://example.com/news')
        self.assertEqual(article['description'], 'Test description')
        self.assertEqual(article['published_at'], '2024-03-14T10:00:00Z')
        self.assertEqual(article['source'], 'Test Source')

    def test_get_financial_news_custom_query(self):
        """Test getting financial news with custom query"""
        # Configure mock
        self.mock_news_api.get_top_headlines.return_value = {'articles': []}
        
        # Call method with custom query
        self.news_service.get_financial_news(query='stocks')
        
        # Verify custom query parameter
        self.mock_news_api.get_top_headlines.assert_called_with(
            q='stocks',
            language='en'
        )

    def test_get_financial_news_empty_response(self):
        """Test handling of empty response"""
        # Configure mock
        self.mock_news_api.get_top_headlines.return_value = {'articles': []}
        
        articles = self.news_service.get_financial_news()
        self.assertEqual(articles, [])

    def test_get_financial_news_missing_fields(self):
        """Test handling of missing fields in response"""
        mock_response = {
            'articles': [{
                'title': 'Test News'
                # Missing other fields
            }]
        }
        
        # Configure mock
        self.mock_news_api.get_top_headlines.return_value = mock_response
        
        articles = self.news_service.get_financial_news()
        
        self.assertEqual(len(articles), 1)
        article = articles[0]
        self.assertEqual(article['title'], 'Test News')
        self.assertEqual(article['url'], '')
        self.assertEqual(article['description'], '')
        self.assertEqual(article['published_at'], '')
        self.assertEqual(article['source'], '')

    def test_get_financial_news_null_values(self):
        """Test handling of null values in response"""
        mock_response = {
            'articles': [{
                'title': None,
                'url': None,
                'description': None,
                'publishedAt': None,
                'source': None
            }]
        }
        
        # Configure mock
        self.mock_news_api.get_top_headlines.return_value = mock_response
        
        articles = self.news_service.get_financial_news()
        
        self.assertEqual(len(articles), 1)
        article = articles[0]
        self.assertEqual(article['title'], '')
        self.assertEqual(article['url'], '')
        self.assertEqual(article['description'], '')
        self.assertEqual(article['published_at'], '')
        self.assertEqual(article['source'], '')

    def test_get_financial_news_api_error(self):
        """Test handling of API errors"""
        # Configure mock to raise an exception
        self.mock_news_api.get_top_headlines.side_effect = Exception("API Error")
        
        with self.assertRaises(Exception) as context:
            self.news_service.get_financial_news()
        
        self.assertTrue("Error fetching news: API Error" in str(context.exception))

if __name__ == '__main__':
    unittest.main() 