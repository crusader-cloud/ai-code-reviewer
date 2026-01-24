from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import (
    PullRequest, ReviewComment, ManualReview, Repository, 
    User, Feedback, ReviewStatus, FeedbackType
)

router = APIRouter()


@router.get("/stats/overview")
async def get_overview_stats(db: Session = Depends(get_db)):
    """Get overall statistics for the dashboard"""
    
    # Total counts
    total_prs = db.query(PullRequest).count()
    total_manual_reviews = db.query(ManualReview).count()
    total_comments = db.query(ReviewComment).count()
    total_repos = db.query(Repository).filter(Repository.is_active == True).count()
    
    # Average scores
    avg_scores = db.query(
        func.avg(PullRequest.overall_score).label('overall'),
        func.avg(PullRequest.correctness_score).label('correctness'),
        func.avg(PullRequest.performance_score).label('performance'),
        func.avg(PullRequest.readability_score).label('readability'),
        func.avg(PullRequest.maintainability_score).label('maintainability')
    ).first()
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_prs = db.query(PullRequest).filter(
        PullRequest.created_at >= week_ago
    ).count()
    
    recent_reviews = db.query(ManualReview).filter(
        ManualReview.created_at >= week_ago
    ).count()
    
    # Issue severity breakdown
    critical_issues = db.query(ReviewComment).filter(
        ReviewComment.severity == 'critical'
    ).count()
    
    warnings = db.query(ReviewComment).filter(
        ReviewComment.severity == 'warning'
    ).count()
    
    suggestions = db.query(ReviewComment).filter(
        ReviewComment.severity == 'suggestion'
    ).count()
    
    return {
        "totals": {
            "pull_requests": total_prs,
            "manual_reviews": total_manual_reviews,
            "comments": total_comments,
            "active_repositories": total_repos
        },
        "average_scores": {
            "overall": round(avg_scores.overall or 0, 2),
            "correctness": round(avg_scores.correctness or 0, 2),
            "performance": round(avg_scores.performance or 0, 2),
            "readability": round(avg_scores.readability or 0, 2),
            "maintainability": round(avg_scores.maintainability or 0, 2)
        },
        "recent_activity": {
            "prs_last_7_days": recent_prs,
            "reviews_last_7_days": recent_reviews
        },
        "issue_breakdown": {
            "critical": critical_issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "info": total_comments - critical_issues - warnings - suggestions
        }
    }


@router.get("/stats/trends")
async def get_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get trends over time for charts"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily PR counts
    daily_prs = db.query(
        func.date(PullRequest.created_at).label('date'),
        func.count(PullRequest.id).label('count')
    ).filter(
        PullRequest.created_at >= start_date
    ).group_by(
        func.date(PullRequest.created_at)
    ).order_by('date').all()
    
    # Daily average scores
    daily_scores = db.query(
        func.date(PullRequest.created_at).label('date'),
        func.avg(PullRequest.overall_score).label('avg_score')
    ).filter(
        PullRequest.created_at >= start_date,
        PullRequest.overall_score.isnot(None)
    ).group_by(
        func.date(PullRequest.created_at)
    ).order_by('date').all()
    
    # Issue trends
    daily_issues = db.query(
        func.date(ReviewComment.created_at).label('date'),
        ReviewComment.severity,
        func.count(ReviewComment.id).label('count')
    ).filter(
        ReviewComment.created_at >= start_date
    ).group_by(
        func.date(ReviewComment.created_at),
        ReviewComment.severity
    ).order_by('date').all()
    
    return {
        "pr_activity": [
            {"date": str(item.date), "count": item.count}
            for item in daily_prs
        ],
        "score_trends": [
            {"date": str(item.date), "score": round(item.avg_score, 2)}
            for item in daily_scores
        ],
        "issue_trends": [
            {"date": str(item.date), "severity": item.severity, "count": item.count}
            for item in daily_issues
        ]
    }


@router.get("/stats/repositories")
async def get_repository_stats(db: Session = Depends(get_db)):
    """Get statistics per repository"""
    
    repos = db.query(Repository).filter(Repository.is_active == True).all()
    
    repo_stats = []
    for repo in repos:
        pr_count = db.query(PullRequest).filter(
            PullRequest.repository_id == repo.id
        ).count()
        
        avg_score = db.query(
            func.avg(PullRequest.overall_score)
        ).filter(
            PullRequest.repository_id == repo.id,
            PullRequest.overall_score.isnot(None)
        ).scalar()
        
        issue_count = db.query(ReviewComment).join(PullRequest).filter(
            PullRequest.repository_id == repo.id
        ).count()
        
        repo_stats.append({
            "id": repo.id,
            "name": repo.full_name,
            "pr_count": pr_count,
            "avg_score": round(avg_score or 0, 2),
            "issue_count": issue_count
        })
    
    return {"repositories": repo_stats}


