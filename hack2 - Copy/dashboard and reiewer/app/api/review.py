from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from app.db.session import get_db
from app.db.models import ManualReview, ReviewStatus
from app.api.schemas import ManualReviewRequest, ManualReviewResponse
from app.services.review_service import get_code_review_service
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/manual")
async def review_code_manually(request: ManualReviewRequest):
    """
    Manually review a code snippet
    
    This endpoint allows users to paste code and get an AI review
    without needing a GitHub PR.
    """
    try:
        # Perform review
        review_service = get_code_review_service()
        result = review_service.review_code(
            code=request.code,
            language=request.language,
            context=request.context
        )
        
        # Return results directly
        return {
            "id": 0,
            "status": "completed",
            "issues": result["issues"],
            "scores": result["scores"],
            "overall_score": result["overall_score"],
            "summary": result["summary"],
            "total_issues": result["total_issues"],
            "critical_issues": result["critical_issues"],
            "warnings": result["warnings"],
            "reviewed_at": datetime.utcnow()
        }
    
    except Exception as e:
        import traceback
        print(f"Review error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


@router.get("/manual/{review_id}", response_model=ManualReviewResponse)
async def get_manual_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Get a manual review by ID"""
    review = db.query(ManualReview).filter(ManualReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    result = json.loads(review.review_result) if review.review_result else {}
    
    return ManualReviewResponse(
        id=review.id,
        status=review.status.value,
        issues=result.get("issues", []),
        scores=result.get("scores", {}),
        overall_score=review.overall_score or 0.0,
        summary=result.get("summary", ""),
        total_issues=result.get("total_issues", 0),
        critical_issues=result.get("critical_issues", 0),
        warnings=result.get("warnings", 0),
        reviewed_at=review.reviewed_at
    )
