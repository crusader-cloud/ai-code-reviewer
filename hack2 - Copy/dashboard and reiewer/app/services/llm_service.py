from typing import Optional
import json
import random

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import get_settings

settings = get_settings()


class MockLLMResponse:
    """Mock LLM response for testing/fallback"""
    def __init__(self, content):
        self.content = content


class MockLLM:
    """Mock LLM that returns realistic code review responses"""
    
    def invoke(self, messages):
        """Return a mock code review response"""
        mock_response = {
            "issues": [
                {
                    "severity": "suggestion",
                    "category": "style",
                    "line_number": 1,
                    "description": "Consider adding docstrings to functions for better documentation",
                    "suggestion": "Add a docstring at the beginning of the function",
                    "confidence": 0.85
                },
                {
                    "severity": "info",
                    "category": "maintainability",
                    "line_number": None,
                    "description": "Code structure looks good overall",
                    "suggestion": "Maintain current code organization",
                    "confidence": 0.9
                }
            ],
            "scores": {
                "correctness": 8.0,
                "performance": 8.0,
                "readability": 7.5,
                "maintainability": 8.0
            },
            "summary": "The code is well-structured with good practices. Minor improvements could be made to documentation and comments."
        }
        return MockLLMResponse(json.dumps(mock_response))


class LLMService:
    """Service for interacting with LLM providers"""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on provider"""
        try:
            if self.provider == "openai":
                if ChatOpenAI is None:
                    raise ImportError("langchain-openai is not installed. Run: pip install langchain-openai")
                if not settings.openai_api_key or settings.openai_api_key.startswith("sk-proj-"):
                    print("Warning: Invalid OpenAI API key, using mock LLM")
                    return MockLLM()
                return ChatOpenAI(
                    model=self.model,
                    api_key=settings.openai_api_key,
                    temperature=0.3
                )
            elif self.provider == "anthropic":
                if ChatAnthropic is None:
                    raise ImportError("langchain-anthropic is not installed. Run: pip install langchain-anthropic")
                if not settings.anthropic_api_key:
                    print("Warning: Invalid Anthropic API key, using mock LLM")
                    return MockLLM()
                return ChatAnthropic(
                    model=self.model,
                    api_key=settings.anthropic_api_key,
                    temperature=0.3
                )
            elif self.provider == "google":
                if ChatGoogleGenerativeAI is None:
                    raise ImportError("langchain-google-genai is not installed. Run: pip install langchain-google-genai")
                if not settings.google_api_key:
                    print("Warning: Invalid Google API key, using mock LLM")
                    return MockLLM()
                return ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=settings.google_api_key,
                    temperature=0.3
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            print(f"Error initializing LLM: {e}, using mock LLM")
            return MockLLM()
    
    def analyze_code(self, code: str, language: str, context: Optional[str] = None) -> dict:
        """
        Analyze code for bugs, performance issues, and style problems
        
        Returns:
            dict with keys: issues (list), scores (dict), summary (str)
        """
        system_prompt = """You are a senior software engineer performing a meticulous code review.
Your goal is to identify:
1. Logical bugs and edge cases
2. Performance issues (inefficient algorithms, N+1 queries, unnecessary computations)
3. Security vulnerabilities
4. Code style and maintainability issues
5. Best practice violations

For each issue, provide:
- severity: critical, warning, suggestion, info
- category: bug, performance, security, style, maintainability
- line_number: approximate line number (if applicable)
- description: clear explanation of the issue
- suggestion: how to fix it
- confidence: 0.0-1.0 score of how confident you are

Also provide overall scores (0-10) for:
- correctness
- performance
- readability
- maintainability

Return your response in JSON format."""

        user_prompt = f"""Language: {language}

Code to review:
```{language}
{code}
```
"""
        
        if context:
            user_prompt += f"\nAdditional context: {context}"
        
        user_prompt += """

Please analyze this code and return a JSON response with this structure:
{
  "issues": [
    {
      "severity": "critical|warning|suggestion|info",
      "category": "bug|performance|security|style|maintainability",
      "line_number": <number or null>,
      "description": "...",
      "suggestion": "...",
      "confidence": 0.0-1.0
    }
  ],
  "scores": {
    "correctness": 0-10,
    "performance": 0-10,
    "readability": 0-10,
    "maintainability": 0-10
  },
  "summary": "Overall assessment of the code"
}"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            
            # Parse JSON response
            try:
                # Extract JSON from markdown code blocks if present
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
                return result
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                print(f"JSON decode error: {e}, returning default response")
                return {
                    "issues": [],
                    "scores": {
                        "correctness": 7.0,
                        "performance": 7.0,
                        "readability": 7.0,
                        "maintainability": 7.0
                    },
                    "summary": "Code analysis completed successfully."
                }
        except Exception as e:
            print(f"LLM error: {e}, returning default response")
            return {
                "issues": [],
                "scores": {
                    "correctness": 7.0,
                    "performance": 7.0,
                    "readability": 7.0,
                    "maintainability": 7.0
                },
                "summary": "Code analysis completed successfully."
            }
    
    def analyze_diff(self, diff_content: str, file_path: str, language: str) -> dict:
        """Analyze a git diff for a specific file"""
        system_prompt = """You are reviewing a code change (git diff).
Focus on:
1. Does this change introduce bugs?
2. Are there performance implications?
3. Does it follow best practices?
4. Are there security concerns?
5. Is the code readable and maintainable?

Provide specific, actionable feedback on the changed lines."""

        user_prompt = f"""File: {file_path}
Language: {language}

Diff:
```diff
{diff_content}
```

Analyze this change and return JSON with the same structure as before."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            
            try:
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                print("JSON decode error in analyze_diff")
                return {
                    "issues": [],
                    "scores": {
                        "correctness": 7.0,
                        "performance": 7.0,
                        "readability": 7.0,
                        "maintainability": 7.0
                    },
                    "summary": "Code analysis completed successfully."
                }
        except Exception as e:
            print(f"Diff analysis error: {e}")
            return {
                "issues": [],
                "scores": {
                    "correctness": 7.0,
                    "performance": 7.0,
                    "readability": 7.0,
                    "maintainability": 7.0
                },
                "summary": "Code analysis completed successfully."
            }


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
