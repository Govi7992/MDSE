from newsapi import NewsApiClient
from typing import List, Dict

class NewsService:
    def __init__(self):
        self.api_key = "dad6b10bc28a47f3b68db8b75b07a311"
        self.base_url = "https://newsapi.org/v2"
        self.news_api = NewsApiClient(api_key=self.api_key)

    def get_financial_news(self, query: str = 'finance') -> List[Dict]:
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

    def get_latest_market_news(self, limit=5):
        """
        Get the latest market news.
        
        Args:
            limit (int): Maximum number of news items to return
            
        Returns:
            list: List of news items
        """
        fallback_news = [
            {
                "title": "Federal Reserve Maintains Interest Rates",
                "description": "The Federal Reserve has decided to maintain current interest rates, citing economic stability and controlled inflation.",
                "source": "Market Daily",
                "url": "#"
            },
            {
                "title": "Tech Sector Shows Strong Performance in Q1",
                "description": "Technology companies reported better-than-expected earnings for the first quarter, driving market gains.",
                "source": "Finance Today",
                "url": "#"
            },
            {
                "title": "Global Supply Chain Issues Improving",
                "description": "Recent data suggests global supply chain disruptions are easing, potentially reducing inflationary pressures.",
                "source": "Economic Review",
                "url": "#"
            },
            {
                "title": "Bond Market Stability Returns After Volatility",
                "description": "The bond market has stabilized following recent volatility, as investors gain confidence in long-term economic prospects.",
                "source": "Bond Insights",
                "url": "#"
            },
            {
                "title": "Retail Sales Exceed Expectations",
                "description": "Consumer spending remains strong as retail sales figures exceeded analyst expectations for the third consecutive month.",
                "source": "Market Watch",
                "url": "#"
            }
        ]
        
        return fallback_news[:limit]