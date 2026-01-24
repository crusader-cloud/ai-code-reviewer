# AI-Powered GitHub Pull Request Reviewer

An intelligent, automated code review system that acts like a meticulous human reviewer, not just a linter. Built for hackathons and production use.

## 🎯 Features

- **Automated PR Reviews**: Automatically review pull requests via GitHub webhooks
- **Intelligent Analysis**: Combines LLM reasoning with static code analysis
- **Multi-Language Support**: JavaScript, TypeScript, Python, Java, and more
- **Manual Code Review**: Paste code directly for instant AI feedback
- **Learning Loop**: Tracks feedback to improve future reviews
- **Comprehensive Scoring**: Rates code on correctness, performance, readability, and maintainability

## 🏗️ Architecture

```
┌─────────────┐
│   GitHub    │
│  Webhooks   │
└──────┬──────┘
       │
       v
┌─────────────────────────────────────┐
│         FastAPI Backend             │
├─────────────────────────────────────┤
│  ┌──────────┐    ┌──────────────┐  │
│  │ Webhook  │    │ Manual Review│  │
│  │ Handler  │    │   Endpoint   │  │
│  └────┬─────┘    └──────┬───────┘  │
│       │                 │           │
│       v                 v           │
│  ┌─────────────────────────────┐   │
│  │   Code Review Service       │   │
│  ├─────────────────────────────┤   │
│  │  LLM Service  │  Static     │   │
│  │  (GPT/Claude) │  Analyzer   │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   GitHub Service            │   │
│  │   (API Integration)         │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
       │
       v
┌─────────────┐
│  SQLite DB  │
│  (Storage)  │
└─────────────┘
```

## 🗄️ Database Schema

- **users**: GitHub OAuth tokens and user info
- **repositories**: Tracked repositories
- **pull_requests**: PR metadata and review scores
- **review_comments**: Individual code review comments
- **feedback**: User reactions to AI suggestions
- **manual_reviews**: Direct code review submissions

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- GitHub account
- LLM API key (OpenAI, Anthropic, or Google)

### Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd hackathon
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Initialize database**
```bash
alembic upgrade head
```

5. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Deployment

```bash
docker-compose up -d
```

## 📡 API Endpoints

### Manual Code Review
```bash
POST /review/manual
Content-Type: application/json

{
  "code": "def example():\n    return True",
  "language": "python",
  "context": "Optional context about the code"
}
```

### GitHub Webhook
```bash
POST /webhook/github
X-Hub-Signature-256: <signature>

# GitHub automatically sends PR events here
```

### Authentication
```bash
GET /auth/login          # Start OAuth flow
GET /auth/callback       # OAuth callback
GET /auth/user           # Get current user
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App ID | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth Secret | Yes |
| `GITHUB_WEBHOOK_SECRET` | Webhook secret | Yes |
| `OPENAI_API_KEY` | OpenAI API key | If using OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic API key | If using Claude |
| `GOOGLE_API_KEY` | Google API key | If using Gemini |
| `LLM_PROVIDER` | `openai`, `anthropic`, or `google` | Yes |
| `LLM_MODEL` | Model name | Yes |
| `APP_SECRET_KEY` | JWT secret | Yes |

### GitHub Setup

1. Create a GitHub OAuth App:
   - Go to Settings → Developer settings → OAuth Apps
   - Set callback URL to `http://localhost:8000/auth/callback`

2. Create a GitHub Webhook:
   - Go to your repository → Settings → Webhooks
   - Set URL to `http://your-domain.com/webhook/github`
   - Select "Pull requests" event
   - Set content type to `application/json`

## 🎨 Web Interface

A simple web interface is provided at `index.html` for manual code reviews. Open it in a browser to:

- Paste code snippets
- Select programming language
- Get instant AI-powered review feedback

## 📊 Review Output Example

```json
{
  "issues": [
    {
      "severity": "warning",
      "category": "performance",
      "line_number": 15,
      "description": "Inefficient loop - O(n²) complexity",
      "suggestion": "Use a hash map for O(n) lookup",
      "confidence": 0.9
    }
  ],
  "scores": {
    "correctness": 8.5,
    "performance": 6.0,
    "readability": 9.0,
    "maintainability": 7.5
  },
  "overall_score": 7.75,
  "summary": "Code is generally well-written but has performance concerns"
}
```

## 🧠 How It Works

1. **Webhook Trigger**: GitHub sends PR event
2. **Diff Parsing**: Extract changed files and lines
3. **Static Analysis**: Run AST-based checks (syntax, common patterns)
4. **LLM Analysis**: Send code to AI for deep reasoning
5. **Issue Merging**: Combine and deduplicate findings
6. **Comment Posting**: Post inline comments on GitHub
7. **Feedback Loop**: Track user reactions to improve

## 🎯 Stretch Goals

- [ ] Support for more languages (Go, Rust, C++)
- [ ] Custom rule configuration per repository
- [ ] Integration with CI/CD pipelines
- [ ] Slack/Discord notifications
- [ ] Team analytics dashboard
- [ ] Fine-tuned models on historical reviews

## 📝 License

MIT License - feel free to use in your projects!

## 🤝 Contributing

Contributions welcome! This is a hackathon project designed for rapid iteration.

## 🐛 Known Limitations

- SQLite is used for simplicity (use PostgreSQL for production)
- LLM rate limits may affect large PRs
- Static analysis is basic (can be enhanced with dedicated tools)
- No authentication on manual review endpoint (add as needed)

## 📞 Support

For issues or questions, please open a GitHub issue.
