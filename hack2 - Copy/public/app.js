// ============= STATE MANAGEMENT =============

let currentUser = null;
let currentRepo = null;
let currentPR = null;
let currentReview = null;
let allRepos = [];

// ============= INITIALIZATION =============

document.addEventListener('DOMContentLoaded', async () => {
    // Check for OAuth errors
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('error')) {
        showError('loginError', 'Authentication failed. Please try again.');
    }

    // Check if user is already logged in
    await checkAuth();
});

// ============= AUTHENTICATION =============

async function checkAuth() {
    try {
        const response = await fetch('/api/user');
        if (response.ok) {
            currentUser = await response.json();
            showMainApp();
            loadRepositories();
        } else {
            showLoginScreen();
        }
    } catch (error) {
        showLoginScreen();
    }
}

function loginWithGitHub() {
    window.location.href = '/auth/github';
}

async function logout() {
    try {
        await fetch('/auth/logout');
        currentUser = null;
        currentRepo = null;
        currentPR = null;
        currentReview = null;
        showLoginScreen();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// ============= VIEW MANAGEMENT =============

function showLoginScreen() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

function showMainApp() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    document.getElementById('userInfo').textContent = `Logged in as ${currentUser.login}`;
    showRepoView();
}

function showRepoView() {
    document.getElementById('repoView').classList.remove('hidden');
    document.getElementById('prView').classList.add('hidden');
    document.getElementById('reviewView').classList.add('hidden');
}

function showPRView() {
    document.getElementById('repoView').classList.add('hidden');
    document.getElementById('prView').classList.remove('hidden');
    document.getElementById('reviewView').classList.add('hidden');
}

function showReviewView() {
    document.getElementById('repoView').classList.add('hidden');
    document.getElementById('prView').classList.add('hidden');
    document.getElementById('reviewView').classList.remove('hidden');
}

function showManualReview() {
    currentRepo = null;
    currentPR = null;
    document.getElementById('codeInput').value = '';
    document.getElementById('prInfo').classList.add('hidden');
    document.getElementById('results').innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">📝</div>
      <p>Paste code and analyze</p>
    </div>
  `;
    showReviewView();
}

// ============= REPOSITORY MANAGEMENT =============

async function loadRepositories() {
    const repoList = document.getElementById('repoList');
    repoList.innerHTML = '<div class="loading">Loading repositories...</div>';

    try {
        const response = await fetch('/api/repos');
        if (!response.ok) throw new Error('Failed to fetch repositories');

        allRepos = await response.json();
        displayRepositories(allRepos);
    } catch (error) {
        repoList.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

function displayRepositories(repos) {
    const repoList = document.getElementById('repoList');

    if (repos.length === 0) {
        repoList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📁</div>
        <p>No repositories found</p>
      </div>
    `;
        return;
    }

    repoList.innerHTML = repos.map(repo => `
    <div class="repo-item" onclick="selectRepository('${repo.owner}', '${repo.name}')">
      <div class="repo-name">${repo.name}</div>
      <div class="repo-desc">${repo.description || 'No description'}</div>
      <div class="repo-meta">
        ${repo.language ? `<span>💻 ${repo.language}</span>` : ''}
        ${repo.private ? '<span>🔒 Private</span>' : '<span>🌍 Public</span>'}
        <span>📋 ${repo.open_issues_count} open issues</span>
      </div>
    </div>
  `).join('');
}

function filterRepos() {
    const searchTerm = document.getElementById('repoSearch').value.toLowerCase();
    const filtered = allRepos.filter(repo =>
        repo.name.toLowerCase().includes(searchTerm) ||
        (repo.description && repo.description.toLowerCase().includes(searchTerm))
    );
    displayRepositories(filtered);
}

async function selectRepository(owner, name) {
    currentRepo = { owner, name };
    document.getElementById('prViewTitle').textContent = `Pull Requests - ${owner}/${name}`;
    showPRView();
    await loadPullRequests();
}

// ============= PULL REQUEST MANAGEMENT =============

