from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserCreate(BaseModel):
    github_id: int
    username: str
    email: Optional[str] = None
    access_token: str
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    github_id: int
    username: str
    email: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ManualReviewRequest(BaseModel):
    code: str
    language: str
    context: Optional[str] = None


class ManualReviewResponse(BaseModel):
    id: int
    status: str
    issues: List[Dict[str, Any]]
    scores: Dict[str, float]
    overall_score: float
    summary: str
    total_issues: int
    critical_issues: int
    warnings: int
    reviewed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    action: str
    pull_request: Dict[str, Any]
    repository: Dict[str, Any]


class ReviewCommentResponse(BaseModel):
    id: int
    file_path: str
    line_number: Optional[int]
    comment_text: str
    severity: str
    category: str
    confidence_score: Optional[float]
    
    class Config:
        from_attributes = True


class PullRequestResponse(BaseModel):
    id: int
    pr_number: int
    title: str
    author: str
    status: str
    overall_score: Optional[float]
    files_changed: int
    created_at: datetime
    reviewed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
