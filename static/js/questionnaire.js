/**
 * Renders a question and its options into the container
 */
function renderQuestion(question) {
    const container = document.getElementById('question-container');
    
    if (!question) {
        container.innerHTML = '<div class="error-message">Error loading question. Please refresh the page.</div>';
        return;
    }
    
    let html = `
        <div class="question">
            <h2>${question.text}</h2>
            ${question.description ? `<p class="question-description">${question.description}</p>` : ''}
        </div>
        <div class="options-container">
    `;
    
    // Check if options is defined and is an array before iterating
    if (question.options && Array.isArray(question.options)) {
        question.options.forEach((option, index) => {
            html += `
                <div class="option">
                    <input type="radio" name="answer" id="option-${index}" value="${option.value}" ${currentResponses[currentQuestion] === option.value ? 'checked' : ''}>
                    <label for="option-${index}" class="option-label">
                        <span class="option-text">${option.text}</span>
                        ${option.description ? `<span class="option-description">${option.description}</span>` : ''}
                    </label>
                </div>
            `;
        });
    } else {
        // Handle case where options are missing or not an array
        html += '<div class="error-message">No options available for this question. Please contact support.</div>';
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// Fetch next question
function fetchQuestion() {
    // Show loading state
    document.getElementById('question-container').innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading question...</p>
        </div>
    `;
    
    // Make API request
    fetch('/generate-question', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            current_question: currentQuestion,
            responses: responses 
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            throw new Error(data.error);
        }
        
        // Ensure data and data.question exist
        if (!data || !data.question) {
            throw new Error('Invalid response format');
        }
        
        // Ensure options exist and are an array
        if (!data.question.options) {
            data.question.options = [];
        }
        
        currentQuestion = data.question.id || currentQuestion;
        totalQuestions = data.total_questions || 10;
        
        // Update UI
        renderQuestion(data.question);
        updateProgress();
    })
    .catch(error => {
        console.error('Error fetching question:', error);
        document.getElementById('question-container').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Error fetching question: ${error.message}. Please try again.</p>
                <button class="btn btn-secondary retry-btn">Retry</button>
            </div>
        `;
        
        // Add retry button functionality
        document.querySelector('.retry-btn').addEventListener('click', fetchQuestion);
    });
} 