async function loadPullRequests() {
    if (!currentRepo) return;

    const prList = document.getElementById('prList');
    prList.innerHTML = '<div class="loading">Loading pull requests...</div>';

    const state = document.getElementById('prStateFilter').value;

    try {
        const response = await fetch(
            `/api/repos/${currentRepo.owner}/${currentRepo.name}/pulls?state=${state}`
        );

        if (!response.ok) throw new Error('Failed to fetch pull requests');

        const pulls = await response.json();
        displayPullRequests(pulls);
    } catch (error) {
        prList.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

function displayPullRequests(pulls) {
    const prList = document.getElementById('prList');

    if (pulls.length === 0) {
        prList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📋</div>
        <p>No pull requests found</p>
      </div>
    `;
        return;
    }

    prList.innerHTML = pulls.map(pr => `
    <div class="pr-item" onclick="selectPullRequest(${pr.number})">
      <div class="pr-header">
        <div class="pr-title">${pr.title}</div>
        <div class="pr-number">#${pr.number}</div>
      </div>
      <div class="pr-meta">
        <span class="pr-badge badge-${pr.state}">${pr.state}</span>
        <span>👤 ${pr.user.login}</span>
        <span>📝 ${pr.changed_files} files</span>
        <span>+${pr.additions} -${pr.deletions}</span>
        <span>🕒 ${formatDate(pr.updated_at)}</span>
      </div>
    </div>
  `).join('');
}

async function selectPullRequest(prNumber) {
    if (!currentRepo) return;

    currentPR = prNumber;
    showReviewView();

    // Show loading state
    document.getElementById('codeInput').value = 'Loading PR files...';
    document.getElementById('analyzeBtn').disabled = true;

    try {
        const response = await fetch(
            `/api/repos/${currentRepo.owner}/${currentRepo.name}/pulls/${prNumber}/files`
        );

        if (!response.ok) throw new Error('Failed to fetch PR files');

        const files = await response.json();

        // Combine all file changes
        const code = files
            .filter(f => f.patch)
            .map(f => `// File: ${f.filename}\n// Status: ${f.status}\n// Changes: +${f.additions} -${f.deletions}\n\n${f.patch}`)
            .join('\n\n' + '='.repeat(80) + '\n\n');

        document.getElementById('codeInput').value = code;

        // Detect language from files
        const languages = files.map(f => {
            const ext = f.filename.split('.').pop().toLowerCase();
            const langMap = {
                'js': 'javascript', 'jsx': 'javascript', 'ts': 'typescript',
                'tsx': 'typescript', 'py': 'python', 'java': 'java',
                'go': 'go', 'rs': 'rust', 'cpp': 'cpp', 'cs': 'csharp'
            };
            return langMap[ext] || 'javascript';
        });

        if (languages.length > 0) {
            document.getElementById('language').value = languages[0];
        }

        // Show PR info
        document.getElementById('prInfo').innerHTML = `
      <h3>PR #${prNumber} - ${currentRepo.owner}/${currentRepo.name}</h3>
      <p>${files.length} file(s) changed</p>
    `;
        document.getElementById('prInfo').classList.remove('hidden');

        document.getElementById('analyzeBtn').disabled = false;

        // Show success message
        showError('errorBox', `✅ Loaded ${files.length} file(s) from PR #${prNumber}`);
        setTimeout(() => hideError('errorBox'), 3000);

    } catch (error) {
        document.getElementById('codeInput').value = '';
        showError('errorBox', `Error loading PR: ${error.message}`);
        document.getElementById('analyzeBtn').disabled = false;
    }
}

// ============= CODE ANALYSIS =============

async function analyzeCode() {
    const code = document.getElementById('codeInput').value.trim();
    if (!code) {
        showError('errorBox', 'Please enter code or select a PR to analyze');
        return;
    }

    const btn = document.getElementById('analyzeBtn');
    const originalText = btn.textContent;
    btn.textContent = '🔄 Analyzing...';
    btn.disabled = true;
    hideError('errorBox');

    // Show loading in results
    document.getElementById('results').innerHTML = `
    <div class="loading">
      <div style="font-size: 2rem; margin-bottom: 1rem;">🤖</div>
      <p>AI is reviewing your code...</p>
    </div>
  `;

    try {
        const language = document.getElementById('language').value;
        const response = await fetch('/api/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Analysis failed');
        }

        currentReview = await response.json();
        displayReview(currentReview);

    } catch (error) {
        showError('errorBox', `Analysis error: ${error.message}`);
        document.getElementById('results').innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">❌</div>
        <p>Analysis failed</p>
      </div>
    `;
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

function displayReview(review) {
    const statusClass = review.approved ? 'status-good' : 'status-bad';
    const statusText = review.approved ? '✅ Approved' : '⚠️ Changes Requested';

    let html = `
    <div class="status ${statusClass}">
      <div style="font-weight: 600; margin-bottom: 0.5rem;">${statusText}</div>
      <div style="font-size: 0.9rem; opacity: 0.9;">Severity: ${review.severity}</div>
      <p style="margin-top: 0.5rem;">${review.summary}</p>
    </div>
  `;

    if (review.bugs?.length) {
        html += `<div class="issue issue-bugs"><h3>🐛 Bugs Found</h3>`;
        review.bugs.forEach(b => html += `<p style="margin: 0.25rem 0;">• ${b}</p>`);
        html += `</div>`;
    }

    if (review.security?.length) {
        html += `<div class="issue issue-sec"><h3>🔒 Security Issues</h3>`;
        review.security.forEach(s => html += `<p style="margin: 0.25rem 0;">• ${s}</p>`);
        html += `</div>`;
    }

    if (review.performance?.length) {
        html += `<div class="issue issue-perf"><h3>⚡ Performance Issues</h3>`;
        review.performance.forEach(p => html += `<p style="margin: 0.25rem 0;">• ${p}</p>`);
        html += `</div>`;
    }

    if (review.suggestions?.length) {
        html += `<div class="issue issue-sug"><h3>💡 Suggestions</h3>`;
        review.suggestions.forEach(s => html += `<p style="margin: 0.25rem 0;">• ${s}</p>`);
        html += `</div>`;
    }

    document.getElementById('results').innerHTML = html;

    // Show post button only if we have a PR selected
    if (currentPR && currentRepo) {
        document.getElementById('postBtn').classList.remove('hidden');
    }
}

// ============= GITHUB INTEGRATION =============

async function postToGitHub() {
    if (!currentReview || !currentPR || !currentRepo) {
        showError('errorBox', 'No review or PR selected');
        return;
    }

    const btn = document.getElementById('postBtn');
    const originalText = btn.textContent;
    btn.textContent = '📤 Posting...';
    btn.disabled = true;

    try {
        const response = await fetch(
            `/api/repos/${currentRepo.owner}/${currentRepo.name}/pulls/${currentPR}/comments`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ review: currentReview })
            }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to post comment');
        }

        const result = await response.json();

        // Show success message
        showError('errorBox', '✅ Review posted to GitHub successfully!');
        setTimeout(() => hideError('errorBox'), 5000);

        // Optionally open the comment in a new tab
        if (result.comment_url) {
            window.open(result.comment_url, '_blank');
        }

    } catch (error) {
        showError('errorBox', `Failed to post: ${error.message}`);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// ============= UTILITY FUNCTIONS =============

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.classList.remove('hidden');
}

function hideError(elementId) {
    document.getElementById(elementId).classList.add('hidden');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 30) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}
