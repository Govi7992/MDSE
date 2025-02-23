import yfinance as yf
import pandas as pd
from typing import Dict, List
import numpy as np
import requests
from textblob import TextBlob
from datetime import datetime, timedelta
from newsapi import NewsApiClient

class RecommendationEngine:
    def __init__(self):
        self.sp500_tickers = self._get_sp500_tickers()
        self.risk_allocations = {
            'conservative': {
                'large_cap_value': 30,
                'bonds': 50,
                'cash': 20
            },
            'moderate': {
                'large_cap_growth': 30,
                'bonds': 30,
                'mid_cap': 20,
                'cash': 20
            },
            'aggressive': {
                'large_cap_growth': 50,
                'small_cap': 30,
                'bonds': 10,
                'cash': 10
            }
        }
        self.newsapi = NewsApiClient(api_key="efaf1927918946c297fbec474b5758a3")

    def _get_sp500_tickers(self) -> Dict:
        """Get S&P 500 stocks and their market data"""
        try:
            # Get S&P 500 data using yfinance
            sp500_data = {}
            tickers = [
                'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META',  # Large Cap Growth
                'BRK-B', 'JPM', 'JNJ', 'PG', 'V',         # Large Cap Value
                'AMD', 'NVDA', 'PYPL', 'ADBE', 'CRM',     # Large Cap Growth Tech
                'XOM', 'CVX', 'PFE', 'BAC', 'WMT'         # Large Cap Value
            ]  # Add more tickers as needed

            for ticker in tickers:
                stock = yf.Ticker(ticker)
                info = stock.info
                sp500_data[ticker] = {
                    'name': info.get('longName', ticker),
                    'sector': info.get('sector', 'Unknown'),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('forwardPE', 0),
                    'dividend_yield': info.get('dividendYield', 0),
                    'beta': info.get('beta', 1),
                }
            return sp500_data
        except Exception as e:
            print(f"Error fetching S&P 500 data: {e}")
            return {}

    def get_recommendations(self, risk_profile: str) -> Dict:
        """Generate stock and bond recommendations based on risk profile"""
        try:
            # Normalize risk profile
            if risk_profile in ['conservative', 'moderate_conservative']:
                profile = 'conservative'
            elif risk_profile in ['moderate']:
                profile = 'moderate'
            else:
                profile = 'aggressive'

            # Get allocation strategy
            allocation = self.risk_allocations[profile]

            # Select stocks based on profile
            recommendations = {
                'description': f'Recommended {profile} investment strategy',
                'allocation': allocation,
                'stock_recommendations': self._get_stock_recommendations(profile),
                'explanation': self._get_strategy_explanation(profile)
            }

            # Calculate total allocation
            total_allocation = sum(allocation.values())
            if total_allocation < 100:
                # Adjust allocations to sum to 100%
                for key in allocation:
                    allocation[key] = (allocation[key] / total_allocation) * 100

            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._get_default_recommendations()

    def _get_stock_recommendations(self, profile: str) -> List[Dict]:
        """Get specific stock and bond recommendations based on risk profile"""
        stocks = []
        
        if profile == 'conservative':
            # Conservative: Focus on large-cap value stocks and bonds
            stocks = self._filter_stocks(
                min_market_cap=100e9,  # $100B market cap
                max_beta=1.0,
                min_dividend_yield=0.02
            )
            stocks.append({'ticker': 'BND', 'name': 'Vanguard Total Bond Market ETF', 'allocation': 50, 'reason': 'Stable bond investment'})
        elif profile == 'moderate':
            # Moderate: Mix of growth stocks and bonds
            stocks = self._filter_stocks(
                min_market_cap=50e9,  # $50B market cap
                max_beta=1.5
            )
            stocks.append({'ticker': 'AGG', 'name': 'iShares Core U.S. Aggregate Bond ETF', 'allocation': 30, 'reason': 'Diversified bond exposure'})
        else:
            # Aggressive: Growth stocks, higher beta
            stocks = self._filter_stocks(
                min_market_cap=10e9,  # $10B market cap
                min_beta=1.0
            )
            stocks.append({'ticker': 'HYG', 'name': 'iShares iBoxx $ High Yield Corporate Bond ETF', 'allocation': 10, 'reason': 'Higher yield potential'})

        return stocks

    def _filter_stocks(self, min_market_cap=0, max_beta=float('inf'), 
                      min_beta=0, min_dividend_yield=0) -> List[Dict]:
        """Filter stocks based on criteria"""
        filtered_stocks = []
        
        for ticker, data in self.sp500_tickers.items():
            if (data['market_cap'] >= min_market_cap and
                min_beta <= data['beta'] <= max_beta and
                data['dividend_yield'] >= min_dividend_yield):
                
                filtered_stocks.append({
                    'ticker': ticker,
                    'name': data['name'],
                    'allocation': self._calculate_allocation(data, len(filtered_stocks)),
                    'reason': self._get_stock_reason(data)
                })

        return sorted(filtered_stocks, key=lambda x: x['allocation'], reverse=True)

    def _calculate_allocation(self, stock_data: Dict, position: int) -> float:
        """Calculate recommended allocation percentage for a stock"""
        base_allocation = 5.0  # Base allocation percentage
        market_cap_factor = min(stock_data['market_cap'] / 1e12, 2.0)  # Market cap factor
        position_factor = 1.0 / (position + 1)  # Position factor
        
        allocation = base_allocation * market_cap_factor * position_factor
        return round(min(allocation, 15.0), 1)  # Cap at 15%

    def _get_stock_reason(self, stock_data: Dict) -> str:
        """Generate reason for stock recommendation"""
        reasons = []
        if stock_data['market_cap'] > 100e9:
            reasons.append("Large, stable company")
        if stock_data['dividend_yield'] > 0.02:
            reasons.append("Good dividend yield")
        if stock_data['beta'] < 1.0:
            reasons.append("Lower volatility than market")
        elif stock_data['beta'] > 1.2:
            reasons.append("Higher growth potential")
            
        return ", ".join(reasons) or "Balanced investment choice"

    def _get_strategy_explanation(self, profile: str) -> str:
        """Get detailed explanation of the investment strategy"""
        explanations = {
            'conservative': "This strategy focuses on stable, large-cap companies with strong dividend histories and lower volatility.",
            'moderate': "This balanced approach combines stable value stocks with growth opportunities while maintaining moderate risk levels.",
            'aggressive': "This growth-oriented strategy focuses on companies with higher return potential, accepting higher volatility."
        }
        return explanations.get(profile, "Balanced investment strategy across different sectors")

    def _get_default_recommendations(self) -> Dict:
        """Return default recommendations if error occurs"""
        return {
            'description': 'Default balanced investment strategy',
            'allocation': {'stocks': 60, 'bonds': 30, 'cash': 10},
            'stock_recommendations': [],
            'explanation': 'Error occurred. Showing default conservative allocation.'
        }

    def fetch_news(self, ticker: str) -> List[Dict]:
        """Fetch recent news articles with sentiment analysis"""
        try:
            # Get news from the last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Fetch news using NewsAPI
            news = self.newsapi.get_everything(
                q=f"{ticker} stock",
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=5  # Limit to 5 most relevant articles
            )

            articles = []
            for article in news.get('articles', []):
                # Perform sentiment analysis on title and description
                text = f"{article['title']} {article['description']}"
                sentiment = TextBlob(text).sentiment
                
                # Calculate sentiment score (-1 to 1)
                sentiment_score = sentiment.polarity
                
                # Determine sentiment category
                if sentiment_score > 0.1:
                    sentiment_category = "Positive"
                    sentiment_color = "text-success"
                elif sentiment_score < -0.1:
                    sentiment_category = "Negative"
                    sentiment_color = "text-danger"
                else:
                    sentiment_category = "Neutral"
                    sentiment_color = "text-secondary"

                articles.append({
                    'title': article['title'],
                    'url': article['url'],
                    'date': datetime.strptime(article['publishedAt'][:10], '%Y-%m-%d').strftime('%b %d, %Y'),
                    'sentiment': sentiment_category,
                    'sentiment_color': sentiment_color,
                    'sentiment_score': round(sentiment_score, 2)
                })

            # Sort by sentiment score (most positive first)
            return sorted(articles, key=lambda x: x['sentiment_score'], reverse=True)

        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return []

    def get_recommendations_with_news(self, risk_profile: str) -> Dict:
        """Generate recommendations along with analyzed news articles"""
        recommendations = self.get_recommendations(risk_profile)
        
        # Add market sentiment analysis
        total_sentiment = 0
        article_count = 0
        
        for stock in recommendations['stock_recommendations']:
            stock['news'] = self.fetch_news(stock['ticker'])
            
            # Calculate average sentiment for this stock
            sentiments = [article['sentiment_score'] for article in stock['news']]
            if sentiments:
                stock['avg_sentiment'] = round(sum(sentiments) / len(sentiments), 2)
                total_sentiment += stock['avg_sentiment']
                article_count += 1
        
        # Add overall market sentiment
        if article_count > 0:
            recommendations['market_sentiment'] = {
                'score': round(total_sentiment / article_count, 2),
                'analysis': self._get_sentiment_analysis(total_sentiment / article_count)
            }
        
        return recommendations

    def _get_sentiment_analysis(self, sentiment_score: float) -> str:
        """Generate market sentiment analysis"""
        if sentiment_score > 0.3:
            return "Market sentiment is very positive, suggesting strong investor confidence."
        elif sentiment_score > 0.1:
            return "Market sentiment is mildly positive, indicating cautious optimism."
        elif sentiment_score < -0.3:
            return "Market sentiment is very negative, suggesting investor concerns."
        elif sentiment_score < -0.1:
            return "Market sentiment is mildly negative, indicating some market uncertainty."
        else:
            return "Market sentiment is neutral, suggesting balanced market conditions."