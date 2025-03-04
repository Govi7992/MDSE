import unittest
from unittest.mock import patch, MagicMock
from risk_assessment import RiskAssessor

class TestRiskAssessor(unittest.TestCase):
    def setUp(self):
        with patch('google.generativeai.configure'):  
            self.risk_assessor = RiskAssessor()

    def test_init(self):
        self.assertIsNotNone(self.risk_assessor)
        self.assertEqual(len(self.risk_assessor.risk_profiles), 5)
        self.assertEqual(sum(self.risk_assessor.risk_weights.values()), 1.0)

    def test_generate_first_question(self):
        question = self.risk_assessor.generate_question({})
        self.assertIsInstance(question, str)
        self.assertTrue(question.startswith("To what extent"))

    @patch('google.generativeai.GenerativeModel')
    def test_generate_subsequent_question_success(self, mock_model_class):
        
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "To what extent do you agree or disagree with the following statement: I prefer steady, reliable returns over potentially higher but more volatile returns."
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        
        self.risk_assessor.model = mock_model

        previous_responses = {
            1: "Agree",
            2: "Strongly Agree"
        }
        
        question = self.risk_assessor.generate_question(previous_responses)
        self.assertIsInstance(question, str)
        self.assertTrue(question.startswith("To what extent"))

    @patch('google.generativeai.GenerativeModel')
    def test_generate_subsequent_question_api_failure(self, mock_model_class):
        
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model

        
        self.risk_assessor.model = mock_model

        previous_responses = {
            1: "Agree",
            2: "Strongly Agree"
        }
        
        question = self.risk_assessor.generate_question(previous_responses)
        self.assertIsInstance(question, str)
        
        self.assertTrue(
            any(question == q for q in [
                "To what extent do you agree or disagree with the following statement: I am comfortable making investment decisions that could significantly impact my financial future, even if it means navigating uncertain economic conditions, managing emotional stress, and adapting to changing market trends.",
                "To what extent do you agree or disagree with the following statement: I prioritize long-term financial growth over short-term stability, even if it means accepting potential losses in the short run.",
                "To what extent do you agree or disagree with the following statement: I have the knowledge and experience to assess investment risks independently and adjust my strategy accordingly.",
                "To what extent do you agree or disagree with the following statement: During periods of market downturns, I remain confident in my investment choices and avoid making impulsive financial decisions based on fear or uncertainty.",
                "To what extent do you agree or disagree with the following statement: I am willing to allocate a significant portion of my disposable income toward high-risk, high-reward investments, even if it means sacrificing some financial security in the short term.",
            ])
        )

    def test_assess_risk_conservative(self):
        user_id = "test_user_1"
        responses = {
            1: "Strongly Disagree",
            2: "Disagree",
            3: "Disagree"
        }
        
        profile = self.risk_assessor.assess_risk(user_id, responses)
        self.assertEqual(profile, "conservative")

    def test_assess_risk_aggressive(self):
        user_id = "test_user_2"
        responses = {
            1: "Strongly Agree",
            2: "Strongly Agree",
            3: "Agree"
        }
        
        profile = self.risk_assessor.assess_risk(user_id, responses)
        self.assertEqual(profile, "aggressive")

    def test_get_risk_profile_existing_user(self):
        user_id = "test_user_3"
        responses = {
            1: "Neutral",
            2: "Neutral",
            3: "Neutral"
        }
        
        self.risk_assessor.assess_risk(user_id, responses)
        profile = self.risk_assessor.get_risk_profile(user_id)
        
        self.assertIsNotNone(profile)
        self.assertIn('score', profile)
        self.assertIn('profile', profile)
        self.assertIn('responses', profile)

    def test_get_risk_profile_nonexistent_user(self):
        profile = self.risk_assessor.get_risk_profile("nonexistent_user")
        self.assertIsNone(profile)

    def test_risk_score_calculation(self):
        user_id = "test_user_4"
        responses = {
            1: "Neutral",  
            2: "Agree",    
            3: "Disagree"  
        }
        
        self.risk_assessor.assess_risk(user_id, responses)
        profile = self.risk_assessor.get_risk_profile(user_id)
        
        expected_score = (50 + 75 + 25) / 3
        self.assertEqual(profile['score'], expected_score)

if __name__ == '__main__':
    unittest.main() 
