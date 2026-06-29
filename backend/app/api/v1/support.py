import hashlib
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.api.deps import get_db, get_current_user, get_current_ngo_user
from app.models.support import ForumPost, ForumReply
from app.models.user import User
from app.services.gemini_service import moderate_forum_post
from app.core.config import settings

router = APIRouter()

# ---------------------------------------------------------
# CRYPTOGRAPHIC ANONYMITY HELPER
# ---------------------------------------------------------
def generate_pseudonymous_hash(user_id: int) -> str:
    """Irreversibly hashes the user ID with a system secret."""
    raw = f"{user_id}:{settings.SECRET_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()

class ReplyCreate(BaseModel):
    content: str

class ReplyResponse(BaseModel):
    id: int
    content: str
    created_at: datetime

class PostCreate(BaseModel):
    title: str
    content: str
    category: str = "menstrual_health"

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    created_at: datetime
    replies: List[ReplyResponse] = []

@router.post("/posts", response_model=PostResponse)
async def create_anonymous_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Creates a new anonymous post and runs it through the AI Moderator."""
    is_crisis = await run_in_threadpool(moderate_forum_post, post_in.content)
    user = db.query(User).filter(User.username == current_user).first()
    
    new_post = ForumPost(
        author_hash=generate_pseudonymous_hash(user.id), # 🔥 Structurally Anonymized
        title=post_in.title,
        content=post_in.content,
        category=post_in.category,
        requires_human_review=is_crisis 
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return new_post

@router.get("/posts", response_model=List[PostResponse])
def get_safe_posts(
    category: str = "menstrual_health",
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Fetches all approved, non-crisis posts for the community feed."""
    posts = db.query(ForumPost).filter(
        ForumPost.category == category,
        ForumPost.requires_human_review == False 
    ).order_by(ForumPost.created_at.desc()).all()
    
    return posts

@router.post("/posts/{post_id}/replies", response_model=ReplyResponse)
async def create_reply(
    post_id: int,
    reply_in: ReplyCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Adds an anonymous reply to a specific post."""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    is_crisis = await run_in_threadpool(moderate_forum_post, reply_in.content)
    user = db.query(User).filter(User.username == current_user).first()
    
    new_reply = ForumReply(
        post_id=post_id,
        author_hash=generate_pseudonymous_hash(user.id), # 🔥 Structurally Anonymized
        content=reply_in.content,
        requires_human_review=is_crisis
    )
    
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    
    return new_reply

# ---------------------------------------------------------
# 🔥 NEW: MODERATION REVIEW QUEUE
# ---------------------------------------------------------
@router.get("/moderation/queue", response_model=List[PostResponse])
def get_flagged_posts(
    db: Session = Depends(get_db),
    ngo_user: User = Depends(get_current_ngo_user) # 🔒 Locked to NGOs only
):
    """
    [P1] Dashboard endpoint for human counsellors to review posts 
    that the AI flagged for self-harm, crisis, or abuse.
    """
    flagged_posts = db.query(ForumPost).filter(
        ForumPost.requires_human_review == True
    ).order_by(ForumPost.created_at.desc()).all()
    
    return flagged_posts