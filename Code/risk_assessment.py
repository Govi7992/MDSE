import google.generativeai as genai
from typing import Dict, Optional
from datetime import datetime

class RiskAssessor:
    def __init__(self):
        """Initialize RiskAssessor with risk profiles and LLM."""
        self.risk_profiles = {
            'conservative': (0, 30),
            'moderate_conservative': (31, 45),
            'moderate': (46, 65),
            'moderate_aggressive': (66, 80),
            'aggressive': (81, 100)
        }
        
        self.risk_weights = {
            'investment_experience': 0.25,
            'time_horizon': 0.25,
            'risk_tolerance': 0.30,
            'financial_goals': 0.20
        }
        
        self.response_scores = {
            'Beginner': 20,
            'Intermediate': 50,
            'Experienced': 80,
            'Expert': 100,
            
            'Short-term': 20,
            'Medium-term': 50,
            'Long-term': 80,
            'Very Long-term': 100,
            
            'Low': 20,
            'Medium': 50,
            'High': 80,
            'Very High': 100,
            
            'Preservation': 20,
            'Balanced Growth': 50,
            'Growth': 80,
            'Aggressive Growth': 100,
            
            'Strongly Disagree': 0,
            'Disagree': 25,
            'Neutral': 50,
            'Agree': 75,
            'Strongly Agree': 100
        }
        
        self.user_profiles = {}
        
        self.fallback_questions = [
            "How comfortable are you with market volatility?",
            "What is your primary investment goal?",
            "How long do you plan to hold your investments?",
            "How would you describe your investment knowledge?",
            "What percentage of your savings are you willing to invest?"
        ]

        try:
            genai.configure(api_key="AIzaSyBSMKG56NPzUzupcaGW86LyFsHEvox4NU8")
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        except Exception as e:
            print(f"Error initializing Gemini API: {e}")
            self.model = None

    def generate_question(self, previous_responses: Dict) -> str:
        try:
            if not previous_responses:
                return "To what extent do you agree or disagree with the following statement: Given my investment experience, economic context, social commitments, and personal resilience, I am comfortable with short-term market volatility in pursuit of long-term growth."
            context = "\n".join([f"Q{i+1}: {resp}" for i, resp in enumerate(previous_responses.values())])
            
            prompt = f"""
            Based on these previous responses:
            {context}
            
            Generate a single, clear situational question about investment risk tolerance that incorporates social, economic, and psychological factors to provide unique insight into the user. The question must begin with "To what extent do you agree or disagree with the following statement:" and be answerable on a five-point scale (strongly agree, agree, neutral, disagree, strongly disagree). It should assess the respondent's risk tolerance, investment experience, financial goals, market understanding, and broader personal context without repeating previous insights.
            
            Return only the question text, without any additional formatting or context.
            """

            print(f"Prompt sent to LLM: {prompt}")
            response = self.model.generate_content(prompt)
            print(f"Response from LLM: {response}") 

            return response.text.strip()
        except Exception as e:
            print(f"Error generating question: {e}")
            fallback_questions = [
                "How comfortable are you with market volatility?",
                "What is your primary investment goal?",
                "How long do you plan to hold your investments?",
                "How would you describe your investment knowledge?",
                "What percentage of your savings are you willing to invest?",
            ]
            question_index = len(previous_responses) % len(fallback_questions)
            return fallback_questions[question_index]


    def assess_risk(self, user_id: str, responses: Dict) -> str:
        """Assess risk profile based on user responses."""
        try:
            if not responses:
                return 'moderate'

            total_score = 0
            total_weight = 0

            for factor, response in responses.items():
                if factor in self.risk_weights:
                    weight = self.risk_weights[factor]
                    score = self.response_scores.get(response, 50)
                    if response == 'Experienced':
                        score = 90
                    elif response == 'High':
                        score = 85
                    elif response == 'Growth':
                        score = 85
                    
                    total_score += score * weight
                    total_weight += weight

            risk_score = total_score / total_weight if total_weight > 0 else 50

            profile_data = {
                'score': risk_score,
                'responses': responses,
                'timestamp': datetime.now().isoformat()
            }

            for profile, (min_score, max_score) in self.risk_profiles.items():
                if min_score <= risk_score <= max_score:
                    profile_data['profile'] = profile
                    self.user_profiles[user_id] = profile_data
                    return profile

            profile_data['profile'] = 'moderate'
            self.user_profiles[user_id] = profile_data
            return 'moderate'

        except Exception as e:
            print(f"Error assessing risk: {e}")
            return 'moderate'

    def get_risk_profile(self, user_id: str) -> Optional[Dict]:
        """Get stored risk profile for a user."""
        return self.user_profiles.get(user_id)
