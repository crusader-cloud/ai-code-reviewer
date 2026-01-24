from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from datetime import datetime
import hmac
import hashlib
import json

from app.db.session import get_db
from app.db.models import Repository, PullRequest, ReviewComment, ReviewStatus, User
from app.services.github_service import get_github_service
from app.services.review_service import get_code_review_service
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify that the payload was sent from GitHub"""
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        settings.github_webhook_secret.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handle GitHub webhook events for pull requests
    
    This endpoint receives PR events and triggers automated reviews.
    """
    # Get raw body for signature verification
    payload_body = await request.body()
    
    # Verify webhook signature
    if not verify_signature(payload_body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse payload
    payload = await request.json()
    
    # Only handle pull_request events
    event_type = request.headers.get("X-GitHub-Event")
    if event_type != "pull_request":
        return {"message": "Event type not supported"}
    
    action = payload.get("action")
    
    # Only process opened and synchronize (new commits) actions
    if action not in ["opened", "synchronize"]:
        return {"message": f"Action '{action}' not processed"}
    
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    
    # Get repository from database
    repo = db.query(Repository).filter(
        Repository.github_repo_id == repo_data["id"]
    ).first()
    
    if not repo or not repo.is_active:
        return {"message": "Repository not registered or inactive"}
    
    # Get user's access token
    user = db.query(User).filter(User.id == repo.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create or update PR record
    pr = db.query(PullRequest).filter(
        PullRequest.github_pr_id == pr_data["id"]
    ).first()
    
    if not pr:
        pr = PullRequest(
            repository_id=repo.id,
            github_pr_id=pr_data["id"],
            pr_number=pr_data["number"],
            title=pr_data["title"],
            author=pr_data["user"]["login"],
            status=ReviewStatus.IN_PROGRESS,
            files_changed=pr_data.get("changed_files", 0),
            lines_added=pr_data.get("additions", 0),
            lines_deleted=pr_data.get("deletions", 0)
        )
        db.add(pr)
        db.commit()
        db.refresh(pr)
    else:
        pr.status = ReviewStatus.IN_PROGRESS
        db.commit()
    
    try:
        # Initialize services
        github_service = get_github_service(user.access_token)
        review_service = get_code_review_service()
        
        # Get PR diffs
        diffs = github_service.get_pr_diff(repo.full_name, pr.pr_number)
        
        all_issues = []
        total_scores = {"correctness": 0, "performance": 0, "readability": 0, "maintainability": 0}
        file_count = 0
        
        # Review each file
        for file_path, diff_content in diffs.items():
            language = github_service.detect_language(file_path)
            
            if language == "unknown":
                continue
            
            # Perform review
            result = review_service.review_diff(diff_content, file_path, language)
            
            # Accumulate scores
            for key in total_scores:
                total_scores[key] += result.get("scores", {}).get(key, 7.0)
            file_count += 1
            
            # Store issues as comments
            for issue in result.get("issues", []):
                comment = ReviewComment(
                    pull_request_id=pr.id,
                    file_path=file_path,
                    line_number=issue.get("line_number"),
                    comment_text=review_service.format_review_comment(issue),
                    severity=issue.get("severity", "info"),
                    category=issue.get("category", "style"),
                    confidence_score=issue.get("confidence", 0.5),
                    suggested_fix=issue.get("suggestion")
                )
                db.add(comment)
                all_issues.append(issue)
                
                # Post comment to GitHub (only for high confidence issues)
                if issue.get("confidence", 0) >= 0.7 and issue.get("line_number"):
                    try:
                        github_comment_id = github_service.post_review_comment(
                            repo.full_name,
                            pr.pr_number,
                            review_service.format_review_comment(issue),
                            pr_data["head"]["sha"],
                            file_path,
                            issue["line_number"]
                        )
                        if github_comment_id:
                            comment.github_comment_id = github_comment_id
                    except Exception as e:
                        print(f"Failed to post comment: {e}")
        
        # Calculate average scores
        if file_count > 0:
            for key in total_scores:
                total_scores[key] /= file_count
        
        overall_score = sum(total_scores.values()) / len(total_scores) if total_scores else 7.0
        
        # Update PR with scores
        pr.correctness_score = total_scores.get("correctness", 7.0)
        pr.performance_score = total_scores.get("performance", 7.0)
        pr.readability_score = total_scores.get("readability", 7.0)
        pr.maintainability_score = total_scores.get("maintainability", 7.0)
        pr.overall_score = overall_score
        pr.status = ReviewStatus.COMPLETED
        pr.reviewed_at = datetime.utcnow()
        
        db.commit()
        
        # Post summary comment
        summary_result = {
            "scores": total_scores,
            "overall_score": overall_score,
            "total_issues": len(all_issues),
            "critical_issues": len([i for i in all_issues if i.get("severity") == "critical"]),
            "warnings": len([i for i in all_issues if i.get("severity") == "warning"]),
            "summary": f"Reviewed {file_count} files with {len(all_issues)} issues found."
        }
        
        summary_comment = review_service.generate_summary_comment(summary_result)
        github_service.post_review_summary(repo.full_name, pr.pr_number, summary_comment)
        
        return {
            "message": "Review completed",
            "pr_number": pr.pr_number,
            "issues_found": len(all_issues),
            "overall_score": overall_score
        }
    
    except Exception as e:
        pr.status = ReviewStatus.FAILED
        db.commit()
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")
