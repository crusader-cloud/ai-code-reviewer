const API_BASE_URL = 'http://localhost:8000';

document.getElementById('reviewBtn').addEventListener('click', async () => {
    const code = document.getElementById('code').value;
    const language = document.getElementById('language').value;
    const context = document.getElementById('context').value;

    if (!code.trim()) {
        alert('Please enter some code to review');
        return;
    }

    const btn = document.getElementById('reviewBtn');
    const btnText = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.loader');

    // Show loading state
    btn.disabled = true;
    btnText.textContent = 'Analyzing...';
    loader.style.display = 'inline-block';
    document.getElementById('results').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/review/manual`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code,
                language: language,
                context: context || null
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to review code. Make sure the API server is running on http://localhost:8000');
    } finally {
        // Reset button state
        btn.disabled = false;
        btnText.textContent = 'Review Code';
        loader.style.display = 'none';
    }
});

function displayResults(data) {
    // Show results section
    document.getElementById('results').style.display = 'block';
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });

    // Display scores
    document.getElementById('overallScore').textContent = data.overall_score.toFixed(1);
    document.getElementById('correctnessScore').textContent = data.scores.correctness.toFixed(1);
    document.getElementById('performanceScore').textContent = data.scores.performance.toFixed(1);
    document.getElementById('readabilityScore').textContent = data.scores.readability.toFixed(1);
    document.getElementById('maintainabilityScore').textContent = data.scores.maintainability.toFixed(1);

    // Color code scores
    colorCodeScore('overallScore', data.overall_score);
    colorCodeScore('correctnessScore', data.scores.correctness);
    colorCodeScore('performanceScore', data.scores.performance);
    colorCodeScore('readabilityScore', data.scores.readability);
    colorCodeScore('maintainabilityScore', data.scores.maintainability);

    // Display summary
    document.getElementById('summary').textContent = data.summary;

    // Display issue count
    document.getElementById('issueCount').textContent = data.total_issues;

    // Display issues
    const issuesList = document.getElementById('issuesList');
    issuesList.innerHTML = '';

    if (data.issues.length === 0) {
        issuesList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">No issues found! 🎉</p>';
    } else {
        data.issues.forEach(issue => {
            const issueCard = createIssueCard(issue);
            issuesList.appendChild(issueCard);
        });
    }
}

function createIssueCard(issue) {
    const card = document.createElement('div');
    card.className = `issue-card ${issue.severity}`;

    const header = document.createElement('div');
    header.className = 'issue-header';

    const badge = document.createElement('span');
    badge.className = `issue-badge ${issue.severity}`;
    badge.textContent = issue.severity;

    const category = document.createElement('span');
    category.className = 'issue-category';
    category.textContent = getCategoryEmoji(issue.category) + ' ' + issue.category;

    header.appendChild(badge);
    header.appendChild(category);

    if (issue.line_number) {
        const line = document.createElement('span');
        line.className = 'issue-line';
        line.textContent = `Line ${issue.line_number}`;
        header.appendChild(line);
    }

    const description = document.createElement('div');
    description.className = 'issue-description';
    description.textContent = issue.description;

    card.appendChild(header);
    card.appendChild(description);

    if (issue.suggestion) {
        const suggestion = document.createElement('div');
        suggestion.className = 'issue-suggestion';
        suggestion.innerHTML = `<strong>💡 Suggestion:</strong> ${issue.suggestion}`;
        card.appendChild(suggestion);
    }

    return card;
}

function getCategoryEmoji(category) {
    const emojis = {
        'bug': '🐛',
        'performance': '⚡',
        'security': '🔒',
        'style': '🎨',
        'maintainability': '🔧'
    };
    return emojis[category] || '📝';
}

function colorCodeScore(elementId, score) {
    const element = document.getElementById(elementId);
    if (score >= 8.5) {
        element.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    } else if (score >= 7.0) {
        element.style.background = 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)';
    } else if (score >= 5.0) {
        element.style.background = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';
    } else {
        element.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
    }
    element.style.webkitBackgroundClip = 'text';
    element.style.webkitTextFillColor = 'transparent';
    element.style.backgroundClip = 'text';
}

// Example code snippets
const examples = {
    python: `def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total

# This could be optimized using sum()`,
    
    javascript: `function findUser(users, id) {
    for (let i = 0; i < users.length; i++) {
        if (users[i].id == id) {
            return users[i];
        }
    }
    return null;
}`,
    
    java: `public class Example {
    public void processData(List<String> data) {
        for (int i = 0; i < data.size(); i++) {
            System.out.println(data.get(i));
        }
    }
}`
};

// Add example button functionality (optional)
document.getElementById('language').addEventListener('change', (e) => {
    const language = e.target.value;
    if (examples[language] && !document.getElementById('code').value) {
        // Optionally pre-fill with example
        // document.getElementById('code').value = examples[language];
    }
});
