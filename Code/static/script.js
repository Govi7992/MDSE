let currentQuestionIndex = 0;
let userResponses = {};
const userId = 'user_' + Date.now();  // Generate a unique user ID

function startAssessment() {
    console.log("Starting assessment...");
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('question-container').style.display = 'block';
    displayQuestion();
}

function restartAssessment() {
    console.log("Restarting assessment...");
    currentQuestionIndex = 0;
    userResponses = {};
    document.getElementById('results').style.display = 'none';
    document.getElementById('welcome-screen').style.display = 'block';
}

function updateProgress() {
    const progress = ((currentQuestionIndex + 1) / 10) * 100;
    document.getElementById('progress').style.width = `${progress}%`;
    document.getElementById('question-number').textContent = `Question ${currentQuestionIndex + 1} of 10`;
}

async function displayQuestion() {
    console.log(`Displaying question ${currentQuestionIndex + 1}...`);
    updateProgress();
    const questionElement = document.getElementById('question');
    const optionsElement = document.getElementById('options');

    if (currentQuestionIndex < 10) {
        showLoading(true);
        try {
            const response = await fetch('/generate-question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ previous_responses: userResponses })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('API Response:', data);

            if (data.question) {
                questionElement.textContent = data.question;
                displayOptions(optionsElement);
            } else if (data.error) {
                console.error('API Error:', data.error);
                questionElement.textContent = "Error: Could not generate question. Please try again.";
            } else {
                console.error('No question returned from API');
                questionElement.textContent = "Error: No question returned.";
            }
        } catch (error) {
            console.error('Error fetching question:', error);
            questionElement.textContent = "Error generating question. Please refresh the page and try again.";
        } finally {
            showLoading(false);
        }
    } else {
        await submitResponses();
    }
}

function displayOptions(optionsElement) {
    const options = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];
    optionsElement.innerHTML = options.map(option => `
        <label class="option-label">
            <input type="radio" name="response" value="${option}">
            <span>${option}</span>
        </label>
    `).join('');
    console.log("Options displayed:", options);
}

async function nextQuestion() {
    const selectedOption = document.querySelector('input[name="response"]:checked');
    if (!selectedOption) {
        showError("Please select an option before proceeding.");
        return;
    }

    userResponses[`question_${currentQuestionIndex + 1}`] = selectedOption.value;
    console.log(`User response recorded: ${selectedOption.value}`);
    currentQuestionIndex++;
    
    if (currentQuestionIndex < 10) {
        displayQuestion();
    } else {
        await submitResponses();
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(errorDiv, document.getElementById('question-container'));
    
    setTimeout(() => errorDiv.remove(), 3000);
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

async function submitResponses() {
    showLoading(true);
    console.log("Submitting responses:", userResponses);
    try {
        const response = await fetch('/api/assess-risk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                responses: userResponses
            })
        });
        
        const data = await response.json();
        console.log('Assessment results:', data);
        displayResults(data);
    } catch (error) {
        console.error('Error submitting responses:', error);
        showError('Error submitting responses');
    } finally {
        showLoading(false);
    }
}

function displayResults(results) {
    document.getElementById('question-container').style.display = 'none';
    const resultsDiv = document.getElementById('results');
    resultsDiv.style.display = 'block';
    
    document.getElementById('risk-profile').textContent = `Risk Profile: ${results.risk_profile}`;
    document.getElementById('risk-score').textContent = `Risk Score: ${results.risk_score}`;
    
    const detailedResponses = document.getElementById('detailed-responses');
    detailedResponses.innerHTML = Object.entries(results.detailed_responses)
        .map(([question, answer]) => `
            <div class="response-item">
                <p class="question-text">${question}</p>
                <p class="answer-text">${answer}</p>
            </div>
        `).join('');
}

// Initialize the welcome screen
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('welcome-screen').style.display = 'block'; // Ensure this element exists
    document.getElementById('question-container').style.display = 'none'; // Ensure this element exists
    document.getElementById('results').style.display = 'none'; // Ensure this element exists
});