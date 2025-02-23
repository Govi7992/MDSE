from news_service import NewsService
from pprint import pprint

def test_news_service():
    # Initialize the news service
    news_service = NewsService()
    
    # Test with different queries
    queries = ['AAPL', 'TSLA', 'MSFT']
    
    for query in queries:
        print(f"\n=== News for {query} ===")
        news = news_service.get_financial_news(query)
        pprint(news)

if __name__ == "__main__":
    test_news_service()