@router.get("/stats/categories")
async def get_category_breakdown(db: Session = Depends(get_db)):
    """Get issue breakdown by category"""
    
    categories = db.query(
        ReviewComment.category,
        func.count(ReviewComment.id).label('count')
    ).group_by(
        ReviewComment.category
    ).order_by(
        desc('count')
    ).all()
    
    return {
        "categories": [
            {"name": cat.category, "count": cat.count}
            for cat in categories
        ]
    }


@router.get("/reviews/recent")
async def get_recent_reviews(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get recent PR reviews"""
    
    prs = db.query(PullRequest).order_by(
        desc(PullRequest.created_at)
    ).limit(limit).all()
    
    result = []
    for pr in prs:
        repo = db.query(Repository).filter(Repository.id == pr.repository_id).first()
        comment_count = db.query(ReviewComment).filter(
            ReviewComment.pull_request_id == pr.id
        ).count()
        
        result.append({
            "id": pr.id,
            "pr_number": pr.pr_number,
            "title": pr.title,
            "author": pr.author,
            "repository": repo.full_name if repo else "Unknown",
            "status": pr.status.value,
            "overall_score": pr.overall_score,
            "comment_count": comment_count,
            "created_at": pr.created_at.isoformat(),
            "reviewed_at": pr.reviewed_at.isoformat() if pr.reviewed_at else None
        })
    
    return {"reviews": result}


@router.get("/reviews/{pr_id}")
async def get_review_details(pr_id: int, db: Session = Depends(get_db)):
    """Get detailed review information for a specific PR"""
    
    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    
    repo = db.query(Repository).filter(Repository.id == pr.repository_id).first()
    
    comments = db.query(ReviewComment).filter(
        ReviewComment.pull_request_id == pr.id
    ).all()
    
    comment_list = []
    for comment in comments:
        feedback_count = db.query(Feedback).filter(
            Feedback.comment_id == comment.id
        ).count()
        
        comment_list.append({
            "id": comment.id,
            "file_path": comment.file_path,
            "line_number": comment.line_number,
            "severity": comment.severity,
            "category": comment.category,
            "comment_text": comment.comment_text,
            "confidence_score": comment.confidence_score,
            "suggested_fix": comment.suggested_fix,
            "feedback_count": feedback_count
        })
    
    return {
        "pr": {
            "id": pr.id,
            "pr_number": pr.pr_number,
            "title": pr.title,
            "author": pr.author,
            "repository": repo.full_name if repo else "Unknown",
            "status": pr.status.value,
            "scores": {
                "overall": pr.overall_score,
                "correctness": pr.correctness_score,
                "performance": pr.performance_score,
                "readability": pr.readability_score,
                "maintainability": pr.maintainability_score
            },
            "files_changed": pr.files_changed,
            "lines_added": pr.lines_added,
            "lines_deleted": pr.lines_deleted,
            "created_at": pr.created_at.isoformat(),
            "reviewed_at": pr.reviewed_at.isoformat() if pr.reviewed_at else None
        },
        "comments": comment_list
    }


@router.get("/manual-reviews/recent")
async def get_recent_manual_reviews(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get recent manual code reviews"""
    
    reviews = db.query(ManualReview).order_by(
        desc(ManualReview.created_at)
    ).limit(limit).all()
    
    result = []
    for review in reviews:
        result.append({
            "id": review.id,
            "language": review.language,
            "status": review.status.value,
            "overall_score": review.overall_score,
            "created_at": review.created_at.isoformat(),
            "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None
        })
    
    return {"reviews": result}


@router.get("/feedback/summary")
async def get_feedback_summary(db: Session = Depends(get_db)):
    """Get summary of user feedback on AI comments"""
    
    feedback_counts = db.query(
        Feedback.feedback_type,
        func.count(Feedback.id).label('count')
    ).group_by(
        Feedback.feedback_type
    ).all()
    
    total_feedback = sum(item.count for item in feedback_counts)
    
    return {
        "total_feedback": total_feedback,
        "breakdown": [
            {
                "type": item.feedback_type.value,
                "count": item.count,
                "percentage": round((item.count / total_feedback * 100) if total_feedback > 0 else 0, 1)
            }
            for item in feedback_counts
        ]
    }
