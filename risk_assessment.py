import google.generativeai as genai
from typing import Dict
from database import store_risk_assessment, get_user_risk_assessment
from datetime import datetime, timedelta
from bson import ObjectId

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
            genai.configure(api_key="AIzaSyAK9Fgpj-PeeDkRk-B5dCZwoNdCMWe6gv0")
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            print(f"Error initializing Gemini API: {e}")
            self.model = None

    def generate_question(self, current_question, previous_responses=None):
        """Generate a risk assessment question with options."""
        if previous_responses is None:
            previous_responses = {}
        
        try:
            if not previous_responses:
                return {
                    "question": {
                        "id": 1,
                        "text": "To what extent do you agree or disagree with the following statement: Given my investment experience, economic context, social commitments, and personal resilience, I am comfortable with short-term market volatility in pursuit of long-term growth.",
                        "options": [
                            {"value": "Strongly Disagree", "text": "Strongly Disagree"},
                            {"value": "Disagree", "text": "Disagree"},
                            {"value": "Neutral", "text": "Neutral"},
                            {"value": "Agree", "text": "Agree"},
                            {"value": "Strongly Agree", "text": "Strongly Agree"}
                        ]
                    },
                    "total_questions": 1
                }
            
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

            return {
                "question": {
                    "id": current_question,
                    "text": response.text.strip(),
                    "options": [
                        {"value": "Strongly Disagree", "text": "Strongly Disagree"},
                        {"value": "Disagree", "text": "Disagree"},
                        {"value": "Neutral", "text": "Neutral"},
                        {"value": "Agree", "text": "Agree"},
                        {"value": "Strongly Agree", "text": "Strongly Agree"}
                    ]
                },
                "total_questions": current_question
            }
        except Exception as e:
            print(f"Error generating question: {e}")

            standard_options = [
                {"value": "Strongly Disagree", "text": "Strongly Disagree"},
                {"value": "Disagree", "text": "Disagree"},
                {"value": "Neutral", "text": "Neutral"},
                {"value": "Agree", "text": "Agree"},
                {"value": "Strongly Agree", "text": "Strongly Agree"}
            ]
            
            fallback_questions = [
                {
                    "id": 1,
                    "text": "To what extent do you agree or disagree with the following statement: I am comfortable making investment decisions that could significantly impact my financial future, even if it means navigating uncertain economic conditions, managing emotional stress, and adapting to changing market trends.",
                    "options": standard_options
                },
                {
                    "id": 2,
                    "text": "To what extent do you agree or disagree with the following statement: I prioritize long-term financial growth over short-term stability, even if it means accepting potential losses in the short run.",
                    "options": standard_options
                },
                {
                    "id": 3,
                    "text": "To what extent do you agree or disagree with the following statement: I have the knowledge and experience to assess investment risks independently and adjust my strategy accordingly.",
                    "options": standard_options
                },
                {
                    "id": 4,
                    "text": "To what extent do you agree or disagree with the following statement: During periods of market downturns, I remain confident in my investment choices and avoid making impulsive financial decisions based on fear or uncertainty.",
                    "options": standard_options
                },
                {
                    "id": 5,
                    "text": "To what extent do you agree or disagree with the following statement: I am willing to allocate a significant portion of my disposable income toward high-risk, high-reward investments, even if it means sacrificing some financial security in the short term.",
                    "options": standard_options
                }
            ]

            question_index = min(current_question - 1, len(previous_responses) % len(fallback_questions))
            question_index = max(0, min(question_index, len(fallback_questions) - 1)) 
            
            return {
                "question": fallback_questions[question_index],
                "total_questions": len(fallback_questions)
            }

    def assess_risk(self, user_id, responses):
        """
        Assess risk profile based on user responses
        
        OCL Constraints:
        pre MinimumResponses: responses->size() >= 3
        pre ValidResponses: responses->forAll(r | Set{'Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'}->includes(r))
        pre ValidUserID: user_id <> null and user_id.size() > 0
        post RiskScoreInRange: (0 <= result.score and result.score <= 100)
        post CorrectProfileMapping: 
            (result.score >= 0 and result.score <= 20 implies result = 'conservative') and
            (result.score > 20 and result.score <= 40 implies result = 'moderate_conservative') and
            (result.score > 40 and result.score <= 60 implies result = 'moderate') and
            (result.score > 60 and result.score <= 80 implies result = 'moderate_aggressive') and
            (result.score > 80 and result.score <= 100 implies result = 'aggressive')
        """
        if not user_id or not isinstance(user_id, (str, ObjectId)) or (isinstance(user_id, str) and len(user_id) == 0):
            raise ValueError("Invalid user ID")

        if len(responses) < 3:
            raise ValueError("A minimum of 3 responses is required for risk assessment")

        valid_responses = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']
        for response in responses.values():
            if response not in valid_responses:
                raise ValueError(f"Invalid response: {response}")

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

        if not (0 <= risk_score <= 100):
            risk_score = max(0, min(100, risk_score))

        if 0 <= risk_score <= 20:
            risk_profile = 'conservative'
        elif 21 <= risk_score <= 40:
            risk_profile = 'moderate_conservative'
        elif 41 <= risk_score <= 60:
            risk_profile = 'moderate'
        elif 61 <= risk_score <= 80:
            risk_profile = 'moderate_aggressive'
        else:
            risk_profile = 'aggressive'

        existing_assessment = get_user_risk_assessment(user_id)
        if existing_assessment:
            created_at = existing_assessment.get('created_at')
            if created_at:
                days_since_creation = (datetime.now() - created_at).days
                if days_since_creation > 30:
                    raise ValueError("Risk assessment can only be modified within 30 days of creation")
        
        self._deactivate_previous_assessments(user_id)
        
        assessment_data = {
            'score': risk_score,
            'profile': risk_profile,
            'responses': responses,
            'risk_weights': self.risk_weights,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'active': True,
            'modification_limit': (datetime.now() + timedelta(days=30))
        }

        store_risk_assessment(user_id, assessment_data)
        return risk_profile
    
    def _deactivate_previous_assessments(self, user_id):
        """Deactivate all previous assessments to maintain SingleActiveAssessment invariant"""
        try:
            from database import risk_assessments_collection
            risk_assessments_collection.update_many(
                {"user_id": ObjectId(user_id), "active": True},
                {"$set": {"active": False}}
            )
            return True
        except Exception as e:
            print(f"Error deactivating previous assessments: {e}")
            return False

    def get_risk_profile(self, user_id):
        assessment = get_user_risk_assessment(user_id)
        if assessment:
            return {
                'score': assessment['score'],
                'profile': assessment['profile'],
                'responses': assessment['responses']
            }
        return None
