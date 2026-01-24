from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import webhook, review, auth, dashboard
from app.db.session import engine, Base
from app.core.config import get_settings

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI PR Reviewer",
    description="Automated Pull Request Reviewer powered by AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])
app.include_router(review.router, prefix="/review", tags=["Reviews"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI PR Reviewer API",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard.html",
        "endpoints": {
            "webhook": "/webhook/github",
            "manual_review": "/review/manual",
            "auth_login": "/auth/login",
            "dashboard_api": "/api/dashboard/stats/overview"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
