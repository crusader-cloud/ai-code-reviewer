const API_BASE = 'http://localhost:8000/api/dashboard';

// Chart instances
let scoresChart, severityChart, activityChart, scoreTrendsChart, categoriesChart, feedbackChart;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadOverviewData();
    loadRecentReviews();
    loadAnalytics(30);
    loadRepositories();

    // Set up period selector
    document.getElementById('trend-period').addEventListener('change', (e) => {
        loadAnalytics(parseInt(e.target.value));
    });
});

// Navigation
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item[data-section]');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            switchSection(section);
        });
    });
}

function switchSection(sectionName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionName}"]`)?.classList.add('active');

    // Update content
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`${sectionName}-section`)?.classList.add('active');

    // Update title
    const titles = {
        'overview': 'Dashboard Overview',
        'reviews': 'Recent Reviews',
        'analytics': 'Trends & Analytics',
        'repositories': 'Repository Statistics'
    };
    document.getElementById('page-title').textContent = titles[sectionName] || 'Dashboard';
}

// Load Overview Data
async function loadOverviewData() {
    try {
        const response = await fetch(`${API_BASE}/stats/overview`);
        const data = await response.json();

        // Update stats cards
        document.getElementById('total-prs').textContent = data.totals.pull_requests;
        document.getElementById('total-manual').textContent = data.totals.manual_reviews;
        document.getElementById('total-comments').textContent = data.totals.comments;
        document.getElementById('avg-score').textContent = data.average_scores.overall.toFixed(1);

        // Update recent activity
        document.getElementById('recent-prs').textContent = data.recent_activity.prs_last_7_days;
        document.getElementById('recent-manual').textContent = data.recent_activity.reviews_last_7_days;

        // Create charts
        createScoresChart(data.average_scores);
        createSeverityChart(data.issue_breakdown);

    } catch (error) {
        console.error('Error loading overview:', error);
    }
}

// Create Scores Chart
function createScoresChart(scores) {
    const ctx = document.getElementById('scoresChart');
    if (scoresChart) scoresChart.destroy();

    scoresChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Correctness', 'Performance', 'Readability', 'Maintainability'],
            datasets: [{
                label: 'Average Scores',
                data: [
                    scores.correctness,
                    scores.performance,
                    scores.readability,
                    scores.maintainability
                ],
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                borderColor: 'rgba(99, 102, 241, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(99, 102, 241, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(99, 102, 241, 1)'
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 10,
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' },
                    pointLabels: { color: '#f1f5f9' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f1f5f9' } }
            }
        }
    });
}

// Create Severity Chart
function createSeverityChart(breakdown) {
    const ctx = document.getElementById('severityChart');
    if (severityChart) severityChart.destroy();

    severityChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Critical', 'Warnings', 'Suggestions', 'Info'],
            datasets: [{
                data: [
                    breakdown.critical,
                    breakdown.warnings,
                    breakdown.suggestions,
                    breakdown.info
                ],
                backgroundColor: [
                    '#ef4444',
                    '#f59e0b',
                    '#3b82f6',
                    '#cbd5e1'
                ],
                borderWidth: 0
            }]
        },
        options: {
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f1f5f9', padding: 15 }
                }
            }
        }
    });
}

// Load Recent Reviews
async function loadRecentReviews() {
    try {
        const response = await fetch(`${API_BASE}/reviews/recent?limit=10`);
        const data = await response.json();

        const container = document.getElementById('reviews-list');
        container.innerHTML = '';

        if (data.reviews.length === 0) {
            container.innerHTML = '<div class="loading">No reviews yet</div>';
            return;
        }

        data.reviews.forEach(review => {
            const item = createReviewItem(review);
            container.appendChild(item);
        });

    } catch (error) {
        console.error('Error loading reviews:', error);
        document.getElementById('reviews-list').innerHTML = '<div class="loading">Error loading reviews</div>';
    }
}

function createReviewItem(review) {
    const div = document.createElement('div');
    div.className = 'review-item';

    const scoreClass = review.overall_score >= 8 ? 'success' : review.overall_score >= 6 ? 'info' : 'warning';
    const statusEmoji = review.status === 'completed' ? '✅' : review.status === 'in_progress' ? '⏳' : '❌';

    div.innerHTML = `
        <div class="review-header">
            <div>
                <div class="review-title">#${review.pr_number} - ${review.title}</div>
                <div class="review-meta">
                    ${statusEmoji} ${review.repository} • by ${review.author} • 
                    ${new Date(review.created_at).toLocaleDateString()}
                </div>
            </div>
            <div class="review-score">${review.overall_score ? review.overall_score.toFixed(1) : 'N/A'}</div>
        </div>
        <div class="review-stats">
            <div class="review-stat">💬 ${review.comment_count} comments</div>
            <div class="review-stat">📅 ${review.reviewed_at ? 'Reviewed' : 'Pending'}</div>
        </div>
    `;

    return div;
}

