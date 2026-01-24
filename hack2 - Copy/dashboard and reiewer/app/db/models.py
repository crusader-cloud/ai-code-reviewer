from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class FeedbackType(enum.Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    CODE_CHANGED = "code_changed"
    IGNORED = "ignored"


class ReviewStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    access_token = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    repositories = relationship("Repository", back_populates="user")


class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    github_repo_id = Column(Integer, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)  # e.g., "owner/repo"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="repositories")
    pull_requests = relationship("PullRequest", back_populates="repository")


class PullRequest(Base):
    __tablename__ = "pull_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    github_pr_id = Column(Integer, index=True, nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    
    # Review scores
    correctness_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    readability_score = Column(Float, nullable=True)
    maintainability_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    
    # Metadata
    files_changed = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    repository = relationship("Repository", back_populates="pull_requests")
    comments = relationship("ReviewComment", back_populates="pull_request", cascade="all, delete-orphan")


class ReviewComment(Base):
    __tablename__ = "review_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    
    # GitHub comment details
    github_comment_id = Column(Integer, nullable=True, index=True)
    file_path = Column(String, nullable=False)
    line_number = Column(Integer, nullable=True)
    
    # Review content
    comment_text = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # critical, warning, suggestion, info
    category = Column(String, nullable=False)  # bug, performance, style, security, etc.
    
    # AI metadata
    confidence_score = Column(Float, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    pull_request = relationship("PullRequest", back_populates="comments")
    feedback = relationship("Feedback", back_populates="comment", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("review_comments.id"), nullable=False)
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    
    # Additional context
    user_comment = Column(Text, nullable=True)
    code_changed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    comment = relationship("ReviewComment", back_populates="feedback")


class ManualReview(Base):
    __tablename__ = "manual_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Code details
    code_snippet = Column(Text, nullable=False)
    language = Column(String, nullable=False)
    context = Column(Text, nullable=True)
    
    # Review results
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    review_result = Column(Text, nullable=True)  # JSON string with review details
    
    # Scores
    correctness_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    readability_score = Column(Float, nullable=True)
    maintainability_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
