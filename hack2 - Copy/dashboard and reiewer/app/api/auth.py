from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from app.db.session import get_db
from app.db.models import User
from app.core.config import get_settings
from app.core.security import create_access_token

router = APIRouter()
settings = get_settings()


@router.get("/login")
async def github_login():
    """
    Initiate GitHub OAuth flow
    
    Redirects user to GitHub for authorization
    """
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.app_url}/auth/callback"
        f"&scope=repo,user:email"
    )
    return RedirectResponse(github_auth_url)


@router.get("/callback")
async def github_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    Handle GitHub OAuth callback
    
    Exchanges code for access token and creates/updates user
    """
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code
            }
        )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Get user info from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        
        user_data = user_response.json()
        
        # Create or update user
        user = db.query(User).filter(User.github_id == user_data["id"]).first()
        
        if user:
            user.access_token = access_token
            user.username = user_data["login"]
            user.email = user_data.get("email")
            user.avatar_url = user_data.get("avatar_url")
        else:
            user = User(
                github_id=user_data["id"],
                username=user_data["login"],
                email=user_data.get("email"),
                access_token=access_token,
                avatar_url=user_data.get("avatar_url")
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        jwt_token = create_access_token({"user_id": user.id, "github_id": user.github_id})
        
        # In a real app, you'd redirect to a frontend with the token
        # For now, return the token
        return {
            "message": "Authentication successful",
            "token": jwt_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url
            }
        }


@router.get("/user")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    # In a real app, you'd validate JWT from Authorization header
    # This is a simplified version
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract and validate token (simplified)
    from app.core.security import decode_access_token
    token = auth_header.replace("Bearer ", "")
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url
    }
