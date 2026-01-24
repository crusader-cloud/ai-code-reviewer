# 🤖 AI GitHub PR Reviewer

An AI-powered GitHub Pull Request reviewer that automatically analyzes code for bugs, security issues, performance problems, and provides intelligent suggestions using Claude AI.

## ✨ Features

- 🔐 **GitHub OAuth Authentication** - Secure login with your GitHub account
- 📚 **Repository Browser** - Browse all your accessible repositories
- 📋 **PR Selector** - View and select pull requests to review
- 🤖 **AI-Powered Analysis** - Automated code review using Claude Sonnet 4
- ✍️ **Manual Code Review** - Paste any code snippet for instant analysis
- 💬 **GitHub Integration** - Post review comments directly to PRs
- 🎨 **Modern UI** - Beautiful, responsive interface with dark mode

## 🚀 Quick Start

### Prerequisites

- Node.js (v14 or higher)
- GitHub account
- Anthropic API key

### 1. Clone and Install

```bash
cd hack2
npm install
```

### 2. Set Up GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **"New OAuth App"**
3. Fill in the details:
   - **Application name**: AI PR Reviewer (or any name)
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:3000/auth/callback`
4. Click **"Register application"**
5. Copy the **Client ID** and **Client Secret**

### 3. Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key and copy it

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_CALLBACK_URL=http://localhost:3000/auth/callback

ANTHROPIC_API_KEY=your_anthropic_api_key_here

SESSION_SECRET=your_random_session_secret_here
PORT=3000
```

**Important**: Generate a secure random string for `SESSION_SECRET`. You can use:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### 5. Start the Server

```bash
npm start
```

The application will be available at `http://localhost:3000`

## 📖 Usage Guide

### Reviewing Pull Requests

1. **Login**: Click "Login with GitHub" and authorize the app
2. **Browse Repositories**: Select a repository from your list
3. **Select PR**: Choose a pull request to review
4. **Analyze**: The code is automatically loaded - click "Analyze Code"
5. **Review Results**: View AI-generated review with bugs, security issues, and suggestions
6. **Post to GitHub**: Click "Post to GitHub" to add the review as a comment

### Manual Code Review

1. Click the **✍️** floating button (bottom right)
2. Select the programming language
3. Paste your code
4. Click "Analyze Code"
5. View the AI-generated review

## 🔧 API Endpoints

### Authentication
- `GET /auth/github` - Initiate GitHub OAuth flow
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout user
- `GET /api/user` - Get current user info

### GitHub Integration
- `GET /api/repos` - List user's repositories
- `GET /api/repos/:owner/:repo/pulls` - List PRs for a repository
- `GET /api/repos/:owner/:repo/pulls/:number/files` - Get PR file changes
- `POST /api/repos/:owner/:repo/pulls/:number/comments` - Post review comment

### AI Review
- `POST /api/review` - Analyze code with AI

## 🎯 Review Categories

The AI analyzes code across multiple dimensions:

- 🐛 **Bugs** - Logic errors, null pointer issues, edge cases
- 🔒 **Security** - Vulnerabilities, injection risks, authentication issues
- ⚡ **Performance** - Inefficient algorithms, memory leaks, optimization opportunities
- 💡 **Suggestions** - Best practices, code style, maintainability improvements

## 🛠️ Tech Stack

- **Backend**: Node.js, Express
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Authentication**: GitHub OAuth 2.0
- **AI**: Anthropic Claude Sonnet 4
- **Session Management**: express-session

## 📝 Project Structure

```
hack2/
├── server.js              # Express server with API endpoints
├── package.json           # Node.js dependencies
├── .env                   # Environment variables (create this)
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── public/               # Frontend files
    ├── index.html        # Main HTML
    ├── styles.css        # Styling
    └── app.js            # Client-side JavaScript
```

## 🔒 Security Notes

- Never commit `.env` file to version control
- Use strong, random session secrets in production
- GitHub tokens are stored in server-side sessions only
- API keys are never exposed to the client

## 🐛 Troubleshooting

### "Authentication failed" error
- Verify your GitHub OAuth credentials in `.env`
- Ensure callback URL matches exactly: `http://localhost:3000/auth/callback`

### "Failed to analyze code" error
- Check your Anthropic API key is valid
- Ensure you have API credits available

### "Failed to fetch repositories" error
- Verify your GitHub token has `repo` and `read:user` scopes
- Check if you're logged in correctly

## 📄 License

MIT

## 🤝 Contributing

This is an MVP project. Feel free to extend it with:
- Webhook support for automatic PR reviews
- Custom review rules and configurations
- Multiple AI model support
- Review history and analytics
- Team collaboration features

---

Built with ❤️ using Claude AI
