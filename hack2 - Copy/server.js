require('dotenv').config();
const express = require('express');
const session = require('express-session');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

// Session configuration
app.use(session({
  secret: process.env.SESSION_SECRET || 'dev-secret-change-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: { 
    secure: false, // Set to true in production with HTTPS
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Authentication middleware
const requireAuth = (req, res, next) => {
  if (!req.session.accessToken) {
    return res.status(401).json({ error: 'Not authenticated' });
  }
  next();
};

// ============= AUTHENTICATION ROUTES =============

// GitHub OAuth login
app.get('/auth/github', (req, res) => {
  const clientId = process.env.GITHUB_CLIENT_ID;
  const redirectUri = process.env.GITHUB_CALLBACK_URL;
  const scope = 'repo,read:user';
  
  const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
  res.redirect(githubAuthUrl);
});

// GitHub OAuth callback
app.get('/auth/callback', async (req, res) => {
  const { code } = req.query;
  
  if (!code) {
    return res.redirect('/?error=no_code');
  }

  try {
    // Exchange code for access token
    const tokenResponse = await axios.post(
      'https://github.com/login/oauth/access_token',
      {
        client_id: process.env.GITHUB_CLIENT_ID,
        client_secret: process.env.GITHUB_CLIENT_SECRET,
        code: code,
        redirect_uri: process.env.GITHUB_CALLBACK_URL
      },
      {
        headers: { Accept: 'application/json' }
      }
    );

    const accessToken = tokenResponse.data.access_token;

    if (!accessToken) {
      return res.redirect('/?error=no_token');
    }

    // Get user info
    const userResponse = await axios.get('https://api.github.com/user', {
      headers: { Authorization: `token ${accessToken}` }
    });

    // Store in session
    req.session.accessToken = accessToken;
    req.session.user = {
      login: userResponse.data.login,
      name: userResponse.data.name,
      avatar_url: userResponse.data.avatar_url,
      email: userResponse.data.email
    };

    res.redirect('/');
  } catch (error) {
    console.error('OAuth error:', error.response?.data || error.message);
    res.redirect('/?error=auth_failed');
  }
});

// Logout
app.get('/auth/logout', (req, res) => {
  req.session.destroy();
  res.json({ success: true });
});

// Get current user
app.get('/api/user', requireAuth, (req, res) => {
  res.json(req.session.user);
});

// ============= GITHUB API ROUTES =============

// Get user's repositories
app.get('/api/repos', requireAuth, async (req, res) => {
  try {
    const response = await axios.get('https://api.github.com/user/repos', {
      headers: { 
        Authorization: `token ${req.session.accessToken}`,
        Accept: 'application/vnd.github.v3+json'
      },
      params: {
        sort: 'updated',
        per_page: 100,
        affiliation: 'owner,collaborator,organization_member'
      }
    });

    const repos = response.data.map(repo => ({
      id: repo.id,
      name: repo.name,
      full_name: repo.full_name,
      owner: repo.owner.login,
      description: repo.description,
      private: repo.private,
      html_url: repo.html_url,
      updated_at: repo.updated_at,
      language: repo.language,
      open_issues_count: repo.open_issues_count
    }));

    res.json(repos);
  } catch (error) {
    console.error('Error fetching repos:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ 
      error: 'Failed to fetch repositories' 
    });
  }
});

// Get pull requests for a repository
app.get('/api/repos/:owner/:repo/pulls', requireAuth, async (req, res) => {
  const { owner, repo } = req.params;
  const { state = 'open' } = req.query;

  try {
    const response = await axios.get(
      `https://api.github.com/repos/${owner}/${repo}/pulls`,
      {
        headers: { 
          Authorization: `token ${req.session.accessToken}`,
          Accept: 'application/vnd.github.v3+json'
        },
        params: { state, per_page: 50 }
      }
    );

    const pulls = response.data.map(pr => ({
      number: pr.number,
      title: pr.title,
      state: pr.state,
      user: {
        login: pr.user.login,
        avatar_url: pr.user.avatar_url
      },
      created_at: pr.created_at,
      updated_at: pr.updated_at,
      html_url: pr.html_url,
      body: pr.body,
      head: {
        ref: pr.head.ref,
        sha: pr.head.sha
      },
      base: {
        ref: pr.base.ref
      },
      mergeable_state: pr.mergeable_state,
      additions: pr.additions,
      deletions: pr.deletions,
      changed_files: pr.changed_files
    }));

    res.json(pulls);
  } catch (error) {
    console.error('Error fetching PRs:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ 
      error: 'Failed to fetch pull requests' 
    });
  }
});

// Get files changed in a pull request
app.get('/api/repos/:owner/:repo/pulls/:number/files', requireAuth, async (req, res) => {
  const { owner, repo, number } = req.params;

  try {
    const response = await axios.get(
      `https://api.github.com/repos/${owner}/${repo}/pulls/${number}/files`,
      {
        headers: { 
          Authorization: `token ${req.session.accessToken}`,
          Accept: 'application/vnd.github.v3+json'
        }
      }
    );

    res.json(response.data);
  } catch (error) {
    console.error('Error fetching PR files:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ 
      error: 'Failed to fetch PR files' 
    });
  }
});

