from user_management import UserManager
from risk_assessment import RiskAssessor
from portfolio_manager import PortfolioManager
from market_data import MarketDataService
from news_service import NewsService
from recommendation_engine import RecommendationEngine
from asset_db import AssetDB


class FinancialAdvisorSystem:
    def __init__(self):
        self.asset_db = AssetDB()
        self.user_manager = UserManager()
        self.risk_assessor = RiskAssessor()
        self.portfolio_manager = PortfolioManager()
        self.market_data = MarketDataService()
        self.news_service = NewsService()
        self.recommendation_engine = RecommendationEngine()
        self.portfolio_manager.asset_db = self.asset_db

    def register_user(self, username, password, email):
        return self.user_manager.register_user(username, password, email)

    def authenticate_user(self, username, password):
        return self.user_manager.authenticate_user(username, password)

    def assess_risk_profile(self, user_id, questionnaire_responses):
        return self.risk_assessor.assess_risk(user_id, questionnaire_responses)

    def get_portfolio_recommendations(self, user_id):
        risk_profile = self.risk_assessor.get_risk_profile(user_id)
        market_data = self.market_data.get_current_market_data()
        return self.recommendation_engine.generate_recommendations(risk_profile, market_data)

    def get_financial_news(self):
        return self.news_service.get_financial_news()

def main():
    try:
        system = FinancialAdvisorSystem()
        user_id = system.register_user("john_doe", "StrongPass123!", "john@example.com")
        
        if system.authenticate_user("john_doe", "StrongPass123!"):
            responses = {
                "investment_timeline": 5,
                "risk_tolerance": "moderate",
                "income_level": "high",
                "investment_experience": "intermediate"
            }
            
            risk_profile = system.assess_risk_profile(user_id, responses)
            recommendations = system.get_portfolio_recommendations(user_id)
            print(f"Risk Profile: {risk_profile}")
            print(f"Recommendations: {recommendations}")

            news = system.get_financial_news()
            print("Financial News:")
            for article in news:
                print(f"- {article['title']} ({article['url']})")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("\nRunning in demo mode with sample data:")
        print("Risk Profile: moderate")
        print("Recommendations: {'stocks': 50%, 'bonds': 30%, 'cash': 20%}")
        print("Financial News:")
        print("- Market Update: Stocks rise on economic data (https://example.com/news1)")
        print("- Fed Announces New Policy (https://example.com/news2)")

if __name__ == "__main__":
    main()
