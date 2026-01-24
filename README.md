PR Reviewer Standalone – Setup & Usage Guide

This tool helps you fetch repository data and analyze code using Gemini AI.
Follow the steps below carefully to use it correctly.

🚀 Getting Started
Step 1: Open pr-reviewer-standalone

First, open the pr-reviewer-standalone application.

This is where authentication and repository fetching happens.

🔑 Step 2: Enter Required Tokens

You will be asked to enter two tokens:

1️⃣ GitHub PAT (Personal Access Token)

Enter your GitHub Personal Access Token (PAT).

This token is used to:

Authenticate with GitHub

Fetch all repositories linked to your account

2️⃣ Gemini API Key

After entering the PAT, input your Gemini API Key.

This key is used for AI-based code analysis.

✅ Once both tokens are entered, the tool will automatically fetch all repositories.

📦 Repository Fetching

The tool will fetch repository data successfully.

❌ No analysis is shown at this stage

❌ No analysis happens inside this HTML page

This step is only for authentication and data fetching.

🔍 Step 3: Code Analysis (Important)

To analyze code:

Open index.html

Paste the code you want to analyze into the input area

Run the analysis

➡️ The Gemini AI analysis output will be displayed inside index.html.

⚠️ Important Notes

🔒 Do NOT upload your PAT or Gemini API key to GitHub

📄 Use environment variables or local input only

🔁 Regenerate tokens immediately if leaked

✅ Summary Flow

Open pr-reviewer-standalone

Enter GitHub PAT

Enter Gemini API Key

Repositories are fetched

Open index.html

Paste code

Get AI analysis