// ============= AI REVIEW ROUTES =============

// Analyze code with AI
app.post('/api/review', requireAuth, async (req, res) => {
  const { code, language = 'javascript' } = req.body;

  if (!code) {
    return res.status(400).json({ error: 'Code is required' });
  }

  try {
    const response = await axios.post(
      'https://api.anthropic.com/v1/messages',
      {
        model: 'claude-sonnet-4-20250514',
        max_tokens: 2000,
        messages: [{
          role: 'user',
          content: `Review this ${language} code as a senior developer. Respond ONLY with valid JSON in this exact format:
{
  "summary": "brief assessment of the code quality and main findings",
  "bugs": ["bug1", "bug2"],
  "performance": ["perf1", "perf2"],
  "style": ["style1", "style2"],
  "security": ["sec1", "sec2"],
  "suggestions": ["sug1", "sug2"],
  "severity": "low|medium|high",
  "approved": true/false
}

Code to review:
${code}`
        }]
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': process.env.ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01'
        }
      }
    );

    const text = response.data.content[0].text.replace(/```json|```/g, '').trim();
    const review = JSON.parse(text);
    
    res.json(review);
  } catch (error) {
    console.error('Error analyzing code:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ 
      error: 'Failed to analyze code',
      details: error.message
    });
  }
});

// Post review comment to GitHub PR
app.post('/api/repos/:owner/:repo/pulls/:number/comments', requireAuth, async (req, res) => {
  const { owner, repo, number } = req.params;
  const { review } = req.body;

  if (!review) {
    return res.status(400).json({ error: 'Review data is required' });
  }

  try {
    let comment = `## 🤖 AI Code Review\n\n`;
    comment += `**Status:** ${review.approved ? '✅ Approved' : '⚠️ Changes Requested'}\n`;
    comment += `**Severity:** ${review.severity}\n`;
    comment += `**Summary:** ${review.summary}\n\n`;
    
    if (review.bugs?.length) {
      comment += `### 🐛 Bugs\n${review.bugs.map(b => `- ${b}`).join('\n')}\n\n`;
    }
    if (review.security?.length) {
      comment += `### 🔒 Security\n${review.security.map(s => `- ${s}`).join('\n')}\n\n`;
    }
    if (review.performance?.length) {
      comment += `### ⚡ Performance\n${review.performance.map(p => `- ${p}`).join('\n')}\n\n`;
    }
    if (review.suggestions?.length) {
      comment += `### 💡 Suggestions\n${review.suggestions.map(s => `- ${s}`).join('\n')}\n`;
    }

    const response = await axios.post(
      `https://api.github.com/repos/${owner}/${repo}/issues/${number}/comments`,
      { body: comment },
      {
        headers: {
          Authorization: `token ${req.session.accessToken}`,
          Accept: 'application/vnd.github.v3+json',
          'Content-Type': 'application/json'
        }
      }
    );

    res.json({ success: true, comment_url: response.data.html_url });
  } catch (error) {
    console.error('Error posting comment:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ 
      error: 'Failed to post comment to GitHub' 
    });
  }
});

// ============= START SERVER =============

app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(`📝 Make sure to configure .env file with your credentials`);
});
