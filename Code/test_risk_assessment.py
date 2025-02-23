from risk_assessment import RiskAssessor

def test_ai_question_generation():
    print("\n=== Testing AI Question Generation ===\n")
    risk_assessor = RiskAssessor()
    
    # Test initial question (no previous responses)
    print("Testing initial question:")
    question1 = risk_assessor.generate_question({})
    print(f"Question 1: {question1}\n")

    # Test follow-up questions with different responses
    responses = {}
    
    # Simulate a sequence of questions and responses
    for i in range(3):  # Test 3 follow-up questions
        responses[f'question_{i+1}'] = 'Agree'
        print(f"Testing question after {len(responses)} response(s):")
        print(f"Previous responses: {responses}")
        question = risk_assessor.generate_question(responses)
        print(f"Generated Question: {question}\n")

if __name__ == "__main__":
    test_ai_question_generation()