// Load Analytics
async function loadAnalytics(days) {
    try {
        const [trendsResponse, categoriesResponse, feedbackResponse] = await Promise.all([
            fetch(`${API_BASE}/stats/trends?days=${days}`),
            fetch(`${API_BASE}/stats/categories`),
            fetch(`${API_BASE}/feedback/summary`)
        ]);

        const trends = await trendsResponse.json();
        const categories = await categoriesResponse.json();
        const feedback = await feedbackResponse.json();

        createActivityChart(trends.pr_activity);
        createScoreTrendsChart(trends.score_trends);
        createCategoriesChart(categories.categories);
        createFeedbackChart(feedback.breakdown);

    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// Create Activity Chart
function createActivityChart(data) {
    const ctx = document.getElementById('activityChart');
    if (activityChart) activityChart.destroy();

    activityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => new Date(d.date).toLocaleDateString()),
            datasets: [{
                label: 'Pull Requests',
                data: data.map(d => d.count),
                backgroundColor: 'rgba(99, 102, 241, 0.8)',
                borderColor: 'rgba(99, 102, 241, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                },
                x: {
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f1f5f9' } }
            }
        }
    });
}

// Create Score Trends Chart
function createScoreTrendsChart(data) {
    const ctx = document.getElementById('scoreTrendsChart');
    if (scoreTrendsChart) scoreTrendsChart.destroy();

    scoreTrendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => new Date(d.date).toLocaleDateString()),
            datasets: [{
                label: 'Average Score',
                data: data.map(d => d.score),
                borderColor: 'rgba(16, 185, 129, 1)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                },
                x: {
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f1f5f9' } }
            }
        }
    });
}

// Create Categories Chart
function createCategoriesChart(data) {
    const ctx = document.getElementById('categoriesChart');
    if (categoriesChart) categoriesChart.destroy();

    categoriesChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(c => c.name.charAt(0).toUpperCase() + c.name.slice(1)),
            datasets: [{
                data: data.map(c => c.count),
                backgroundColor: [
                    '#ef4444',
                    '#f59e0b',
                    '#10b981',
                    '#3b82f6',
                    '#a855f7'
                ],
                borderWidth: 0
            }]
        },
        options: {
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f1f5f9', padding: 15 }
                }
            }
        }
    });
}

// Create Feedback Chart
function createFeedbackChart(data) {
    const ctx = document.getElementById('feedbackChart');
    if (feedbackChart) feedbackChart.destroy();

    if (!data || data.length === 0) {
        ctx.getContext('2d').fillStyle = '#cbd5e1';
        ctx.getContext('2d').font = '14px Inter';
        ctx.getContext('2d').textAlign = 'center';
        ctx.getContext('2d').fillText('No feedback data yet', ctx.width / 2, ctx.height / 2);
        return;
    }

    feedbackChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(f => f.type.replace('_', ' ').toUpperCase()),
            datasets: [{
                data: data.map(f => f.count),
                backgroundColor: [
                    '#10b981',
                    '#ef4444',
                    '#3b82f6',
                    '#f59e0b'
                ],
                borderWidth: 0
            }]
        },
        options: {
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f1f5f9', padding: 15 }
                }
            }
        }
    });
}

// Load Repositories
async function loadRepositories() {
    try {
        const response = await fetch(`${API_BASE}/stats/repositories`);
        const data = await response.json();

        const container = document.getElementById('repos-list');
        container.innerHTML = '';

        if (data.repositories.length === 0) {
            container.innerHTML = '<div class="loading">No repositories yet</div>';
            return;
        }

        data.repositories.forEach(repo => {
            const card = createRepoCard(repo);
            container.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading repositories:', error);
        document.getElementById('repos-list').innerHTML = '<div class="loading">Error loading repositories</div>';
    }
}

function createRepoCard(repo) {
    const div = document.createElement('div');
    div.className = 'repo-card';

    div.innerHTML = `
        <div class="repo-name">📦 ${repo.name}</div>
        <div class="repo-stats">
            <div class="repo-stat-item">
                <span class="repo-stat-label">Pull Requests</span>
                <span class="repo-stat-value">${repo.pr_count}</span>
            </div>
            <div class="repo-stat-item">
                <span class="repo-stat-label">Average Score</span>
                <span class="repo-stat-value">${repo.avg_score.toFixed(1)}</span>
            </div>
            <div class="repo-stat-item">
                <span class="repo-stat-label">Issues Found</span>
                <span class="repo-stat-value">${repo.issue_count}</span>
            </div>
        </div>
    `;

    return div;
}

// Refresh Data
function refreshData() {
    const activeSection = document.querySelector('.nav-item.active')?.dataset.section || 'overview';

    switch (activeSection) {
        case 'overview':
            loadOverviewData();
            break;
        case 'reviews':
            loadRecentReviews();
            break;
        case 'analytics':
            const days = parseInt(document.getElementById('trend-period').value);
            loadAnalytics(days);
            break;
        case 'repositories':
            loadRepositories();
            break;
    }

    // Show refresh animation
    const refreshIcon = document.querySelector('.refresh-icon');
    refreshIcon.style.transform = 'rotate(360deg)';
    setTimeout(() => {
        refreshIcon.style.transform = 'rotate(0deg)';
    }, 300);
}
