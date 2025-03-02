import google.generativeai as genai
from typing import Dict

class RiskAssessor:
    def __init__(self):
        self.risk_profiles = {
            'conservative': (0, 20),
            'moderate_conservative': (21, 40),
            'moderate': (41, 60),
            'moderate_aggressive': (61, 80),
            'aggressive': (81, 100)
        }
        self.user_profiles = {}
        self.risk_weights = {
            "investment_timeline": 0.25,
            "risk_tolerance": 0.3,
            "income_level": 0.2,
            "investment_experience": 0.25
        }
        
        try:
            genai.configure(api_key="AIzaSyAl6NUnmxZYP4A8e6cyrQgseEjWIoKnOPk")
            self.model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            print(f"Error initializing Gemini API: {e}")
            self.model = None

    def generate_question(self, previous_responses: Dict) -> str:
        try:
            # For the first question
            if not previous_responses:
                return "To what extent do you agree or disagree with the following statement: Given my investment experience, economic context, social commitments, and personal resilience, I am comfortable with short-term market volatility in pursuit of long-term growth."
            
            # Create context from previous responses
            context = "\n".join([f"Q{i+1}: {resp}" for i, resp in enumerate(previous_responses.values())])
            
            prompt = f"""
            Based on these previous responses:
            {context}
            
            Generate a single, clear situational question about investment risk tolerance that incorporates social, economic, and psychological factors to provide unique insight into the user. The question must begin with "To what extent do you agree or disagree with the following statement:" and be answerable on a five-point scale (strongly agree, agree, neutral, disagree, strongly disagree). It should assess the respondent's risk tolerance, investment experience, financial goals, market understanding, and broader personal context without repeating previous insights.
            
            Return only the question text, without any additional formatting or context.
            """

            print(f"Prompt sent to LLM: {prompt}")  # Debugging line

            # Call the LLM to generate a question
            response = self.model.generate_content(prompt)
            print(f"Response from LLM: {response}")  # Debugging line

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

    def assess_risk(self, user_id, responses):
        # Calculate risk score (0-100)
        total_score = 0
        weights = {
            'Strongly Disagree': 0,
            'Disagree': 25,
            'Neutral': 50,
            'Agree': 75,
            'Strongly Agree': 100
        }

        for response in responses.values():
            total_score += weights.get(response, 50)

        risk_score = total_score / len(responses)

        # Determine risk profile
        risk_profile = 'moderate'  # default
        for profile, (min_score, max_score) in self.risk_profiles.items():
            if min_score <= risk_score <= max_score:
                risk_profile = profile
                break

        # Store user profile
        self.user_profiles[user_id] = {
            'score': risk_score,
            'profile': risk_profile,
            'responses': responses
        }

        return risk_profile

    def get_risk_profile(self, user_id):
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            return {
                'score': profile['score'],
                'profile': profile['profile'],
                'responses': profile['responses']
            }
        return None
