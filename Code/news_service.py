from newsapi import NewsApiClient

class NewsService:
    def __init__(self):
        self.api_key = "efaf1927918946c297fbec474b5758a3"
        self.base_url = "https://newsapi.org/v2"
        self.newsapi = NewsApiClient(api_key=self.api_key)

    def get_financial_news(self, query="finance"):
        top_headlines = self.newsapi.get_top_headlines(q=query, category='business', language='en')
        articles = top_headlines.get('articles', [])
        return [{
            'title': article['title'],
            'url': article['url'],
            'description': article.get('description', ''),
            'published_at': article.get('publishedAt', ''),
            'source': article.get('source', {}).get('name', '')
        } for article in articles]