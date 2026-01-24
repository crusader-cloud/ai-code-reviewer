from typing import List, Dict, Any, Optional
from app.services.llm_service import get_llm_service
from app.services.static_analyzer import get_static_analyzer


class CodeReviewService:
    """Combined code review service using LLM + static analysis"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.static_analyzer = get_static_analyzer()
    
    def review_code(
        self, 
        code: str, 
        language: str, 
        context: Optional[str] = None,
        use_static_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive code review
        
        Args:
            code: Code to review
            language: Programming language
            context: Additional context about the code
            use_static_analysis: Whether to include static analysis
        
        Returns:
            Dictionary with issues, scores, and summary
        """
        # Get LLM analysis
        llm_result = self.llm_service.analyze_code(code, language, context)
        
        # Get static analysis if enabled
        static_issues = []
        if use_static_analysis:
            static_issues = self.static_analyzer.analyze(code, language)
        
        # Merge issues (deduplicate based on line number and description similarity)
        all_issues = llm_result.get("issues", []) + static_issues
        
        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "suggestion": 2, "info": 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 4))
        
        # Calculate overall score
        scores = llm_result.get("scores", {})
        overall_score = sum(scores.values()) / len(scores) if scores else 7.0
        
        return {
            "issues": all_issues,
            "scores": scores,
            "overall_score": overall_score,
            "summary": llm_result.get("summary", "Code review completed."),
            "total_issues": len(all_issues),
            "critical_issues": len([i for i in all_issues if i.get("severity") == "critical"]),
            "warnings": len([i for i in all_issues if i.get("severity") == "warning"])
        }
    
    def review_diff(
        self,
        diff_content: str,
        file_path: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Review a git diff
        
        Args:
            diff_content: The diff content
            file_path: Path to the file
            language: Programming language
        
        Returns:
            Review results
        """
        return self.llm_service.analyze_diff(diff_content, file_path, language)
    
    def format_review_comment(self, issue: Dict[str, Any]) -> str:
        """Format an issue as a human-readable review comment"""
        severity_emoji = {
            "critical": "🚨",
            "warning": "⚠️",
            "suggestion": "💡",
            "info": "ℹ️"
        }
        
        category_emoji = {
            "bug": "🐛",
            "performance": "⚡",
            "security": "🔒",
            "style": "🎨",
            "maintainability": "🔧"
        }
        
        severity = issue.get("severity", "info")
        category = issue.get("category", "style")
        
        comment = f"{severity_emoji.get(severity, '')} {category_emoji.get(category, '')} "
        comment += f"**{severity.upper()}** - {category.title()}\n\n"
        comment += f"{issue.get('description', 'No description')}\n\n"
        
        if issue.get("suggestion"):
            comment += f"**Suggestion:** {issue['suggestion']}\n\n"
        
        confidence = issue.get("confidence", 0.5)
        if confidence < 0.7:
            comment += f"_Confidence: {confidence:.0%} - Please verify this suggestion_\n"
        
        return comment
    
    def generate_summary_comment(self, review_result: Dict[str, Any]) -> str:
        """Generate a summary comment for the entire review"""
        scores = review_result.get("scores", {})
        overall = review_result.get("overall_score", 7.0)
        total = review_result.get("total_issues", 0)
        critical = review_result.get("critical_issues", 0)
        warnings = review_result.get("warnings", 0)
        
        # Determine overall assessment
        if overall >= 8.5:
            assessment = "✅ Excellent"
        elif overall >= 7.0:
            assessment = "👍 Good"
        elif overall >= 5.0:
            assessment = "⚠️ Needs Improvement"
        else:
            assessment = "🚨 Significant Issues"
        
        comment = f"## 🤖 AI Code Review Summary\n\n"
        comment += f"**Overall Assessment:** {assessment} ({overall:.1f}/10)\n\n"
        
        comment += f"### 📊 Scores\n"
        comment += f"- **Correctness:** {scores.get('correctness', 7.0):.1f}/10\n"
        comment += f"- **Performance:** {scores.get('performance', 7.0):.1f}/10\n"
        comment += f"- **Readability:** {scores.get('readability', 7.0):.1f}/10\n"
        comment += f"- **Maintainability:** {scores.get('maintainability', 7.0):.1f}/10\n\n"
        
        comment += f"### 🔍 Issues Found\n"
        comment += f"- Total: {total}\n"
        comment += f"- Critical: {critical}\n"
        comment += f"- Warnings: {warnings}\n\n"
        
        comment += f"### 📝 Summary\n"
        comment += f"{review_result.get('summary', 'No summary available.')}\n\n"
        
        comment += f"---\n"
        comment += f"_This review was generated by AI. Please use your judgment when applying suggestions._\n"
        
        return comment


def get_code_review_service() -> CodeReviewService:
    """Get code review service instance"""
    return CodeReviewService()
