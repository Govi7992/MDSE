import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
import numpy as np
import requests
from textblob import TextBlob
from datetime import datetime, timedelta
from newsapi import NewsApiClient
import re
from database import store_recommendations, get_user_recommendations, get_user_by_email, create_or_update_user

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
        """
        Generate stock and bond recommendations based on risk profile
        
        OCL Constraints:
        pre ValidRiskProfile: Set{'Conservative', 'Moderate', 'Aggressive'}->includes(risk_profile)
        post RecommendationsMatchProfile: 
            (risk_profile = 'Conservative' implies result.profile = 'Conservative') and
            (risk_profile = 'Moderate' implies result.profile = 'Moderate') and
            (risk_profile = 'Aggressive' implies result.profile = 'Aggressive')
        post ValidAssetAllocation: 
            result.asset_allocation->values()->sum() = 100 and
            result.asset_allocation->values()->forAll(v | v >= 0)
        post InvestmentAllocationConsistency:
            result.investments->collect(i | i.allocation)->sum() = 100
        """
        try:
            valid_profiles = {'Conservative', 'Moderate', 'Aggressive'}
            normalized_profile = None

            if isinstance(risk_profile, dict):

                profile_type = risk_profile.get('profile', 'Moderate')
                if isinstance(profile_type, str):
                    if profile_type.lower() in ['conservative', 'moderate_conservative']:
                        normalized_profile = 'Conservative'
                    elif profile_type.lower() in ['moderate']:
                        normalized_profile = 'Moderate'
                    else:
                        normalized_profile = 'Aggressive'
                else:
                    normalized_profile = 'Moderate' 
            else:
                if isinstance(risk_profile, str):
                    if risk_profile.lower() in ['conservative', 'moderate_conservative']:
                        normalized_profile = 'Conservative'
                    elif risk_profile.lower() in ['moderate']:
                        normalized_profile = 'Moderate'
                    else:
                        normalized_profile = 'Aggressive'
                else:
                    normalized_profile = 'Moderate' 

            if normalized_profile not in valid_profiles:
                raise ValueError(f"Invalid risk profile: {risk_profile}")
            
            profile = normalized_profile
            print(f"Processing recommendation for profile: {profile}")

            stock_recommendations = self._get_stock_recommendations(profile)

            total_investment_allocation = sum(stock['allocation'] for stock in stock_recommendations)
            if total_investment_allocation != 100:
                scaling_factor = 100 / total_investment_allocation
                for stock in stock_recommendations:
                    stock['allocation'] = round(stock['allocation'] * scaling_factor)

                current_sum = sum(stock['allocation'] for stock in stock_recommendations)
                if current_sum != 100:
                    stock_recommendations.sort(key=lambda x: x['allocation'], reverse=True)
                    stock_recommendations[0]['allocation'] += (100 - current_sum)

            asset_allocation = self._get_asset_allocation(profile)

            allocation_sum = sum(asset_allocation.values())
            if allocation_sum != 100:
                scaling_factor = 100 / allocation_sum
                for asset_class in asset_allocation:
                    asset_allocation[asset_class] = round(asset_allocation[asset_class] * scaling_factor)

                current_sum = sum(asset_allocation.values())
                if current_sum != 100:
                    largest_class = max(asset_allocation.items(), key=lambda x: x[1])[0]
                    asset_allocation[largest_class] += (100 - current_sum)
            
            if any(v < 0 for v in asset_allocation.values()):
                raise ValueError("Asset allocations cannot be negative")

            recommendations = {
                'profile': profile,
                'description': f'Recommended {profile} investment strategy',
                'asset_allocation': asset_allocation,
                'investments': stock_recommendations,
                'explanation': self._get_strategy_explanation(profile.lower()),
                'timestamp': datetime.now().isoformat()
            }
            recommendations['display_data'] = self._format_for_display(recommendations)

            print(f"Generated recommendations: {recommendations}")
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._get_default_recommendations()

    def _get_stock_recommendations(self, profile: str) -> List[Dict]:
        """
        Get specific stock and bond recommendations based on risk profile
        
        OCL Constraints:
        post DiversifiedPortfolio: result->size() >= 3
        post AllocationSumCorrect: result->collect(r | r.allocation)->sum() <= 100
        """
        stocks = []

        if profile == 'Conservative':
            stocks = [
                {
                    'ticker': 'JNJ',
                    'name': 'Johnson & Johnson',
                    'allocation': 0.10,
                    'reason': 'Large, stable company with strong dividend history'
                },
                {
                    'ticker': 'PG',
                    'name': 'Procter & Gamble',
                    'allocation': 0.10,
                    'reason': 'Consumer staples company with stable earnings'
                },
                {
                    'ticker': 'KO',
                    'name': 'Coca-Cola Company',
                    'allocation': 0.8,
                    'reason': 'Consistent dividend payer with low volatility'
                },
                {
                'ticker': 'BND',
                'name': 'Vanguard Total Bond Market ETF',
                    'allocation': 0.40,
                    'reason': 'Broad exposure to U.S. investment-grade bonds'
                },
                {
                    'ticker': 'VCSH',
                    'name': 'Vanguard Short-Term Corporate Bond ETF',
                    'allocation': 0.20,
                    'reason': 'Short-term corporate bonds for income with lower interest rate risk'
                },
                {
                    'ticker': 'MUB',
                    'name': 'iShares National Muni Bond ETF',
                    'allocation': 0.12,
                    'reason': 'Tax-advantaged municipal bond exposure'
                }
            ]
        elif profile == 'Moderate':
            stocks = [
                {
                    'ticker': 'AAPL',
                    'name': 'Apple Inc.',
                    'allocation': 0.12,
                    'reason': 'Large tech company with strong balance sheet'
                },
                {
                    'ticker': 'MSFT',
                    'name': 'Microsoft Corporation',
                    'allocation': 0.12,
                    'reason': 'Diversified technology company with consistent growth'
                },
                {
                    'ticker': 'V',
                    'name': 'Visa Inc.',
                    'allocation': 0.10,
                    'reason': 'Financial services company with strong cash flow'
                },
                {
                    'ticker': 'VTI',
                    'name': 'Vanguard Total Stock Market ETF',
                    'allocation': 0.16,
                    'reason': 'Broad U.S. stock market exposure'
                },
                {
                'ticker': 'AGG',
                'name': 'iShares Core U.S. Aggregate Bond ETF',
                'allocation': 0.30,
                    'reason': 'Core bond holding for moderate portfolios'
                },
                {
                    'ticker': 'IVV',
                    'name': 'iShares Core S&P 500 ETF',
                    'allocation': 0.10,
                    'reason': 'Low-cost S&P 500 index exposure'
                },
                {
                    'ticker': 'VEA',
                    'name': 'Vanguard FTSE Developed Markets ETF',
                    'allocation': 0.10,
                    'reason': 'International developed markets exposure'
                }
            ]
        else:  
            stocks = [
                {
                    'ticker': 'NVDA',
                    'name': 'NVIDIA Corporation',
                    'allocation': 0.15,
                    'reason': 'High-growth technology company in AI and computing'
                },
                {
                    'ticker': 'AMZN',
                    'name': 'Amazon.com, Inc.',
                    'allocation': 0.15,
                    'reason': 'E-commerce and cloud computing leader with growth potential'
                },
                {
                    'ticker': 'TSLA',
                    'name': 'Tesla, Inc.',
                    'allocation': 0.10,
                    'reason': 'Electric vehicle pioneer with disruptive technology'
                },
                {
                    'ticker': 'QQQ',
                    'name': 'Invesco QQQ Trust (NASDAQ-100 Index)',
                    'allocation': 0.20,
                    'reason': 'Technology-focused growth ETF'
                },
                {
                    'ticker': 'VWO',
                    'name': 'Vanguard Emerging Markets ETF',
                    'allocation': 0.15,
                    'reason': 'Emerging markets exposure for higher growth potential'
                },
                {
                    'ticker': 'VBK',
                    'name': 'Vanguard Small-Cap Growth ETF',
                    'allocation': 0.15,
                    'reason': 'Small-cap growth companies with high return potential'
                },
                {
                'ticker': 'HYG',
                'name': 'iShares iBoxx $ High Yield Corporate Bond ETF',
                'allocation': 0.10,
                    'reason': 'Higher yield potential for aggressive portfolios'
                }
            ]
        
        if len(stocks) < 3:
            default_stocks = [
                {
                    'ticker': 'VTI',
                    'name': 'Vanguard Total Stock Market ETF',
                    'allocation': 0.5,
                    'reason': 'Added for diversification'
                },
                {
                    'ticker': 'BND',
                    'name': 'Vanguard Total Bond Market ETF',
                    'allocation': 0.5,
                    'reason': 'Added for diversification'
                },
                {
                    'ticker': 'VEA',
                    'name': 'Vanguard FTSE Developed Markets ETF',
                    'allocation': 0.5,
                    'reason': 'Added for international exposure'
                }
            ]

            for i in range(min(3 - len(stocks), len(default_stocks))):
                stocks.append(default_stocks[i])

        total_allocation = sum(stock['allocation'] for stock in stocks)
        if total_allocation > 100:

            scaling_factor = 100 / total_allocation
            for stock in stocks:
                stock['allocation'] = round(stock['allocation'] * scaling_factor)

            current_sum = sum(stock['allocation'] for stock in stocks)
            if current_sum != 100:

                stocks.sort(key=lambda x: x['allocation'], reverse=True)
                stocks[0]['allocation'] += (100 - current_sum)
        
        return stocks

    def _get_strategy_explanation(self, profile: str) -> str:
        """Get detailed explanation of the investment strategy"""
        explanations = {
            'conservative': "This conservative strategy focuses on capital preservation and income generation. It emphasizes stable, large-cap companies with strong dividend histories and lower volatility. A significant portion (60%) is allocated to bonds for stability, with the remaining invested in high-quality stocks. This approach is suitable for investors with a shorter time horizon or lower risk tolerance.",
            
            'moderate': "This balanced approach combines stable value stocks with growth opportunities while maintaining moderate risk levels. With a 40/60 split between bonds and stocks, this strategy aims to generate both income and capital appreciation. It includes exposure to large and mid-cap stocks, along with some international diversification. Suitable for investors with a medium-term time horizon who can tolerate some market fluctuations.",
            
            'aggressive': "This growth-oriented strategy focuses on companies and sectors with higher return potential, accepting higher volatility in pursuit of long-term capital appreciation. With a significant allocation to technology and growth stocks, along with emerging markets exposure, this approach aims to maximize returns over time. The limited bond allocation (20%) provides some stability. Suitable for investors with a long time horizon who can withstand significant market fluctuations."
        }
        return explanations.get(profile, "Balanced investment strategy across different sectors")

    def _get_asset_allocation(self, profile: str) -> Dict:
        """Get asset allocation for the given risk profile"""
        if profile == 'Conservative':
            return {
                'Bonds': 60,
                'Large Cap Stocks': 25,
                'Mid Cap Stocks': 10,
                'Small Cap Stocks': 3,
                'International Stocks': 2,
                'Commodities': 0
            }
        elif profile == 'Moderate':
            return {
                'Bonds': 40,
                'Large Cap Stocks': 30,
                'Mid Cap Stocks': 15,
                'Small Cap Stocks': 10,
                'International Stocks': 5,
                'Commodities': 0
            }
        else:  
            return {
                'Bonds': 20,
                'Large Cap Stocks': 30,
                'Mid Cap Stocks': 25,
                'Small Cap Stocks': 15,
                'International Stocks': 10,
                'Commodities': 0
            }

    def _format_for_display(self, recommendations: Dict) -> Dict:
        """Format recommendations for easy display in UI"""
        profile = recommendations.get('profile', 'Unknown')
        asset_allocation = recommendations.get('asset_allocation', {})
        investments = recommendations.get('investments', [])
        
        allocation_summary = []
        for asset_class, percentage in asset_allocation.items():
            if percentage > 0:
                allocation_summary.append({
                    'name': asset_class,
                    'percentage': percentage,
                    'color': self._get_color_for_asset_class(asset_class)
                })
        
        categorized_investments = {
            'Stocks': [],
            'ETFs': [],
            'Bonds': []
        }
        
        for investment in investments:
            ticker = investment.get('ticker', '')
            if 'bond' in investment.get('name', '').lower() or ticker in ['BND', 'AGG', 'VCSH', 'MUB', 'HYG']:
                categorized_investments['Bonds'].append(investment)
            elif ticker in ['VTI', 'QQQ', 'VWO', 'VBK', 'VEA', 'IVV']:
                categorized_investments['ETFs'].append(investment)
            else:
                categorized_investments['Stocks'].append(investment)

        highlighted_recommendations = []
        if profile == 'Conservative':
            highlighted_recommendations = [
                {
                    'title': 'Focus on Stability',
                    'description': 'Your portfolio emphasizes bonds and dividend-paying stocks for stability and income.'
                },
                {
                    'title': 'Dividend Income',
                    'description': 'Conservative stocks like Johnson & Johnson and Procter & Gamble provide reliable dividends.'
                },
                {
                    'title': 'Bond Protection',
                    'description': 'A significant bond allocation helps protect your capital during market downturns.'
                }
            ]
        elif profile == 'Moderate':
            highlighted_recommendations = [
                {
                    'title': 'Balanced Approach',
                    'description': 'Your portfolio balances growth potential with stability through a mix of stocks and bonds.'
                },
                {
                    'title': 'Quality Companies',
                    'description': 'Established companies like Apple and Microsoft offer growth potential with reasonable risk.'
                },
                {
                    'title': 'Diversification',
                    'description': 'ETFs provide broad market exposure to enhance diversification.'
                }
            ]
        else: 
            highlighted_recommendations = [
                {
                    'title': 'Growth Focus',
                    'description': 'Your portfolio emphasizes high-growth companies and sectors for maximum appreciation.'
                },
                {
                    'title': 'Innovation Leaders',
                    'description': 'Companies like NVIDIA and Tesla are at the forefront of technological innovation.'
                },
                {
                    'title': 'Global Opportunities',
                    'description': 'Emerging markets exposure captures growth opportunities worldwide.'
                }
            ]
        
        return {
            'profile_name': profile,
            'profile_description': self._get_profile_description(profile),
            'allocation_summary': allocation_summary,
            'categorized_investments': categorized_investments,
            'highlighted_recommendations': highlighted_recommendations,
            'total_investments': len(investments)
        }

    def _get_color_for_asset_class(self, asset_class: str) -> str:
        """Get color for asset class visualization"""
        colors = {
            'Bonds': '#4682B4',  # Steel Blue
            'Large Cap Stocks': '#228B22',  # Forest Green
            'Mid Cap Stocks': '#32CD32',  # Lime Green
            'Small Cap Stocks': '#7FFF00',  # Chartreuse
            'International Stocks': '#FF8C00',  # Dark Orange
            'Commodities': '#FFD700'  # Gold
        }
        return colors.get(asset_class, '#808080')  # Default Gray

    def _get_profile_description(self, profile: str) -> str:
        """Get a short description of the risk profile"""
        descriptions = {
            'Conservative': 'Prioritizes safety of principal and steady income with minimal volatility.',
            'Moderate': 'Balances growth potential with stability for medium-term goals.',
            'Aggressive': 'Maximizes long-term growth potential while accepting higher volatility.'
        }
        return descriptions.get(profile, 'Customized investment approach based on your preferences.')

    def _get_default_recommendations(self) -> Dict:
        """Return default recommendations if error occurs"""
        default_allocation = {
            'Bonds': 50,
            'Large Cap Stocks': 30,
            'Mid Cap Stocks': 10,
            'Small Cap Stocks': 5,
            'International Stocks': 5,
            'Commodities': 0
        }
        
        default_investments = [
            {
                'ticker': 'VTI',
                'name': 'Vanguard Total Stock Market ETF',
                'allocation': 30,
                'reason': 'Broad market exposure through index ETF'
            },
            {
                'ticker': 'BND',
                'name': 'Vanguard Total Bond Market ETF',
                'allocation': 50,
                'reason': 'Stable bond investment for income and capital preservation'
            },
            {
                'ticker': 'VEA',
                'name': 'Vanguard FTSE Developed Markets ETF',
                'allocation': 10,
                'reason': 'International exposure for diversification'
            },
            {
                'ticker': 'VCSH',
                'name': 'Vanguard Short-Term Corporate Bond ETF',
                'allocation': 10,
                'reason': 'Short-term bonds for stability and income'
            }
        ]
        
        recommendations = {
            'profile': 'Moderate',
            'description': 'Default balanced investment strategy',
            'asset_allocation': default_allocation,
            'investments': default_investments,
            'explanation': 'This default strategy provides a balanced approach suitable for most investors.',
            'timestamp': datetime.now().isoformat()
        }

        recommendations['display_data'] = self._format_for_display(recommendations)
        
        return recommendations

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
            if not self._has_valid_assessment(user_id):
                raise ValueError("User must have a valid risk assessment")

            if not self._is_assessment_before_recommendation(user_id):
                raise ValueError("Risk assessment must be performed before generating recommendations")

            if not risk_profile:
                raise ValueError("Risk profile is required for recommendations")

            risk_tolerance = risk_profile.get('risk_tolerance', 'Moderate')
            investment_horizon = risk_profile.get('investment_horizon', 'Medium')
            financial_goals = risk_profile.get('financial_goals', [])
            current_holdings = risk_profile.get('current_holdings', {})

            base_allocation = self.asset_classes[risk_tolerance].copy()

            if investment_horizon == 'Long':
                base_allocation['Bonds'] *= 0.8
                base_allocation['Large Cap Stocks'] *= 1.1
                base_allocation['Mid Cap Stocks'] *= 1.1
                base_allocation['Small Cap Stocks'] *= 1.1
            elif investment_horizon == 'Short':
                base_allocation['Bonds'] *= 1.2
                base_allocation['Large Cap Stocks'] *= 0.9
                base_allocation['Mid Cap Stocks'] *= 0.9
                base_allocation['Small Cap Stocks'] *= 0.9
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

            total = sum(base_allocation.values())
            normalized_allocation = {k: round(v/total * 100, 2) for k, v in base_allocation.items()}

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

            recommendations.sort(key=lambda x: x['adjustment'], reverse=True)

            stock_recommendations = self._get_stock_recommendations(risk_tolerance)

            for stock in stock_recommendations:
                news = self.fetch_news(stock['ticker'])
                if news:
                    sentiments = [article['sentiment_score'] for article in news]
                    stock['avg_sentiment'] = sum(sentiments) / len(sentiments)
                    stock['news'] = news

            market_indices = self._get_market_indices()

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

            final_recommendations = {
                'user_id': user_id,
                'risk_profile': risk_profile,
                'asset_allocation': normalized_allocation,
                'recommendations': recommendations[:5], 
                'stock_recommendations': stock_recommendations,
                'market_indices': market_indices,
                'market_sentiment': market_sentiment,
                'risk_tolerance': risk_tolerance,
                'investment_horizon': investment_horizon,
                'financial_goals': financial_goals,
                'created_at': datetime.utcnow()
            }

            store_recommendations(user_id, final_recommendations)
            
            return final_recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
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
                'risk_tolerance': risk_profile.get('risk_tolerance', 'Moderate'),
                'investment_horizon': risk_profile.get('investment_horizon', 'Medium'),
                'financial_goals': risk_profile.get('financial_goals', []),
                'created_at': datetime.utcnow()
            }

    def _has_valid_assessment(self, user_id):
        """OCL: LinkedToAssessment"""
        return True  
    
    def _is_assessment_before_recommendation(self, user_id):
        """OCL: RecommendationAfterAssessment"""
        return True 

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
                    'rationale': self._get_recommendation_rationale(asset, asset_type, market_data[asset]),
                    'type': self.determine_investment_type(asset, market_data[asset]['name'])
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

    def create_user(self, email, password, user_data=None):
        try:
            existing_user = get_user_by_email(email)
            if existing_user:
                raise ValueError("Email already exists")
            
            if not self._validate_password_strength(password):
                raise ValueError("Password does not meet security requirements")

            if user_data and 'phone_number' in user_data:
                if not self._validate_phone_number(user_data['phone_number']):
                    raise ValueError("Invalid phone number format")

            if user_data and 'date_of_birth' in user_data:
                if not self._validate_age(user_data['date_of_birth']):
                    raise ValueError("User must be at least 18 years old")

            if user_data is None:
                user_data = {
                    "email": email,
                    "password": password
                }
            
            return create_or_update_user(user_data)
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
        
    def _validate_password_strength(self, password):
        """OCL: PasswordStrength"""
        print(f"Validating password: {'*' * len(password)}")
        
        if not password or not isinstance(password, str):
            print("Password validation failed: Invalid password type")
            return False
        
        if len(password) < 8:
            print("Password validation failed: Password too short")
            return False
        
        if not re.search(r"[A-Z]", password):
            print("Password validation failed: Missing uppercase letter")
            return False
        
        if not re.search(r"[a-z]", password):
            print("Password validation failed: Missing lowercase letter") 
            return False
        
        if not re.search(r"[0-9]", password):
            print("Password validation failed: Missing number")
            return False
        
        if not re.search(r"[@$!%*?&]", password):
            print("Password validation failed: Missing special character")
            return False
        
        print("Password validation passed")
        return True
        
    def _validate_phone_number(self, phone_number):
        """OCL: ValidPhoneNumber"""
        print(f"Validating phone number: {phone_number}")
        
        if not phone_number or not isinstance(phone_number, str):
            print("Phone validation failed: Invalid phone number type")
            return False
        
        if not re.match(r'^\+?[0-9]{10,15}$', phone_number):
            print(f"Phone validation failed: Phone number doesn't match pattern (^\+?[0-9]{{10,15}}$)")
            return False
        
        print("Phone validation passed")
        return True
        
    def _validate_age(self, date_of_birth):
        """OCL: AgeRestriction"""
        print(f"Validating date of birth: {date_of_birth}")
        
        if not date_of_birth or not isinstance(date_of_birth, str):
            print("Age validation failed: Invalid date format")
            return False
        
        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            print(f"Calculated age: {age} years")
            
            if age < 18:
                print("Age validation failed: User is under 18 years old")
                return False
            
            print("Age validation passed")
            return True
        except Exception as e:
            print(f"Age validation failed: {str(e)}")
            return False

    def determine_investment_type(self, symbol, name):
        """Determine investment type based on symbol and name"""
        if symbol.endswith('F'):
            return 'Mutual Fund'
        elif symbol.endswith('X'):
            return 'Index Fund'
        elif 'ETF' in name:
            return 'ETF'
        elif 'Index' in name:
            return 'Index Fund'
        elif 'Bond' in name or 'Treasury' in name:
            return 'Bond'
        elif 'REIT' in name or 'Real Estate' in name:
            return 'REIT'
        elif 'Fund' in name:
            return 'Mutual Fund'
        else:
            return 'Stock'
