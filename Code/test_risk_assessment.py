import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from risk_assessment import RiskAssessor

class TestRiskAssessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.risk_assessor = RiskAssessor()
        
        # Sample test responses
        self.conservative_responses = {
            'investment_experience': 'Beginner',
            'time_horizon': 'Short-term',
            'risk_tolerance': 'Low',
            'financial_goals': 'Preservation'
        }
        
        self.aggressive_responses = {
            'investment_experience': 'Expert',
            'time_horizon': 'Very Long-term',
            'risk_tolerance': 'Very High',
            'financial_goals': 'Aggressive Growth'
        }
        
        self.moderate_responses = {
            'investment_experience': 'Intermediate',
            'time_horizon': 'Medium-term',
            'risk_tolerance': 'Medium',
            'financial_goals': 'Balanced Growth'
        }

    def test_initialization(self):
        """Test proper initialization of RiskAssessor"""
        # Test risk profiles initialization
        self.assertIsNotNone(self.risk_assessor.risk_profiles)
        self.assertIn('conservative', self.risk_assessor.risk_profiles)
        self.assertIn('moderate', self.risk_assessor.risk_profiles)
        self.assertIn('aggressive', self.risk_assessor.risk_profiles)
        
        # Test risk weights
        weights_sum = sum(self.risk_assessor.risk_weights.values())
        self.assertAlmostEqual(weights_sum, 1.0)
        
        # Test fallback questions
        self.assertIsNotNone(self.risk_assessor.fallback_questions)
        self.assertTrue(len(self.risk_assessor.fallback_questions) > 0)

    def test_assess_risk_conservative(self):
        """Test risk assessment for conservative profile"""
        user_id = "test_user_1"
        profile = self.risk_assessor.assess_risk(user_id, self.conservative_responses)
        
        self.assertEqual(profile, 'conservative')
        
        # Verify stored profile
        stored_profile = self.risk_assessor.get_risk_profile(user_id)
        self.assertIsNotNone(stored_profile)
        self.assertEqual(stored_profile['profile'], 'conservative')
        self.assertLessEqual(stored_profile['score'], 30)

    def test_assess_risk_aggressive(self):
        """Test risk assessment for aggressive profile"""
        user_id = "test_user_2"
        profile = self.risk_assessor.assess_risk(user_id, self.aggressive_responses)
        
        self.assertEqual(profile, 'aggressive')
        
        stored_profile = self.risk_assessor.get_risk_profile(user_id)
        self.assertEqual(stored_profile['profile'], 'aggressive')
        self.assertGreaterEqual(stored_profile['score'], 81)

    def test_assess_risk_moderate(self):
        """Test risk assessment for moderate profile"""
        user_id = "test_user_3"
        profile = self.risk_assessor.assess_risk(user_id, self.moderate_responses)
        
        self.assertEqual(profile, 'moderate')
        
        stored_profile = self.risk_assessor.get_risk_profile(user_id)
        self.assertTrue(46 <= stored_profile['score'] <= 65)

    def test_missing_responses(self):
        """Test handling of missing responses"""
        user_id = "test_user_4"
        incomplete_responses = {
            'investment_experience': 'Intermediate'
        }
        
        profile = self.risk_assessor.assess_risk(user_id, incomplete_responses)
        self.assertEqual(profile, 'moderate')  # Default to moderate

    def test_invalid_responses(self):
        """Test handling of invalid response values"""
        user_id = "test_user_5"
        invalid_responses = {
            'investment_experience': 'Invalid',
            'time_horizon': 'Unknown',
            'risk_tolerance': 'None',
            'financial_goals': 'Other'
        }
        
        profile = self.risk_assessor.assess_risk(user_id, invalid_responses)
        self.assertEqual(profile, 'moderate')  # Default to moderate

    def test_profile_storage(self):
        """Test profile storage and retrieval"""
        user_id = "test_user_6"
        self.risk_assessor.assess_risk(user_id, self.moderate_responses)
        
        stored_profile = self.risk_assessor.get_risk_profile(user_id)
        
        self.assertIsNotNone(stored_profile)
        self.assertIn('score', stored_profile)
        self.assertIn('profile', stored_profile)
        self.assertIn('responses', stored_profile)
        self.assertIn('timestamp', stored_profile)
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(stored_profile['timestamp'])
        self.assertIsInstance(timestamp, datetime)

    def test_nonexistent_profile(self):
        """Test retrieval of non-existent profile"""
        profile = self.risk_assessor.get_risk_profile("nonexistent_user")
        self.assertIsNone(profile)

    @patch('google.generativeai.GenerativeModel')
    def test_generate_question_llm(self, mock_model):
        """Test question generation using LLM"""
        # Mock LLM response
        mock_instance = Mock()
        mock_instance.generate_content.return_value.text = "Test question?"
        mock_model.return_value = mock_instance
        
        # Test first question
        question = self.risk_assessor.generate_question({})
        self.assertIsInstance(question, str)
        self.assertGreater(len(question), 0)
        
        # Test follow-up question
        previous_responses = {1: "Experienced"}
        question = self.risk_assessor.generate_question(previous_responses)
        self.assertIsInstance(question, str)
        self.assertGreater(len(question), 0)

    def test_generate_question_fallback(self):
        """Test fallback question generation when LLM is unavailable"""
        # Disable LLM
        self.risk_assessor.model = None
        
        # Test first question
        question = self.risk_assessor.generate_question({})
        self.assertIn(question, self.risk_assessor.fallback_questions)
        
        # Test subsequent questions
        for i in range(1, len(self.risk_assessor.fallback_questions)):
            previous_responses = {j: "Response" for j in range(i)}
            question = self.risk_assessor.generate_question(previous_responses)
            self.assertIn(question, self.risk_assessor.fallback_questions)

    def test_risk_weights(self):
        """Test risk weight calculations"""
        user_id = "test_user_7"
        # Test that each factor contributes proportionally to the final score
        for factor in self.risk_assessor.risk_weights:
            responses = {
                'investment_experience': 'Beginner',
                'time_horizon': 'Short-term',
                'risk_tolerance': 'Low',
                'financial_goals': 'Preservation'
            }
            responses[factor] = 'Expert'  # Change one factor to high value
            
            profile = self.risk_assessor.assess_risk(user_id, responses)
            stored_profile = self.risk_assessor.get_risk_profile(user_id)
            
            # Verify the score increased due to the high-value factor
            self.assertGreater(stored_profile['score'], 20)

if __name__ == '__main__':
    unittest.main() 