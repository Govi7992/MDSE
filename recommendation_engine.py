import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
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
                'large_c    ap_growth': 30,
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
        self.newsapi = NewsApiClient(api_key="dad6b10bc28a47f3b68db8b75b07a311")

    def _get_sp500_tickers(self) -> Dict[str, Dict[str, any]]:
        try:
            sp500_data = {}
            tickers = [
                'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META',  
                'BRK-B', 'JPM', 'JNJ', 'PG', 'V',         
                'AMD', 'NVDA', 'PYPL', 'ADBE', 'CRM',     
                'XOM', 'CVX', 'PFE', 'BAC', 'WMT'        
            ]

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
        try:
            if risk_profile in ['conservative', 'moderate_conservative']:
                profile = 'conservative'
            elif risk_profile in ['moderate']:
                profile = 'moderate'
            else:
                profile = 'aggressive'

            allocation = self.risk_allocations[profile]

            total_allocation = sum(allocation.values())
            print(f"Initial total allocation for {profile}: {total_allocation}")

            if total_allocation != 100:
                for key in allocation:
                    allocation[key] = (allocation[key] / total_allocation) * 100
                print(f"Normalized allocations for {profile}: {allocation}")

            recommendations = {
                'description': f'Recommended {profile} investment strategy',
                'allocation': allocation,
                'stock_recommendations': self._get_stock_recommendations(profile),
                'explanation': self._get_strategy_explanation(profile)
            }

            print(f"Generated recommendations: {recommendations}")
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._get_default_recommendations()

    def _get_stock_recommendations(self, profile: str) -> List[Dict]:
        stocks = []
        
        if profile == 'conservative':
            stocks = self._filter_stocks(
                min_market_cap=100e9,
                max_beta=1.0,
                min_dividend_yield=0.02
            )
            stocks.append({'ticker': 'BND', 'name': 'Vanguard Total Bond Market ETF', 'allocation': 50, 'reason': 'Stable bond investment'})
        elif profile == 'moderate':
            stocks = self._filter_stocks(
                min_market_cap=50e9, 
                max_beta=1.5
            )
            stocks.append({'ticker': 'AGG', 'name': 'iShares Core U.S. Aggregate Bond ETF', 'allocation': 30, 'reason': 'Diversified bond exposure'})
        else:
            stocks = self._filter_stocks(
                min_market_cap=10e9,
                min_beta=1.0
            )
            stocks.append({'ticker': 'HYG', 'name': 'iShares iBoxx $ High Yield Corporate Bond ETF', 'allocation': 10, 'reason': 'Higher yield potential'})
        return stocks

    def _filter_stocks(self, min_market_cap=0, max_beta=float('inf'), 
                    min_beta=0, min_dividend_yield=0) -> List[Dict]:
        filtered_stocks = []
        
        for ticker, data in self.sp500_tickers.items():
            if (data['market_cap'] >= min_market_cap and
                min_beta <= data['beta'] <= max_beta and
                data['dividend_yield'] >= min_dividend_yield):
                
                filtered_stocks.append({
                    'ticker': ticker,
                    'name': data['name'],
                    'allocation': 0,
                    'reason': self._get_stock_reason(data)
                })

        return sorted(filtered_stocks, key=lambda x: x['allocation'], reverse=True)

    def _calculate_allocation(self, stock_data: Dict, position: int) -> float:
        position_factor = 1.0 / (position + 1)

        market_cap_factor = min(stock_data['market_cap'] / 1e12, 2.0)
        
        raw_allocation = position_factor * market_cap_factor * 20.0 
        
        return round(min(raw_allocation, 25.0), 1)

    def _get_stock_reason(self, stock_data: Dict) -> str:
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
        explanations = {
            'conservative': "This strategy focuses on stable, large-cap companies with strong dividend histories and lower volatility.",
            'moderate': "This balanced approach combines stable value stocks with growth opportunities while maintaining moderate risk levels.",
            'aggressive': "This growth-oriented strategy focuses on companies with higher return potential, accepting higher volatility."
        }
        return explanations.get(profile, "Balanced investment strategy across different sectors")

    def _get_default_recommendations(self) -> Dict:
        return {
            'description': 'Default balanced investment strategy',
            'allocation': {'stocks': 60, 'bonds': 30, 'cash': 10},
            'stock_recommendations': [],
            'explanation': 'Error occurred. Showing default conservative allocation.'
        }

    def fetch_news(self, ticker: str) -> List[Dict]:
        try:
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            news = self.newsapi.get_everything(
                q=f"{ticker} stock",
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=5 
            )

            articles = []
            for article in news.get('articles', []):
                text = f"{article['title']} {article['description']}"
                sentiment = TextBlob(text).sentiment
                sentiment_score = sentiment.polarity
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

            return sorted(articles, key=lambda x: x['sentiment_score'], reverse=True)

        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return []

    def get_recommendations_with_news(self, risk_profile: str) -> Dict:
        recommendations = self.get_recommendations(risk_profile)
        total_sentiment = 0
        article_count = 0
        
        for stock in recommendations['stock_recommendations']:
            stock['news'] = self.fetch_news(stock['ticker'])
            sentiments = [article['sentiment_score'] for article in stock['news']]
            if sentiments:
                stock['avg_sentiment'] = round(sum(sentiments) / len(sentiments), 2)
                total_sentiment += stock['avg_sentiment']
                article_count += 1
        if article_count > 0:
            recommendations['market_sentiment'] = {
                'score': round(total_sentiment / article_count, 2),
                'analysis': self._get_sentiment_analysis(total_sentiment / article_count)
            }
        return recommendations

    def _get_sentiment_analysis(self, sentiment_score: float) -> str:
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

    def generate_recommendations(self, risk_profile: dict, market_data: dict) -> dict:
        try:
            if not risk_profile or 'profile' not in risk_profile:
                raise ValueError("Invalid risk profile")
            if not market_data:
                raise ValueError("Market data is required")

            profile_type = risk_profile['profile']
            if profile_type not in self.risk_allocations:
                raise ValueError(f"Unsupported risk profile: {profile_type}")
            allocations = self._calculate_portfolio_allocations(profile_type)
            filtered_assets = self._filter_assets_by_risk(market_data, risk_profile)
            specific_recommendations = self._generate_specific_recommendations(
                allocations,
                market_data,
                risk_profile
            )

            for rec in specific_recommendations:
                news_sentiment = self.fetch_news(rec['symbol'])
                rec['sentiment'] = news_sentiment.get('sentiment', 'neutral')
                rec['news'] = news_sentiment.get('articles', [])

            return {
                'allocations': allocations,
                'specific_recommendations': specific_recommendations
            }

        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return {
                'allocations': self._get_default_allocations(),
                'specific_recommendations': []
            }

    def _calculate_portfolio_allocations(self, profile_type: str) -> dict:
        return self.risk_allocations.get(profile_type, self.risk_allocations['moderate'])

    def _filter_assets_by_risk(self, market_data: dict, risk_profile: dict) -> list:
        filtered_assets = []
        risk_score = risk_profile.get('score', 50)
        
        for symbol, data in market_data.items():
            volatility = data.get('volatility', 0.5)
            if (risk_score < 30 and volatility < 0.3) or \
            (30 <= risk_score <= 70 and volatility < 0.5) or \
            (risk_score > 70):
                filtered_assets.append(symbol)
        
        return filtered_assets

    def _generate_specific_recommendations(self, allocations: dict, market_data: dict, risk_profile: dict) -> list:
        recommendations = []
        risk_score = risk_profile.get('score', 50)
        
        for asset_type, allocation in allocations.items():
            suitable_assets = [
                symbol for symbol, data in market_data.items()
                if self._is_suitable_for_allocation(symbol, asset_type, data, risk_score)
            ]
            
            for asset in suitable_assets[:3]:
                recommendations.append({
                    'symbol': asset,
                    'percentage': round(allocation / len(suitable_assets), 2),
                    'rationale': self._get_recommendation_rationale(asset, asset_type, market_data[asset])
                })
        
        return recommendations

    def _is_suitable_for_allocation(self, symbol: str, asset_type: str, data: dict, risk_score: float) -> bool:
        if asset_type == 'stocks':
            return data.get('volatility', 1) * 100 <= risk_score
        elif asset_type == 'bonds':
            return data.get('volatility', 1) * 100 <= 30
        elif asset_type == 'etfs':
            return True
        return False

    def _get_recommendation_rationale(self, symbol: str, asset_type: str, data: dict) -> str:
        volatility = data.get('volatility', 0.5)
        return f"Recommended {symbol} as a {asset_type} investment with {'low' if volatility < 0.3 else 'moderate' if volatility < 0.6 else 'high'} volatility"

    def _get_default_allocations(self) -> dict:
        return {
            'stocks': 0.4,
            'bonds': 0.4,
            'etfs': 0.2
        }
