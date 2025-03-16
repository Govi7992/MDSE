import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
import numpy as np
import requests
from textblob import TextBlob
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from database import store_recommendations, get_user_recommendations

class RecommendationEngine:
    def __init__(self):
        self.sp500_tickers = self._get_sp500_tickers()
        self.risk_levels = {
            'Conservative': 0.2,
            'Moderate': 0.5,
            'Aggressive': 0.8
        }
        
        self.asset_classes = {
            'Conservative': {
                'Bonds': 0.6,
                'Large Cap Stocks': 0.3,
                'Mid Cap Stocks': 0.1,
                'Small Cap Stocks': 0.0,
                'International Stocks': 0.0,
                'Commodities': 0.0
            },
            'Moderate': {
                'Bonds': 0.4,
                'Large Cap Stocks': 0.4,
                'Mid Cap Stocks': 0.15,
                'Small Cap Stocks': 0.05,
                'International Stocks': 0.0,
                'Commodities': 0.0
            },
            'Aggressive': {
                'Bonds': 0.2,
                'Large Cap Stocks': 0.4,
                'Mid Cap Stocks': 0.2,
                'Small Cap Stocks': 0.1,
                'International Stocks': 0.1,
                'Commodities': 0.0
            }
        }
        self.newsapi = NewsApiClient(api_key="dad6b10bc28a47f3b68db8b75b07a311")

    def _get_sp500_tickers(self) -> Dict[str, Dict[str, any]]:
        """Get S&P 500 stocks and their market data"""
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
            allocation = self.asset_classes[profile]

            # Calculate total allocation
            total_allocation = sum(allocation.values())
            print(f"Initial total allocation for {profile}: {total_allocation}")

            if total_allocation != 100:
                # Adjust allocations to sum to 100%
                for key in allocation:
                    allocation[key] = (allocation[key] / total_allocation) * 100
                print(f"Normalized allocations for {profile}: {allocation}")

            # Select stocks based on profile
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
        """Get specific stock and bond recommendations based on risk profile"""
        stocks = []
        
        if profile == 'Conservative':
            # Conservative profile - focus on large, stable companies with dividends
            filtered_stocks = self._filter_stocks(
                min_market_cap=100e9,
                max_beta=1.0,
                min_dividend_yield=0.02
            )
            total_allocation = 40  # 40% in stocks for conservative
            stocks = self._assign_allocations(filtered_stocks, total_allocation)
            # Add bond ETF
            stocks.append({
                'ticker': 'BND',
                'name': 'Vanguard Total Bond Market ETF',
                'allocation': 50,
                'reason': 'Stable bond investment for conservative portfolio'
            })
            
        elif profile == 'Moderate':
            # Moderate profile - mix of growth and stability
            filtered_stocks = self._filter_stocks(
                min_market_cap=50e9,
                max_beta=1.5
            )
            total_allocation = 60  # 60% in stocks for moderate
            stocks = self._assign_allocations(filtered_stocks, total_allocation)
            # Add bond ETF
            stocks.append({
                'ticker': 'AGG',
                'name': 'iShares Core U.S. Aggregate Bond ETF',
                'allocation': 30,
                'reason': 'Balanced bond exposure for moderate portfolio'
            })
            
        else:  # Aggressive
            # Aggressive profile - focus on growth potential
            filtered_stocks = self._filter_stocks(
                min_market_cap=10e9,
                min_beta=1.0
            )
            total_allocation = 80  # 80% in stocks for aggressive
            stocks = self._assign_allocations(filtered_stocks, total_allocation)
            # Add high-yield bond ETF
            stocks.append({
                'ticker': 'HYG',
                'name': 'iShares iBoxx $ High Yield Corporate Bond ETF',
                'allocation': 10,
                'reason': 'Higher yield potential for aggressive portfolio'
            })
        
        return stocks

    def _assign_allocations(self, stocks: List[Dict], total_allocation: float) -> List[Dict]:
        """Assign allocation percentages to stocks"""
        if not stocks:
            return []
            
        # Sort stocks by market cap for weighting
        stocks.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        
        # Calculate base allocation per stock
        base_allocation = total_allocation / len(stocks)
        
        # Adjust allocations based on market cap weight
        total_market_cap = sum(stock.get('market_cap', 0) for stock in stocks)
        
        for stock in stocks:
            if total_market_cap > 0:
                # Weight by market cap but keep within reasonable bounds
                market_cap_weight = stock.get('market_cap', 0) / total_market_cap
                allocation = base_allocation * (0.5 + 0.5 * market_cap_weight)  # Blend of equal weight and market cap weight
            else:
                allocation = base_allocation
                
            stock['allocation'] = round(allocation, 1)
            
            # Add reason based on stock characteristics
            reasons = []
            if stock.get('market_cap', 0) > 100e9:
                reasons.append("Large, stable company")
            if stock.get('dividend_yield', 0) > 0.02:
                reasons.append("Good dividend yield")
            if stock.get('beta', 1) < 1.0:
                reasons.append("Lower volatility than market")
            elif stock.get('beta', 1) > 1.2:
                reasons.append("Higher growth potential")
            
            stock['reason'] = ", ".join(reasons) if reasons else "Balanced investment choice"
        
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
                    'market_cap': data['market_cap'],
                    'beta': data['beta'],
                    'dividend_yield': data['dividend_yield'],
                    'reason': self._get_stock_reason(data)
                })

        return filtered_stocks[:10]  # Limit to top 10 stocks

    def _calculate_allocation(self, stock_data: Dict, position: int) -> float:
        """Calculate recommended allocation percentage for a stock"""
        # Base allocation inversely proportional to position (earlier stocks get higher allocation)
        position_factor = 1.0 / (position + 1)
        
        # Market cap factor (larger companies get slightly higher allocation)
        market_cap_factor = min(stock_data['market_cap'] / 1e12, 2.0)
        
        # Calculate raw allocation
        raw_allocation = position_factor * market_cap_factor * 20.0  # Increased base multiplier
        
        # Cap individual allocations at 25%
        return round(min(raw_allocation, 25.0), 1)

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

    def get_recommendations_with_news(self, risk_profile, user_id):
        try:
            # Get user's risk tolerance and preferences
            risk_tolerance = risk_profile.get('risk_tolerance', 'Moderate')
            investment_horizon = risk_profile.get('investment_horizon', 'Medium')
            financial_goals = risk_profile.get('financial_goals', [])
            current_holdings = risk_profile.get('current_holdings', {})
            
            # Get base allocation based on risk tolerance
            base_allocation = self.asset_classes[risk_tolerance].copy()
            
            # Adjust allocation based on investment horizon
            if investment_horizon == 'Long':
                # Shift more towards stocks for long-term growth
                base_allocation['Bonds'] *= 0.8
                base_allocation['Large Cap Stocks'] *= 1.1
                base_allocation['Mid Cap Stocks'] *= 1.1
                base_allocation['Small Cap Stocks'] *= 1.1
            elif investment_horizon == 'Short':
                # Shift more towards bonds for stability
                base_allocation['Bonds'] *= 1.2
                base_allocation['Large Cap Stocks'] *= 0.9
                base_allocation['Mid Cap Stocks'] *= 0.9
                base_allocation['Small Cap Stocks'] *= 0.9
            
            # Adjust based on financial goals
            if 'Capital Preservation' in financial_goals:
                base_allocation['Bonds'] *= 1.2
                base_allocation['Large Cap Stocks'] *= 0.9
                base_allocation['Mid Cap Stocks'] *= 0.9
                base_allocation['Small Cap Stocks'] *= 0.9
            elif 'Growth' in financial_goals:
                base_allocation['Bonds'] *= 0.8
                base_allocation['Large Cap Stocks'] *= 1.1
                base_allocation['Mid Cap Stocks'] *= 1.1
                base_allocation['Small Cap Stocks'] *= 1.1
            
            # Normalize allocations to ensure they sum to 100%
            total = sum(base_allocation.values())
            normalized_allocation = {k: round(v/total * 100, 2) for k, v in base_allocation.items()}
            
            # Generate specific recommendations based on current holdings
            recommendations = []
            for asset, target in normalized_allocation.items():
                current = current_holdings.get(asset, 0)
                if target > current:
                    recommendations.append({
                        'action': 'Buy',
                        'asset': asset,
                        'target_percentage': target,
                        'current_percentage': current,
                        'adjustment': round(target - current, 2)
                    })
                elif target < current:
                    recommendations.append({
                        'action': 'Sell',
                        'asset': asset,
                        'target_percentage': target,
                        'current_percentage': current,
                        'adjustment': round(current - target, 2)
                    })
            
            # Sort recommendations by adjustment size
            recommendations.sort(key=lambda x: x['adjustment'], reverse=True)
            
            # Get stock recommendations based on risk profile
            stock_recommendations = self._get_stock_recommendations(risk_tolerance)
            
            # Add news and sentiment analysis for each stock
            for stock in stock_recommendations:
                news = self.fetch_news(stock['ticker'])
                if news:
                    sentiments = [article['sentiment_score'] for article in news]
                    stock['avg_sentiment'] = sum(sentiments) / len(sentiments)
                    stock['news'] = news
            
            # Get market indices data
            market_indices = self._get_market_indices()
            
            # Calculate overall market sentiment
            total_sentiment = 0
            sentiment_count = 0
            for stock in stock_recommendations:
                if 'avg_sentiment' in stock:
                    total_sentiment += stock['avg_sentiment']
                    sentiment_count += 1
            
            market_sentiment = {
                'score': round(total_sentiment / sentiment_count if sentiment_count > 0 else 0, 2),
                'analysis': self._get_sentiment_analysis(total_sentiment / sentiment_count if sentiment_count > 0 else 0)
            }
            
            # Create the final recommendations object
            final_recommendations = {
                'user_id': user_id,
                'risk_profile': risk_profile,
                'asset_allocation': normalized_allocation,
                'recommendations': recommendations[:5],  # Top 5 recommendations
                'stock_recommendations': stock_recommendations,
                'market_indices': market_indices,
                'market_sentiment': market_sentiment,
                'risk_tolerance': risk_tolerance,
                'investment_horizon': investment_horizon,
                'financial_goals': financial_goals,
                'created_at': datetime.utcnow()
            }
            
            # Store recommendations in database
            store_recommendations(user_id, final_recommendations)
            
            return final_recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            # Return a default structure in case of error
            return {
                'user_id': user_id,
                'risk_profile': risk_profile,
                'asset_allocation': {
                    'Bonds': 40,
                    'Large Cap Stocks': 40,
                    'Mid Cap Stocks': 15,
                    'Small Cap Stocks': 5
                },
                'recommendations': [],
                'stock_recommendations': [],
                'market_indices': [],
                'market_sentiment': {
                    'score': 0,
                    'analysis': 'Unable to analyze market sentiment at this time.'
                },
                'risk_tolerance': 'Moderate',
                'investment_horizon': 'Medium',
                'financial_goals': [],
                'created_at': datetime.utcnow()
            }

    def _get_market_indices(self):
        """Get current market indices data"""
        try:
            indices = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
                '^FTSE': 'FTSE 100'
            }
            
            market_data = []
            for symbol, name in indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    current_price = info.get('regularMarketPrice', 0)
                    previous_close = info.get('previousClose', 0)
                    change = ((current_price - previous_close) / previous_close) * 100 if previous_close else 0
                    
                    market_data.append({
                        'name': name,
                        'value': f"${current_price:,.2f}",
                        'change': f"{change:+.2f}"
                    })
                except Exception as e:
                    print(f"Error fetching data for {symbol}: {e}")
                    continue
                
            return market_data
        except Exception as e:
            print(f"Error fetching market indices: {e}")
            return []

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

    def generate_recommendations(self, risk_profile: dict, market_data: dict) -> dict:
        """
        Generate investment recommendations based on risk profile and market data.
        
        Args:
            risk_profile (dict): User's risk profile containing 'profile' and 'score'
            market_data (dict): Current market data for available assets
        
        Returns:
            dict: Recommendations including allocations and specific recommendations
        """
        try:
            if not risk_profile or 'profile' not in risk_profile:
                raise ValueError("Invalid risk profile")
            if not market_data:
                raise ValueError("Market data is required")

            profile_type = risk_profile['profile']
            if profile_type not in self.asset_classes:
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
        """Calculate portfolio allocations based on risk profile."""
        return self.asset_classes.get(profile_type, self.asset_classes['moderate'])

    def _filter_assets_by_risk(self, market_data: dict, risk_profile: dict) -> list:
        """Filter assets based on risk profile."""
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
        """Generate specific asset recommendations."""
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
        """Determine if an asset is suitable for a particular allocation type."""
        if asset_type == 'stocks':
            return data.get('volatility', 1) * 100 <= risk_score
        elif asset_type == 'bonds':
            return data.get('volatility', 1) * 100 <= 30
        elif asset_type == 'etfs':
            return True
        return False

    def _get_recommendation_rationale(self, symbol: str, asset_type: str, data: dict) -> str:
        """Generate rationale for recommending an asset."""
        volatility = data.get('volatility', 0.5)
        return f"Recommended {symbol} as a {asset_type} investment with {'low' if volatility < 0.3 else 'moderate' if volatility < 0.6 else 'high'} volatility"

    def _get_default_allocations(self) -> dict:
        """Return default allocations for fallback."""
        return {
            'stocks': 0.4,
            'bonds': 0.4,
            'etfs': 0.2
        }
