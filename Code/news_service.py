from newsapi import NewsApiClient
from typing import List, Dict

class NewsService:
    def __init__(self):
        """Initialize NewsService with API key and base URL."""
        self.api_key = "dad6b10bc28a47f3b68db8b75b07a311"
        self.base_url = "https://newsapi.org/v2"
        self.news_api = NewsApiClient(api_key=self.api_key)

    def get_financial_news(self, query: str = 'finance') -> List[Dict]:
        """
        Get financial news articles.
        
        Args:
            query: Search query for news (default: 'finance')
            
        Returns:
            List of dictionaries containing news articles
        """
        try:
            response = self.news_api.get_top_headlines(
                q=query,
                language='en'
            )
            
            articles = response.get('articles', [])
            formatted_articles = []
            
            for article in articles:
                formatted_article = {
                    'title': article.get('title', '') or '',
                    'url': article.get('url', '') or '',
                    'description': article.get('description', '') or '',
                    'published_at': article.get('publishedAt', '') or '',
                    'source': article.get('source', {}).get('name', '') if article.get('source') else ''
                }
                formatted_articles.append(formatted_article)
            
            return formatted_articles
        
        except Exception as e:
            raise Exception(f"Error fetching news: {e}")
